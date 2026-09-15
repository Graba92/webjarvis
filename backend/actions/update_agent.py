"""
backend/actions/update_agent.py — Native CachyOS / Arch Linux Update- & Maintenance-Agent.
- Liest anstehende Updates aus offiziellen Repos (checkupdates) und dem AUR (yay -Qu).
- Filtert und markiert sicherheitskritische Systemkomponenten (Kernel, Systemd, Glibc, OpenSSL, Sudo, PipeWire).
- Sichert Upgrades ZWINGEND über das Hardware Confirmation Gate (confirm.py) ab.
"""

from __future__ import annotations
import shutil
import subprocess
from typing import Dict, List, Any
from core import confirm

CRITICAL_PACKAGES = {
    "linux", "linux-cachyos", "linux-zen", "linux-lts",
    "cachyos-settings", "systemd", "glibc", "openssl",
    "sudo", "bubblewrap", "pipewire", "wireplumber", "mesa", "nvidia"
}

def get_pending_updates() -> Dict[str, Any]:
    """Liest anstehende Paketaktualisierungen für CachyOS / Arch Linux aus."""
    official_updates: List[str] = []
    aur_updates: List[str] = []
    critical_updates: List[str] = []

    # 1. Offizielle Repositories via checkupdates (aus pacman-contrib)
    if shutil.which("checkupdates"):
        try:
            res = subprocess.run(["checkupdates"], capture_output=True, text=True, timeout=12)
            if res.returncode == 0 and res.stdout.strip():
                official_updates = [line.strip() for line in res.stdout.strip().split("\n") if line.strip()]
        except Exception:
            pass

    # 2. AUR & CachyOS Repos via yay
    if shutil.which("yay"):
        try:
            res = subprocess.run(["yay", "-Qu"], capture_output=True, text=True, timeout=15)
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.strip().split("\n"):
                    clean = line.strip()
                    if clean and clean not in official_updates:
                        aur_updates.append(clean)
        except Exception:
            pass

    all_updates = official_updates + aur_updates
    for item in all_updates:
        pkg_name = item.split()[0].lower() if item else ""
        if pkg_name in CRITICAL_PACKAGES or any(pkg_name.startswith(c) for c in ("linux-", "nvidia-", "systemd-")):
            critical_updates.append(item)

    return {
        "official_count": len(official_updates),
        "aur_count": len(aur_updates),
        "total_count": len(all_updates),
        "critical_updates": critical_updates,
        "critical_count": len(critical_updates),
        "sample_updates": all_updates[:8]
    }

def run_actual_upgrade() -> str:
    """Führt das eigentliche System-Upgrade nach physischer Freigabe durch."""
    cmd = ["yay", "-Syu", "--noconfirm"] if shutil.which("yay") else ["sudo", "pacman", "-Syu", "--noconfirm"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if proc.returncode == 0:
            return "System-Upgrade erfolgreich abgeschlossen. Alle Pakete sind auf dem neuesten Stand."
        return f"Upgrade mit Exit-Code {proc.returncode} beendet:\n{proc.stderr[-300:] if proc.stderr else proc.stdout[-300:]}"
    except Exception as e:
        return f"Fehler während der Upgrade-Ausführung: {e}"

def system_updates(action: str = "check", **kwargs) -> str:
    """
    Handler für den CachyOS / Arch Update-Agenten.
    - action='check': Prüft alle anstehenden Updates und markiert sicherheitskritische Pakete.
    - action='upgrade': Startet das Upgrade (erfordert zwingend Bestätigung im HUD Confirmation-Gate).
    """
    act = (action or "check").strip().lower()

    if act == "check":
        data = get_pending_updates()
        total = data["total_count"]
        if total == 0:
            return "CachyOS / Arch System ist auf dem aktuellen Stand. Keine ausstehenden Updates."

        lines = [
            f"CachyOS Paket-Update Status:",
            f"• Ausstehende Pakete: {total} gesamt ({data['official_count']} offiziell, {data['aur_count']} AUR)",
        ]
        if data["critical_count"] > 0:
            lines.append(f"• ⚠️ Sicherheitskritische Kernkomponenten ({data['critical_count']}):")
            for c in data["critical_updates"]:
                lines.append(f"  - {c}")
        else:
            lines.append("• Keine kritischen Kernel- oder Systemd-Upgrades dabei.")

        if data["sample_updates"]:
            lines.append("\nAuszug anstehender Pakete:")
            for p in data["sample_updates"]:
                lines.append(f"  • {p}")

        lines.append("\nUm das Upgrade durchzuführen, sage: 'Führe System-Upgrade aus' (erfordert Bestätigung im HUD).")
        return "\n".join(lines)

    elif act == "upgrade":
        data = get_pending_updates()
        total = data["total_count"]
        detail_msg = f"{total} Pakete werden aktualisiert ({data['critical_count']} sicherheitskritisch)."
        return confirm.request(
            action="cachyos_system_upgrade",
            label="CachyOS / Arch System-Upgrade (yay -Syu)",
            detail=detail_msg,
            run=run_actual_upgrade,
            timeout=120.0
        )

    return f"Unbekannte Aktion '{action}'. Gültige Aktionen sind: 'check' oder 'upgrade'."

TOOL = {
    "name": "update_agent",
    "description": (
        "Prüft und verwaltet CachyOS / Arch Linux Paketaktualisierungen via checkupdates und yay. "
        "Erkennt ausstehende offizielle und AUR-Updates sowie sicherheitskritische Kernel- und Systempakete. "
        "Das Ausführen von Upgrades ('upgrade') ist durch das Hardware Confirmation Gate physisch geschützt."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "Die Aktion: 'check' (prüft Updates und listet kritische Pakete) oder 'upgrade' (triggert das Hardware-Gate für yay -Syu)."
            }
        },
        "required": ["action"]
    },
    "handler": system_updates
}
