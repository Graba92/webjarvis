"""
backend/actions/manage_mcp.py — MCP (Model Context Protocol) Skill Matrix Manager für Cypher / J.A.R.V.I.S.
Ermöglicht der KI, die eigenen MCP-Skills autonom zu kennen, abzufragen und auf Wunsch ein- oder auszuschalten.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Callable, Optional

CONFIG_DIR = Path(__file__).parent.parent / "config"
MCP_CONFIG_FILE = CONFIG_DIR / "mcp_servers.json"

def _load_mcp_config() -> dict:
    if MCP_CONFIG_FILE.exists():
        try:
            return json.loads(MCP_CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"mcpServers": {}}

def _save_mcp_config(data: dict) -> None:
    MCP_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    MCP_CONFIG_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def manage_mcp(action: str, id: str = "", enabled: bool = False, ws_broadcast: Optional[Callable[[dict], None]] = None, registry: Optional[Any] = None, **kwargs) -> str:
    """
    Verwaltet die MCP-Skills (Model Context Protocol).
    - action='list': Gibt alle bekannten MCP-Server, deren Beschreibung und Aktivierungsstatus zurück.
    - action='status': Detaillierte Konfigurations- und Umgebungsvariablen-Infos zu einem spezifischen Skill.
    - action='toggle': Aktiviert oder deaktiviert einen MCP-Skill und synchronisiert das System in Echtzeit.
    """
    action = (action or "").strip().lower()
    data = _load_mcp_config()
    servers = data.get("mcpServers", {})

    if action == "list":
        if not servers:
            return "Es sind aktuell keine MCP-Server in mcp_servers.json hinterlegt."
        lines = ["MCP Skill Matrix Status:"]
        active_count = 0
        for s_id, s_info in servers.items():
            is_on = s_info.get("enabled", False)
            if is_on:
                active_count += 1
            status_tag = "🟢 AKTIV" if is_on else "⚪ STANDBY"
            desc = s_info.get("description", "Keine Beschreibung")
            lines.append(f"• [{status_tag}] {s_id}: {desc}")
        lines.append(f"\nGesamt: {len(servers)} Module ({active_count} aktiv).")
        lines.append("Hinweis: Module können per 'manage_mcp(action=\"toggle\", id=\"<name>\", enabled=True)' oder mit einem Klick auf das Puzzle-Icon im HUD-Dock aktiviert werden.")
        return "\n".join(lines)

    elif action == "status":
        s_id = (id or "").strip().lower()
        if not s_id or s_id not in servers:
            valid_ids = ", ".join(servers.keys())
            return f"MCP-Skill '{s_id}' nicht gefunden. Verfügbare Skills: {valid_ids}"
        info = servers[s_id]
        is_on = info.get("enabled", False)
        status_tag = "Aktiviert (Bereit für Tool-Aufrufe)" if is_on else "Deaktiviert (Standby)"
        cmd = info.get("command", "")
        args = " ".join(info.get("args", []))
        env_keys = list(info.get("env", {}).keys())
        env_str = f"Benötigte Env-Variablen: {', '.join(env_keys)}" if env_keys else "Keine speziellen Umgebungsvariablen erforderlich"
        return (
            f"MCP Skill '{s_id}':\n"
            f"• Status: {status_tag}\n"
            f"• Beschreibung: {info.get('description', '')}\n"
            f"• Ausführungsbefehl: {cmd} {args}\n"
            f"• {env_str}\n"
            f"• Umschaltbar über: HUD-Dock (Puzzle-Icon) oder 'manage_mcp(action=\"toggle\", id=\"{s_id}\", enabled={not is_on})'"
        )

    elif action == "toggle":
        s_id = (id or "").strip().lower()
        if not s_id or s_id not in servers:
            valid_ids = ", ".join(servers.keys())
            return f"Fehler: MCP-Skill '{s_id}' existiert nicht in der Konfiguration. Verfügbare IDs: {valid_ids}"
        
        servers[s_id]["enabled"] = bool(enabled)
        _save_mcp_config(data)

        if ws_broadcast:
            try:
                ws_broadcast({
                    "type": "mcp_servers_data",
                    "servers": servers
                })
            except Exception:
                pass

        if registry and hasattr(registry, "reload_mcp"):
            try:
                registry.reload_mcp(MCP_CONFIG_FILE)
            except Exception:
                pass

        state_str = "aktiviert" if enabled else "deaktiviert"
        return (
            f"MCP-Skill '{s_id}' wurde erfolgreich {state_str}.\n"
            f"Die Konfiguration wurde synchronisiert und im Frontend-HUD aktualisiert."
        )

    else:
        return f"Unbekannte Aktion '{action}'. Gültige Aktionen sind: 'list', 'status', 'toggle'."

TOOL = {
    "name": "manage_mcp",
    "description": (
        "Ermöglicht der KI die Abfrage und Steuerung der eigenen MCP (Model Context Protocol) Skill Matrix. "
        "Kann alle verfügbaren MCP-Server auflisten ('list'), Details und Voraussetzungen abrufen ('status') "
        "sowie Server direkt auf Nutzeranweisung aktivieren oder deaktivieren ('toggle'). "
        "Verfügbare Module umfassen z.B. filesystem, sqlite, fetch, github, brave_search, memory, time, puppeteer."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "Die auszuführende Aktion: 'list' (alle Skills anzeigen), 'status' (Details zu einem Skill), oder 'toggle' (Skill an/ausschalten)."
            },
            "id": {
                "type": "STRING",
                "description": "Die ID des MCP-Servers, z. B. 'github', 'sqlite', 'filesystem', 'fetch', 'brave_search', 'memory', 'time', 'puppeteer' (für 'status' und 'toggle')."
            },
            "enabled": {
                "type": "BOOLEAN",
                "description": "True zum Aktivieren, False zum Deaktivieren (nur bei 'toggle')."
            }
        },
        "required": ["action"]
    },
    "handler": manage_mcp
}
