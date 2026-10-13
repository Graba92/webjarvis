"""
backend/core/undo.py — Zentraler Undo-Stack für umkehrbare Operationen.
Verwaltet bis zu 10 Mutationen (Dateiverschiebungen, Lautstärke, Helligkeit etc.).
"""

from __future__ import annotations
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

MAX_DEPTH = 10

@dataclass
class _Entry:
    label: str
    undo: Callable[[], str]
    at: float = field(default_factory=time.monotonic)

_stack: list[_Entry] = []
_lock = threading.Lock()

def push_undo(label: str, undo_fn: Callable[[], str]) -> None:
    if not callable(undo_fn):
        return
    try:
        with _lock:
            _stack.append(_Entry(label=str(label)[:120], undo=undo_fn))
            while len(_stack) > MAX_DEPTH:
                _stack.pop(0)
    except Exception as e:
        print(f"[Undo] Registrierung fehlgeschlagen: {e}")

def can_undo() -> bool:
    with _lock:
        return bool(_stack)

def peek() -> str:
    with _lock:
        return _stack[-1].label if _stack else ""

def history() -> list[str]:
    with _lock:
        return [e.label for e in reversed(_stack)]

def undo_last() -> str:
    with _lock:
        entry = _stack.pop() if _stack else None

    if entry is None:
        return "Es gibt keine Aktion zum Rückgängigmachen. Ich tracke nur selbst ausgeführte Datei- und Systemeinstellungen."

    try:
        detail = entry.undo() or ""
    except Exception as e:
        return f"Fehler beim Rückgängigmachen von '{entry.label}': {e}"

    return f"Rückgängig gemacht: {entry.label}." + (f" {detail}" if detail else "")

def clear() -> None:
    with _lock:
        _stack.clear()
