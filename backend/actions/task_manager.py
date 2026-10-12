"""
backend/actions/task_manager.py — Gemini Live Tool für das Markdown Task Backlog.
Ermöglicht der KI das Abrufen, Abhaken und Hinzufügen von Aufgaben in backlog.md.
"""

from __future__ import annotations
import asyncio
from typing import Dict, Any, Optional
from core.task_manager import get_task_manager

TOOL = {
    "name": "manage_tasks",
    "description": (
        "Verwaltet Aufgaben im Task-Backlog (backlog.md). "
        "Unterstützt das Auflisten offener/erledigter Aufgaben, das Hinzufügen neuer Aufgaben, "
        "das Abhaken (Erledigen) und das Löschen von Aufgaben."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "Die auszuführende Aktion: 'list', 'complete', 'add', 'delete', 'toggle'.",
                "enum": ["list", "complete", "add", "delete", "toggle"]
            },
            "task_id": {
                "type": "STRING",
                "description": "Die ID der Aufgabe (z.B. 'tk-wiki-init' oder 'task-1-abcd') oder ein Titel-Suchbegriff."
            },
            "text": {
                "type": "STRING",
                "description": "Der Aufgabentext beim Hinzufügen einer neuen Aufgabe."
            },
            "status_filter": {
                "type": "STRING",
                "description": "Filter für 'list': 'all', 'pending' (nur offene) oder 'done' (nur erledigte).",
                "enum": ["all", "pending", "done"]
            },
            "priority": {
                "type": "STRING",
                "description": "Priorität beim Hinzufügen: 'high', 'normal' oder 'low'.",
                "enum": ["high", "normal", "low"]
            }
        },
        "required": ["action"]
    }
}

def manage_tasks(parameters: Dict[str, Any], **kwargs) -> str:
    action = str(parameters.get("action", "list")).lower().strip()
    task_id = parameters.get("task_id")
    text = parameters.get("text")
    status_filter = str(parameters.get("status_filter", "pending")).lower().strip()
    priority = str(parameters.get("priority", "normal")).lower().strip()

    tm = get_task_manager()

    if action == "list":
        tasks = tm.get_tasks()
        if status_filter == "pending":
            tasks = [t for t in tasks if not t["completed"]]
        elif status_filter == "done":
            tasks = [t for t in tasks if t["completed"]]

        if not tasks:
            return f"Keine Aufgaben gefunden (Filter: {status_filter}). Das Backlog ist aktuell leer."

        lines = [f"Aktuelle Aufgaben ({len(tasks)} Einträge, Filter: {status_filter}):"]
        for t in tasks:
            status_symbol = "✓" if t["completed"] else "○"
            prio_tag = f" [{t['priority'].upper()}]" if t.get("priority") != "normal" else ""
            lines.append(f"  {status_symbol} [{t['id']}]{prio_tag} {t['text']}")
        return "\n".join(lines)

    elif action in ("complete", "toggle"):
        if not task_id:
            return "Fehler: 'task_id' (ID oder Text der Aufgabe) muss angegeben werden."
        
        # Falls task_id kein exakter Match ist, versuche Textsuche
        tasks = tm.get_tasks()
        target = next((t for t in tasks if t["id"].lower() == task_id.lower()), None)
        if not target:
            target = next((t for t in tasks if task_id.lower() in t["text"].lower()), None)
            
        if not target:
            return f"Aufgabe '{task_id}' konnte im Backlog nicht gefunden werden."

        target_status = True if action == "complete" else not target["completed"]
        res = tm.toggle_task_sync(target["id"], completed=target_status)
        if res:
            state_str = "als erledigt abgehakt" if res["completed"] else "wieder als offen markiert"
            return f"Aufgabe '{res['text']}' [{res['id']}] wurde {state_str}."
        return f"Fehler beim Aktualisieren der Aufgabe '{task_id}'."

    elif action == "add":
        if not text or not str(text).strip():
            return "Fehler: 'text' für die neue Aufgabe muss angegeben werden."
        item = tm.add_task_sync(str(text).strip(), priority=priority)
        return f"Aufgabe erfolgreich zum Backlog hinzugefügt: '{item['text']}' [ID: {item['id']}]."

    elif action == "delete":
        if not task_id:
            return "Fehler: 'task_id' muss zum Löschen angegeben werden."
        tasks = tm.get_tasks()
        target = next((t for t in tasks if t["id"].lower() == task_id.lower()), None)
        if not target:
            target = next((t for t in tasks if task_id.lower() in t["text"].lower()), None)
        if not target:
            return f"Aufgabe '{task_id}' zum Löschen nicht gefunden."

        success = tm.delete_task_sync(target["id"])
        if success:
            return f"Aufgabe '{target['text']}' [ID: {target['id']}] wurde aus dem Backlog entfernt."
        return f"Fehler beim Löschen der Aufgabe '{task_id}'."

    return f"Unbekannte Aktion '{action}'. Unterstützt: list, complete, add, delete, toggle."

TOOL["handler"] = manage_tasks
