"""
backend/actions/backup_agent.py — Gemini Tool-Bridge für 1-Click Backup & Restore ("Brain Vault").
"""

from __future__ import annotations
from core.backup_manager import export_brain, import_brain

def backup_agent(action: str = "export", path: str = "", passphrase: str = "", **kwargs) -> str:
    """
    Sichert oder restauriert das vollständige Systemgedächtnis (Langzeitspeicher, Termine, Vektordaten, MCPs, Prompts).
    - action='export': Erstellt ein ZIP-Backup im backups/-Verzeichnis.
    - action='import': Stellt Daten aus einem bestehenden ZIP-Archiv wieder her.
    """
    act = (action or "export").strip().lower()

    if act in ("export", "backup", "save"):
        return export_brain(output_path=path or None, passphrase=passphrase or None)
    elif act in ("import", "restore", "load"):
        if not path:
            return "Fehler: Für den Import muss ein Pfad zum ZIP-Archiv angegeben werden."
        return import_brain(archive_path=path, passphrase=passphrase or None)
    return f"Unbekannte Aktion '{action}'. Gültige Aktionen sind: 'export' und 'import'."

TOOL = {
    "name": "backup_agent",
    "description": (
        "Erstellt ein 1-Click Backup des gesamten KI-Gedächtnisses (Langzeit-Fakten, Termine, "
        "Vektor-Datenbank, MCP-Server, SOUL.md) als ZIP-Archiv oder stellt ein vorhandenes Backup wieder her."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "Die Aktion: 'export' (Brain sichern) oder 'import' (Brain wiederherstellen)."
            },
            "path": {
                "type": "STRING",
                "description": "Optionaler Ziel- oder Quellpfad für das ZIP-Archiv."
            },
            "passphrase": {
                "type": "STRING",
                "description": "Optionale Passphrase zur Sicherung des Archivs."
            }
        },
        "required": ["action"]
    },
    "handler": backup_agent
}
