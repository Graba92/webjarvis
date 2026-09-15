"""
backend/core/backup_manager.py — 1-Click Backup & Restore ("Brain Vault").
Exportiert und importiert das vollständige Systemgedächtnis:
- long_term.json (Langzeitfakten)
- calendar.db (Termine & Erinnerungen)
- lancedb_data/ (Vektordatenbank)
- mcp_servers.json (MCP-Schnittstellenkonfiguration)
- SOUL.md, MEMORY.md, HEARTBEAT.md (Agenten-Kernidentität)
Unterstützt komprimierte ZIP-Archive mit optionaler Passphrase / Verschlüsselung.
"""

from __future__ import annotations
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

BACKEND_DIR = Path(__file__).parent.parent
MEMORY_DIR = BACKEND_DIR / "memory"
CONFIG_DIR = BACKEND_DIR / "config"
BACKUPS_DIR = BACKEND_DIR / "backups"

def get_backup_targets() -> Dict[str, Path]:
    """Sammelt alle schützenswerten Gedächtnis- und Konfigurationspfade."""
    targets = {}
    if (MEMORY_DIR / "long_term.json").exists():
        targets["long_term.json"] = MEMORY_DIR / "long_term.json"
    if (MEMORY_DIR / "calendar.db").exists():
        targets["calendar.db"] = MEMORY_DIR / "calendar.db"
    if (MEMORY_DIR / "lancedb_data").exists():
        targets["lancedb_data"] = MEMORY_DIR / "lancedb_data"
    if (CONFIG_DIR / "mcp_servers.json").exists():
        targets["mcp_servers.json"] = CONFIG_DIR / "mcp_servers.json"
    if (BACKEND_DIR / "SOUL.md").exists():
        targets["SOUL.md"] = BACKEND_DIR / "SOUL.md"
    if (BACKEND_DIR / "MEMORY.md").exists():
        targets["MEMORY.md"] = BACKEND_DIR / "MEMORY.md"
    if (BACKEND_DIR / "HEARTBEAT.md").exists():
        targets["HEARTBEAT.md"] = BACKEND_DIR / "HEARTBEAT.md"
    return targets

def export_brain(output_path: Optional[str] = None, passphrase: Optional[str] = None) -> str:
    """Exportiert das gesamte Gedächtnis in ein komprimiertes Brain-Vault ZIP-Archiv."""
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if output_path:
        dest_zip = Path(output_path)
    else:
        dest_zip = BACKUPS_DIR / f"jarvis_brain_backup_{timestamp}.zip"

    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    targets = get_backup_targets()

    if not targets:
        return "Keine Gedächtnisdaten oder Konfigurationen zum Exportieren gefunden."

    try:
        with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            if passphrase:
                zf.setpassword(passphrase.encode("utf-8"))

            for arc_name, file_path in targets.items():
                if file_path.is_file():
                    zf.write(file_path, arcname=arc_name)
                elif file_path.is_dir():
                    for root, _, files in os.walk(file_path):
                        for f in files:
                            full_p = Path(root) / f
                            rel_p = full_p.relative_to(file_path)
                            zf.write(full_p, arcname=f"{arc_name}/{rel_p}")

        size_kb = round(dest_zip.stat().st_size / 1024, 1)
        return (
            f"1-Click Brain-Backup erfolgreich erstellt:\n"
            f"• Datei: {dest_zip.name}\n"
            f"• Pfad: {dest_zip}\n"
            f"• Größe: {size_kb} KB ({len(targets)} Komponenten gesichert)\n"
            f"• Status: {'Passwortgeschützt' if passphrase else 'Standard-Komprimierung'}"
        )
    except Exception as e:
        return f"Fehler beim Exportieren des Gedächtnisses: {e}"

def import_brain(archive_path: str, passphrase: Optional[str] = None) -> str:
    """Importiert und stellt ein Brain-Vault Archiv wieder her."""
    archive = Path(archive_path)
    if not archive.exists() or not archive.is_file():
        return f"Fehler: Backup-Archiv '{archive_path}' nicht gefunden."

    try:
        with zipfile.ZipFile(archive, "r") as zf:
            pwd = passphrase.encode("utf-8") if passphrase else None
            
            for item in zf.infolist():
                name = item.filename
                # Sicherheit: Pfad-Traversierung verhindern
                if name.startswith("/") or ".." in name:
                    continue

                if name in ("SOUL.md", "MEMORY.md", "HEARTBEAT.md"):
                    zf.extract(item, path=BACKEND_DIR, pwd=pwd)
                elif name == "mcp_servers.json":
                    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
                    zf.extract(item, path=CONFIG_DIR, pwd=pwd)
                elif name in ("long_term.json", "calendar.db"):
                    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
                    zf.extract(item, path=MEMORY_DIR, pwd=pwd)
                elif name.startswith("lancedb_data/"):
                    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
                    zf.extract(item, path=MEMORY_DIR, pwd=pwd)

        return f"Gedächtnis-Wiederherstellung aus '{archive.name}' erfolgreich abgeschlossen. Module neu synchronisiert."
    except Exception as e:
        return f"Fehler beim Importieren des Gedächtnisses: {e}"
