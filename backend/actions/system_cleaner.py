"""
backend/actions/system_cleaner.py — CachyOS / Arch Linux System- & Cache-Bereinigungs-Agent.
Führt deterministische und sichere Cache-Bereinigungen durch:
- 'paccache -rk1' (behält das letzte Paket im Cache zur Rollback-Sicherheit)
- 'pacman -Sc' (bereinigt ungenutzte Repositories & Sync-Datenbanken)
- Hardware Confirmation Gate Absicherung (confirm.py)
"""

from __future__ import annotations
import shutil
import subprocess
from typing import Dict, Any, List
from core import confirm

def get_cache_telemetry() -> Dict[str, Any]:
    """Ermittelt den aktuellen Speicherverbrauch des pacman-Caches."""
    cache_path = "/var/cache/pacman/pkg"
    size_str = "0 MB"
    candidates_count = 0

    try:
        du_res = subprocess.run(["du", "-sh", cache_path], capture_output=True, text=True, timeout=5)
        if du_res.returncode == 0 and du_res.stdout:
            size_str = du_res.stdout.split()[0]
    except Exception:
        pass

    if shutil.which("paccache"):
        try:
            # Trockenlauf / dry-run mit -d -k1
            p_res = subprocess.run(["paccache", "-d", "-k1"], capture_output=True, text=True, timeout=8)
            if p_res.stdout:
                for line in p_res.stdout.splitlines():
                    if "candidate packages found" in line:
                        parts = line.split()
                        for p in parts:
                            if p.isdigit():
                                candidates_count = int(p)
                                break
        except Exception:
            pass

    return {
        "cache_path": cache_path,
        "cache_size": size_str,
        "candidates_count": candidates_count
    }

def run_actual_cleanup() -> str:
    """Führt die Cache-Bereinigung nach Bestätigung sicher im Hintergrund aus."""
    outputs: List[str] = []

    # 1. paccache -rk1 (behält die letzte installierte Version)
    if shutil.which("paccache"):
        try:
            res1 = subprocess.run(
                ["sudo", "-n", "paccache", "-rk1"],
                capture_output=True,
                text=True,
                timeout=60
            )
            if res1.returncode == 0:
                outputs.append("paccache: Veraltete Paketversionen erfolgreich bereinigt (-rk1 aktiv).")
            elif "Passwort" in (res1.stderr or ""):
                # Fallback ohne sudo, falls Benutzer Schreibrechte auf den Cache hat oder Terminal-Konsole nötig ist
                outputs.append("paccache: Sudo-Rechte erforderlich (Passwortabfrage nötig).")
            else:
                outputs.append(f"paccache Info: {res1.stdout.strip() or res1.stderr.strip()}")
        except Exception as e:
            outputs.append(f"paccache Fehler: {e}")
    else:
        outputs.append("paccache nicht im PATH gefunden (pacman-contrib erforderlich).")

    # 2. pacman -Sc --noconfirm
    try:
        res2 = subprocess.run(
            ["sudo", "-n", "pacman", "-Sc", "--noconfirm"],
            capture_output=True,
            text=True,
            timeout=60
        )
        if res2.returncode == 0:
            outputs.append("pacman -Sc: Ungenutzte Repositorien und alte Cache-Tarballs entfernt.")
        elif "Passwort" in (res2.stderr or ""):
            outputs.append("pacman -Sc: Sudo-Rechte erforderlich (Passwortabfrage nötig).")
        else:
            outputs.append(f"pacman -Sc: {res2.stdout.strip() or res2.stderr.strip()}")
    except Exception as e:
        outputs.append(f"pacman -Sc Fehler: {e}")

    return "\n".join(outputs) if outputs else "Cache-Bereinigung abgeschlossen."

def clean_system_cache(action: str = "check", **kwargs) -> str:
    """
    Handler für den Cache-Cleaner:
    - action='check': Zeigt Belegung von /var/cache/pacman/pkg und Kandidaten.
    - action='clean': Fordert Freigabe im Confirmation-Gate an und führt 'paccache -rk1 && pacman -Sc' aus.
    """
    act = (action or "check").strip().lower()

    if act == "check":
        telemetry = get_cache_telemetry()
        lines = [
            "🧹 CachyOS / Arch Cache-Status:",
            f"• Speicherort: {telemetry['cache_path']}",
            f"• Belegter Speicherplatz: {telemetry['cache_size']}",
            f"• Bereinigbare Pakete (paccache -rk1): {telemetry['candidates_count']}",
            "\nUm den Cache zu bereinigen, sage: 'Bereinige Paket-Cache' oder führe action='clean' aus."
        ]
        return "\n".join(lines)

    elif act == "clean":
        telemetry = get_cache_telemetry()
        detail_msg = (
            f"Bereinigt /var/cache/pacman/pkg (aktuell {telemetry['cache_size']}) mit 'paccache -rk1' "
            f"und entfernt ungenutzte Sync-Repos via 'pacman -Sc'."
        )
        return confirm.request(
            action="pacman_cache_clean",
            label="Pacman & Paccache Cache-Bereinigung (paccache -rk1 && pacman -Sc)",
            detail=detail_msg,
            run=run_actual_cleanup,
            timeout=120.0
        )

    return f"Unbekannte Aktion '{action}'. Unterstützte Aktionen sind 'check' oder 'clean'."

TOOL = {
    "name": "clean_system_cache",
    "description": (
        "Prüft und bereinigt den CachyOS / Arch Linux Paket-Cache via 'paccache -rk1' und 'pacman -Sc'. "
        "Behält die letzte Paketversion für sichere Rollbacks bei und entfernt veraltete Archiv-Tarballs. "
        "Das Ausführen der Bereinigung ('clean') ist durch das Hardware Confirmation Gate physisch geschützt."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "Die Aktion: 'check' (prüft Cache-Größe und bereinigbare Pakete) oder 'clean' (triggert Hardware-Gate zur Bereinigung).",
                "enum": ["check", "clean"]
            }
        },
        "required": ["action"]
    },
    "handler": clean_system_cache
}
