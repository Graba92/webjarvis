"""
backend/actions/open_app.py — Anwendungsstarter für CachyOS / KDE Plasma Linux.
Durchsucht Desktop-Einträge (/usr/share/applications, ~/.local/share/applications)
und startet Anwendungen entkoppelt im Hintergrund.
"""

from __future__ import annotations
import os
import subprocess
import shutil
from pathlib import Path

DESKTOP_DIRS = [
    Path("/usr/share/applications"),
    Path.home() / ".local/share/applications"
]

def _find_app(query: str) -> tuple[str, str] | None:
    query_clean = query.lower().strip()
    
    # 1. Direkter Befehl im PATH vorhanden?
    which_path = shutil.which(query_clean)
    if which_path:
        return query_clean, which_path

    # 2. Desktop-Dateien durchsuchen
    candidates = []
    for d in DESKTOP_DIRS:
        if not d.exists():
            continue
        for f in d.glob("*.desktop"):
            name = f.stem.lower()
            if query_clean in name:
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    exec_cmd = None
                    app_name = f.stem
                    for line in content.splitlines():
                        if line.startswith("Name=") and not app_name:
                            app_name = line.split("=", 1)[1].strip()
                        if line.startswith("Exec=") and not exec_cmd:
                            raw_cmd = line.split("=", 1)[1].strip()
                            # Feldcodes wie %u, %U, %f etc. entfernen
                            exec_cmd = " ".join([part for part in raw_cmd.split() if not part.startswith("%")])
                    if exec_cmd:
                        candidates.append((app_name, exec_cmd))
                except Exception:
                    continue

    if candidates:
        # Beste Übereinstimmung
        candidates.sort(key=lambda c: len(c[0]))
        return candidates[0]

    return None

_ACTIVE_PROCESSES: list[subprocess.Popen] = []

def _reap_processes():
    """Prüft mit .poll() auf beendete Prozesse, um unclosed resource warnings und Zombies zu verhindern."""
    global _ACTIVE_PROCESSES
    still_active = []
    for proc in _ACTIVE_PROCESSES:
        if proc.poll() is None:
            still_active.append(proc)
    _ACTIVE_PROCESSES = still_active

def open_app(parameters: dict, **kwargs) -> str:
    app_query = str(parameters.get("app_name", "")).strip()
    if not app_query:
        return "Kein Anwendungsname angegeben."

    found = _find_app(app_query)
    if not found:
        return f"Konnte keine Anwendung für '{app_query}' auf dem System finden."

    name, cmd = found
    try:
        _reap_processes()
        proc = subprocess.Popen(
            cmd,
            shell=True,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        # Unmittelbarer Status-Check via .poll() und Referenzhaltung zur Vermeidung von Destruktor-Warnungen
        proc.poll()
        _ACTIVE_PROCESSES.append(proc)
        return f"Anwendung '{name}' ({cmd}) wurde erfolgreich gestartet."
    except Exception as e:
        return f"Fehler beim Starten von '{name}': {e}"

TOOL = {
    "name": "open_app",
    "description": "Startet eine installierte Desktop-Anwendung auf CachyOS Linux (z. B. 'brave', 'dolphin', 'konsole', 'spotify', 'vlc', 'discord', 'steam').",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "app_name": {
                "type": "STRING",
                "description": "Name oder Alias der zu startenden Anwendung."
            }
        },
        "required": ["app_name"]
    },
    "handler": open_app
}
