"""
backend/core/mcp_client.py — Model Context Protocol (MCP) Client Bridge für J.A.R.V.I.S. AI OS.
Verbindet J.A.R.V.I.S. mit Open-Source MCP-Servern über stdio (JSON-RPC 2.0) oder HTTP/SSE.
Ermöglicht das automatische Laden und Ausführen externer MCP-Tools direkt durch Gemini Live.
"""

from __future__ import annotations
import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

_MCP_REQ_ID = 0
_REQ_LOCK = threading.Lock()

def _next_id() -> int:
    global _MCP_REQ_ID
    with _REQ_LOCK:
        _MCP_REQ_ID += 1
        return _MCP_REQ_ID

class MCPStdioServer:
    """Verwaltet eine persistente Stdio-Verbindung zu einem MCP-Serverprozess."""
    def __init__(self, name: str, command: str, args: list[str], env: dict | None = None, cwd: str | None = None, logger: Callable[[str], None] = print):
        self.name = name
        self.command = command
        self.args = args
        self.env = env or os.environ.copy()
        self.cwd = cwd
        self.logger = logger
        self.proc: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._initialized = False

    def is_running(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def start(self) -> bool:
        """Startet den MCP Server-Prozess und führt den Handshake aus."""
        cmd_path = shutil.which(self.command)
        if not cmd_path:
            self.logger(f"[MCP/{self.name}] Befehl '{self.command}' nicht im PATH gefunden.")
            return False

        full_cmd = [cmd_path] + self.args
        try:
            self.proc = subprocess.Popen(
                full_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=self.env,
                cwd=self.cwd
            )
            # stderr Logger im Hintergrund
            def _log_stderr():
                if not self.proc or not self.proc.stderr:
                    return
                for line in self.proc.stderr:
                    clean = line.strip()
                    if clean:
                        self.logger(f"[MCP/{self.name} STDERR] {clean[:140]}")
            threading.Thread(target=_log_stderr, daemon=True).start()

            # Handshake senden
            init_req = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "jarvis-mcp-bridge", "version": "1.0.0"}
                },
                "id": _next_id()
            }
            init_resp = self._send_request(init_req, timeout=8.0)
            if not init_resp or "result" not in init_resp:
                self.logger(f"[MCP/{self.name}] Initialisierung fehlgeschlagen oder keine Antwort.")
                self.stop()
                return False

            # Initialized Notification senden
            notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
            self._send_notification(notif)
            self._initialized = True
            self.logger(f"[MCP/{self.name}] Erfolgreich gestartet & via JSON-RPC 2.0 initialisiert.")
            return True

        except Exception as e:
            self.logger(f"[MCP/{self.name}] Startfehler: {e}")
            self.stop()
            return False

    def _send_notification(self, payload: dict) -> None:
        if not self.is_running() or not self.proc or not self.proc.stdin:
            return
        line = json.dumps(payload) + "\n"
        try:
            self.proc.stdin.write(line)
            self.proc.stdin.flush()
        except Exception:
            pass

    def _send_request(self, payload: dict, timeout: float = 10.0) -> Optional[dict]:
        with self._lock:
            if not self.is_running() or not self.proc or not self.proc.stdin or not self.proc.stdout:
                return None
            req_id = payload.get("id")
            line = json.dumps(payload) + "\n"
            try:
                self.proc.stdin.write(line)
                self.proc.stdin.flush()
            except Exception as e:
                self.logger(f"[MCP/{self.name}] Write-Fehler: {e}")
                return None

            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.proc.poll() is not None:
                    return None
                resp_line = self.proc.stdout.readline()
                if not resp_line:
                    time.sleep(0.05)
                    continue
                clean = resp_line.strip()
                if not clean:
                    continue
                try:
                    data = json.loads(clean)
                    if data.get("id") == req_id:
                        return data
                except Exception:
                    continue
            self.logger(f"[MCP/{self.name}] Request-Timeout nach {timeout}s.")
            return None

    def list_tools(self) -> List[dict]:
        """Ruft verfügbare Tools via tools/list ab."""
        if not self._initialized and not self.start():
            return []
        req = {"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": _next_id()}
        resp = self._send_request(req, timeout=6.0)
        if resp and "result" in resp:
            return resp["result"].get("tools", [])
        return []

    def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Führt ein Tool via tools/call aus."""
        if not self.is_running():
            if not self.start():
                return f"MCP-Server '{self.name}' ist offline und konnte nicht gestartet werden."
        req = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
            "id": _next_id()
        }
        resp = self._send_request(req, timeout=30.0)
        if not resp:
            return f"Keine Antwort vom MCP-Server '{self.name}' erhalten (Timeout)."
        if "error" in resp:
            err = resp["error"]
            return f"MCP Fehler ({err.get('code')}): {err.get('message')}"
        res = resp.get("result", {})
        content_items = res.get("content", [])
        text_outputs = []
        for c in content_items:
            if isinstance(c, dict) and c.get("type") == "text":
                text_outputs.append(c.get("text", ""))
            elif isinstance(c, str):
                text_outputs.append(c)
        if text_outputs:
            return "\n".join(text_outputs)
        return json.dumps(res, ensure_ascii=False)

    def stop(self) -> None:
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=2.0)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
            self.proc = None
            self._initialized = False

class MCPManager:
    """Verwaltet alle konfigurierten MCP-Server und deren Registrierung als Gemini-Tools."""
    def __init__(self, config_path: Path, logger: Callable[[str], None] = print):
        self.config_path = config_path
        self.logger = logger
        self.servers: Dict[str, MCPStdioServer] = {}

    def ensure_default_config(self) -> None:
        """Erstellt eine Beispieldatei falls backend/config/mcp_servers.json nicht existiert."""
        if not self.config_path.exists():
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            sample = {
                "mcpServers": {
                    "system_info": {
                        "command": "python3",
                        "args": ["-c", "import sys, json; from http.server import HTTPServer; print('System MCP Helper')"],
                        "description": "Beispiel MCP Server",
                        "enabled": False
                    }
                }
            }
            self.config_path.write_text(json.dumps(sample, indent=2), encoding="utf-8")

    def load_mcp_servers(self) -> List[dict]:
        """Lädt MCP Server Konfigurationen und liefert Tool-Definitionen."""
        self.ensure_default_config()
        if not self.config_path.exists():
            return []

        try:
            cfg = json.loads(self.config_path.read_text(encoding="utf-8"))
        except Exception as e:
            self.logger(f"[MCPManager] Fehler beim Parsen von {self.config_path.name}: {e}")
            return []

        servers_cfg = cfg.get("mcpServers", {})
        discovered_tools = []

        for s_name, s_data in servers_cfg.items():
            if not isinstance(s_data, dict):
                continue
            enabled = s_data.get("enabled", True)
            if not enabled:
                continue

            cmd = s_data.get("command")
            args = s_data.get("args", [])
            if not cmd:
                continue

            server = MCPStdioServer(
                name=s_name,
                command=cmd,
                args=args,
                cwd=s_data.get("cwd"),
                logger=self.logger
            )
            self.servers[s_name] = server

            # Tools abfragen
            tools = server.list_tools()
            for t in tools:
                raw_name = t.get("name", "tool")
                t_name = f"mcp_{s_name}_{raw_name}"
                desc = t.get("description") or f"MCP Tool aus Server '{s_name}'"
                schema = t.get("inputSchema") or {"type": "OBJECT", "properties": {}}

                # Normalisierung von schema type nach OBJECT
                if isinstance(schema, dict) and schema.get("type") == "object":
                    schema["type"] = "OBJECT"

                def make_handler(srv: MCPStdioServer, real_t_name: str):
                    def _h(**kwargs):
                        params = kwargs.get("parameters") or kwargs
                        return srv.call_tool(real_t_name, params)
                    return _h

                discovered_tools.append({
                    "name": t_name,
                    "description": f"[MCP: {s_name}] {desc}",
                    "parameters": schema,
                    "handler": make_handler(server, raw_name),
                    "file": f"mcp_servers.json ({s_name})"
                })

        return discovered_tools

    def shutdown(self) -> None:
        for srv in self.servers.values():
            srv.stop()
