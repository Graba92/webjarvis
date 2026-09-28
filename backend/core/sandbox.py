"""
backend/core/sandbox.py — Bubblewrap (bwrap) Sandbox Engine für J.A.R.V.I.S. AI OS.
Verwaltet konfigurierbare Arbeitsverzeichnisse (Sandbox Allowed Paths) sowie den
Vollzugriffs-Modus (Full OS Access), der persistent gespeichert oder dynamisch
im Web-HUD umgeschaltet werden kann.
"""

from __future__ import annotations
import os
import json
import shutil
import subprocess
import unicodedata
from pathlib import Path
from typing import List, Optional, Tuple, Union

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
SANDBOX_CONFIG_FILE = CONFIG_DIR / "sandbox_config.json"

DEFAULT_SANDBOX_DIR = BASE_DIR / "sandbox_workspace"
DEFAULT_SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

BWRAP_BIN = shutil.which("bwrap") or "/usr/bin/bwrap"

# Laufzeit-Zustand (wird beim Start aus sandbox_config.json initialisiert)
_FULL_OS_ACCESS: bool = False

def normalize_path(p: Union[str, Path]) -> str:
    """
    Normalisiert einen Pfad nach Unicode NFC, expandiert Tilde (~),
    löst Symlinks via realpath/resolve auf und entfernt trailing Whitespaces.
    """
    if p is None:
        return ""
    s = str(p).strip()
    if not s:
        return ""
    # Unicode NFC Normalisierung (z.B. für deutsche Umlaute wie Ü, Ä, Ö in Pfadnamen)
    s_nfc = unicodedata.normalize("NFC", s)
    expanded = os.path.expanduser(s_nfc)
    try:
        return str(Path(expanded).resolve())
    except Exception:
        return os.path.realpath(expanded)

def is_bubblewrap_available() -> bool:
    """Prüft, ob bwrap im System verfügbar und ausführbar ist."""
    return os.path.exists(BWRAP_BIN) and os.access(BWRAP_BIN, os.X_OK)

def is_full_os_access() -> bool:
    """Gibt zurück, ob der uneingeschränkte OS-Vollzugriff aktiv ist."""
    global _FULL_OS_ACCESS
    return _FULL_OS_ACCESS

def set_full_os_access(enabled: bool) -> bool:
    """Schaltet den vollen OS-Zugriff um und speichert die Einstellung persistent."""
    global _FULL_OS_ACCESS
    _FULL_OS_ACCESS = bool(enabled)
    try:
        clean_paths = []
        if SANDBOX_CONFIG_FILE.exists():
            try:
                data = json.loads(SANDBOX_CONFIG_FILE.read_text(encoding="utf-8"))
                for p in data.get("allowed_paths", []):
                    np = normalize_path(p)
                    if np and np not in clean_paths:
                        clean_paths.append(np)
            except Exception:
                pass

        if not clean_paths:
            clean_paths = [str(DEFAULT_SANDBOX_DIR.resolve())]

        payload = {
            "allowed_paths": clean_paths,
            "full_os_access": _FULL_OS_ACCESS
        }
        SANDBOX_CONFIG_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"[Sandbox] Fehler beim Persistieren von full_os_access: {e}")
    return _FULL_OS_ACCESS

def load_sandbox_config() -> dict:
    """Lädt die Sandbox-Konfiguration (erlaubte Pfade & OS-Vollzugriff) aus der JSON-Datei."""
    global _FULL_OS_ACCESS
    default_config = {
        "allowed_paths": [
            str(DEFAULT_SANDBOX_DIR.resolve())
        ],
        "full_os_access": _FULL_OS_ACCESS
    }

    # Falls Umgebungsvariable gesetzt ist, diese einbeziehen
    env_workspace = os.getenv("JARVIS_WORKSPACE") or os.getenv("JARVIS_SANDBOX_PATH")
    if env_workspace:
        default_config["allowed_paths"].append(normalize_path(env_workspace))

    if not SANDBOX_CONFIG_FILE.exists():
        save_sandbox_config(default_config)
        return default_config

    try:
        data = json.loads(SANDBOX_CONFIG_FILE.read_text(encoding="utf-8"))
        paths = data.get("allowed_paths", [])
        if not isinstance(paths, list):
            paths = []

        # Pfade normalisieren (NFC)
        normalized_paths = []
        for p in paths:
            np = normalize_path(p)
            if np and np not in normalized_paths:
                normalized_paths.append(np)

        # Standard-Pfad sicherstellen falls leer
        if not normalized_paths:
            desktop_test = normalize_path(Path.home() / "Schreibtisch" / "jarvistestlauf")
            normalized_paths = [desktop_test]

        data["allowed_paths"] = normalized_paths

        # Full OS Access synchronisieren (aus Datei)
        if "full_os_access" in data:
            _FULL_OS_ACCESS = bool(data["full_os_access"])
        data["full_os_access"] = _FULL_OS_ACCESS

        return data
    except Exception as e:
        print(f"[Sandbox] Fehler beim Laden von sandbox_config.json: {e}")
        return default_config

def save_sandbox_config(config: dict) -> None:
    """Speichert die Sandbox-Pfade und den Vollzugriffs-Status persistent in config/sandbox_config.json."""
    try:
        clean_paths = []
        for p in config.get("allowed_paths", []):
            np = normalize_path(p)
            if np and np not in clean_paths:
                clean_paths.append(np)

        payload = {
            "allowed_paths": clean_paths,
            "full_os_access": bool(config.get("full_os_access", _FULL_OS_ACCESS))
        }
        SANDBOX_CONFIG_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"[Sandbox] Fehler beim Speichern von sandbox_config.json: {e}")

# Initiales Laden beim Modulimport
try:
    load_sandbox_config()
except Exception:
    pass

def get_allowed_paths() -> List[str]:
    """Gibt eine Liste aller aktuell erlaubten Sandbox-Pfade zurück (vollständig normalisiert)."""
    cfg = load_sandbox_config()
    raw_paths = cfg.get("allowed_paths", [])
    resolved_paths: List[str] = []

    for p in raw_paths:
        try:
            norm = normalize_path(p)
            if norm and norm not in resolved_paths:
                resolved_paths.append(norm)
        except Exception:
            pass

    # Standard-Sandbox-Workspace immer zulassen
    def_str = normalize_path(DEFAULT_SANDBOX_DIR)
    if def_str not in resolved_paths:
        resolved_paths.append(def_str)

    return resolved_paths

def add_allowed_path(path_str: str) -> Tuple[bool, str]:
    """Fügt einen neuen erlaubten Pfad zur Sandbox hinzu und legt ihn ggf. an."""
    clean = str(path_str or "").strip()
    if not clean:
        return False, "Fehler: Kein Pfad angegeben."

    try:
        norm_path = normalize_path(clean)
        target = Path(norm_path)
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
    clean = str(path_str or "").strip()
    if not clean:
        return False, "Fehler: Kein Pfad angegeben."

    try:
        norm_target = normalize_path(clean)

        cfg = load_sandbox_config()
        paths = cfg.get("allowed_paths", [])

        new_paths = [p for p in paths if normalize_path(p) != norm_target and p != clean]
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
    Arbeitet Unicode-NFC-bereinigt und löst Symlinks/Realdateipfade auf.
    """
    if is_full_os_access():
        return True

    try:
        target_str = normalize_path(p)
        if not target_str:
            return False
        target_path = Path(target_str)
        real_target_str = os.path.realpath(target_str)
        real_target = Path(real_target_str)
    except Exception:
        return False

    allowed = get_allowed_paths()
    for ap in allowed:
        try:
            ap_str = normalize_path(ap)
            if not ap_str:
                continue
            ap_path = Path(ap_str)
            real_ap_str = os.path.realpath(ap_str)
            real_ap = Path(real_ap_str)

            # 1. Direkte Übereinstimmung
            if target_str == ap_str or real_target_str == real_ap_str or target_path == ap_path:
                return True

            # 2. Path.relative_to auf target_path
            try:
                target_path.relative_to(ap_path)
                return True
            except ValueError:
                pass

            # 3. Path.relative_to auf real_target
            try:
                real_target.relative_to(real_ap)
                return True
            except ValueError:
                pass

            # 4. String-Präfix-Prüfung mit Trennzeichen
            sep = os.sep
            ap_prefix = ap_str if ap_str.endswith(sep) else ap_str + sep
            if target_str.startswith(ap_prefix):
                return True

            real_prefix = real_ap_str if real_ap_str.endswith(sep) else real_ap_str + sep
            if real_target_str.startswith(real_prefix):
                return True

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
            n_wp = normalize_path(wp)
            if n_wp and n_wp not in all_writable:
                all_writable.append(n_wp)

    for wp in all_writable:
        try:
            p = Path(normalize_path(wp))
            if p.exists():
                args.extend(["--bind", str(p), str(p)])
        except Exception:
            pass

    # Arbeitsverzeichnis festlegen
    work_path_str = normalize_path(work_dir)
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
            cand = Path(normalize_path(cwd))
            if cand.exists():
                target_cwd = cand
        except Exception:
            pass
    elif get_allowed_paths():
        try:
            first_allowed = Path(normalize_path(get_allowed_paths()[0]))
            if first_allowed.exists():
                target_cwd = first_allowed
        except Exception:
            pass

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
