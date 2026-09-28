"""
backend/actions/jarvis_control.py — Dedizierte Sprachsteuerung für J.A.R.V.I.S. AI OS.
Verarbeitet die spezifischen Voice Commands:
- "jarvis neustart": Startet ausschließlich das Tool (Webjarvis) neu, NIEMALS das gesamte Betriebssystem!
- "jarvis stop": Unterbricht sofort Sprachausgabe, laufende Tasks und Aktionen.
- "jarvis mute": Schaltet das Mikrofon stumm (Paranoia Killswitch aktiv).
- "jarvis update": Prüft und zieht Updates direkt aus dem GitHub-Repository (https://github.com/Graba92/webjarvis).
"""

from __future__ import annotations
import os
import sys
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Any

REPO_DIR = Path(__file__).resolve().parent.parent.parent
RESTART_SCRIPT = REPO_DIR / "restart.sh"
GITHUB_REMOTE_URL = "https://github.com/Graba92/webjarvis"

def _perform_tool_restart():
    """Führt nach kurzer Verzögerung den Tool-Neustart aus."""
    time.sleep(1.0)
    if RESTART_SCRIPT.exists():
        subprocess.Popen(["bash", str(RESTART_SCRIPT)], cwd=str(REPO_DIR))
    else:
        # Fallback: stop.sh und run.sh
        stop_sh = REPO_DIR / "stop.sh"
        run_sh = REPO_DIR / "run.sh"
        if stop_sh.exists() and run_sh.exists():
            subprocess.Popen(["bash", "-c", f"bash {stop_sh} && sleep 1 && nohup bash {run_sh} &"], cwd=str(REPO_DIR))

def _check_and_apply_git_update() -> str:
    """Prüft und aktualisiert Jarvis aus dem GitHub-Repository."""
    try:
        # 1. Fetch remote changes
        fetch_res = subprocess.run(
            ["git", "fetch", "origin", "main"],
            cwd=str(REPO_DIR),
            capture_output=True,
            text=True,
            timeout=25
        )
        if fetch_res.returncode != 0:
            return f"Fehler bei Verbindung zum GitHub-Repository:\n{fetch_res.stderr.strip() or fetch_res.stdout.strip()}"

        # 2. Aktuellen HEAD und Remote vergleichen
        head_rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO_DIR), capture_output=True, text=True, timeout=5).stdout.strip()
        remote_rev = subprocess.run(["git", "rev-parse", "origin/main"], cwd=str(REPO_DIR), capture_output=True, text=True, timeout=5).stdout.strip()

        if head_rev == remote_rev:
            short_rev = head_rev[:7]
            return f"J.A.R.V.I.S. ist bereits auf dem neuesten Stand von GitHub (Commit {short_rev}). Keine Updates ausstehend."

        # 3. Pull Updates
        pull_res = subprocess.run(
            ["git", "pull", "--ff-only", "origin", "main"],
            cwd=str(REPO_DIR),
            capture_output=True,
            text=True,
            timeout=30
        )
        if pull_res.returncode != 0:
            return f"Update heruntergeladen, aber Zusammenführung fehlgeschlagen:\n{pull_res.stderr.strip() or pull_res.stdout.strip()}"

        new_rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(REPO_DIR), capture_output=True, text=True, timeout=5).stdout.strip()
        log_res = subprocess.run(["git", "log", "-1", "--pretty=%B"], cwd=str(REPO_DIR), capture_output=True, text=True, timeout=5).stdout.strip()

        return (
            f"Update erfolgreich eingespielt! Neuer Commit: {new_rev}\n"
            f"Änderung: {log_res}\n"
            f"Sage 'Jarvis Neustart', um das Tool mit der neuen Version neu zu laden."
        )
    except Exception as e:
        return f"Fehler während des GitHub-Self-Updates: {e}"

def jarvis_control(action: str = "", audio: Any = None, interrupt: Any = None, ws_broadcast: Any = None, **kwargs) -> str:
    """Handler für 'jarvis neustart', 'jarvis stop', 'jarvis mute', 'jarvis update'."""
    act = str(action or "").lower().strip()

    # 1. jarvis neustart (Tool-Neustart)
    if act in ("restart_tool", "neustart", "tool_neustart", "jarvis_neustart", "restart"):
        threading.Thread(target=_perform_tool_restart, daemon=True).start()
        if ws_broadcast:
            ws_broadcast({
                "type": "log",
                "speaker": "SYS",
                "text": "J.A.R.V.I.S. Tool-Neustart angefordert. Starte Prozesse neu...",
                "ts": time.strftime("%H:%M:%S")
            })
        return "J.A.R.V.I.S. AI OS wird jetzt neu gestartet. Das Betriebssystem bleibt aktiv. Bis gleich!"

    # 2. jarvis stop
    elif act in ("stop", "anhalten", "abort", "halt", "cancel", "jarvis_stop"):
        if interrupt:
            try:
                interrupt()
            except Exception:
                pass
        if ws_broadcast:
            ws_broadcast({
                "type": "state",
                "state": "ONLINE"
            })
            ws_broadcast({
                "type": "log",
                "speaker": "SYS",
                "text": "Befehl STOP ausgeführt: Sprachausgabe & Tasks angehalten.",
                "ts": time.strftime("%H:%M:%S")
            })
        return "Verstanden. Sprachausgabe und laufende Aktionen sofort angehalten."

    # 3. jarvis mute
    elif act in ("mute", "stumm", "paranoia_mute", "mic_mute", "jarvis_mute", "silent"):
        if audio and hasattr(audio, "set_paranoia_mute"):
            audio.set_paranoia_mute(True)
        if ws_broadcast:
            ws_broadcast({"type": "paranoia_mute_status", "active": True, "muted": True})
            ws_broadcast({"type": "paranoia_mute_state", "active": True, "muted": True})
            ws_broadcast({
                "type": "log",
                "speaker": "SYS",
                "text": "🛑 PARANOIA KILLSWITCH AKTIVIERT: Mikrofon-Stream hardwarenah getrennt.",
                "ts": time.strftime("%H:%M:%S")
            })
        return "Mikrofon stummgeschaltet. Paranoia-Killswitch aktiv – ich höre ab jetzt nicht mehr mit. Du kannst das Mikrofon im HUD reaktivieren."

    # 4. jarvis update
    elif act in ("self_update", "update", "github_update", "jarvis_update", "aktualisieren"):
        if ws_broadcast:
            ws_broadcast({
                "type": "log",
                "speaker": "SYS",
                "text": f"Prüfe GitHub-Repository ({GITHUB_REMOTE_URL}) auf Updates...",
                "ts": time.strftime("%H:%M:%S")
            })
        return _check_and_apply_git_update()

    return (
        f"Unbekannte Aktion '{action}'. Unterstützte Aktionen sind: "
        f"'restart_tool' (Tool neustarten), 'stop' (Ausgabe/Aktion anhalten), "
        f"'mute' (Mikrofon stummschalten), 'self_update' (Update von GitHub ziehen)."
    )

TOOL = {
    "name": "jarvis_control",
    "description": (
        "Zentrale Steuerfunktion für J.A.R.V.I.S. AI OS selbst: "
        "1. 'restart_tool': Startet NUR das Tool J.A.R.V.I.S. neu (NICHT den PC / Rechner!). "
        "2. 'stop': Hält Sprachausgabe und laufende Prozesse sofort an. "
        "3. 'mute': Schaltet das Mikrofon stumm (Paranoia-Killswitch), sodass Jarvis nicht mehr zuhört. "
        "4. 'self_update': Prüft und installiert Updates direkt aus dem GitHub-Repository (https://github.com/Graba92/webjarvis). "
        "WICHTIG: Wenn der Nutzer 'Jarvis neustarten' oder 'Tool neustarten' sagt, rufe IMMER dieses Tool mit action='restart_tool' auf und NIEMALS computer_settings mit reboot!"
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "Die Steueraktion: 'restart_tool' (Jarvis-Tool neustarten), 'stop' (Sprachausgabe/Task anhalten), 'mute' (Mikrofon stummschalten), oder 'self_update' (GitHub Update ziehen)."
            }
        },
        "required": ["action"]
    },
    "handler": jarvis_control
}
