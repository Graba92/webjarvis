"""
backend/actions/computer_settings.py — OS- & Hardware-Steuerung für CachyOS / Arch Linux.
- PipeWire Audio (pactl) mit automatischer Undo-Registrierung
- Display-Helligkeit (brightnessctl) mit Undo
- Netzwerk / WLAN (nmcli)
- Irreversible Aktionen (Shutdown, Reboot) durch core.confirm.request geschützt
"""

from __future__ import annotations
import subprocess
import re
import shutil
from core.undo import push_undo
from core.confirm import request as confirm_request

def _get_current_volume() -> int:
    try:
        res = subprocess.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"], capture_output=True, text=True, timeout=2)
        match = re.search(r"(\d+)%", res.stdout)
        if match:
            return int(match.group(1))
    except Exception:
        pass
    return 50

def _set_volume(pct: int) -> str:
    clamped = max(0, min(150, int(pct)))
    subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{clamped}%"], check=True, timeout=3)
    return f"Lautstärke auf {clamped}% gesetzt."

def _get_current_brightness() -> int:
    try:
        res = subprocess.run(["brightnessctl", "get"], capture_output=True, text=True, timeout=2)
        max_res = subprocess.run(["brightnessctl", "max"], capture_output=True, text=True, timeout=2)
        curr = int(res.stdout.strip())
        mx = int(max_res.stdout.strip())
        if mx > 0:
            return int((curr / mx) * 100)
    except Exception:
        pass
    return 80

def _set_brightness(pct: int) -> str:
    clamped = max(5, min(100, int(pct)))
    subprocess.run(["brightnessctl", "set", f"{clamped}%"], check=True, timeout=3)
    return f"Display-Helligkeit auf {clamped}% eingestellt."

def computer_settings(parameters: dict, **kwargs) -> str:
    action = str(parameters.get("action", "")).lower().strip()
    value = parameters.get("value")

    if action in ("volume", "set_volume", "lautstaerke"):
        if value is None:
            return f"Aktuelle Lautstärke: {_get_current_volume()}%"
        try:
            val_int = int(value)
            old_vol = _get_current_volume()
            res = _set_volume(val_int)
            push_undo(f"Lautstärke {val_int}% → {old_vol}%", lambda: _set_volume(old_vol))
            return f"{res} (Vorher: {old_vol}%)"
        except Exception as e:
            return f"Fehler beim Setzen der Lautstärke: {e}"

    elif action in ("mute", "unmute", "stumm"):
        try:
            subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"], check=True, timeout=3)
            push_undo("Mute toggle rückgängig", lambda: subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"], timeout=3).stdout or "Mute getoggelt")
            return "Audio-Stummschaltung umgeschaltet."
        except Exception as e:
            return f"Fehler bei Audio Mute: {e}"

    elif action in ("brightness", "helligkeit"):
        if not shutil.which("brightnessctl"):
            return "brightnessctl ist auf dem System nicht installiert."
        if value is None:
            return f"Aktuelle Helligkeit: {_get_current_brightness()}%"
        try:
            val_int = int(value)
            old_b = _get_current_brightness()
            res = _set_brightness(val_int)
            push_undo(f"Helligkeit {val_int}% → {old_b}%", lambda: _set_brightness(old_b))
            return f"{res} (Vorher: {old_b}%)"
        except Exception as e:
            return f"Fehler beim Ändern der Helligkeit: {e}"

    elif action in ("wifi_status", "wifi_networks"):
        try:
            res = subprocess.run(["nmcli", "-t", "-f", "SSID,SIGNAL,BARS,SECURITY", "device", "wifi", "list"], capture_output=True, text=True, timeout=5)
            lines = [line for line in res.stdout.strip().split("\n") if line]
            if not lines:
                return "Keine WLAN-Netzwerke in Reichweite gefunden."
            return "Verfügbare WLAN-Netzwerke:\n" + "\n".join(lines[:6])
        except Exception as e:
            return f"Fehler bei WLAN-Abfrage via nmcli: {e}"

    elif action in ("reboot", "neustart", "restart", "rebooten", "sys_reboot"):
        def _do_reboot():
            subprocess.run(["systemctl", "reboot"], timeout=5)
            return "System fährt herunter zum Neustart."
        return confirm_request(
            action="reboot",
            label="System neu starten",
            detail="Möchten Sie CachyOS jetzt wirklich neu starten? Ungespeicherte Daten gehen verloren.",
            run=_do_reboot,
            timeout=90
        )

    elif action in ("shutdown", "herunterfahren", "poweroff", "ausschalten", "ausmachen", "abschalten", "turn_off", "sys_shutdown"):
        def _do_shutdown():
            subprocess.run(["systemctl", "poweroff"], timeout=5)
            return "System schaltet sich ab."
        return confirm_request(
            action="shutdown",
            label="System herunterfahren",
            detail="Möchten Sie CachyOS jetzt vollständig ausschalten? Alle laufenden Prozesse werden beendet.",
            run=_do_shutdown,
            timeout=90
        )

    elif action in ("lock_screen", "sperren", "lock"):
        try:
            subprocess.run(["loginctl", "lock-session"], timeout=5)
            return "Bildschirm wurde gesperrt."
        except Exception as e:
            return f"Fehler beim Sperren: {e}"

    return f"Unbekannte Einstellung '{action}'. Unterstützt: volume, mute, brightness, wifi_status, reboot, shutdown, lock_screen."

TOOL = {
    "name": "computer_settings",
    "description": (
        "Steuert CachyOS/Arch Linux Systemeinstellungen: Audio (Lautstärke, Mute über PipeWire/pactl), "
        "Display-Helligkeit (brightnessctl), WLAN-Netzwerke (nmcli) sowie irreversible System-Power-Befehle "
        "(Shutdown / Herunterfahren / Ausschalten, Reboot / Neustart, Sperren). "
        "WICHTIG: Rufe diese Funktion IMMER sofort auf, wenn der Benutzer den PC/das System herunterfahren, ausschalten oder neu starten möchte!"
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "Die auszuführende Aktion: 'shutdown' (Herunterfahren/Ausschalten), 'reboot' (Neustart), 'volume' (Lautstärke), 'mute' (Stummschalten), 'brightness' (Helligkeit), 'wifi_status' (WLAN), 'lock_screen' (Bildschirm sperren)."
            },
            "value": {
                "type": "STRING",
                "description": "Optionaler Wert, z.B. 60 für 60% Lautstärke oder Helligkeit."
            }
        },
        "required": ["action"]
    },
    "handler": computer_settings
}
