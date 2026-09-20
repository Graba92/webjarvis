"""
backend/actions/calendar_manager.py — Bidirektionaler Kalender & Termin-Scheduler für J.A.R.V.I.S. AI OS.
- Lokale SQLite-Datenbank in backend/memory/calendar.db mit Single Source of Truth.
- Schema: calendar_events mit Unterstützung für Wiederholungsregeln und gestaffelte Erinnerungsstrategien.
- Event-Driven Live-Sync via WebSockets (CALENDAR_SYNC Broadcasts für INSERT, UPDATE, DELETE).
- Gemini Function Calling Tool: create_calendar_entry (mit Slot-Filling & Bestätigungs-Gate).
"""

from __future__ import annotations
import json
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

DB_DIR = Path(__file__).parent.parent / "memory"
DB_FILE = DB_DIR / "calendar.db"

_BROADCAST_FN: Optional[Callable[[dict], None]] = None

def bind_broadcast(fn: Callable[[dict], None]):
    """Registriert die globale WebSocket-Broadcast-Funktion für Live-Synchronisation."""
    global _BROADCAST_FN
    _BROADCAST_FN = fn

def _broadcast_sync(action: str, event_data: dict):
    """Sendet ein CALENDAR_SYNC Event an alle verbundenen WebSockets (Next.js HUD)."""
    if _BROADCAST_FN:
        try:
            _BROADCAST_FN({
                "type": "CALENDAR_SYNC",
                "action": action.upper(),  # "INSERT", "UPDATE", "DELETE"
                "data": event_data
            })
            _BROADCAST_FN({
                "type": "calendar_events_data",
                "events": get_events_list()
            })
        except Exception as e:
            print(f"[CalendarSync] Broadcast error: {e}")

def _get_connection() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_FILE), timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=10000;")
    with conn:
        # 1. Neues relationales Schema gemäß Spezifikation 2.1
        conn.execute("""
            CREATE TABLE IF NOT EXISTS calendar_events (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                category TEXT DEFAULT 'Termin',
                start_time DATETIME NOT NULL,
                end_time DATETIME DEFAULT '',
                is_recurring BOOLEAN DEFAULT 0,
                recurrence_rule TEXT DEFAULT 'NONE',
                reminder_strategy TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_calendar_start ON calendar_events(start_time);")

        # Automatische Migration für bestehende Datenbanken (category Spalte)
        try:
            cur_cols = conn.execute("PRAGMA table_info(calendar_events);").fetchall()
            existing_col_names = [col["name"] for col in cur_cols]
            if "category" not in existing_col_names:
                conn.execute("ALTER TABLE calendar_events ADD COLUMN category TEXT DEFAULT 'Termin';")
        except Exception:
            pass

        # 2. Migration aus bestehender legacy 'events'-Tabelle falls vorhanden
        try:
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events';")
            if cur.fetchone():
                c_cur = conn.execute("SELECT count(*) FROM calendar_events;")
                if c_cur.fetchone()[0] == 0:
                    legacy_rows = conn.execute("SELECT * FROM events;").fetchall()
                    for r in legacy_rows:
                        rem_min = r['reminder_offset_minutes'] if 'reminder_offset_minutes' in r.keys() else 15
                        strategy = json.dumps({"rules": [{"trigger": f"-{rem_min}m", "frequency": "once"}]})
                        conn.execute("""
                            INSERT INTO calendar_events (id, title, description, category, start_time, end_time, is_recurring, recurrence_rule, reminder_strategy, created_at, updated_at)
                            VALUES (?, ?, ?, 'Termin', ?, ?, 0, 'NONE', ?, ?, ?)
                        """, (
                            str(r['id']),
                            r['title'],
                            r['description'] if 'description' in r.keys() else '',
                            r['start_time'],
                            r['end_time'] if 'end_time' in r.keys() else '',
                            strategy,
                            r['created_at'] if 'created_at' in r.keys() else datetime.now().isoformat(),
                            datetime.now().isoformat()
                        ))
        except Exception:
            pass

    return conn

@contextmanager
def get_db():
    """Kontextmanager für sichere SQLite-Transaktionen mit automatischem Close."""
    conn = _get_connection()
    try:
        with conn:
            yield conn
    finally:
        try:
            conn.close()
        except Exception:
            pass


def parse_natural_datetime(text: str, default_hour: int = 9, default_minute: int = 0) -> Optional[datetime]:
    """Wandelt natürliche Zeitangaben (Deutsch/Englisch) in ein datetime-Objekt um."""
    if not text:
        return None
    raw = text.strip().lower()
    now = datetime.now()

    # 1. ISO-Format oder YYYY-MM-DD HH:MM
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
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
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM calendar_events WHERE start_time >= ? AND start_time <= ? ORDER BY start_time ASC",
            (now_str, until_str)
        )
        return [dict(row) for row in cursor.fetchall()]

def get_events_list(limit: int = 100) -> List[Dict[str, Any]]:
    """Gibt alle aktiven Termine als formatierte Dict-Liste für das HUD zurück."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM calendar_events ORDER BY start_time ASC LIMIT ?",
            (limit,)
        )
        events = []
        for row in cursor.fetchall():
            d = dict(row)
            # JSON-Reminder-Strategie parsen
            try:
                if isinstance(d.get("reminder_strategy"), str):
                    d["reminder_strategy_parsed"] = json.loads(d["reminder_strategy"])
            except Exception:
                d["reminder_strategy_parsed"] = {"rules": []}
            events.append(d)
        return events

def add_event_entry(
    title: str,
    start_time: str,
    end_time: str = "",
    description: str = "",
    category: str = "Termin",
    reminder: str = "15 Minuten vorher",
    recurrence_rule: str = "NONE",
    reminder_strategy: Optional[Any] = None
) -> Dict[str, Any]:
    """Erstellt einen Termin direkt über das Frontend oder Backend und synchronisiert via WebSocket."""
    dt = parse_natural_datetime(start_time)
    if not dt:
        dt = datetime.now() + timedelta(hours=1)
    
    start_iso = dt.strftime("%Y-%m-%d %H:%M")
    end_iso = ""
    if end_time:
        edt = parse_natural_datetime(end_time)
        if edt:
            end_iso = edt.strftime("%Y-%m-%d %H:%M")

    # Erinnerungsstrategie formulieren
    if reminder_strategy and isinstance(reminder_strategy, (dict, list)):
        if isinstance(reminder_strategy, list):
            strategy_dict = {"rules": reminder_strategy}
        else:
            strategy_dict = reminder_strategy
        strategy_json = json.dumps(strategy_dict, ensure_ascii=False)
    else:
        offset_mins = parse_reminder_offset(reminder)
        strategy_json = json.dumps({
            "rules": [
                {"trigger": f"-{offset_mins}m", "frequency": "once"}
            ]
        }, ensure_ascii=False)

    rec_rule = (recurrence_rule or "NONE").upper()
    if rec_rule not in ("NONE", "DAILY", "WEEKLY", "MONTHLY", "YEARLY"):
        rec_rule = "NONE"
    is_rec = 1 if rec_rule != "NONE" else 0

    new_id = f"cal_{uuid.uuid4().hex[:10]}"
    now_iso = datetime.now().isoformat()
    cat_val = (category or "Termin").strip()

    with get_db() as conn:
        conn.execute("""
            INSERT INTO calendar_events (id, title, description, category, start_time, end_time, is_recurring, recurrence_rule, reminder_strategy, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            new_id,
            title.strip(),
            description.strip(),
            cat_val,
            start_iso,
            end_iso,
            is_rec,
            rec_rule,
            strategy_json,
            now_iso,
            now_iso
        ))
        row = conn.execute("SELECT * FROM calendar_events WHERE id = ?", (new_id,)).fetchone()
        event_data = dict(row)

    # Event-Driven Live-Sync an Frontend ausstoßen
    _broadcast_sync("INSERT", event_data)
    return event_data

def delete_event_entry(event_id: str | int) -> bool:
    """Löscht einen Termin anhand seiner ID und triggert den Live-Sync."""
    eid_str = str(event_id)
    with get_db() as conn:
        cur = conn.execute("DELETE FROM calendar_events WHERE id = ?", (eid_str,))
        # Fallback falls ID integer war
        if cur.rowcount == 0 and eid_str.isdigit():
            cur = conn.execute("DELETE FROM calendar_events WHERE id = ?", (int(eid_str),))
        
        success = cur.rowcount > 0

    if success:
        _broadcast_sync("DELETE", {"id": eid_str})
    return success

# ── Gemini Live Function Calling Handler: create_calendar_entry ───────────────
def handle_create_calendar_entry(
    title: str,
    start_time: str,
    recurrence: str = "NONE",
    reminders: Optional[List[Dict[str, str]]] = None,
    end_time: str = "",
    description: str = "",
    category: str = "Termin",
    **kwargs
) -> str:
    """
    Spezifischer Handler für das Gemini Function Calling Tool.
    Wird vom LLM aufgerufen, nachdem Datum, Uhrzeit, Wiederholung und Erinnerung
    vollständig geklärt und vom Operator bestätigt wurden.
    """
    if not title:
        return "Fehler: Der Termin benötigt einen aussagekräftigen Titel."
    if not start_time:
        return "Fehler: Startzeitpunkt fehlt."

    rem_list = reminders or [{"trigger": "-15m", "frequency": "once"}]
    rec = (recurrence or "NONE").upper()
    if rec not in ("NONE", "DAILY", "WEEKLY", "MONTHLY", "YEARLY"):
        rec = "NONE"

    ev = add_event_entry(
        title=title,
        start_time=start_time,
        end_time=end_time,
        description=description,
        category=category,
        recurrence_rule=rec,
        reminder_strategy={"rules": rem_list}
    )

    rem_summary = ", ".join([f"{r.get('trigger', '')} ({r.get('frequency', '')})" for r in rem_list])
    return (
        f"Termin '{title}' erfolgreich im Kalender angelegt:\n"
        f"• ID: {ev['id']}\n"
        f"• Start: {ev['start_time']}\n"
        f"• Kategorie: {ev.get('category', 'Termin')}\n"
        f"• Modus: {rec}\n"
        f"• Erinnerung: {rem_summary}\n"
        f"Das HUD-Dashboard wurde via WebSocket in Echtzeit synchronisiert."
    )

# ── Universeller CRUD-Handler (calendar_manager) ─────────────────────────────
def calendar_manager(
    action: str = "list",
    title: str = "",
    start_time: str = "",
    description: str = "",
    category: str = "Termin",
    reminder: str = "",
    event_id: str | int = "",
    timeframe: str = "upcoming",
    recurrence: str = "NONE",
    reminders: Optional[Any] = None,
    **kwargs
) -> str:
    """Universeller CRUD-Handler für den Kalender."""
    act = (action or "list").strip().lower()

    if act in ("create", "add", "new"):
        t_clean = (title or kwargs.get("name") or "").strip()
        if not t_clean:
            return "Fehler: Ein Titel für den Termin ist erforderlich."

        dt_str = start_time or kwargs.get("date") or kwargs.get("time") or ""
        ev = add_event_entry(
            title=t_clean,
            start_time=dt_str,
            description=description,
            category=category,
            reminder=reminder,
            recurrence_rule=recurrence,
            reminder_strategy=reminders
        )
        return f"Termin '{t_clean}' erfolgreich eingetragen für {ev['start_time']} (ID: {ev['id']})."

    elif act == "list":
        tf = (timeframe or "upcoming").strip().lower()
        now_iso = datetime.now().strftime("%Y-%m-%d %H:%M")
        query = "SELECT * FROM calendar_events"
        params: list[Any] = []

        if tf == "today":
            today_end = datetime.now().strftime("%Y-%m-%d 23:59")
            query += " WHERE start_time >= ? AND start_time <= ? ORDER BY start_time ASC"
            params = [now_iso, today_end]
        elif tf == "upcoming":
            query += " WHERE start_time >= ? ORDER BY start_time ASC LIMIT 15"
            params = [now_iso]
        else:
            query += " ORDER BY start_time ASC LIMIT 25"

        with get_db() as conn:
            rows = conn.execute(query, params).fetchall()

        if not rows:
            return "Keine anstehenden Termine im Kalender gefunden."

        lines = ["📅 Anstehende Termine:"]
        for r in rows:
            rec_badge = f" [{r['recurrence_rule']}]" if r['recurrence_rule'] != 'NONE' else ""
            lines.append(f"• [{r['id']}] {r['start_time']} — {r['title']}{rec_badge}")
            if r['description']:
                lines.append(f"    Notiz: {r['description']}")
        return "\n".join(lines)

    elif act in ("delete", "remove"):
        if not event_id:
            return "Fehler: Keine Termin-ID angegeben."
        ok = delete_event_entry(event_id)
        if ok:
            return f"Termin #{event_id} erfolgreich gelöscht."
        return f"Termin #{event_id} nicht gefunden."

    return f"Unbekannte Aktion '{action}'."

# ── Werkzeug-Deklarationen für Gemini Live ActionRegistry ────────────────────

# 1. Spezialisiertes Tool gemäß Spezifikation 2.2
CREATE_CALENDAR_ENTRY_TOOL = {
    "name": "create_calendar_entry",
    "description": "Erstellt einen neuen Termin erst NACH vollständiger Klärung aller Parameter mit dem Nutzer.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "title": {
                "type": "STRING",
                "description": "Titel des Eintrags"
            },
            "start_time": {
                "type": "STRING",
                "description": "ISO-8601 Format (YYYY-MM-DDTHH:MM:SS)"
            },
            "end_time": {
                "type": "STRING",
                "description": "Optionales Ende im ISO-8601 Format"
            },
            "recurrence": {
                "type": "STRING",
                "enum": ["NONE", "DAILY", "WEEKLY", "MONTHLY", "YEARLY"],
                "description": "Wiederholungsintervall"
            },
            "reminders": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "trigger": {
                            "type": "STRING",
                            "description": "Relativer Offset z. B. '-7d', '-1d', '-1h', '-15m'"
                        },
                        "frequency": {
                            "type": "STRING",
                            "enum": ["once", "daily"],
                            "description": "Häufigkeit der Erinnerung"
                        }
                    },
                    "required": ["trigger", "frequency"]
                },
                "description": "Gestaffelte Erinnerungslogik"
            }
        },
        "required": ["title", "start_time", "recurrence", "reminders"]
    },
    "handler": handle_create_calendar_entry
}

# 2. Bestehendes Tool für allgemeine Kalenderabfragen und Listen
TOOL = {
    "name": "calendar_manager",
    "description": (
        "Verwaltet persönliche Termine und den Zeitplan mit lokaler SQLite-Persistenz. "
        "Unterstützt natürliche Spracheingaben für Datum, Uhrzeit, Auflistung ('list') und Löschen ('delete')."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "Die Aktion: 'create' (neuen Termin eintragen), 'list' (Termine abfragen), 'delete' (löschen)."
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
            "event_id": {
                "type": "STRING",
                "description": "ID des Termins für 'delete'."
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

TOOLS = [CREATE_CALENDAR_ENTRY_TOOL, TOOL]
