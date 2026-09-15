"""
backend/core/sandbox.py — Bubblewrap (bwrap) Sandbox Engine für J.A.R.V.I.S. AI OS.
Isoliert die Ausführung von Shell-Befehlen und Skripten auf CachyOS / Arch Linux hermetisch.
Verhindert unautorisierte Zugriffe auf das Host-Dateisystem, persönliche Dateien und Systemkonfigurationen.
"""

from __future__ import annotations
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SANDBOX_DIR = BASE_DIR / "sandbox_workspace"
DEFAULT_SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

BWRAP_BIN = shutil.which("bwrap") or "/usr/bin/bwrap"

def is_bubblewrap_available() -> bool:
    """Prüft, ob bwrap im System verfügbar und ausführbar ist."""
    return os.path.exists(BWRAP_BIN) and os.access(BWRAP_BIN, os.X_OK)

def build_bwrap_args(
    work_dir: Path,
    writable_paths: Optional[List[str]] = None,
    allow_network: bool = True
) -> List[str]:
    """Baut eine gehärtete Argumentliste für Bubblewrap zusammen."""
    args = [
        BWRAP_BIN,
        # Virtuelle & ephemere Dateisysteme
        "--proc", "/proc",
        "--dev", "/dev",
        "--tmpfs", "/tmp",
        "--tmpfs", "/run",
        # Namensraum-Isolation
        "--unshare-pid",
        "--unshare-ipc",
        "--unshare-uts",
    ]

    if not allow_network:
        args.append("--unshare-net")

    # Read-Only Mounts grundlegender Systembinaries & Bibliotheken
    system_dirs = ["/usr", "/lib", "/lib64", "/bin", "/sbin"]
    for d in system_dirs:
        if os.path.exists(d):
            args.extend(["--ro-bind", d, d])

    # Wichtige Netzwerk- & Zertifikatsdateien read-only einbinden
    net_files = [
        "/etc/resolv.conf",
        "/etc/ssl",
        "/etc/ca-certificates",
        "/etc/hosts",
        "/etc/passwd",
        "/etc/nsswitch.conf"
    ]
    for nf in net_files:
        if os.path.exists(nf):
            args.extend(["--ro-bind", nf, nf])

    # Arbeitsverzeichnis isoliert nach /workspace einhängen
    work_path_str = str(work_dir.resolve())
    args.extend(["--dir", "/workspace"])
    args.extend(["--bind", work_path_str, "/workspace"])
    args.extend(["--chdir", "/workspace"])

    # Zusätzliche erlaubte Pfade beschreibbar machen
    if writable_paths:
        for wp in writable_paths:
            p = Path(wp).resolve()
            if p.exists():
                args.extend(["--bind", str(p), str(p)])

    # Isolation des Rests des Dateisystems: Home-Verzeichnis außerhalb der Work-Dirs ist unsichtbar
    return args

def execute_sandboxed(
    command: str,
    cwd: Optional[str] = None,
    writable_paths: Optional[List[str]] = None,
    allow_network: bool = True,
    timeout: int = 30
) -> Tuple[int, str, str, bool]:
    """
    Führt einen Shell-Befehl isoliert in der Bubblewrap-Sandbox aus.
    Rückgabe: (exit_code, stdout, stderr, was_sandboxed)
    """
    clean_cmd = str(command or "").strip()
    if not clean_cmd:
        return 1, "", "Fehler: Kein Befehl übergeben.", False

    target_cwd = Path(cwd).resolve() if cwd else DEFAULT_SANDBOX_DIR
    target_cwd.mkdir(parents=True, exist_ok=True)

    if not is_bubblewrap_available():
        # Fallback falls bwrap nicht installiert ist (mit deutlicher Warnung)
        try:
            res = subprocess.run(
                clean_cmd,
                shell=True,
                cwd=str(target_cwd),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return res.returncode, res.stdout, f"[WARNUNG: bwrap fehlt, ungesandboxt ausgeführt] {res.stderr}", False
        except subprocess.TimeoutExpired:
            return 124, "", f"Timeout nach {timeout}s.", False
        except Exception as e:
            return 1, "", str(e), False

    # Bubblewrap-Befehl konstruieren
    bwrap_cmd = build_bwrap_args(
        work_dir=target_cwd,
        writable_paths=writable_paths,
        allow_network=allow_network
    )
    bwrap_cmd.extend(["bash", "-c", clean_cmd])

    try:
        proc = subprocess.run(
            bwrap_cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return proc.returncode, proc.stdout, proc.stderr, True
    except subprocess.TimeoutExpired:
        return 124, "", f"Sandbox-Ausführung nach {timeout}s abgebrochen (Timeout).", True
    except Exception as e:
        return 1, "", f"Sandbox-Fehler: {e}", True
