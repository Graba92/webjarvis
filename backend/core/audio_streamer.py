"""
backend/core/audio_streamer.py — SoundDevice Audio Engine für CachyOS / Linux (PipeWire).
- 16 kHz Mono Ingestion (Mikrofon)
- 24 kHz Mono Playback (Gemini Live Audio Synthesis)
- Sub-50ms Barge-In Interruption & RMS Pegelmessung für das Arc Reactor HUD
"""

from __future__ import annotations
import asyncio
import numpy as np
import sounddevice as sd
from typing import Callable, Optional

LEVEL_FLOOR = 60.0
LEVEL_FULL = 2600.0

def calculate_pcm_level(samples: np.ndarray) -> float:
    """Berechnet den normalisierten RMS-Pegel [0.0 - 1.0] für das Arc-Reactor-HUD."""
    if samples is None or len(samples) == 0:
        return 0.0
    try:
        rms = float(np.sqrt(np.mean(samples.astype(np.float32) ** 2)))
        clamped = max(LEVEL_FLOOR, min(LEVEL_FULL, rms))
        return (clamped - LEVEL_FLOOR) / (LEVEL_FULL - LEVEL_FLOOR)
    except Exception:
        return 0.0

class AudioStreamer:
    def __init__(self, input_rate: int = 16000, output_rate: int = 24000, chunk_size: int = 1024):
        self.input_rate = input_rate
        self.output_rate = output_rate
        self.chunk_size = chunk_size

        self.audio_in_queue: asyncio.Queue[bytes] = asyncio.Queue()
        self.audio_out_queue: asyncio.Queue[bytes] = asyncio.Queue()

        self._in_stream: Optional[sd.InputStream] = None
        self._out_stream: Optional[sd.RawOutputStream] = None
        self._is_speaking = False
        self._is_listening = True
        self._muted = False

        self.on_level_change: Optional[Callable[[float], None]] = None
        self.on_log: Optional[Callable[[str], None]] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    def set_speaking(self, speaking: bool):
        self._is_speaking = speaking

    def set_muted(self, muted: bool):
        self._muted = muted

    def is_speaking(self) -> bool:
        return self._is_speaking

    def is_muted(self) -> bool:
        return self._muted

    def start_input(self):
        if self._in_stream is not None:
            return

        def _mic_callback(indata, frames, time_info, status):
            if self._muted or self._is_speaking:
                return
            pcm_bytes = indata.tobytes()
            if self._loop and not self._loop.is_closed():
                self._loop.call_soon_threadsafe(self.audio_out_queue.put_nowait, pcm_bytes)
            # Pegelmessung für HUD
            if self.on_level_change:
                level = calculate_pcm_level(np.frombuffer(pcm_bytes, dtype=np.int16))
                self.on_level_change(level)

        try:
            self._in_stream = sd.InputStream(
                samplerate=self.input_rate,
                channels=1,
                dtype="int16",
                blocksize=self.chunk_size,
                callback=_mic_callback
            )
            self._in_stream.start()
            if self.on_log:
                self.on_log("SYS: Mikrofon-Stream (16 kHz) aktiv.")
        except Exception as e:
            if self.on_log:
                self.on_log(f"WARN: Lokales Mikrofon konnte nicht geöffnet werden: {e}")

    def start_output(self):
        if self._out_stream is not None:
            return
        try:
            self._out_stream = sd.RawOutputStream(
                samplerate=self.output_rate,
                channels=1,
                dtype="int16",
                blocksize=self.chunk_size
            )
            self._out_stream.start()
            if self.on_log:
                self.on_log("SYS: Lautsprecher-Stream (24 kHz) aktiv.")
        except Exception as e:
            if self.on_log:
                self.on_log(f"WARN: Lautsprecher konnte nicht geöffnet werden: {e}")

    async def play_audio_worker(self):
        """Spielt eingehende Gemini-Audiosamples kontinuierlich ab."""
        while True:
            try:
                chunk = await self.audio_in_queue.get()
                self._is_speaking = True
                
                # Pegelmessung während Jarvis spricht
                if self.on_level_change:
                    level = calculate_pcm_level(np.frombuffer(chunk, dtype=np.int16))
                    self.on_level_change(level)

                if self._out_stream and self._out_stream.active:
                    await asyncio.to_thread(self._out_stream.write, chunk)
                else:
                    await asyncio.sleep(len(chunk) / (self.output_rate * 2))
            except asyncio.CancelledError:
                break
            except Exception as e:
                await asyncio.sleep(0.05)
            finally:
                if self.audio_in_queue.empty():
                    self._is_speaking = False

    def interrupt(self):
        """Barge-In: Entleert sofort alle Audio-Queues und stoppt Sprachausgabe."""
        drained = 0
        while not self.audio_in_queue.empty():
            try:
                self.audio_in_queue.get_nowait()
                drained += 1
            except Exception:
                break
        self._is_speaking = False
        if self.on_level_change:
            self.on_level_change(0.0)
        if self.on_log and drained > 0:
            self.on_log(f"SYS: Barge-In Unterbrechung ({drained} Pufferpakete verworfen).")

    def stop(self):
        if self._in_stream:
            try:
                self._in_stream.stop()
                self._in_stream.close()
            except Exception:
                pass
            self._in_stream = None
        if self._out_stream:
            try:
                self._out_stream.stop()
                self._out_stream.close()
            except Exception:
                pass
            self._out_stream = None
