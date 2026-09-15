"""
backend/actions/file_controller.py — Dateisystem-Steuerung mit automatischer Undo-Sicherung.
Unterstützt Lesen, Schreiben, Verschieben, Löschen (send2trash) und Desktop-Organisation.
"""

from __future__ import annotations
import os
import shutil
from pathlib import Path
from send2trash import send2trash
from core.undo import push_undo

def _resolve_path(p: str) -> Path:
    expanded = os.path.expanduser(p)
    return Path(expanded).resolve()

def file_controller(parameters: dict, **kwargs) -> str:
    action = str(parameters.get("action", "")).lower().strip()
    path_str = parameters.get("path", "")
    dest_str = parameters.get("destination", "")
    content = parameters.get("content", "")

    if not path_str and action != "organize_desktop":
        return "Pfad muss angegeben werden."

    target = _resolve_path(path_str) if path_str else Path.home() / "Schreibtisch"

    if action in ("read", "lesen", "cat"):
        if not target.exists():
            return f"Datei {target} existiert nicht."
        if not target.is_file():
            return f"{target} ist keine reguläre Datei."
        try:
            text = target.read_text(encoding="utf-8", errors="replace")
            if len(text) > 4000:
                text = text[:4000] + f"\n... [Gekürzt; Datei hat {len(text)} Zeichen]"
            return f"Inhalt von {target.name}:\n{text}"
        except Exception as e:
            return f"Fehler beim Lesen von {target}: {e}"

    elif action in ("write", "schreiben", "create"):
        parent = target.parent
        parent.mkdir(parents=True, exist_ok=True)
        old_content = None
        existed = target.exists()
        if existed:
            try:
                if target.stat().st_size < 1_000_000:
                    old_content = target.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass

        try:
            target.write_text(content, encoding="utf-8")
            if existed and old_content is not None:
                push_undo(f"Überschreiben von {target.name}", lambda: target.write_text(old_content, encoding="utf-8") or f"{target.name} wiederhergestellt")
            elif not existed:
                push_undo(f"Erstellung von {target.name}", lambda: target.unlink(missing_ok=True) or f"{target.name} entfernt")
            return f"Datei {target} erfolgreich geschrieben ({len(content)} Zeichen)."
        except Exception as e:
            return f"Fehler beim Schreiben von {target}: {e}"

    elif action in ("list", "ls", "dir"):
        if not target.exists() or not target.is_dir():
            return f"Verzeichnis {target} existiert nicht."
        try:
            items = []
            for item in target.iterdir():
                prefix = "[DIR] " if item.is_dir() else "[FILE]"
                items.append(f"{prefix} {item.name}")
            return f"Inhalt von {target}:\n" + "\n".join(items[:50]) + (f"\n(+{len(items)-50} weitere)" if len(items) > 50 else "")
        except Exception as e:
            return f"Fehler beim Auflisten von {target}: {e}"

    elif action in ("move", "rename", "verschieben"):
        if not dest_str:
            return "Zielpfad (destination) erforderlich."
        dest = _resolve_path(dest_str)
        if not target.exists():
            return f"Quelldatei {target} existiert nicht."
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(target), str(dest))
            push_undo(f"Verschieben von {target.name} nach {dest.name}", lambda: shutil.move(str(dest), str(target)) or f"Zurück nach {target} verschoben")
            return f"{target} erfolgreich nach {dest} verschoben."
        except Exception as e:
            return f"Fehler beim Verschieben: {e}"

    elif action in ("delete", "loeschen", "remove"):
        if not target.exists():
            return f"Datei oder Ordner {target} existiert nicht."
        try:
            send2trash(str(target))
            return f"{target} wurde sicher in den Papierkorb verschoben."
        except Exception as e:
            return f"Fehler beim Verschieben in den Papierkorb: {e}"

    elif action == "organize_desktop":
        desktop_dir = Path.home() / "Schreibtisch"
        if not desktop_dir.exists():
            desktop_dir = Path.home() / "Desktop"
        if not desktop_dir.exists():
            return "Schreibtisch-Verzeichnis nicht gefunden."

        categories = {
            "Bilder": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"},
            "Dokumente": {".pdf", ".docx", ".txt", ".md", ".xlsx", ".pptx", ".csv"},
            "Code": {".py", ".sh", ".js", ".ts", ".tsx", ".html", ".css", ".json"},
            "Archive": {".zip", ".tar", ".gz", ".xz", ".7z", ".rar"},
            "Audio_Video": {".mp3", ".wav", ".flac", ".mp4", ".mkv", ".webm"}
        }

        journal = []
        moved_count = 0
        for item in desktop_dir.iterdir():
            if item.is_file() and not item.name.startswith("."):
                ext = item.suffix.lower()
                matched_cat = None
                for cat_name, exts in categories.items():
                    if ext in exts:
                        matched_cat = cat_name
                        break
                if matched_cat:
                    target_folder = desktop_dir / matched_cat
                    target_folder.mkdir(exist_ok=True)
                    target_dest = target_folder / item.name
                    if not target_dest.exists():
                        shutil.move(str(item), str(target_dest))
                        journal.append((target_dest, item))
                        moved_count += 1

        if journal:
            def _undo_organize():
                restored = 0
                for curr, orig in journal:
                    if curr.exists():
                        shutil.move(str(curr), str(orig))
                        restored += 1
                return f"{restored} Dateien auf den Schreibtisch zurückgeführt."
            push_undo(f"Schreibtisch-Organisation ({moved_count} Dateien)", _undo_organize)
            return f"Schreibtisch aufgeräumt: {moved_count} Dateien in Kategorie-Ordner sortiert. (Undo verfügbar)"
        else:
            return "Keine losen Dateien auf dem Schreibtisch zum Einsortieren gefunden."

    return f"Unbekannte Aktion '{action}'. Unterstützt: read, write, list, move, delete, organize_desktop."

TOOL = {
    "name": "file_controller",
    "description": "Verwaltet das Dateisystem: Dateien lesen, schreiben, verschieben, löschen (Papierkorb) oder den Schreibtisch aufräumen. Alle Mutationen sind über Undo reversibel.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "Aktion: 'read', 'write', 'list', 'move', 'delete', 'organize_desktop'"
            },
            "path": {
                "type": "STRING",
                "description": "Pfad zur Zieldatei oder dem Verzeichnis."
            },
            "destination": {
                "type": "STRING",
                "description": "Zielpfad bei Verschiebe- oder Umbenennungs-Aktionen."
            },
            "content": {
                "type": "STRING",
                "description": "Inhalt beim Schreiben einer Datei."
            }
        },
        "required": ["action"]
    },
    "handler": file_controller
}
