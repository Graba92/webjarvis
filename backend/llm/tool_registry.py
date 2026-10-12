"""
backend/llm/tool_registry.py — Standardisierte Tool-Calling & MCP Schnittstelle.
Kapselt Host-, Second-Brain- und Dropzone-Werkzeuge in ein einheitliches
Interface für Ollama, Gemini, Claude und MCP-Server.
"""

from __future__ import annotations
import inspect
import json
import os
import subprocess
import sqlite3
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field

# Dynamische Pfadauflösung
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def _resolve_db_path() -> Path:
    candidates = [
        os.getenv("AGY_DB_PATH"),
        os.getenv("AGY_DATA_POOL", str(PROJECT_ROOT / "agy_components" / "data-pool")) + "/MASTER_INDEX.db",
        PROJECT_ROOT / "agy_components" / "data-pool" / "MASTER_INDEX.db",
        PROJECT_ROOT.parent / "Agy-data-pool" / "MASTER_INDEX.db",
    ]
    for c in candidates:
        if c and Path(c).is_file():
            return Path(c).resolve()
    return PROJECT_ROOT / "agy_components" / "data-pool" / "MASTER_INDEX.db"

def _resolve_exchange_dir() -> Path:
    candidates = [
        os.getenv("EXCHANGE_DROPZONE"),
        PROJECT_ROOT / "agent_exchange" / "dropzone",
        PROJECT_ROOT / "agent_exchange",
        PROJECT_ROOT.parent / "Agent-Exchange",
    ]
    for c in candidates:
        if c and Path(c).is_dir():
            return Path(c).resolve()
    target = PROJECT_ROOT / "agent_exchange" / "dropzone"
    target.mkdir(parents=True, exist_ok=True)
    return target

DB_PATH = _resolve_db_path()
EXCHANGE_DIR = _resolve_exchange_dir()


@dataclass
class ToolParameter:
    name: str
    type_str: str  # string, integer, boolean, object, array
    description: str
    required: bool = True
    enum: Optional[List[str]] = None


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: List[ToolParameter]
    handler: Callable[..., Any]
    requires_confirmation: bool = False

    def to_openai_schema(self) -> Dict[str, Any]:
        properties = {}
        required = []
        for p in self.parameters:
            prop: Dict[str, Any] = {"type": p.type_str, "description": p.description}
            if p.enum:
                prop["enum"] = p.enum
            properties[p.name] = prop
            if p.required:
                required.append(p.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

    def to_gemini_schema(self) -> Dict[str, Any]:
        """Konform zu Gemini / OpenAPI Schema Deklarationen."""
        properties = {}
        required = []
        for p in self.parameters:
            t = p.type_str.upper()
            prop: Dict[str, Any] = {
                "type": t if t in ["STRING", "INTEGER", "NUMBER", "BOOLEAN", "ARRAY", "OBJECT"] else "STRING",
                "description": p.description
            }
            if p.enum:
                prop["enum"] = p.enum
            properties[p.name] = prop
            if p.required:
                required.append(p.name)

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "OBJECT",
                "properties": properties,
                "required": required
            }
        }


class ToolRegistry:
    """Verwaltet registrierte native Tools und externe MCP-Server."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_builtin_tools()

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def get_schemas(self, format_type: str = "openai") -> List[Dict[str, Any]]:
        if format_type == "gemini":
            return [t.to_gemini_schema() for t in self._tools.values()]
        return [t.to_openai_schema() for t in self._tools.values()]

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        tool = self._tools.get(tool_name)
        if not tool:
            return f"Fehler: Werkzeug '{tool_name}' nicht registriert."

        try:
            if inspect.iscoroutinefunction(tool.handler):
                res = await tool.handler(**arguments)
            else:
                res = tool.handler(**arguments)
            return json.dumps(res, ensure_ascii=False) if isinstance(res, (dict, list)) else str(res)
        except Exception as e:
            return f"Fehler bei Tool-Ausführung '{tool_name}': {e}"

    # -------------------------------------------------------------
    # Eingebaute Werkzeuge für WebJarvis & Friday
    # -------------------------------------------------------------
    def _register_builtin_tools(self) -> None:
        # 1. Dateisystem-Werkzeug
        self.register(ToolDefinition(
            name="fs_read_file",
            description="Liest eine Datei aus dem sicheren Workspace-Pfad.",
            parameters=[
                ToolParameter("path", "string", "Absoluter oder relativer Pfad zur Datei")
            ],
            handler=self._tool_fs_read
        ))

        # 2. SQLite Second Brain Suche
        self.register(ToolDefinition(
            name="sqlite_search_knowledge",
            description="Durchsucht den MASTER_INDEX.db Wissensspeicher nach Suchbegriffen.",
            parameters=[
                ToolParameter("query", "string", "Suchbegriff für den Volltext-/Metadaten-Index"),
                ToolParameter("limit", "integer", "Maximale Anzahl Ergebnisse", required=False)
            ],
            handler=self._tool_sqlite_search
        ))

        # 3. Brave-Bridge / Inbox Trigger
        self.register(ToolDefinition(
            name="send_agent_message",
            description="Schreibt eine formatierte Nachricht in die Agent-Exchange Dropzone.",
            parameters=[
                ToolParameter("target", "string", "Ziel-Agent (z.B. JARVIS, FRIDAY, OPERATOR)"),
                ToolParameter("message", "string", "Nachrichteninhalt oder Payload")
            ],
            handler=self._tool_send_exchange_msg
        ))

        # 4. Sandboxed Terminal (CachyOS Host Hook)
        self.register(ToolDefinition(
            name="terminal_execute",
            description="Führt sichere Lese- und Diagnosebefehle im Host-Terminal aus.",
            parameters=[
                ToolParameter("command", "string", "Der auszuführende Shell-Befehl")
            ],
            handler=self._tool_terminal_exec,
            requires_confirmation=True
        ))

    def _tool_fs_read(self, path: str) -> str:
        target = Path(path)
        if not target.is_absolute():
            target = PROJECT_ROOT / target
        if not target.exists():
            return f"Datei nicht gefunden: {target}"
        return target.read_text(encoding="utf-8", errors="replace")[:8000]

    def _tool_sqlite_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        db = _resolve_db_path()
        if not db.exists() or db.stat().st_size == 0:
            try:
                sys.path.insert(0, str(PROJECT_ROOT / "backend" / "memory"))
                from master_index_init import init_db
                init_db(db)
            except Exception:
                pass
        try:
            with sqlite3.connect(str(db), timeout=5.0) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        "SELECT path, filename, content_preview, rowid FROM knowledge_units_fts WHERE knowledge_units_fts MATCH ? LIMIT ?",
                        (query, limit)
                    )
                    rows = cursor.fetchall()
                except Exception:
                    cursor.execute(
                        "SELECT path, filename, content_preview, last_modified FROM knowledge_units WHERE filename LIKE ? OR content_preview LIKE ? LIMIT ?",
                        (f"%{query}%", f"%{query}%", limit)
                    )
                    rows = cursor.fetchall()
                return [
                    {"path": r[0], "filename": r[1], "preview": r[2], "mtime": r[3]}
                    for r in rows
                ]
        except Exception as e:
            return [{"error": str(e)}]

    def _tool_send_exchange_msg(self, target: str, message: str) -> str:
        ex = _resolve_exchange_dir()
        ex.mkdir(parents=True, exist_ok=True)
        import time
        ts = int(time.time())
        filename = ex / f"msg_{ts}.json"
        payload = {
            "sender": "WEBJARVIS_CORE",
            "target": target.upper(),
            "message": message,
            "timestamp": ts
        }
        filename.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return f"Nachricht erfolgreich nach {filename.name} geschrieben."

    def _tool_terminal_exec(self, command: str) -> str:
        forbidden = ["rm -rf", "mkfs", "dd if=", ":(){ :|:& };:", "shutdown", "reboot"]
        if any(f in command for f in forbidden):
            return "Befehl durch WebJarvis Security Policy blockiert."

        res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
        return res.stdout if res.returncode == 0 else f"Stderr: {res.stderr}"
