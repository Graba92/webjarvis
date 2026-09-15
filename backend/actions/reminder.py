"""
backend/actions/reminder.py — Zeitgesteuerte Benachrichtigungen auf CachyOS / KDE Plasma.
Nutzt notify-send für native Desktop-Meldungen.
"""

from __future__ import annotations
import threading
import time
import subprocess
import shutil

def _fire_notification(title: str, message: str, delay_seconds: float):
    def _worker():
        if delay_seconds > 0:
            time.sleep(delay_seconds)
        if shutil.which("notify-send"):
            try:
                proc = subprocess.Popen(["notify-send", "-u", "critical", "-a", "J.A.R.V.I.S.", title, message])
                proc.wait(timeout=5)
            except Exception:
                pass
        # Sound-Alert via pactl / paplay
        if shutil.which("paplay"):
            try:
                proc = subprocess.Popen(["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"], stderr=subprocess.DEVNULL)
                proc.wait(timeout=5)
            except Exception:
                pass

    t = threading.Thread(target=_worker, daemon=True, name=f"reminder-{title[:15]}")
    t.start()

def reminder(parameters: dict, **kwargs) -> str:
    message = str(parameters.get("message", "")).strip()
    seconds = float(parameters.get("seconds", 0))

    if not message:
        return "Erinnerungstext fehlt."

    if seconds <= 0:
        minutes = float(parameters.get("minutes", 0))
        if minutes > 0:
            seconds = minutes * 60

    if seconds <= 0:
        seconds = 60

    _fire_notification("J.A.R.V.I.S. Erinnerung", message, seconds)
    return f"Erinnerung für '{message}' in {int(seconds)} Sekunden eingerichtet."

TOOL = {
    "name": "reminder",
    "description": "Richtet eine zeitgesteuerte Desktop-Benachrichtigung auf CachyOS ein.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "message": {
                "type": "STRING",
                "description": "Der Erinnerungstext."
            },
            "seconds": {
                "type": "NUMBER",
                "description": "Wartezeit in Sekunden (oder Minuten)."
            },
            "minutes": {
                "type": "NUMBER",
                "description": "Optionale Wartezeit in Minuten."
            }
        },
        "required": ["message"]
    },
    "handler": reminder
}
