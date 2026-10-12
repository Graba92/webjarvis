#!/usr/bin/env python3
"""
Graba Master Wartungs- & Verwaltungs-HUB
Zentraler Leitstand & Orchestrator für die neutralen IT- & Gastro-Werkzeuge:
- Order-Relay Core (Shop-Bestellen :8080)
- Fleet-Command Nexus Hub (Multi-Host Telemetrie :9090)
- Gastro-Dispatcher OS (ESC/POS Thermodruck, Spooler & Alarmierung)
- Server-Guard Pro (Sys-Sentinel & Backup-Vault)
- Linux-Control-Kit (System-Diagnose & Kernel-Tuning)

Stand: 2026 | BSI IT-Grundschutz, SPS-Prinzip & Systemd-Native
Made by Matze Graba (@Graba92)
"""

import os
import sys
import time
import json
import curses
import subprocess
import urllib.request
import urllib.error
import shutil
import argparse
import signal
from pathlib import Path
from typing import Dict, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent

# Sicheres Runtime-Verzeichnis für PIDs (XDG oder Fallback)
RUNTIME_DIR = Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/graba_hub_run_{os.getuid()}"))
PID_DIR = RUNTIME_DIR / "graba_hub_pids"
PID_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)

SERVICES_CONFIG = {
    "order_relay": {
        "name": "Order-Relay Core",
        "dir": BASE_DIR / "Graba_Master_Wartungs_verwaltungs_HUB/modules/Shop-bestellen",
        "script": "server.py",
        "port": 8080,
        "health_url": "http://127.0.0.1:8080/api/health",
        "log": "/tmp/hub_order_relay.log",
        "systemd_type": "simple",
        "desc": "Webshop-Order Ingress Server & PAngV Preisvalidierung"
    },
    "nexus_hub": {
        "name": "Fleet Nexus Hub",
        "dir": BASE_DIR / "Graba_Master_Wartungs_verwaltungs_HUB/modules/andere",
        "script": "nexus_hub.py",
        "port": 9090,
        "health_url": "http://127.0.0.1:9090/api/health",
        "log": "/tmp/hub_nexus_hub.log",
        "systemd_type": "simple",
        "desc": "Multi-Host Telemetrie & Heartbeat Aggregator"
    },
    "gastro_dispatcher": {
        "name": "Gastro Dispatcher",
        "dir": BASE_DIR / "Graba_Master_Wartungs_verwaltungs_HUB/modules/Gastro",
        "script": "dispatcher_daemon.py",
        "port": None,
        "health_url": None,
        "log": "/tmp/hub_gastro_dispatcher.log",
        "systemd_type": "simple",
        "desc": "ESC/POS Bon-Drucker Spooler & Alert-Engine"
    },
    "sys_sentinel": {
        "name": "Server-Guard Sentinel",
        "dir": BASE_DIR / "Graba_Master_Wartungs_verwaltungs_HUB/modules/Wartung_Online",
        "script": "sys_sentinel.py",
        "port": None,
        "health_url": None,
        "status_file": "/tmp/server_guard_status.json",
        "log": "/tmp/hub_sys_sentinel.log",
        "systemd_type": "notify",
        "desc": "Autonomer Server-Health-Daemon & Systemd-Watchdog"
    },
    "sb_sentinel": {
        "name": "Second Brain Sentinel",
        "dir": Path("agy_components/data-pool"),
        "script": "sb_sentinel.py",
        "port": None,
        "health_url": None,
        "log": "/tmp/hub_sb_sentinel.log",
        "systemd_type": "simple",
        "desc": "Knowledge Ingest & Indexing Daemon für SB"
    }
}


def get_pid_file(svc_key: str) -> Path:
    return PID_DIR / f"{svc_key}.pid"


def read_pid_from_file(svc_key: str) -> Optional[int]:
    pid_file = get_pid_file(svc_key)
    if pid_file.is_file():
        try:
            val = int(pid_file.read_text(encoding="utf-8").strip())
            return val
        except Exception:
            pass
    return None


def write_pid_to_file(svc_key: str, pid: int) -> None:
    try:
        get_pid_file(svc_key).write_text(str(pid), encoding="utf-8")
    except Exception:
        pass


def clear_pid_file(svc_key: str) -> None:
    pid_file = get_pid_file(svc_key)
    try:
        if pid_file.exists():
            pid_file.unlink()
    except Exception:
        pass


def is_pid_alive(pid: Optional[int]) -> bool:
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def is_process_matching_service(pid: int, svc_key: str) -> bool:
    """Verifiziert via /proc/PID/cmdline, dass der Prozess wirklich das Zielskript ausführt."""
    cfg = SERVICES_CONFIG.get(svc_key)
    if not cfg:
        return False
    proc_cmdline = Path(f"/proc/{pid}/cmdline")
    if not proc_cmdline.exists():
        return False
    try:
        content = proc_cmdline.read_bytes().decode("utf-8", "ignore").replace("\0", " ")
        return cfg["script"] in content
    except Exception:
        return False


def get_process_for_service(svc_key: str) -> Optional[int]:
    """Sichere PID-Ermittlung mit /proc-Validierung und defensiver Stale-PID-Bereinigung."""
    cfg = SERVICES_CONFIG.get(svc_key)
    if not cfg:
        return None

    # 1. PID-Datei prüfen & validieren
    file_pid = read_pid_from_file(svc_key)
    if file_pid:
        if is_pid_alive(file_pid) and is_process_matching_service(file_pid, svc_key):
            return file_pid
        else:
            clear_pid_file(svc_key)

    # 2. Defensiver Fallback: pgrep
    try:
        res = subprocess.run(["pgrep", "-a", "-f", cfg["script"]], stdout=subprocess.PIPE, text=True)
        current_pid = os.getpid()
        for line in res.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=1)
            pid = int(parts[0])
            if pid == current_pid:
                continue
            cmdline = parts[1] if len(parts) > 1 else ""
            if cfg["script"] in cmdline and ("python" in cmdline or ".py" in cmdline):
                write_pid_to_file(svc_key, pid)
                return pid
    except Exception:
        pass

    return None


def check_http_health(url: Optional[str], timeout: float = 1.5) -> Tuple[bool, Optional[dict]]:
    if not url:
        return False, None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GrabaMasterHub/2026"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return True, data
    except Exception:
        pass
    return False, None


def start_service(svc_key: str) -> Tuple[bool, str]:
    cfg = SERVICES_CONFIG.get(svc_key)
    if not cfg:
        return False, "Unbekannter Dienst"
    
    existing_pid = get_process_for_service(svc_key)
    if existing_pid:
        return False, f"Läuft bereits (PID {existing_pid})"
    
    script_path = cfg["dir"] / cfg["script"]
    if not script_path.exists():
        return False, f"Skript nicht gefunden: {script_path}"
    
    log_fp = open(cfg["log"], "a", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-u", str(script_path)],
        cwd=str(cfg["dir"]),
        stdout=log_fp,
        stderr=subprocess.STDOUT,
        start_new_session=True
    )
    write_pid_to_file(svc_key, proc.pid)
    time.sleep(0.4)
    return True, f"Gestartet (PID {proc.pid})"


def stop_service(svc_key: str) -> Tuple[bool, str]:
    cfg = SERVICES_CONFIG.get(svc_key)
    if not cfg:
        return False, "Unbekannter Dienst"
    
    pid = get_process_for_service(svc_key)
    if not pid:
        clear_pid_file(svc_key)
        return False, "Dienst läuft nicht"
    
    try:
        os.kill(pid, signal.SIGTERM)
        for _ in range(12):
            time.sleep(0.1)
            if not is_pid_alive(pid):
                break
        else:
            os.kill(pid, signal.SIGKILL)
        clear_pid_file(svc_key)
        return True, f"Dienst gestoppt (PID {pid})"
    except Exception as e:
        clear_pid_file(svc_key)
        return False, f"Fehler beim Stoppen: {e}"


def get_full_status() -> dict:
    status = {}
    for key, cfg in SERVICES_CONFIG.items():
        pid = get_process_for_service(key)
        alive = is_pid_alive(pid)
        
        info = {
            "name": cfg["name"],
            "pid": pid,
            "running": alive,
            "port": cfg.get("port"),
            "health": None
        }
        
        if cfg.get("health_url"):
            healthy, hdata = check_http_health(cfg["health_url"])
            info["healthy"] = healthy
            info["health_data"] = hdata
        else:
            info["healthy"] = alive
            info["health_data"] = None
            
        status[key] = info
    return status


def generate_systemd_units(output_dir: Optional[Path] = None) -> list:
    """Erzeugt saubere systemd --user Unit-Dateien für alle Dienste."""
    target_dir = output_dir or (Path.home() / ".config/systemd/user")
    target_dir.mkdir(parents=True, exist_ok=True)
    created_files = []

    # 1. Master Target
    target_content = """[Unit]
Description=Graba Master Hub: Gesamtes Service-Portfolio
After=network.target

[Install]
WantedBy=default.target
"""
    target_file = target_dir / "graba-hub.target"
    target_file.write_text(target_content, encoding="utf-8")
    created_files.append(target_file)

    # 2. Einzelne Services
    for svc_key, cfg in SERVICES_CONFIG.items():
        unit_name = f"graba-{svc_key.replace('_', '-')}.service"
        unit_file = target_dir / unit_name
        
        unit_content = f"""[Unit]
Description=Graba Hub: {cfg['name']} ({cfg['desc']})
After=network.target
PartOf=graba-hub.target

[Service]
Type={cfg['systemd_type']}
WorkingDirectory={cfg['dir']}
ExecStart={sys.executable} -u {cfg['dir']}/{cfg['script']}
Restart=always
RestartSec=3
TimeoutStopSec=8
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target graba-hub.target
"""
        unit_file.write_text(unit_content, encoding="utf-8")
        created_files.append(unit_file)

    return created_files


def run_cli_audit():
    print("=" * 68)
    print("      GRABA MASTER WARTUNGS- & VERWALTUNGS-HUB : AUDIT")
    print("      Stand: 2026 | Made by Matze Graba (@Graba92)")
    print("=" * 68)
    st = get_full_status()
    for k, v in st.items():
        state = "[ AKTIV ]" if v["running"] else "[INAKTIV]"
        port_str = f":{v['port']}" if v['port'] else "Daemon"
        print(f" {state} {v['name']:<24} {port_str:<12} PID: {str(v['pid']):<7}")
        if v.get("health_data"):
            meta = v["health_data"]
            print(f"           -> Modus: {meta.get('mode', meta.get('service', 'OK'))} | Stand: 2026")
    print("=" * 68)
    print(f"PID-Verzeichnis: {PID_DIR}")
    print("=" * 68)


def draw_tui(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(1000)
    
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLUE)

    msg = "Bereit. [1-5] Umschalten | [b] Brain Suche | [a] Alle | [x] Stopp | [h] Auto-Heal"
    auto_heal = False
    desired_active = {k: False for k in SERVICES_CONFIG}

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        title = "=== GRABA MASTER WARTUNGS- & VERWALTUNGS-HUB (STAND 2026) ==="
        stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
        stdscr.addstr(1, max(2, (w - len(title)) // 2), title[:w-3])
        stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)
        
        # Systeminfo
        load1, load5, _ = os.getloadavg()
        total, used, _ = shutil.disk_usage("/")
        disk_pct = round(used / total * 100, 1)
        heal_str = "[Auto-Heal: AKTIV]" if auto_heal else "[Auto-Heal: AUS]"
        heal_color = curses.color_pair(1) if auto_heal else curses.color_pair(4)
        
        sys_info = f"Host: {os.uname().nodename} | Load: {load1:.2f}, {load5:.2f} | Disk: {disk_pct}% | {heal_str}"
        stdscr.addstr(3, 3, sys_info[:w-6], heal_color | curses.A_BOLD)
        
        stdscr.addstr(4, 3, "-" * min(w - 6, 75))
        
        # Status Tabelle
        st = get_full_status()
        
        # SPS Auto-Heal Watchdog Überprüfung
        if auto_heal:
            for k, desired in desired_active.items():
                if desired and not st[k]["running"]:
                    ok, res_msg = start_service(k)
                    msg = f"Auto-Heal: {SERVICES_CONFIG[k]['name']} reanimiert!"
                    st = get_full_status()

        row = 6
        stdscr.addstr(row, 3, f"{'KEY':<5} {'DIENST':<24} {'PORT/TYP':<14} {'STATUS':<12} {'PID':<8}", curses.A_UNDERLINE)
        row += 1
        
        keys_map = [
            ("1", "order_relay"),
            ("2", "nexus_hub"),
            ("3", "gastro_dispatcher"),
            ("4", "sys_sentinel"),
            ("5", "sb_sentinel")
        ]
        
        for num, key in keys_map:
            svc = st[key]
            stdscr.addstr(row, 3, f"[{num}]  {svc['name']:<24}")
            port_str = f":{svc['port']}" if svc['port'] else "Daemon"
            stdscr.addstr(row, 32, f"{port_str:<14}")
            
            if svc["running"]:
                stdscr.addstr(row, 46, "● AKTIV   ", curses.color_pair(1) | curses.A_BOLD)
            else:
                stdscr.addstr(row, 46, "○ INAKTIV ", curses.color_pair(2))
                
            stdscr.addstr(row, 58, f"{str(svc['pid']):<8}")
            row += 1
            
        row += 1
        stdscr.addstr(row, 3, "-" * min(w - 6, 75))
        row += 1
        
        # Statusmeldung
        stdscr.addstr(row, 3, f"Meldung: {msg[:w-12]}", curses.color_pair(4) | curses.A_BOLD)
        
        # Shortcuts
        footer_y = max(row + 2, h - 3)
        stdscr.addstr(footer_y, 3, "[1-5] Toggle | [b] Brain Suche | [a] Alle An | [x] Stopp | [q] Ende", curses.color_pair(3))
        
        stdscr.refresh()
        key_char = stdscr.getch()
        
        if key_char in [ord('q'), ord('Q'), 27]:
            break
        elif key_char == ord('1'):
            if st["order_relay"]["running"]:
                ok, m = stop_service("order_relay")
                desired_active["order_relay"] = False
            else:
                ok, m = start_service("order_relay")
                desired_active["order_relay"] = True
            msg = f"Order-Relay: {m}"
        elif key_char == ord('2'):
            if st["nexus_hub"]["running"]:
                ok, m = stop_service("nexus_hub")
                desired_active["nexus_hub"] = False
            else:
                ok, m = start_service("nexus_hub")
                desired_active["nexus_hub"] = True
            msg = f"Nexus Hub: {m}"
        elif key_char == ord('3'):
            if st["gastro_dispatcher"]["running"]:
                ok, m = stop_service("gastro_dispatcher")
                desired_active["gastro_dispatcher"] = False
            else:
                ok, m = start_service("gastro_dispatcher")
                desired_active["gastro_dispatcher"] = True
            msg = f"Gastro Dispatcher: {m}"
        elif key_char == ord('4'):
            if st["sys_sentinel"]["running"]:
                ok, m = stop_service("sys_sentinel")
                desired_active["sys_sentinel"] = False
            else:
                ok, m = start_service("sys_sentinel")
                desired_active["sys_sentinel"] = True
            msg = f"Sys-Sentinel: {m}"
        elif key_char == ord('5'):
            if st["sb_sentinel"]["running"]:
                ok, m = stop_service("sb_sentinel")
                desired_active["sb_sentinel"] = False
            else:
                ok, m = start_service("sb_sentinel")
                desired_active["sb_sentinel"] = True
            msg = f"SB-Sentinel: {m}"
        elif key_char in [ord('b'), ord('B')]:
            msg = "Gebe Suchbegriff in der Shell ein..."
            stdscr.endwin()
            term = input("\nBrain Suche -> Begriff: ").strip()
            if term:
                try:
                    import sqlite3
                    db_path = "GIT-Projekte/Eigene/Github-Ready/webjarvis/agy_components/data-pool/MASTER_INDEX.db"
                    conn = sqlite3.connect(db_path)
                    cur = conn.cursor()
                    cur.execute("SELECT filename, path FROM knowledge_units WHERE filename LIKE ? OR content_preview LIKE ?", (f"%{term}%", f"%{term}%"))
                    rows = cur.fetchall()
                    print(f"\nGefundene Wissenseinheiten für '{term}':")
                    for i, r in enumerate(rows, 1):
                        print(f"{i}. {r[0]} ({r[1]})")
                    input("\nDrücke Enter zum Fortfahren...")
                except Exception as e:
                    print(f"Fehler bei der Suche: {e}")
                    time.sleep(2)
            stdscr = curses.initscr()
            curses.noecho()
            curses.cbreak()
            stdscr.keypad(True)


def main():
    parser = argparse.ArgumentParser(description="Graba Master Wartungs- & Verwaltungs-HUB (Stand 2026)")
    parser.add_argument("--audit", "-a", action="store_true", help="Einmaliger CLI-Status-Audit")
    parser.add_argument("--start-all", action="store_true", help="Startet alle Hintergrunddienste")
    parser.add_argument("--stop-all", action="store_true", help="Stoppt alle Hintergrunddienste")
    parser.add_argument("--export-systemd", action="store_true", help="Exportiert native systemd --user Service-Units")
    parser.add_argument("--install-systemd", action="store_true", help="Installiert Units nach ~/.config/systemd/user und fuehrt daemon-reload aus")
    args = parser.parse_args()
    
    if args.audit:
        run_cli_audit()
        return
        
    if args.start_all:
        for k in SERVICES_CONFIG:
            ok, m = start_service(k)
            print(f"[*] {k}: {m}")
        return
        
    if args.stop_all:
        for k in SERVICES_CONFIG:
            ok, m = stop_service(k)
            print(f"[*] {k}: {m}")
        return

    if args.export_systemd:
        export_dir = BASE_DIR / "Graba_Master_Wartungs_verwaltungs_HUB" / "systemd_units"
        units = generate_systemd_units(export_dir)
        print(f"[+] {len(units)} Systemd-Units erfolgreich exportiert nach:")
        print(f"    {export_dir}")
        for u in units:
            print(f"    • {u.name}")
        return

    if args.install_systemd:
        user_unit_dir = Path.home() / ".config/systemd/user"
        units = generate_systemd_units(user_unit_dir)
        print(f"[+] {len(units)} Systemd-Units erfolgreich installiert nach:")
        print(f"    {user_unit_dir}")
        for u in units:
            print(f"    • {u.name}")
        try:
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
            print("[+] systemctl --user daemon-reload erfolgreich ausgeführt.")
            print("\nBefehle zur Aktivierung:")
            print("  systemctl --user enable --now graba-hub.target")
            print("  systemctl --user status graba-hub.target")
        except Exception as e:
            print(f"[!] Hinweis: systemctl Aufruf fehlgeschlagen: {e}")
        return
        
    curses.wrapper(draw_tui)


if __name__ == "__main__":
    main()
