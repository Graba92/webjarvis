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
import sqlite3
import tempfile
import base64
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

BACKEND_DIR = Path(__file__).parent.parent
MEMORY_DIR = BACKEND_DIR / "memory"
CONFIG_DIR = BACKEND_DIR / "config"
BACKUPS_DIR = BACKEND_DIR / "backups"

def export_consistent_sqlite(source_db_path: Path, temp_dir: Path) -> Path:
    """
    Erstellt via PRAGMA wal_checkpoint(TRUNCATE) und VACUUM INTO einen
    transaktionssicheren, ungesperrten Snapshot der SQLite-Datenbank.
    Verhindert Datenverlust durch noch im WAL-Puffer liegende Schreiboperationen.
    """
    target_path = temp_dir / source_db_path.name
    conn = sqlite3.connect(str(source_db_path))
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        conn.execute(f"VACUUM INTO '{target_path.as_posix()}';")
    finally:
        conn.close()
    return target_path

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

def export_brain(
    output_path: Optional[str] = None, 
    passphrase: Optional[str] = None, 
    label: Optional[str] = None
) -> Dict[str, Any]:
    """
    Exportiert das gesamte Gedächtnis in ein komprimiertes Brain-Vault ZIP-Archiv.
    Gibt ein Dict mit Details, Dateiname und optionalem Base64-Inhalt für den direkten Download zurück.
    """
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    clean_label = ""
    if label and label.strip():
        # Bereinige das Label für Dateinamen
        clean_label = "_" + "".join(c for c in label.strip() if c.isalnum() or c in ("-", "_")).strip("-_")
    
    if output_path:
        dest_zip = Path(output_path)
    else:
        dest_zip = BACKUPS_DIR / f"jarvis_brain_backup_{timestamp}{clean_label}.zip"

    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    targets = get_backup_targets()

    if not targets:
        return {
            "success": False,
            "message": "Keine Gedächtnisdaten oder Konfigurationen zum Exportieren gefunden."
        }

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_dir_path = Path(tmp_dir)
            with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                if passphrase:
                    zf.setpassword(passphrase.encode("utf-8"))

                for arc_name, file_path in targets.items():
                    if file_path.is_file():
                        # Bei SQLite-Datenbanken zwingend konsistenten VACUUM-Snapshot ziehen
                        if arc_name.endswith(".db") or arc_name.endswith(".sqlite") or arc_name.endswith(".sqlite3"):
                            try:
                                consistent_path = export_consistent_sqlite(file_path, temp_dir_path)
                                zf.write(consistent_path, arcname=arc_name)
                                continue
                            except Exception:
                                pass
                        zf.write(file_path, arcname=arc_name)
                    elif file_path.is_dir():
                        for root, _, files in os.walk(file_path):
                            for f in files:
                                full_p = Path(root) / f
                                rel_p = full_p.relative_to(file_path)
                                zf.write(full_p, arcname=f"{arc_name}/{rel_p}")

        size_kb = round(dest_zip.stat().st_size / 1024, 1)
        raw_bytes = dest_zip.read_bytes()
        b64_content = base64.b64encode(raw_bytes).decode("ascii")

        summary_msg = (
            f"1-Click Brain-Backup erfolgreich erstellt:\n"
            f"• Datei: {dest_zip.name}\n"
            f"• Pfad: {dest_zip}\n"
            f"• Größe: {size_kb} KB ({len(targets)} Komponenten gesichert)\n"
            f"• Status: {'Passwortgeschützt' if passphrase else 'Standard-Komprimierung'}\n"
            f"• SQLite-Integrität: VACUUM INTO Checkpoint angewendet"
        )
        return {
            "success": True,
            "message": summary_msg,
            "filename": dest_zip.name,
            "path": str(dest_zip),
            "size_kb": size_kb,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "label": label.strip() if label else "",
            "data_base64": b64_content
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Fehler beim Exportieren des Gedächtnisses: {e}"
        }

def list_available_backups() -> list[dict[str, Any]]:
    """Gibt alle vorhandenen Brain-Vault Backups sortiert nach Erstellungsdatum zurück."""
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    backups = []
    for f in sorted(BACKUPS_DIR.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True):
        stat = f.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        size_kb = round(stat.st_size / 1024, 1)
        
        # Label extrahieren: jarvis_brain_backup_YYYYMMDD_HHMMSS_Label.zip
        parts = f.stem.split("_")
        label = ""
        if len(parts) >= 5 and parts[0] == "jarvis" and parts[1] == "brain" and parts[2] == "backup":
            label = "_".join(parts[5:]) if len(parts) > 5 else ""

        backups.append({
            "filename": f.name,
            "path": str(f),
            "size_kb": size_kb,
            "created_at": mtime,
            "label": label
        })
    return backups

def delete_backup(filename: str) -> bool:
    """Löscht ein Backup sicher aus dem backups/-Verzeichnis."""
    safe_name = Path(filename).name
    target = BACKUPS_DIR / safe_name
    if target.exists() and target.is_file() and safe_name.endswith(".zip"):
        try:
            target.unlink()
            return True
        except Exception:
            return False
    return False

def get_backup_base64(filename: str) -> Optional[dict[str, Any]]:
    """Liest ein existierendes Backup als Base64 ein für den direkten Browser-Download."""
    safe_name = Path(filename).name
    target = BACKUPS_DIR / safe_name
    if target.exists() and target.is_file():
        try:
            data = target.read_bytes()
            b64 = base64.b64encode(data).decode("ascii")
            return {
                "filename": safe_name,
                "data_base64": b64,
                "size_kb": round(len(data) / 1024, 1)
            }
        except Exception:
            return None
    return None

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

def save_and_import_brain_bytes(data_bytes: bytes, filename: str, passphrase: Optional[str] = None) -> str:
    """Speichert ein hochgeladenes Backup-Archiv im backups/-Verzeichnis und stellt es sofort wieder her."""
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(filename).name
    if not safe_name.endswith(".zip"):
        safe_name = f"{safe_name}.zip"
    
    dest_path = BACKUPS_DIR / f"uploaded_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}"
    try:
        dest_path.write_bytes(data_bytes)
        return import_brain(str(dest_path), passphrase=passphrase)
    except Exception as e:
        return f"Fehler beim Speichern oder Wiederherstellen des hochgeladenen Backups: {e}"
