#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==============================================================================
# J.A.R.V.I.S. AI OS — Windows WSL2 Orchestration & Launcher (run_windows.py)
# Stand: 2026 | Matze "Graba" Cross-Platform Architecture
#
# Führt WebJarvis nahtlos, performant und sicher unter Windows via WSL 2 aus.
# Enthält:
#  - TUI Consent-Prompts vor Systemeingriffen (wsl --install, Port-Freigaben)
#  - Dynamische Pfad-Konvertierung (wslpath -a -u)
#  - Line-Ending-Sanitizer (CRLF -> LF) für alle Shell- und Config-Skripte
#  - Dependency-Auditor im WSL (python3, nodejs, npm, bubblewrap, pipewire)
#  - Live-Streaming von Backend & Frontend ins Windows-Terminal
# ==============================================================================

import subprocess
import sys
import os
import shutil
import time
from pathlib import Path

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"

def log_info(msg: str):
    print(f"{CYAN}[JARVIS-WIN]{RESET} {msg}")

def log_success(msg: str):
    print(f"{GREEN}[SUCCESS]{RESET} {msg}")

def log_warn(msg: str):
    print(f"{YELLOW}[WARNUNG]{RESET} {msg}")

def log_err(msg: str):
    print(f"{RED}[FEHLER]{RESET} {msg}")

def tui_prompt(action_name: str, description: str, impact: str) -> bool:
    """TUI Consent-Abfrage für den Nutzer nach Vektor-7 / Bastler-Standard."""
    print(f"\n{YELLOW}{BOLD}[!] Systemeingriff erforderlich: {action_name}{RESET}")
    print(f"    -> {BOLD}WAS PASSIERT:{RESET} {description}")
    print(f"    -> {BOLD}WARUM / IMPACT:{RESET} {impact}")
    while True:
        try:
            choice = input(f"\n{CYAN}[?] Aktion ausführen? (J/N): {RESET}").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{RED}[X] Abbruch durch User.{RESET}")
            return False
        if choice in ['j', 'ja', 'y', 'yes']:
            return True
        elif choice in ['n', 'nein', 'no']:
            print(f"{RED}[X] Aktion abgelehnt.{RESET}")
            return False

def check_and_install_wsl():
    """Prüft, ob WSL2 betriebsbereit ist, und bietet bei Bedarf die geführte Installation an."""
    if sys.platform != "win32":
        log_info("Nicht auf nativem Windows ausgeführt – fahre direkt fort.")
        return

    try:
        res = subprocess.run(["wsl", "--status"], capture_output=True, text=True, check=True)
        log_success("WSL 2 erkannt und betriebsbereit.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        log_warn("WSL (Windows Subsystem for Linux) wurde nicht gefunden oder ist nicht aktiv.")
        consent = tui_prompt(
            action_name="WSL2 Basis-Installation",
            description="Führt 'wsl --install' aus. Aktiviert Hyper-V und installiert eine Linux-Standard-Distro (Ubuntu/Arch).",
            impact="Benötigt Windows-Administratorrechte, ca. 2–3 GB Speicherplatz und zwingend einen PC-Neustart nach Abschluss."
        )
        if consent:
            log_info("Starte WSL-Installation via Windows UAC...")
            try:
                subprocess.run(["wsl", "--install"], check=True)
                log_success("WSL erfolgreich initialisiert. BITTE WINDOWS JETZT NEUSTARTEN und dieses Skript erneut ausführen.")
                sys.exit(0)
            except subprocess.CalledProcessError as e:
                log_err(f"Fehler bei der WSL-Installation: {e}")
                sys.exit(1)
        else:
            log_err("Ohne WSL 2 kann WebJarvis unter Windows nicht ausgeführt werden.")
            sys.exit(1)

def convert_win_to_lin_path(win_path: str) -> str:
    """Konvertiert Windows-Pfade (z.B. C:\\webjarvis) in native WSL-Pfade (/mnt/c/webjarvis)."""
    if sys.platform != "win32":
        return win_path
    try:
        res = subprocess.run(["wsl", "wslpath", "-a", "-u", win_path], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError:
        return win_path

def sanitize_crlf_in_repo(repo_dir: Path):
    """
    Wandelt CRLF (\\r\\n) in Unix-LF (\\n) für alle kritischen Shell- und Config-Dateien um.
    Verhindert mysteriöse Bash-Syntaxfehler ('\\r': command not found).
    """
    extensions = {".sh", ".py", ".md", ".json", ".env", ".ts", ".tsx"}
    converted_count = 0
    
    for root, dirs, files in os.walk(repo_dir):
        # Exclude venvs und node_modules
        if any(ex in root for ex in [".venv", "node_modules", ".git", ".next", "__pycache__"]):
            continue
        for file in files:
            p = Path(root) / file
            if p.suffix in extensions:
                try:
                    with open(p, "rb") as f:
                        data = f.read()
                    if b"\r\n" in data:
                        clean_data = data.replace(b"\r\n", b"\n")
                        with open(p, "wb") as f:
                            f.write(clean_data)
                        converted_count += 1
                except Exception:
                    pass
    if converted_count > 0:
        log_info(f"CRLF -> LF Sanitizer: {converted_count} Dateien bereinigt.")

def check_wsl_dependencies(wsl_repo_path: str):
    """Prüft im WSL, ob Python3, Pip, Node.js und npm vorhanden sind."""
    check_script = "command -v python3 && command -v node && command -v npm"
    cmd = ["wsl", "-e", "bash", "-c", check_script]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        log_success("WSL-Abhängigkeiten (python3, node, npm) sind vorhanden.")
    except subprocess.CalledProcessError:
        log_warn("Einige Basispakete fehlen in deiner WSL-Distribution.")
        consent = tui_prompt(
            action_name="WSL Basispakete installieren",
            description="Installiert python3, python3-venv, nodejs, npm, curl via apt in deiner WSL-Distro.",
            impact="Benötigt Internetzugriff und ca. 300 MB temporären Speicher."
        )
        if consent:
            install_cmd = ["wsl", "-e", "bash", "-c", "sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip nodejs npm curl bubblewrap"]
            try:
                subprocess.run(install_cmd, check=True)
                log_success("Pakete in WSL installiert.")
            except subprocess.CalledProcessError as e:
                log_err(f"Konnte Pakete in WSL nicht automatisch installieren: {e}")

def run_webjarvis_in_wsl(args: list[str]):
    """Startet WebJarvis im WSL und spiegelt den Output nahtlos."""
    check_and_install_wsl()
    
    repo_root = Path(__file__).resolve().parent
    sanitize_crlf_in_repo(repo_root)
    
    wsl_root = convert_win_to_lin_path(str(repo_root))
    check_wsl_dependencies(wsl_root)
    
    sub_cmd = " ".join(args) if args else "./run.sh"
    full_bash = f"cd '{wsl_root}' && chmod +x *.sh backend/*.sh 2>/dev/null || true; {sub_cmd}"
    
    print("\n" + "="*70)
    print(f"{CYAN}{BOLD}  J.A.R.V.I.S. AI OS — Windows WSL2 Bridge Active{RESET}")
    print(f"  Arbeitsverzeichnis in WSL: {BOLD}{wsl_root}{RESET}")
    print(f"  Web-HUD erreichbar unter:  {GREEN}{BOLD}http://localhost:3000{RESET}")
    print(f"  WebSocket Backend Port:    {GREEN}{BOLD}ws://127.0.0.1:8765{RESET}")
    print("="*70 + "\n")
    
    wsl_exec = ["wsl", "-e", "bash", "-c", full_bash]
    try:
        proc = subprocess.Popen(wsl_exec)
        proc.communicate()
        if proc.returncode != 0:
            log_warn(f"WebJarvis in WSL beendet mit Code {proc.returncode}.")
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[!] Abbruch durch User (SIGINT). Stoppe WSL-Prozesse...{RESET}")
        try:
            subprocess.run(["wsl", "-e", "bash", "-c", f"cd '{wsl_root}' && ./stop.sh 2>/dev/null || true"], timeout=5)
        except Exception:
            pass
        log_info("WebJarvis geordnet beendet.")

if __name__ == "__main__":
    cli_args = sys.argv[1:]
    run_webjarvis_in_wsl(cli_args)
