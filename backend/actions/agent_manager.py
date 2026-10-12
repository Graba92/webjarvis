"""
backend/actions/agent_manager.py — Spezialisten-Agenten Manager für J.A.R.V.I.S. / WebJarvis.
Ermöglicht das autonome und manuelle Aktivieren, Deaktivieren, Abfragen und Konsultieren
von spezialisierten Wartungs- und Kognitions-Agenten (Frontend, Backend, MCP, Reasoning).
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Callable, Optional

CONFIG_DIR = Path(__file__).parent.parent / "config"
AGENTS_DIR = CONFIG_DIR / "agents"
REGISTRY_FILE = CONFIG_DIR / "agents_registry.json"

def _load_registry() -> dict:
    if REGISTRY_FILE.exists():
        try:
            return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"active_agents": [], "agents": {}}

def _save_registry(data: dict) -> None:
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    active = [k for k, v in data.get("agents", {}).items() if v.get("active", False)]
    data["active_agents"] = active
    REGISTRY_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def get_agent_content(agent_file: str) -> str:
    path = AGENTS_DIR / agent_file
    if path.exists():
        try:
            return path.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    return ""

def load_active_agents_prompt() -> str:
    """Liest alle aktiven Agenten aus und gibt einen kombinierten Direktiven-String zurück."""
    reg = _load_registry()
    agents = reg.get("agents", {})
    active_prompts = []
    for a_id, a_data in agents.items():
        if a_data.get("active", False):
            f_name = a_data.get("file", "")
            content = get_agent_content(f_name)
            if content:
                active_prompts.append(
                    f"\n═══════════════════════════════════════════════════════════════\n"
                    f"⚡ [AKTIVER SPEZIALISTEN-MODUS: {a_data.get('name', a_id).upper()}]\n"
                    f"═══════════════════════════════════════════════════════════════\n"
                    f"{content}\n"
                )
    return "\n".join(active_prompts)

def manage_agents(action: str, 
                  id: str = "", 
                  enabled: bool = False, 
                  query: str = "",
                  ws_broadcast: Optional[Callable[[dict], None]] = None, 
                  registry: Optional[Any] = None, 
                  **kwargs) -> str:
    """
    Verwaltet die spezialisierten Betriebs- und Wartungsagenten von WebJarvis.
    - action='list': Gibt alle verfügbaren Agenten, deren Profil und Status (aktiv/inaktiv) zurück.
    - action='status': Zeigt das vollständige Mandat und die Vorgaben eines Agenten.
    - action='toggle': Aktiviert oder deaktiviert einen Agenten dynamisch zur Laufzeit.
    - action='consult': Gibt die spezifischen Vorgaben des Agenten für eine gezielte Fragestellung zurück.
    """
    action = (action or "").strip().lower()
    data = _load_registry()
    agents = data.get("agents", {})

    if action == "list":
        if not agents:
            return "Es sind aktuell keine Agenten in agents_registry.json registriert."
        lines = ["🤖 WebJarvis Spezialisten-Agenten:"]
        active_count = 0
        for a_id, a_info in agents.items():
            is_active = a_info.get("active", False)
            if is_active:
                active_count += 1
            tag = "🟢 AKTIV" if is_active else "⚪ STANDBY"
            name = a_info.get("name", a_id)
            desc = a_info.get("description", "")
            lines.append(f"• [{tag}] ID: '{a_id}' — {name}\n  Fokus: {desc}")
        lines.append(f"\nStatus: {active_count} von {len(agents)} Agenten aktiv geschaltet.")
        lines.append("Tipp: Du kannst Agenten mit manage_agents(action=\"toggle\", id=\"backend\", enabled=True) ein- oder ausschalten.")
        return "\n".join(lines)

    elif action == "status":
        a_id = (id or "").strip().lower()
        if not a_id or a_id not in agents:
            valid_ids = ", ".join(agents.keys())
            return f"Agent '{a_id}' nicht gefunden. Verfügbare IDs: {valid_ids}"
        info = agents[a_id]
        content = get_agent_content(info.get("file", ""))
        state_str = "🟢 AKTIVIERT" if info.get("active", False) else "⚪ DEAKTIVIERT (Standby)"
        return (
            f"=== Agent-Profil: {info.get('name', a_id)} ===\n"
            f"Status: {state_str}\n"
            f"Datei: config/agents/{info.get('file')}\n\n"
            f"--- MANDAT & INSTRUKTIONEN ---\n"
            f"{content[:800]}...\n(Vollständiges Dokument vorhanden)"
        )

    elif action == "toggle":
        a_id = (id or "").strip().lower()
        if not a_id or a_id not in agents:
            valid_ids = ", ".join(agents.keys())
            return f"Agent '{a_id}' nicht gefunden. Verfügbare IDs: {valid_ids}"

        agents[a_id]["active"] = bool(enabled)
        _save_registry(data)
        state_str = "aktiviert" if enabled else "deaktiviert"

        # Broadcast ans HUD
        if ws_broadcast:
            try:
                ws_broadcast({
                    "type": "agents_updated",
                    "status": "ok",
                    "registry": data,
                    "toggled_agent": a_id,
                    "active": enabled
                })
            except Exception:
                pass

        return (
            f"Spezialist '{agents[a_id].get('name', a_id)}' (ID: {a_id}) wurde erfolgreich {state_str}.\n"
            f"Die System-Direktiven wurden aktualisiert und stehen dem Live-System zur Verfügung."
        )

    elif action == "consult":
        a_id = (id or "").strip().lower()
        if not a_id or a_id not in agents:
            valid_ids = ", ".join(agents.keys())
            return f"Agent '{a_id}' nicht gefunden. Verfügbare IDs: {valid_ids}"
        info = agents[a_id]
        content = get_agent_content(info.get("file", ""))

        # State-Persistenz bei Agenten-Wechsel & Konsultation
        state_block = ""
        try:
            from core.state_hydration import build_hydration_payload
            state_data = build_hydration_payload()
            state_block = f"\n<current_state>\n{state_data}\n</current_state>\n"
        except Exception:
            pass

        return (
            f"[KONSULTATION: {info.get('name')}]\n"
            f"{state_block}"
            f"Frage / Kontext: {query}\n"
            f"Spezialisten-Vorgaben:\n{content}\n"
            f"Wende diese Vorgaben nun exakt auf das Problem und den aktuellen Bearbeitungsstand an."
        )

    else:
        return f"Unbekannte Aktion '{action}'. Gültige Aktionen: 'list', 'status', 'toggle', 'consult'."

TOOL = {
    "name": "manage_agents",
    "description": (
        "Ermöglicht J.A.R.V.I.S. die Verwaltung und Aktivierung von spezialisierten Sub-Agenten "
        "(z. B. 'frontend' für Next.js/UI, 'backend' für FastAPI/SPS-Stabilität, 'mcp_api' für MCP/Tools, "
        "oder 'reasoning_core' für kognitives First-Principles Denken). "
        "Kann Agenten auflisten ('list'), Status abrufen ('status'), zur Laufzeit an-/abschalten ('toggle') "
        "oder für eine konkrete Aufgabe konsultieren ('consult')."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "Die Aktion: 'list' (alle Agenten anzeigen), 'status' (Details anzeigen), 'toggle' (Agent aktivieren/deaktivieren), oder 'consult' (Spezialisten befragen)."
            },
            "id": {
                "type": "STRING",
                "description": "Die ID des Agenten: 'frontend', 'backend', 'mcp_api' oder 'reasoning_core'."
            },
            "enabled": {
                "type": "BOOLEAN",
                "description": "True zum Aktivieren des Agenten, False zum Deaktivieren (nur bei 'toggle')."
            },
            "query": {
                "type": "STRING",
                "description": "Die konkrete Frage oder Problemstellung bei 'consult'."
            }
        },
        "required": ["action"]
    },
    "handler": manage_agents
}
