"""
backend/memory/memory_manager.py — Budgetiertes Zwei-Ebenen-Langzeitgedächtnis.
- Level 1: System-Prompt-Core (max 900 Zeichen) mit Identität & Top-Recency-Fakten.
- Level 2: On-Demand Indizierung & Keyword-Suche via recall_memory Tool.
"""

from __future__ import annotations
import os
import tempfile
import json
import re
from datetime import datetime
from threading import Lock
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MEMORY_PATH = BASE_DIR / "memory" / "long_term.json"
_lock = Lock()
MAX_VALUE_LENGTH = 380

MEMORY_MAX_CHARS = 200_000
PROMPT_CORE_CHARS = 900
PROMPT_INDEX_CHARS = 420
PROMPT_MAX_PER_CATEGORY = 6

def _empty_memory() -> dict:
    return {
        "identity": {},
        "preferences": {},
        "projects": {},
        "relationships": {},
        "wishes": {},
        "notes": {},
        "sessions": []
    }

def load_memory() -> dict:
    if not MEMORY_PATH.exists():
        return _empty_memory()
    with _lock:
        try:
            data = json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                base = _empty_memory()
                for k in base:
                    if k not in data:
                        data[k] = {} if k != "sessions" else []
                return data
            return _empty_memory()
        except Exception as e:
            print(f"[Memory] Ladefehler: {e}")
            return _empty_memory()

def save_memory(memory: dict) -> None:
    if not isinstance(memory, dict):
        return
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        content = json.dumps(memory, indent=2, ensure_ascii=False)
        temp_file = tempfile.NamedTemporaryFile("w", dir=MEMORY_PATH.parent, delete=False, encoding="utf-8")
        try:
            temp_file.write(content)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_file.close()
            os.replace(temp_file.name, MEMORY_PATH)
        except Exception:
            if os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass
            raise

def _truncate_value(val: str) -> str:
    if isinstance(val, str) and len(val) > MAX_VALUE_LENGTH:
        return val[:MAX_VALUE_LENGTH].rstrip() + "…"
    return val

def _entry_value(entry) -> str:
    if isinstance(entry, dict):
        return str(entry.get("value", "") or "").strip()
    return str(entry or "").strip()

def _pretty(key: str) -> str:
    return key.replace("_", " ").strip()

_CATEGORY_LABELS = {
    "preferences": "Präferenzen",
    "projects": "Aktive Projekte / Ziele",
    "relationships": "Personen / Kontakte",
    "wishes": "Wünsche / Vorhaben",
    "notes": "Notizen",
}

_IDENTITY_FIELDS = ["name", "city", "os", "desktop", "language"]

def format_memory_for_prompt(memory: dict | None) -> str:
    if not memory:
        return ""

    core_lines: list[str] = []
    identity = memory.get("identity", {}) or {}
    for field in _IDENTITY_FIELDS:
        val = _entry_value(identity.get(field))
        if val:
            core_lines.append(f"{field.title()}: {val}")
    for key, entry in identity.items():
        if key in _IDENTITY_FIELDS:
            continue
        val = _entry_value(entry)
        if val:
            core_lines.append(f"{_pretty(key).title()}: {val}")

    rest: list[tuple[str, str, str, str]] = []
    for cat in _CATEGORY_LABELS:
        for key, entry in (memory.get(cat, {}) or {}).items():
            val = _entry_value(entry)
            if not val:
                continue
            updated = (entry.get("updated", "") if isinstance(entry, dict) else "") or "0000-00-00"
            rest.append((updated, cat, key, val))
    rest.sort(key=lambda t: t[0], reverse=True)

    used = sum(len(l) + 1 for l in core_lines)
    shown: dict[str, list[str]] = {}
    overflow: dict[str, list[str]] = {}
    per_cat_used: dict[str, int] = {}

    for _updated, cat, key, val in rest:
        line = f"  - {_pretty(key).title()}: {val}"
        if per_cat_used.get(cat, 0) < PROMPT_MAX_PER_CATEGORY and used + len(line) + 1 <= PROMPT_CORE_CHARS:
            shown.setdefault(cat, []).append(line)
            per_cat_used[cat] = per_cat_used.get(cat, 0) + 1
            used += len(line) + 1
        else:
            overflow.setdefault(cat, []).append(_pretty(key))

    indexed: list[str] = []
    if overflow:
        for cat in _CATEGORY_LABELS:
            indexed.extend(overflow.get(cat, []))

    for cat, label in _CATEGORY_LABELS.items():
        if shown.get(cat):
            core_lines.append("")
            core_lines.append(f"{label}:")
            core_lines.extend(shown[cat])

    if not core_lines and not indexed:
        return ""

    out = [
        "[GESPEICHERTER KONTEXT ÜBER DEN NUTZER — natürlich im Dialog berücksichtigen]",
        *core_lines,
    ]

    if indexed:
        out.append("")
        out.append(f"[WEITERE ERINNERUNGEN AUF DER FESTPLATTE (mit recall_memory abrufbar): {', '.join(indexed[:10])}]")

    return "\n".join(out) + "\n"

def search_memory(query: str, limit: int = 8) -> str:
    memory = load_memory()
    words = [w for w in re.split(r"[^\w]+", (query or "").lower()) if len(w) > 1]
    rows: list[tuple[int, str, str, str]] = []

    for cat, items in memory.items():
        if not isinstance(items, dict):
            continue
        for key, entry in items.items():
            val = _entry_value(entry)
            if not val:
                continue
            score = 0
            hay_key = _pretty(key).lower()
            hay_val = val.lower()
            for w in words:
                if w == hay_key:
                    score += 10
                elif w in hay_key:
                    score += 6
                if w in hay_val:
                    score += 3
                if w in cat:
                    score += 1
            if words and score > 0:
                rows.append((score, cat, key, val))
            elif not words:
                rows.append((1, cat, key, val))

    if not rows:
        return f"Keine Fakten zu '{query}' im Langzeitgedächtnis gefunden."

    rows.sort(key=lambda r: (-r[0], r[2]))
    lines = [f"{cat}/{_pretty(key)}: {val}" for _s, cat, key, val in rows[:limit]]
    return f"Gedächtnisabfrage für '{query}':\n" + "\n".join(lines)

MEMORY_MD_PATH = BASE_DIR / "MEMORY.md"

def append_to_memory_md(category: str, key: str, value: str):
    """Schreibt neue Erkenntnisse und Präferenzen autonom in MEMORY.md fort."""
    try:
        if MEMORY_MD_PATH.exists():
            content = MEMORY_MD_PATH.read_text(encoding="utf-8")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            entry_line = f"- [{timestamp}] **{category.title()} / {_pretty(key)}:** {value}\n"
            if "## 6. Autonome Notizen & Neue Erkenntnisse" not in content:
                content += "\n---\n\n## 6. Autonome Notizen & Neue Erkenntnisse\n"
            content += entry_line
            MEMORY_MD_PATH.write_text(content, encoding="utf-8")
    except Exception as e:
        print(f"[Memory] Fehler beim Schreiben in MEMORY.md: {e}")

def remember(key: str, value: str, category: str = "notes") -> str:
    valid = {"identity", "preferences", "projects", "relationships", "wishes", "notes"}
    if category not in valid:
        category = "notes"
    mem = load_memory()
    if category not in mem or not isinstance(mem[category], dict):
        mem[category] = {}
    mem[category][key] = {
        "value": _truncate_value(value),
        "updated": datetime.now().strftime("%Y-%m-%d")
    }
    save_memory(mem)
    append_to_memory_md(category, key, value)
    return f"Gemerkt: {category}/{key} = {value}"

def forget(key: str, category: str = "notes") -> str:
    mem = load_memory()
    cat_data = mem.get(category, {})
    if key in cat_data:
        del cat_data[key]
        mem[category] = cat_data
        save_memory(mem)
        return f"Vergessen: {category}/{key}"
    return f"Nicht gefunden: {category}/{key}"

def all_entries_for_ui() -> list[dict]:
    memory = load_memory()
    rows = []
    for cat, items in memory.items():
        if not isinstance(items, dict):
            continue
        for key, entry in items.items():
            val = _entry_value(entry)
            if val:
                rows.append({
                    "category": cat,
                    "key": key,
                    "value": val,
                    "updated": entry.get("updated", "") if isinstance(entry, dict) else ""
                })
    rows.sort(key=lambda r: r.get("updated", "0000-00-00"), reverse=True)
    return rows
