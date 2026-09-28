"""
backend/core/sandbox.py — Bubblewrap (bwrap) Sandbox Engine für J.A.R.V.I.S. AI OS.
Verwaltet konfigurierbare Arbeitsverzeichnisse (Sandbox Allowed Paths) sowie den temporären
Vollzugriffs-Modus (Full OS Access), der bis zum erneuten Klick oder Jarvis-Neustart aktiv bleibt.
"""

from __future__ import annotations
import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple, Union

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
SANDBOX_CONFIG_FILE = CONFIG_DIR / "sandbox_config.json"

DEFAULT_SANDBOX_DIR = BASE_DIR / "sandbox_workspace"
DEFAULT_SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

BWRAP_BIN = shutil.which("bwrap") or "/usr/bin/bwrap"

# Laufzeit-Zustand (in-memory): Voller OS-Zugriff bleibt nur aktiv bis zum Klick oder Server-Neustart!
_FULL_OS_ACCESS: bool = False

def is_bubblewrap_available() -> bool:
    """Prüft, ob bwrap im System verfügbar und ausführbar ist."""
    return os.path.exists(BWRAP_BIN) and os.access(BWRAP_BIN, os.X_OK)

def is_full_os_access() -> bool:
    """Gibt zurück, ob der temporäre volle OS-Zugriff aktuell aktiv ist."""
    global _FULL_OS_ACCESS
    return _FULL_OS_ACCESS

def set_full_os_access(enabled: bool) -> bool:
    """Schaltet den vollen OS-Zugriff um (gilt nur für die aktuelle Laufzeit)."""
    global _FULL_OS_ACCESS
    _FULL_OS_ACCESS = bool(enabled)
    return _FULL_OS_ACCESS

def load_sandbox_config() -> dict:
    """Lädt die Sandbox-Konfiguration (erlaubte Pfade) aus der JSON-Datei."""
    default_config = {
        "allowed_paths": [
            str(DEFAULT_SANDBOX_DIR.resolve())
        ]
    }

    # Falls Umgebungsvariable gesetzt ist, diese einbeziehen
    env_workspace = os.getenv("JARVIS_WORKSPACE") or os.getenv("JARVIS_SANDBOX_PATH")
    if env_workspace:
        default_config["allowed_paths"].append(str(Path(env_workspace).resolve()))

    if not SANDBOX_CONFIG_FILE.exists():
        save_sandbox_config(default_config)
        return default_config

    try:
        data = json.loads(SANDBOX_CONFIG_FILE.read_text(encoding="utf-8"))
        paths = data.get("allowed_paths", [])
        if not isinstance(paths, list):
            paths = []
        
        # Standard-Pfad sicherstellen falls leer
        if not paths:
            paths = [str(Path.home() / "Schreibtisch" / "jarvistestlauf")]
            data["allowed_paths"] = paths
            save_sandbox_config(data)
        return data
    except Exception:
        return default_config

def save_sandbox_config(config: dict) -> None:
    """Speichert die Sandbox-Pfade persistent in config/sandbox_config.json."""
    try:
        # Pfade deduplizieren und säubern
        clean_paths = []
        for p in config.get("allowed_paths", []):
            sp = str(p).strip()
            if sp and sp not in clean_paths:
                clean_paths.append(sp)
        payload = {"allowed_paths": clean_paths}
        SANDBOX_CONFIG_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"[Sandbox] Fehler beim Speichern von sandbox_config.json: {e}")

def get_allowed_paths() -> List[str]:
    """Gibt eine Liste aller aktuell erlaubten Sandbox-Pfade zurück."""
    cfg = load_sandbox_config()
    raw_paths = cfg.get("allowed_paths", [])
    resolved_paths: List[str] = []

    for p in raw_paths:
        try:
            expanded = os.path.expanduser(str(p))
            resolved = str(Path(expanded).resolve())
            if resolved not in resolved_paths:
                resolved_paths.append(resolved)
        except Exception:
            pass

    # Standard-Sandbox-Workspace immer zulassen
    def_str = str(DEFAULT_SANDBOX_DIR.resolve())
    if def_str not in resolved_paths:
        resolved_paths.append(def_str)

    return resolved_paths

def add_allowed_path(path_str: str) -> Tuple[bool, str]:
    """Fügt einen neuen erlaubten Pfad zur Sandbox hinzu und legt ihn ggf. an."""
    clean = str(path_str).strip()
    if not clean:
        return False, "Fehler: Kein Pfad angegeben."

    try:
        expanded = os.path.expanduser(clean)
        target = Path(expanded).resolve()
        target.mkdir(parents=True, exist_ok=True)
        res_str = str(target)

        cfg = load_sandbox_config()
        paths = cfg.get("allowed_paths", [])
        if res_str in paths:
            return True, f"Pfad '{res_str}' ist bereits freigegeben."

        paths.append(res_str)
        cfg["allowed_paths"] = paths
        save_sandbox_config(cfg)
        return True, f"Pfad '{res_str}' erfolgreich zur Sandbox hinzugefügt (Lesen & Schreiben inkl. Unterordner)."
    except Exception as e:
        return False, f"Fehler beim Hinzufügen des Pfades: {e}"

def remove_allowed_path(path_str: str) -> Tuple[bool, str]:
    """Entfernt einen Pfad aus den erlaubten Sandbox-Verzeichnissen."""
    clean = str(path_str).strip()
    if not clean:
        return False, "Fehler: Kein Pfad angegeben."

    try:
        expanded = os.path.expanduser(clean)
        res_str = str(Path(expanded).resolve())

        cfg = load_sandbox_config()
        paths = cfg.get("allowed_paths", [])
        
        # Prüfen ob vorhanden (auch un-resolved)
        new_paths = [p for p in paths if str(Path(os.path.expanduser(p)).resolve()) != res_str and p != clean]
        if len(new_paths) == len(paths):
            return False, f"Pfad '{clean}' war nicht in der Liste der erlaubten Pfade."

        cfg["allowed_paths"] = new_paths
        save_sandbox_config(cfg)
        return True, f"Pfad '{clean}' aus der Sandbox entfernt."
    except Exception as e:
        return False, f"Fehler beim Entfernen des Pfades: {e}"

def is_path_allowed(p: Union[str, Path]) -> bool:
    """
    Prüft, ob ein Zielpfad für Lese- und Schreiboperationen zugelassen ist.
    Gibt True zurück, wenn OS-Vollzugriff aktiv ist ODER der Pfad innerhalb
    eines der freigegebenen Sandbox-Verzeichnisse liegt.
    """
    if is_full_os_access():
        return True

    try:
        expanded = os.path.expanduser(str(p))
        target = Path(expanded).resolve()
    except Exception:
        return False

    allowed = get_allowed_paths()
    for ap in allowed:
        try:
            ap_path = Path(ap).resolve()
            if target == ap_path:
                return True
            try:
                target.relative_to(ap_path)
                return True
            except ValueError:
                pass
        except Exception:
            continue

    return False

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

    # Alle erlaubten Sandbox-Pfade beschreibbar einhängen
    all_writable = list(get_allowed_paths())
    if writable_paths:
        for wp in writable_paths:
            if wp not in all_writable:
                all_writable.append(wp)

    for wp in all_writable:
        p = Path(wp).resolve()
        if p.exists():
            args.extend(["--bind", str(p), str(p)])

    # Arbeitsverzeichnis festlegen
    work_path_str = str(work_dir.resolve())
    args.extend(["--dir", "/workspace"])
    args.extend(["--bind", work_path_str, "/workspace"])
    args.extend(["--chdir", work_path_str])

    return args

def execute_sandboxed(
    command: str,
    cwd: Optional[str] = None,
    writable_paths: Optional[List[str]] = None,
    allow_network: bool = True,
    timeout: int = 30
) -> Tuple[int, str, str, bool]:
    """
    Führt einen Shell-Befehl isoliert in der Bubblewrap-Sandbox aus
    ODER unbeschränkt auf dem Host, falls 'full_os_access' aktiv ist.
    Rückgabe: (exit_code, stdout, stderr, was_sandboxed)
    """
    clean_cmd = str(command or "").strip()
    if not clean_cmd:
        return 1, "", "Fehler: Kein Befehl übergeben.", False

    # Arbeitsverzeichnis ermitteln
    target_cwd = DEFAULT_SANDBOX_DIR
    if cwd:
        try:
            cand = Path(os.path.expanduser(cwd)).resolve()
            if cand.exists():
                target_cwd = cand
        except Exception:
            pass
    elif get_allowed_paths():
        first_allowed = Path(get_allowed_paths()[0]).resolve()
        if first_allowed.exists():
            target_cwd = first_allowed

    target_cwd.mkdir(parents=True, exist_ok=True)

    # 1. Fall: Voller OS-Zugriff ist temporär aktiviert -> Direkte Host-Ausführung
    if is_full_os_access():
        try:
            res = subprocess.run(
                clean_cmd,
                shell=True,
                cwd=str(target_cwd),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return res.returncode, res.stdout, res.stderr, False
        except subprocess.TimeoutExpired:
            return 124, "", f"Befehl nach {timeout}s abgebrochen (Timeout).", False
        except Exception as e:
            return 1, "", f"Ausführungsfehler: {e}", False

    # 2. Fall: bwrap fehlt -> Fallback mit Sicherheitswarnung
    if not is_bubblewrap_available():
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

    # 3. Fall: Härtung via Bubblewrap mit freigegebenen Pfaden
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
