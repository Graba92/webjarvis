"""
backend/core/state_hydration.py — State Hydration Protocol gegen Amnesie.
Injiziert beim Session-Connect oder Reconnect den aktuellen Zustand (backlog.md, MEMORY.md)
nahtlos in das Context-Window der Gemini Live API.
"""

from __future__ import annotations
import asyncio
from pathlib import Path
from core.config import BACKEND_DIR, load_memory_md_content
from core.task_manager import get_task_manager

BACKLOG_FILE = BACKEND_DIR / "backlog.md"

def build_hydration_payload() -> str:
    """Erstellt den maschinenlesbaren Zustands-Prompt aus backlog.md und MEMORY.md."""
    tm = get_task_manager()
    all_tasks = tm.get_tasks()
    pending_tasks = [t for t in all_tasks if not t["completed"]]
    recent_done = [t for t in all_tasks if t["completed"]][-3:]

    mem_md = load_memory_md_content()

    parts = [
        "═══════════════════════════════════════════════════════════════",
        "🧠 [SYSTEM-STATE HYDRATION: ZUSTANDSWIEDERHERSTELLUNG ERFOLGT]",
        "═══════════════════════════════════════════════════════════════",
        "Dies ist dein verbindlicher operativer Systemzustand über Sitzungsgrenzen hinweg.",
        "Halte dich strikt an diese Tasks und stelle keine redundanten Fragen nach bereits bekannten Aufgaben.",
        ""
    ]

    parts.append("[AKTIVES TASK-BACKLOG (backlog.md)]")
    if pending_tasks:
        parts.append("Offene Aufgaben:")
        for t in pending_tasks:
            prio = f" [{t['priority'].upper()}]" if t.get("priority") != "normal" else ""
            parts.append(f"  - [{t['id']}]{prio} {t['text']}")
    else:
        parts.append("  Keine offenen Aufgaben im Backlog.")

    if recent_done:
        parts.append("Kürzlich erledigte Aufgaben:")
        for t in recent_done:
            parts.append(f"  ✓ [{t['id']}] {t['text']}")

    parts.append("")

    if mem_md and mem_md.strip():
        parts.append("[PROJEKT-FOKUS & SYSTEM-GEDÄCHTNIS (MEMORY.md)]")
        parts.append(mem_md.strip())
        parts.append("")

    parts.append("═══════════════════════════════════════════════════════════════")
    return "\n".join(parts)


def sanitize_hydration_data(memory_dump):
    clean_history = []
    for msg in memory_dump:
        # Die Live API akzeptiert als reguläre Messages meist nur user/model
        if msg.get("role") in ["user", "model"] and msg.get("parts"):
            clean_parts = [{"text": part["text"]} for part in msg["parts"] if "text" in part]
            if clean_parts:
                clean_history.append({"role": msg["role"], "parts": clean_parts})
    return clean_history


async def hydrate_session(controller_or_session, memory_dump: list | None = None) -> bool:
    """
    Liest backlog.md und MEMORY.md und injiziert sie direkt in die aktive Gemini Live Session.
    Kompatibel sowohl mit GeminiLiveController als auch direkt mit session.
    Verarbeitet optionalen memory_dump durch Bereinigung via sanitize_hydration_data.
    """
    try:
        hydration_prompt = build_hydration_payload()

        # Unterscheidung: GeminiLiveController oder direkte session
        target_session = getattr(controller_or_session, "session", controller_or_session)

        if target_session is None:
            print("[Hydration] Keine aktive Live-Session vorhanden zum Injizieren.")
            return False

        # 1. Backlog & Projektfokus (Memory.md) Prompt
        await target_session.send_client_content(
            turns={"role": "user", "parts": [{"text": hydration_prompt}]},
            turn_complete=True
        )

        # 2. Optionaler bereinigter Gesprächsverlauf / Memory Dump
        if memory_dump:
            clean_history = sanitize_hydration_data(memory_dump)
            if clean_history:
                try:
                    await target_session.send_client_content(
                        turns=clean_history,
                        turn_complete=True
                    )
                except Exception:
                    for turn in clean_history:
                        await target_session.send_client_content(
                            turns=turn,
                            turn_complete=True
                        )
                print(f"[Hydration] {len(clean_history)} Turns aus memory_dump erfolgreich injiziert.")

        print("[Hydration] Session-Zustand (Backlog + Memory) erfolgreich ins Context-Window injiziert.")
        return True
    except Exception as e:
        print(f"[Hydration] Warnung: Session-Hydrierung fehlgeschlagen: {e}")
        return False

