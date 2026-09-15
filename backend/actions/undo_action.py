"""
backend/actions/undo_action.py — Macht die letzte registrierte Operation rückgängig.
"""

from __future__ import annotations
from core.undo import undo_last, peek, history

def undo_handler(parameters: dict | None = None, **kwargs) -> str:
    return undo_last()

TOOL = {
    "name": "undo",
    "description": "Macht die letzte ausgeführte Datei- oder Systemeinstellung rückgängig (z.B. nach 'Mach das rückgängig', 'Revert', 'Undo').",
    "parameters": {
        "type": "OBJECT",
        "properties": {}
    },
    "handler": undo_handler
}
