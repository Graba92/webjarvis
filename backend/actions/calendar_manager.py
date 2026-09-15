"""
backend/actions/calendar_manager.py — Kalender & Dynamischer Termin-Scheduler für J.A.R.V.I.S. AI OS.
- Lokale SQLite-Datenbank in backend/memory/calendar.db.
- NLP-to-DateTime & Reminder Parser für natürliche Spracheingaben ("Erinnere mich zwei Tage vorher...").
- CRUD-Operationen für Termine & Integration in das Morning Briefing.
"""

from __future__ import annotations
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

DB_DIR = Path(__file__).parent.parent / "memory"
DB_FILE = DB_DIR / "calendar.db"

def _get_connection() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                start_time TEXT NOT NULL,
                end_time TEXT DEFAULT '',
                category TEXT DEFAULT 'Termin',
                reminder_offset_minutes INTEGER DEFAULT 15,
                is_completed INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_start_time ON events(start_time);")
    return conn

def parse_natural_datetime(text: str, default_hour: int = 9, default_minute: int = 0) -> Optional[datetime]:
    """Wandelt natürliche Zeitangaben (Deutsch/Englisch) in ein datetime-Objekt um."""
    if not text:
        return None
    raw = text.strip().lower()
    now = datetime.now()

    # 1. ISO-Format oder YYYY-MM-DD HH:MM
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            pass

    # 2. Uhrzeit extrahieren (z.B. "14 Uhr", "14:30", "um 10")
    target_hour = default_hour
    target_min = default_minute
    time_match = re.search(r'(?:um\s+)?(\d{1,2})(?::(\d{2})|\s*uhr|\s*h)?', raw)
    if time_match:
        try:
            h = int(time_match.group(1))
            m = int(time_match.group(2)) if time_match.group(2) else 0
            if 0 <= h <= 23 and 0 <= m <= 59:
                target_hour = h
                target_min = m
        except Exception:
            pass

    # 3. Relative Tagesangaben
    if "heute" in raw or "today" in raw:
        return now.replace(hour=target_hour, minute=target_min, second=0, microsecond=0)
    elif "morgen" in raw or "tomorrow" in raw:
        base = now + timedelta(days=1)
        return base.replace(hour=target_hour, minute=target_min, second=0, microsecond=0)
    elif "übermorgen" in raw:
        base = now + timedelta(days=2)
        return base.replace(hour=target_hour, minute=target_min, second=0, microsecond=0)

    # 4. In X Stunden / Tagen
    hours_match = re.search(r'in\s+(\d+)\s+stunde', raw)
    if hours_match:
        return now + timedelta(hours=int(hours_match.group(1)))

    days_match = re.search(r'in\s+(\d+)\s+tag', raw)
    if days_match:
        base = now + timedelta(days=int(days_match.group(1)))
        return base.replace(hour=target_hour, minute=target_min, second=0, microsecond=0)

    # 5. Datumsformat DD.MM. oder DD.MM.YYYY
    date_match = re.search(r'(\d{1,2})\.(\d{1,2})\.(?:(\d{2,4}))?', raw)
    if date_match:
        d = int(date_match.group(1))
        m = int(date_match.group(2))
        y = int(date_match.group(3)) if date_match.group(3) else now.year
        if y < 100:
            y += 2000
        return datetime(y, m, d, target_hour, target_min)

    return None

def parse_reminder_offset(text: str) -> int:
    """Parst Vorlaufzeiten für Erinnerungen (z.B. 'zwei Tage vorher' -> 2880 min)."""
    if not text:
        return 15
    raw = text.strip().lower()

    if "zwei tage" in raw or "2 tage" in raw:
        return 2 * 24 * 60
    if "ein tag" in raw or "1 tag" in raw:
        return 24 * 60
    if "zwei stunden" in raw or "2 stunden" in raw:
        return 120
    if "eine stunde" in raw or "1 stunde" in raw:
        return 60
    if "halbe stunde" in raw or "30 minuten" in raw:
        return 30

    m = re.search(r'(\d+)\s*(?:minuten|min)', raw)
    if m:
        return int(m.group(1))

    return 15

def get_upcoming_events(days: int = 1) -> List[Dict[str, Any]]:
    """Gibt alle Termine innerhalb der nächsten X Tage zurück (für Morning Briefing)."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    until_str = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d 23:59")
    with _get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM events WHERE start_time >= ? AND start_time <= ? AND is_completed = 0 ORDER BY start_time ASC",
            (now_str, until_str)
        )
        return [dict(row) for row in cursor.fetchall()]

def calendar_manager(
    action: str = "list",
    title: str = "",
    start_time: str = "",
    description: str = "",
    category: str = "Termin",
    reminder: str = "",
    event_id: int | str = 0,
    timeframe: str = "upcoming",
    **kwargs
) -> str:
    """
    CRUD-Handler für den Kalender & dynamischen Scheduler.
    - action='create': Legt einen Termin mit NLP-Parsing für Zeit und Erinnerung an.
    - action='list': Zeigt anstehende Termine ('today', 'upcoming', 'all').
    - action='delete': Löscht einen Termin anhand seiner ID.
    - action='complete': Markiert einen Termin als erledigt.
    """
    act = (action or "list").strip().lower()

    if act in ("create", "add", "new"):
        t_clean = (title or kwargs.get("name") or "").strip()
        if not t_clean:
            return "Fehler: Ein Titel für den Termin ist erforderlich."

        dt = parse_natural_datetime(start_time or kwargs.get("date") or kwargs.get("time") or "")
        if not dt:
            dt = datetime.now() + timedelta(hours=1)

        start_iso = dt.strftime("%Y-%m-%d %H:%M")
        offset_mins = parse_reminder_offset(reminder or kwargs.get("remind_before") or "")

        with _get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO events (title, description, start_time, category, reminder_offset_minutes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (t_clean, description.strip(), start_iso, category.strip(), offset_mins, datetime.now().isoformat())
            )
            new_id = cursor.lastrowid

        remind_str = f"{offset_mins} Minuten vorher" if offset_mins < 60 else f"{offset_mins // 60} Stunden vorher"
        return f"Termin #{new_id} '{t_clean}' erfolgreich angelegt für {dt.strftime('%A, %d.%m.%Y um %H:%M Uhr')} (Erinnerung: {remind_str})."

    elif act == "list":
        tf = (timeframe or "upcoming").strip().lower()
        now_iso = datetime.now().strftime("%Y-%m-%d %H:%M")
        query = "SELECT * FROM events WHERE is_completed = 0"
        params: list[Any] = []

        if tf == "today":
            today_end = datetime.now().strftime("%Y-%m-%d 23:59")
            query += " AND start_time >= ? AND start_time <= ? ORDER BY start_time ASC"
            params = [now_iso, today_end]
        elif tf == "upcoming":
            query += " AND start_time >= ? ORDER BY start_time ASC LIMIT 10"
            params = [now_iso]
        else:
            query += " ORDER BY start_time ASC LIMIT 20"

        with _get_connection() as conn:
            rows = conn.execute(query, params).fetchall()

        if not rows:
            return "Keine anstehenden Termine gefunden."

        lines = ["Anstehende Termine:"]
        for r in rows:
            lines.append(f"• [ID #{r['id']}] {r['start_time']} — {r['title']} ({r['category']})")
            if r['description']:
                lines.append(f"    Notiz: {r['description']}")
        return "\n".join(lines)

    elif act in ("delete", "remove"):
        try:
            eid = int(event_id)
        except Exception:
            return "Fehler: Ungültige Termin-ID."
        with _get_connection() as conn:
            cur = conn.execute("DELETE FROM events WHERE id = ?", (eid,))
            if cur.rowcount > 0:
                return f"Termin #{eid} erfolgreich gelöscht."
            return f"Termin #{eid} nicht gefunden."

    elif act in ("complete", "done"):
        try:
            eid = int(event_id)
        except Exception:
            return "Fehler: Ungültige Termin-ID."
        with _get_connection() as conn:
            cur = conn.execute("UPDATE events SET is_completed = 1 WHERE id = ?", (eid,))
            if cur.rowcount > 0:
                return f"Termin #{eid} als erledigt markiert."
            return f"Termin #{eid} nicht gefunden."

    return f"Unbekannte Aktion '{action}'. Gültige Aktionen: 'create', 'list', 'delete', 'complete'."

TOOL = {
    "name": "calendar_manager",
    "description": (
        "Verwaltet persönliche Termine und den Zeitplan mit lokaler SQLite-Persistenz. "
        "Unterstützt natürliche Spracheingaben für Datum, Uhrzeit und Vorlaufzeiten von Erinnerungen "
        "(z.B. 'morgen um 15 Uhr', 'in zwei Tagen', 'Erinnere mich 1 Stunde vorher')."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "Die Aktion: 'create' (neuen Termin eintragen), 'list' (Termine abfragen), 'delete' (löschen), 'complete' (erledigt)."
            },
            "title": {
                "type": "STRING",
                "description": "Titel oder Name des Termins / Events."
            },
            "start_time": {
                "type": "STRING",
                "description": "Datum und Uhrzeit (z.B. 'morgen 14 Uhr', '2026-10-15 16:30', 'in 3 Stunden')."
            },
            "description": {
                "type": "STRING",
                "description": "Optionale Notizen oder Beschreibung zum Termin."
            },
            "reminder": {
                "type": "STRING",
                "description": "Vorlaufzeit der Erinnerung (z.B. 'zwei Tage vorher', '1 Stunde vorher', '15 Minuten')."
            },
            "event_id": {
                "type": "INTEGER",
                "description": "ID des Termins für 'delete' oder 'complete'."
            },
            "timeframe": {
                "type": "STRING",
                "description": "Zeitfenster für 'list': 'today', 'upcoming' oder 'all'."
            }
        },
        "required": ["action"]
    },
    "handler": calendar_manager
}
