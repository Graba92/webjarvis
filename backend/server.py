"""
backend/server.py — Zentraler WebSocket & Telemetrie-Bridge-Server.
Verbindet das Python Gemini Live Backend direkt mit dem Next.js 15 / Three.js Frontend.
"""

from __future__ import annotations
import asyncio
import json
import base64
import sys
from pathlib import Path

# Sicherstellen, dass das backend-Verzeichnis im sys.path liegt
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import websockets
from core.config import (
    WS_HOST, WS_PORT, AUDIO_SAMPLE_RATE_INPUT, AUDIO_SAMPLE_RATE_OUTPUT,
    USER_NAME, save_gemini_api_key, is_api_key_configured, get_masked_api_key, get_gemini_api_key
)
from core.action_loader import discover_actions
from core.audio_streamer import AudioStreamer
from core.gemini_live import GeminiLiveController
import core.confirm as confirm_gate
import core.undo as undo_stack
import subprocess
import shutil
from actions.system_monitor import get_system_telemetry
from memory.memory_manager import all_entries_for_ui
from actions.graph_manager import (
    get_full_graph_data, find_node_by_id, add_node_internal, delete_node_internal
)
from actions.open_app import open_app

CONNECTED_CLIENTS: set[websockets.WebSocketServerProtocol] = set()
MAIN_LOOP: Optional[asyncio.AbstractEventLoop] = None

def set_main_loop(loop: asyncio.AbstractEventLoop):
    global MAIN_LOOP
    MAIN_LOOP = loop

async def _safe_send(ws, msg: str):
    try:
        await ws.send(msg)
    except Exception:
        pass

def broadcast(payload: dict):
    if not CONNECTED_CLIENTS:
        return
    msg = json.dumps(payload, ensure_ascii=False)

    def _send_all():
        for ws in list(CONNECTED_CLIENTS):
            asyncio.create_task(_safe_send(ws, msg))

    if MAIN_LOOP and MAIN_LOOP.is_running():
        try:
            current_loop = asyncio.get_running_loop()
            if current_loop == MAIN_LOOP:
                _send_all()
            else:
                MAIN_LOOP.call_soon_threadsafe(_send_all)
        except RuntimeError:
            MAIN_LOOP.call_soon_threadsafe(_send_all)
    else:
        try:
            _send_all()
        except Exception:
            pass

class JarvisServer:
    def __init__(self):
        self.actions_dir = BACKEND_DIR / "actions"
        self.registry = discover_actions(self.actions_dir, logger=self._log)
        self.audio = AudioStreamer(
            input_rate=AUDIO_SAMPLE_RATE_INPUT,
            output_rate=AUDIO_SAMPLE_RATE_OUTPUT
        )
        self.audio.on_level_change = self._on_audio_level
        self.audio.on_log = lambda msg: self.log(msg, "SYS")

        self.controller = GeminiLiveController(
            action_registry=self.registry,
            audio_streamer=self.audio,
            broadcast_cb=broadcast
        )

        # Proaktive Cron-Engine für Heartbeat & autonome Hintergrund-Checks
        from core.cron_engine import CronEngine
        self.cron_engine = CronEngine(broadcast_fn=broadcast, logger=self._log)

        # Confirmation Gate an WebSockets anbinden
        confirm_gate.bind(
            show=self._show_confirm,
            hide=self._hide_confirm,
            log=lambda m: self.log(m, "SYS")
        )

    def _log(self, msg: str):
        print(f"[JarvisServer] {msg}")

    def log(self, text: str, speaker: str = "SYS"):
        self.controller.log(text, speaker)

    def _on_audio_level(self, level: float):
        # Broadcastet den gemessenen Audiopegel an das Frontend für die 60 FPS Reaktor-Visualisierung
        lvl = round(level, 4)
        broadcast({"type": "audio_rms", "level": lvl})
        broadcast({"type": "audio_level", "level": lvl})

    def _show_confirm(self, action: str, label: str, detail: str, timeout: int = 90):
        self._log(f"[SAFETY GATE BROADCAST] Sende confirm_request an Frontend: action='{action}', label='{label}', timeout={timeout}s")
        broadcast({
            "type": "confirm_request",
            "action": action,
            "key": action,
            "label": label,
            "title": label,
            "detail": detail,
            "timeout": timeout
        })

    def _hide_confirm(self):
        self._log("[SAFETY GATE BROADCAST] Sende confirm_hide an Frontend")
        broadcast({"type": "confirm_hide"})

    async def telemetry_loop(self):
        """Sendet 1 Hz Systemmetriken an das Next.js Frontend."""
        while True:
            try:
                if CONNECTED_CLIENTS:
                    telemetry = get_system_telemetry()
                    broadcast({
                        "type": "telemetry",
                        "data": telemetry,
                        "can_undo": undo_stack.can_undo(),
                        "undo_peek": undo_stack.peek(),
                        "actions": list(self.registry.names())
                    })
                await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                await asyncio.sleep(2.0)

    async def handle_client(self, websocket: websockets.WebSocketServerProtocol):
        CONNECTED_CLIENTS.add(websocket)
        self._log(f"Frontend Client verbunden ({websocket.remote_address})")

        # Initialer Begrüßungszustand
        pending = confirm_gate.pending_info()
        mcp_file = BACKEND_DIR / "config" / "mcp_servers.json"
        mcp_servers = {}
        if mcp_file.exists():
            try:
                mcp_servers = json.loads(mcp_file.read_text(encoding="utf-8")).get("mcpServers", {})
            except Exception:
                pass

        welcome_payload = {
            "type": "init",
            "state": "ONLINE",
            "actions": list(self.registry.names()),
            "telemetry": get_system_telemetry(),
            "can_undo": undo_stack.can_undo(),
            "undo_peek": undo_stack.peek(),
            "pending_confirm": pending,
            "memory": all_entries_for_ui(),
            "is_muted": self.audio.is_muted(),
            "mic_active": not self.audio.is_muted(),
            "api_key_status": {
                "configured": is_api_key_configured(),
                "masked_key": get_masked_api_key()
            },
            "graph_data": get_full_graph_data(),
            "mcp_servers": mcp_servers
        }
        await websocket.send(json.dumps(welcome_payload))

        try:
            async for raw_message in websocket:
                try:
                    data = json.loads(raw_message)
                except Exception:
                    continue

                msg_type = data.get("type")

                if msg_type == "text_command":
                    text = data.get("text", "").strip()
                    source = data.get("source")
                    sender = data.get("sender")
                    is_self = data.get("is_self", False)
                    if text:
                        if source == "whatsapp":
                            clean_s = str(sender or "").replace("+", "").strip()
                            sender_display = sender
                            contacts_file = BACKEND_DIR / "config" / "contacts.json"
                            if not contacts_file.exists():
                                contacts_file = BACKEND_DIR / "config" / "contacts.example.json"
                            if contacts_file.exists():
                                try:
                                    cd = json.loads(contacts_file.read_text(encoding="utf-8"))
                                    known = cd.get("contacts", {})
                                    if clean_s in known:
                                        sender_display = f"{known[clean_s]} ({sender})"
                                except Exception:
                                    pass

                            context_info = f"Notiz an mich selbst / WhatsApp-Befehl von {USER_NAME}" if is_self else f"Eingehende WhatsApp von {sender_display}"
                            prompt = f"[{context_info}]: {text}\n(Hinweis: Du kannst bei Bedarf per send_whatsapp(recipient='{sender}', message=...) direkt per WhatsApp auf das Smartphone antworten.)"
                            await self.controller.send_text_prompt(prompt)
                        else:
                            await self.controller.send_text_prompt(text)

                elif msg_type == "interrupt":
                    self.controller.interrupt()

                elif msg_type == "toggle_mic":
                    # Steuersignal vom Frontend (Handsfree/Ohr-Button)
                    active = data.get("active")
                    if active is None:
                        new_muted = not self.audio.is_muted()
                    else:
                        new_muted = not bool(active)
                    self.audio.set_muted(new_muted)
                    broadcast({"type": "mute_state", "muted": new_muted, "active": not new_muted})
                    self.log(f"Mikrofon {'aktiviert' if not new_muted else 'stummgeschaltet'}.", "SYS")

                elif msg_type == "mute_toggle":
                    current = self.audio.is_muted()
                    new_muted = not current
                    self.audio.set_muted(new_muted)
                    broadcast({"type": "mute_state", "muted": new_muted, "active": not new_muted})
                    self.log(f"Mikrofon {'stummgeschaltet' if new_muted else 'aktiviert'}.", "SYS")

                elif msg_type == "confirm_resolve":
                    accepted = bool(data.get("accepted", False))
                    self._log(f"[SAFETY GATE RESOLVE] Rückmeldung vom Frontend: accepted={accepted}")
                    executed = confirm_gate.resolve(accepted)
                    broadcast({
                        "type": "confirm_resolved",
                        "accepted": accepted,
                        "executed": executed
                    })
                    if accepted:
                        self.log("Sicherheitsfreigabe erteilt. Befehl wird ausgeführt.", "SYS")
                    else:
                        self.log("Sicherheitsfreigabe abgebrochen durch Benutzer.", "SYS")

                elif msg_type == "undo":
                    res = undo_stack.undo_last()
                    self.log(res, "SYS")
                    broadcast({"type": "undo_executed", "result": res})

                elif msg_type == "trigger_tool":
                    tool_name = data.get("tool")
                    params = data.get("params", {})
                    if self.registry.has(tool_name):
                        ctx = {"speak": self.controller.send_text_prompt, "ws_broadcast": broadcast}
                        res = await asyncio.to_thread(self.registry.run, tool_name, params, ctx)
                        self.log(f"Manuelle Ausführung von '{tool_name}': {res}", "SYS")

                elif msg_type == "get_memory":
                    await websocket.send(json.dumps({
                        "type": "memory_data",
                        "memory": all_entries_for_ui()
                    }))

                elif msg_type == "get_api_key_status":
                    await websocket.send(json.dumps({
                        "type": "api_key_status",
                        "configured": is_api_key_configured(),
                        "masked_key": get_masked_api_key()
                    }))

                elif msg_type == "set_api_key":
                    new_key = str(data.get("key", "")).strip()
                    if new_key:
                        save_gemini_api_key(new_key)
                        self.controller.notify_key_updated()
                        broadcast({
                            "type": "api_key_status",
                            "configured": True,
                            "masked_key": get_masked_api_key()
                        })
                        self.log(f"GEMINI_API_KEY erfolgreich aktualisiert ({get_masked_api_key()}). Live-Sitzung wird initialisiert...", "SYS")

                elif msg_type == "get_mcp_servers":
                    mcp_file = BACKEND_DIR / "config" / "mcp_servers.json"
                    servers = {}
                    if mcp_file.exists():
                        try:
                            servers = json.loads(mcp_file.read_text(encoding="utf-8")).get("mcpServers", {})
                        except Exception:
                            pass
                    await websocket.send(json.dumps({
                        "type": "mcp_servers_data",
                        "servers": servers
                    }))

                elif msg_type == "toggle_mcp_server":
                    server_id = str(data.get("id", "")).strip()
                    enabled = bool(data.get("enabled", False))
                    mcp_file = BACKEND_DIR / "config" / "mcp_servers.json"
                    if mcp_file.exists() and server_id:
                        try:
                            content = json.loads(mcp_file.read_text(encoding="utf-8"))
                            if server_id in content.get("mcpServers", {}):
                                content["mcpServers"][server_id]["enabled"] = enabled
                                mcp_file.write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")
                                broadcast({
                                    "type": "mcp_servers_data",
                                    "servers": content.get("mcpServers", {})
                                })
                                status_str = "aktiviert" if enabled else "deaktiviert"
                                self.log(f"MCP-Skill '{server_id}' {status_str}.", "SYS")
                        except Exception as e:
                            self.log(f"Fehler beim Umschalten von MCP-Skill '{server_id}': {e}", "ERR")

                elif msg_type == "save_mcp_server":
                    server_id = str(data.get("id", "")).strip().lower().replace(" ", "_")
                    server_cfg = data.get("config", {})
                    mcp_file = BACKEND_DIR / "config" / "mcp_servers.json"
                    if server_id and server_cfg:
                        try:
                            content = {"mcpServers": {}}
                            if mcp_file.exists():
                                content = json.loads(mcp_file.read_text(encoding="utf-8"))
                            content.setdefault("mcpServers", {})[server_id] = server_cfg
                            mcp_file.write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")
                            broadcast({
                                "type": "mcp_servers_data",
                                "servers": content.get("mcpServers", {})
                            })
                            self.log(f"MCP-Skill '{server_id}' erfolgreich gespeichert.", "SYS")
                        except Exception as e:
                            self.log(f"Fehler beim Speichern von MCP-Skill '{server_id}': {e}", "ERR")

                elif msg_type == "delete_mcp_server":
                    server_id = str(data.get("id", "")).strip()
                    mcp_file = BACKEND_DIR / "config" / "mcp_servers.json"
                    if mcp_file.exists() and server_id:
                        try:
                            content = json.loads(mcp_file.read_text(encoding="utf-8"))
                            if server_id in content.get("mcpServers", {}):
                                del content["mcpServers"][server_id]
                                mcp_file.write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")
                                broadcast({
                                    "type": "mcp_servers_data",
                                    "servers": content.get("mcpServers", {})
                                })
                                self.log(f"MCP-Skill '{server_id}' gelöscht.", "SYS")
                        except Exception as e:
                            self.log(f"Fehler beim Löschen von MCP-Skill '{server_id}': {e}", "ERR")

                elif msg_type == "execute_node_action":
                    node_id = str(data.get("node_id", "")).strip()
                    path_val = str(data.get("path", "")).strip()
                    category = str(data.get("category", "")).strip()
                    action = str(data.get("action", "open")).strip().lower()

                    node = find_node_by_id(node_id) or {}
                    node_name = node.get("name", node_id)
                    target_path = path_val or node.get("path", "")
                    node_desc = node.get("description", "")
                    node_cat = category or node.get("category", "")

                    if action == "terminal":
                        workdir = BACKEND_DIR.parent
                        if target_path:
                            p = Path(target_path)
                            if not p.is_absolute():
                                p = (BACKEND_DIR.parent / target_path).resolve()
                            if p.is_dir():
                                workdir = p
                            elif p.is_file():
                                workdir = p.parent

                        term_cmd = None
                        if shutil.which("konsole"):
                            term_cmd = ["konsole", "--workdir", str(workdir)]
                        elif shutil.which("alacritty"):
                            term_cmd = ["alacritty", "--working-directory", str(workdir)]
                        elif shutil.which("xdg-terminal-exec"):
                            term_cmd = ["xdg-terminal-exec"]

                        if term_cmd:
                            subprocess.Popen(term_cmd, start_new_session=True)
                            self.log(f"Terminal in '{workdir}' geöffnet für '{node_name}'.", "SYS")
                        else:
                            self.log(f"Konnte keinen Terminal-Emulator im PATH finden.", "ERR")

                    elif action == "open":
                        if target_path.startswith("http://") or target_path.startswith("https://"):
                            opener = shutil.which("xdg-open") or shutil.which("brave") or shutil.which("firefox")
                            if opener:
                                subprocess.Popen([opener, target_path], start_new_session=True)
                                self.log(f"Webseite '{target_path}' geöffnet ({node_name}).", "SYS")
                        elif target_path:
                            p = Path(target_path)
                            if not p.is_absolute():
                                p = (BACKEND_DIR.parent / target_path).resolve()

                            if p.exists():
                                if p.is_dir():
                                    fm = shutil.which("dolphin") or shutil.which("xdg-open")
                                    if fm:
                                        subprocess.Popen([fm, str(p)], start_new_session=True)
                                        self.log(f"Ordner '{p.name}' im Dateimanager geöffnet.", "SYS")
                                else:
                                    editor = shutil.which("kate") or shutil.which("xdg-open")
                                    if editor:
                                        subprocess.Popen([editor, str(p)], start_new_session=True)
                                        self.log(f"Datei '{p.name}' im Editor geöffnet.", "SYS")
                            else:
                                res = open_app({"app_name": target_path or node_name})
                                self.log(f"Anwendungs-Start für '{node_name}': {res}", "SYS")
                        else:
                            res = open_app({"app_name": node_name})
                            self.log(f"Anwendungs-Start für '{node_name}': {res}", "SYS")

                    elif action == "summarize":
                        prompt = (
                            f"Bitte fasse den Knoten '{node_name}' aus dem interaktiven 3D-Knotengraphen präzise zusammen.\n"
                            f"Kategorie: {node_cat}\n"
                            f"Beschreibung: {node_desc}\n"
                            f"Pfad: {target_path or 'Nicht hinterlegt'}\n"
                            f"Erläutere dessen Systemfunktion, Status und empfohlene nächste Aktionen."
                        )
                        await self.controller.send_text_prompt(prompt)
                        self.log(f"Zusammenfassungs-Anfrage für '{node_name}' an Jarvis übermittelt.", "SYS")

                    elif action == "delete":
                        ok, msg = delete_node_internal(node_id, broadcast_fn=broadcast)
                        self.log(msg, "SYS" if ok else "ERR")

                elif msg_type == "get_graph":
                    await websocket.send(json.dumps({
                        "type": "graph_sync",
                        "data": get_full_graph_data()
                    }))

                elif msg_type == "add_node":
                    title = str(data.get("title", "")).strip()
                    category = str(data.get("category", "Notes")).strip()
                    content = str(data.get("content", "")).strip()
                    linked_to = str(data.get("linked_to", "")).strip()
                    path_v = str(data.get("path", "")).strip()
                    conn = int(data.get("connections", 1))
                    if title:
                        new_node, msg = add_node_internal(
                            title=title,
                            category=category,
                            content=content,
                            connections=conn,
                            linked_to=linked_to,
                            path=path_v,
                            broadcast_fn=broadcast
                        )
                        self.log(msg, "SYS")

                elif msg_type == "delete_node":
                    nid = str(data.get("node_id", "")).strip()
                    if nid:
                        ok, msg = delete_node_internal(nid, broadcast_fn=broadcast)
                        self.log(msg, "SYS" if ok else "ERR")

        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            CONNECTED_CLIENTS.discard(websocket)
            self._log(f"Frontend Client getrennt ({websocket.remote_address})")

    async def start(self):
        loop = asyncio.get_running_loop()
        set_main_loop(loop)
        confirm_gate.set_event_loop(loop)
        # Audio-Streams für CachyOS starten
        self.audio.start_input()
        self.audio.start_output()

        # WebSocket-Server starten
        self._log(f"Starte WebSocket Server auf ws://{WS_HOST}:{WS_PORT}")
        server = await websockets.serve(self.handle_client, WS_HOST, WS_PORT)

        # Gemini Live & Telemetrie & Cron Engine parallel starten
        self.cron_engine.start(controller=self.controller)
        t_live = asyncio.create_task(self.controller.run())
        t_telem = asyncio.create_task(self.telemetry_loop())

        try:
            await asyncio.gather(t_live, t_telem)
        finally:
            self.cron_engine.stop()
            server.close()
            await server.wait_closed()
            self.controller.stop()

if __name__ == "__main__":
    if not is_api_key_configured() and sys.stdin.isatty():
        get_gemini_api_key(prompt_if_missing=True)
    app = JarvisServer()
    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        print("\n[JarvisServer] Heruntergefahren.")
