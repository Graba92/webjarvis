"""
backend/core/gemini_live.py — Gemini Live WebSocket Client mit Vollduplex-Audio & Tool-Routing.
Verwendet das offizielle google-genai SDK (models/gemini-3.1-flash-live-preview).
Unterstützt dynamische API-Key-Aktualisierung, automatische Session-Resumption und
robuste Reconnection bei Session-Timeouts (Code 1008 / GoAway).
"""

from __future__ import annotations
import asyncio
import traceback
from datetime import datetime
from typing import Callable, Optional
from google import genai
from google.genai import types
from google.genai import errors
import websockets.exceptions

from core.config import (
    get_gemini_api_key, LIVE_MODEL, VOICE_NAME, SYSTEM_PROMPT,
    load_soul_instructions, load_memory_md_content, load_heartbeat_checklist
)
from core.action_loader import ActionRegistry
from memory.memory_manager import load_memory, format_memory_for_prompt
from core.audio_streamer import AudioStreamer

class GeminiLiveController:
    def __init__(self, action_registry: ActionRegistry, audio_streamer: AudioStreamer, broadcast_cb: Callable[[dict], None]):
        self.registry = action_registry
        self.audio = audio_streamer
        self.broadcast = broadcast_cb

        self.session = None
        self._running = False
        self._interrupted = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._tasks: list[asyncio.Task] = []
        self._key_event = asyncio.Event()
        self._resumption_handle: Optional[str] = None

    def log(self, text: str, speaker: str = "SYS"):
        self.broadcast({
            "type": "log",
            "speaker": speaker,
            "text": text,
            "ts": datetime.now().strftime("%H:%M:%S")
        })

    def set_state(self, state: str):
        self.broadcast({
            "type": "state",
            "state": state
        })

    def notify_key_updated(self):
        """Wird aufgerufen wenn ein neuer API-Key via WebSocket oder Terminal übergeben wird."""
        self._resumption_handle = None
        if self._key_event:
            self._key_event.set()
        for t in self._tasks:
            t.cancel()

    def _build_config(self, resumption_handle: Optional[str] = None) -> types.LiveConnectConfig:
        memory = load_memory()
        mem_str = format_memory_for_prompt(memory)
        now_str = datetime.now().strftime("%A, %d. %B %Y — %H:%M:%S")

        soul_str = load_soul_instructions()
        mem_md = load_memory_md_content()
        heartbeat_checklist = load_heartbeat_checklist()

        prompt_parts = [
            f"[SYSTEM TIME]\nAktuelle Uhrzeit & Datum: {now_str}\n",
            f"[J.A.R.V.I.S. SOUL & PERSONA DIRECTIVES]\n{soul_str}\n" if soul_str else "",
            f"[J.A.R.V.I.S. PERSISTENT LONG-TERM MEMORY]\n{mem_md}\n" if mem_md else "",
            f"[HEARTBEAT CHECKLIST]\n{heartbeat_checklist}\n" if heartbeat_checklist else "",
            mem_str,
            SYSTEM_PROMPT
        ]

        tools_declarations = self.registry.get_tool_declarations()

        resumption_cfg = (
            types.SessionResumptionConfig(handle=resumption_handle)
            if resumption_handle
            else types.SessionResumptionConfig()
        )

        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE_NAME)
                )
            ),
            output_audio_transcription={},
            input_audio_transcription={},
            system_instruction="\n".join(filter(None, prompt_parts)),
            tools=[{"function_declarations": tools_declarations}],
            session_resumption=resumption_cfg,
            context_window_compression=types.ContextWindowCompressionConfig(
                sliding_window=types.SlidingWindow()
            )
        )

    async def run(self):
        self._loop = asyncio.get_running_loop()
        self.audio.set_loop(self._loop)
        self._running = True

        # Der Playback-Worker läuft über den gesamten Controller-Lebenszyklus,
        # damit die SoundDevice-/PipeWire-Audio-Engine bei Reconnects nicht abreißt.
        play_worker_task = asyncio.create_task(self.audio.play_audio_worker())

        try:
            while self._running:
                api_key = get_gemini_api_key()
                if not api_key:
                    self.log("Kein GEMINI_API_KEY konfiguriert. Bitte Key im HUD (Schlüssel-Symbol) oder Terminal eingeben.", "SYS")
                    self.set_state("NO_API_KEY")
                    self._key_event.clear()
                    try:
                        await self._key_event.wait()
                    except asyncio.CancelledError:
                        break
                    continue

                try:
                    if self._resumption_handle:
                        self.log("Stelle Verbindung mit Session-Resumption wieder her...", "SYS")
                        self.set_state("RECONNECTING")
                    else:
                        self.log("Verbinde mit Gemini Live API...", "SYS")
                        self.set_state("CONNECTING")

                    client = genai.Client(api_key=api_key, http_options={"api_version": "v1alpha"})
                    config = self._build_config(self._resumption_handle)

                    async with client.aio.live.connect(model=LIVE_MODEL, config=config) as session:
                        self.session = session
                        if self._resumption_handle:
                            self.log(f"Live-Sitzung nahtlos fortgesetzt ({LIVE_MODEL}).", "SYS")
                        else:
                            self.log(f"Live-Sitzung etabliert ({LIVE_MODEL} / Stimme: {VOICE_NAME}).", "SYS")
                        self.set_state("ONLINE")

                        # Hintergrund-Tasks für diese Session
                        t_send = asyncio.create_task(self._send_audio_loop())
                        t_recv = asyncio.create_task(self._receive_loop())
                        self._tasks = [t_send, t_recv]

                        # Sobald entweder t_send oder t_recv endet (z. B. durch GoAway oder Code 1008),
                        # beenden wir die Session kontrolliert für den Reconnect.
                        done, pending = await asyncio.wait(
                            [t_send, t_recv],
                            return_when=asyncio.FIRST_COMPLETED
                        )
                        for t in pending:
                            t.cancel()
                            try:
                                await t
                            except (asyncio.CancelledError, Exception):
                                pass

                        self.session = None

                    # Kurze Pause vor Neuaufbau, wenn die Schleife weiterläuft
                    if self._running:
                        self.set_state("RECONNECTING")
                        await asyncio.sleep(0.1)

                except asyncio.CancelledError:
                    break
                except (errors.APIError, websockets.exceptions.ConnectionClosed, websockets.exceptions.ConnectionClosedError, websockets.exceptions.ConnectionClosedOK) as conn_err:
                    code = getattr(conn_err, "code", None)
                    self.session = None
                    self.set_state("RECONNECTING")
                    if code == 1008 or "1008" in str(conn_err):
                        self.log("Gemini Live Session-Zeitlimit erreicht (Code 1008). Starte nahtlosen Reconnect...", "SYS")
                    else:
                        self.log(f"Gemini Live Verbindung getrennt ({conn_err.__class__.__name__}{f' Code {code}' if code else ''}). Starte Reconnect...", "SYS")

                    # Falls Resumption mit dem gespeicherten Handle fehlschlug,
                    # Handle zurücksetzen, um frische Basissitzung aufzubauen.
                    if self._resumption_handle:
                        self._resumption_handle = None
                        await asyncio.sleep(0.3)
                    else:
                        await asyncio.sleep(1.0)

                except Exception as e:
                    self.session = None
                    self._resumption_handle = None
                    self.log(f"Gemini Live Verbindungsfehler: {e}", "ERR")
                    self.set_state("ERROR")
                    traceback.print_exc()
                    await asyncio.sleep(2.0)

        finally:
            play_worker_task.cancel()
            try:
                await play_worker_task
            except (asyncio.CancelledError, Exception):
                pass
            self.stop()

    async def _send_audio_loop(self):
        """Sendet Mikrofon-PCM-Frames kontinuierlich an Gemini."""
        while self._running and self.session:
            try:
                pcm_data = await self.audio.audio_out_queue.get()
                if not self.audio.is_muted() and not self.audio.is_speaking():
                    await self.session.send_realtime_input(
                        audio=types.Blob(data=pcm_data, mime_type="audio/pcm")
                    )
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(0.01)

    async def _receive_loop(self):
        """Empfängt Audio-, Transkriptions- und Tool-Call-Events von Gemini."""
        in_transcript = []
        out_transcript = []

        while self._running and self.session:
            try:
                async for response in self.session.receive():
                    # 0. Session-Resumption und GoAway Signale auswerten
                    if response.session_resumption_update:
                        upd = response.session_resumption_update
                        if upd.new_handle:
                            self._resumption_handle = upd.new_handle

                    if response.go_away:
                        time_left = getattr(response.go_away, "time_left", "unbekannt")
                        self.log(f"Google GoAway-Signal empfangen (Verbleibende Zeit: {time_left}). Bereite Session-Resumption vor.", "SYS")

                    server_content = response.server_content
                    if server_content is not None:
                        model_turn = server_content.model_turn
                        if model_turn is not None:
                            for part in model_turn.parts:
                                # 1. Audio-Daten empfangen & lokal abspielen
                                # Hinweis: Keine Roh-Audiodaten an den Browser senden!
                                # Das Python-Backend bleibt die einzige Ausgabestelle via PipeWire/SoundDevice.
                                if part.inline_data and part.inline_data.data:
                                    raw_audio = part.inline_data.data
                                    if not self._interrupted:
                                        await self.audio.audio_in_queue.put(raw_audio)
                                        self.set_state("SPEAKING")

                                # 2. Transkription empfangen
                                if part.text:
                                    out_transcript.append(part.text)

                        # Nutzer-Sprachtranskription
                        if server_content.input_transcription and server_content.input_transcription.text:
                            txt = server_content.input_transcription.text.strip()
                            if txt:
                                in_transcript.append(txt)

                        # Turn abgeschlossen
                        if server_content.turn_complete:
                            if self._interrupted:
                                self._interrupted = False
                                in_transcript.clear()
                                out_transcript.clear()
                                self.set_state("LISTENING")
                                continue

                            full_user = " ".join(in_transcript).strip()
                            if full_user:
                                self.log(full_user, "YOU")
                                in_transcript.clear()

                            full_ai = " ".join(out_transcript).strip()
                            if full_ai:
                                self.log(full_ai, "JARVIS")
                                out_transcript.clear()

                            self.set_state("ONLINE")

                    # 3. Tool Calls verarbeiten
                    if response.tool_call:
                        self.set_state("THINKING")
                        fn_responses = []
                        for fc in response.tool_call.function_calls:
                            name = fc.name
                            args = fc.args or {}
                            self.log(f"Tool-Aufruf: {name}({args})", "SYS")
                            # Tool ausführen
                            ctx = {
                                "speak": self.send_text_prompt,
                                "ws_broadcast": self.broadcast,
                                "registry": self.registry
                            }
                            res_str = await asyncio.to_thread(self.registry.run, name, args, ctx)
                            self.log(f"Tool-Antwort ({name}): {res_str[:120]}", "SYS")
                            fn_responses.append(types.FunctionResponse(
                                id=fc.id,
                                name=name,
                                response={"result": res_str}
                            ))
                        await self.session.send_tool_response(function_responses=fn_responses)
                        self.set_state("ONLINE")

            except asyncio.CancelledError:
                break
            except (errors.APIError, websockets.exceptions.ConnectionClosed, websockets.exceptions.ConnectionClosedError, websockets.exceptions.ConnectionClosedOK) as e:
                code = getattr(e, "code", None)
                if code == 1008 or "1008" in str(e):
                    self.log("Gemini Live Session-Timeout (Code 1008 / GoAway) sauber abgefangen. Starte Resumption...", "SYS")
                else:
                    self.log(f"Live Stream getrennt ({e.__class__.__name__}{f' Code {code}' if code else ''}). Reconnect...", "SYS")
                break
            except Exception as e:
                self.log(f"Empfangsfehler im WebSocket-Stream: {e}", "ERR")
                traceback.print_exc()
                break

    async def send_text_prompt(self, text: str):
        """Sendet einen Textbefehl in die Live-Session."""
        if not self.session:
            self.log(f"Befehl nicht gesendet (keine aktive Session): {text}", "ERR")
            return
        try:
            self.log(text, "YOU")
            self.set_state("THINKING")
            await self.session.send_client_content(
                turns={"role": "user", "parts": [{"text": text}]},
                turn_complete=True
            )
        except Exception as e:
            self.log(f"Fehler beim Senden des Textbefehls: {e}", "ERR")

    def interrupt(self):
        """Unterbricht die Sprachausgabe von Jarvis blitzschnell."""
        self._interrupted = True
        self.audio.interrupt()
        self.set_state("LISTENING")
        self.log("Barge-In: Sprachausgabe gestoppt.", "SYS")

    def stop(self):
        self._running = False
        self._resumption_handle = None
        self._key_event.set()
        for t in self._tasks:
            t.cancel()
        self.audio.stop()
