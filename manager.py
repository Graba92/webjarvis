#!/usr/bin/env python3
# ==============================================================================
# J.A.R.V.I.S. AI OS — Desktop Maintenance & Orchestration Manager (PyQt6 GUI)
# Autonomes Wartungs- und Kontrollzentrum für CachyOS / Arch Linux
# ==============================================================================

import os
import sys
import json
import socket
import subprocess
import webbrowser
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QColor, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QCheckBox, QTextEdit, QMessageBox,
    QProgressBar, QScrollArea, QGraphicsDropShadowEffect
)

GITHUB_REPO_URL = "https://github.com/Graba92/webjarvis.git"
AUTOSTART_FILE = Path.home() / ".config/autostart/webjarvis.desktop"

# Ermittle das tatsächliche Installations-Verzeichnis
APP_DIR = Path(__file__).resolve().parent
ICON_PATH = APP_DIR / "assets/jarvis-manager.png"
ICON_SVG_PATH = APP_DIR / "assets/jarvis-manager.svg"


def is_port_open(port: int, host: str = "127.0.0.1", timeout: float = 0.3) -> bool:
    """Prüft schnell und non-blocking, ob ein TCP-Port lauscht."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, ConnectionRefusedError):
        return False


def get_local_commit() -> str:
    """Liest den aktuellen lokalen Git-Commit aus."""
    try:
        res = subprocess.run(
            ["git", "-C", str(APP_DIR), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=3
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "unbekannt"


def get_sandbox_path() -> str:
    """Liest den primären erlaubten Sandbox-Pfad aus der Konfiguration."""
    cfg_file = APP_DIR / "backend/config/sandbox_config.json"
    if cfg_file.exists():
        try:
            data = json.loads(cfg_file.read_text(encoding="utf-8"))
            paths = data.get("allowed_paths", [])
            if paths:
                return paths[0]
        except Exception:
            pass
    return str(Path.home() / "Schreibtisch/jarvistestlauf")


# ── Hintergrund-Thread: GitHub Update Check (NUR PRÜFEN, KEIN AUTOMATISCHES INSTALLIEREN!) ──
class UpdateCheckThread(QThread):
    check_finished = pyqtSignal(bool, str, str, str)  # has_update, local_sha, remote_sha, message

    def run(self):
        try:
            local_sha = get_local_commit()
            res = subprocess.run(
                ["git", "ls-remote", GITHUB_REPO_URL, "HEAD"],
                capture_output=True, text=True, timeout=8
            )
            if res.returncode != 0:
                self.check_finished.emit(False, local_sha[:7], "", "GitHub-Server nicht erreichbar (Offline?)")
                return

            lines = res.stdout.strip().split()
            if not lines:
                self.check_finished.emit(False, local_sha[:7], "", "Keine Antwort von GitHub erhalten")
                return

            remote_sha = lines[0].strip()
            if local_sha != "unbekannt" and remote_sha:
                if local_sha == remote_sha:
                    self.check_finished.emit(False, local_sha[:7], remote_sha[:7], "System ist auf dem neuesten Stand.")
                else:
                    self.check_finished.emit(True, local_sha[:7], remote_sha[:7], "Neues Update auf GitHub verfügbar!")
            else:
                self.check_finished.emit(False, local_sha[:7], remote_sha[:7], "Lokaler Status nicht versioniert.")
        except Exception as e:
            self.check_finished.emit(False, "err", "", f"Prüfung fehlgeschlagen: {e}")


# ── Hintergrund-Thread: Selbst-Aktualisierung (NUR NACH NUTZER-KLICK) ──
class PerformUpdateThread(QThread):
    log_line = pyqtSignal(str)
    update_finished = pyqtSignal(bool, str)

    def run(self):
        try:
            self.log_line.emit("[*] Starte Selbst-Aktualisierung von GitHub...")
            self.log_line.emit(f"[*] Ziel: {GITHUB_REPO_URL}")

            # 1. Git pull
            p_pull = subprocess.Popen(
                ["git", "-C", str(APP_DIR), "pull", "--rebase", "origin", "main"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            for line in iter(p_pull.stdout.readline, ""):
                if line:
                    self.log_line.emit(line.strip())
            p_pull.wait()

            if p_pull.returncode != 0:
                self.log_line.emit("[!] Rebase fehlgeschlagen. Versuche git pull Standard...")
                subprocess.run(["git", "-C", str(APP_DIR), "pull", "origin", "main"], check=False)

            # 2. Setup Update ausführen
            self.log_line.emit("\n[*] Führe Paket- & Komponenten-Update aus (setup.sh -u)...")
            setup_script = APP_DIR / "setup.sh"
            if setup_script.exists():
                p_setup = subprocess.Popen(
                    [str(setup_script), "-u"],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=str(APP_DIR)
                )
                for line in iter(p_setup.stdout.readline, ""):
                    if line:
                        self.log_line.emit(line.strip())
                p_setup.wait()

            self.update_finished.emit(True, "Update erfolgreich abgeschlossen!")
        except Exception as e:
            self.log_line.emit(f"\n[✗] Fehler während der Aktualisierung: {e}")
            self.update_finished.emit(False, str(e))


# ── Hauptfenster des Jarvis Managers ──────────────────────────────────────────
class JarvisManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("J.A.R.V.I.S. AI OS — Manager & Control Center")
        self.setFixedSize(580, 680)

        # App-Icon setzen
        if ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_PATH)))
        elif ICON_SVG_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_SVG_PATH)))

        self.setStyleSheet("""
            QMainWindow {
                background-color: #060911;
                color: #e2e8f0;
            }
            QLabel {
                color: #cbd5e1;
            }
            QFrame.card {
                background-color: #0b111e;
                border: 1px solid #1a273f;
                border-radius: 12px;
            }
            QPushButton {
                background-color: #121c2e;
                border: 1px solid #203352;
                border-radius: 8px;
                color: #f8fafc;
                font-size: 11px;
                font-weight: bold;
                padding: 8px 14px;
            }
            QPushButton:hover {
                background-color: #182844;
                border-color: #00d4ff;
            }
            QPushButton.primary {
                background-color: rgba(0, 212, 255, 0.15);
                border: 1px solid #00d4ff;
                color: #00f0ff;
            }
            QPushButton.primary:hover {
                background-color: rgba(0, 212, 255, 0.3);
            }
            QPushButton.danger {
                background-color: rgba(239, 68, 68, 0.15);
                border: 1px solid #ef4444;
                color: #f87171;
            }
            QPushButton.danger:hover {
                background-color: rgba(239, 68, 68, 0.3);
            }
            QPushButton.success {
                background-color: rgba(34, 197, 94, 0.15);
                border: 1px solid #22c55e;
                color: #4ade80;
            }
            QPushButton.success:hover {
                background-color: rgba(34, 197, 94, 0.3);
            }
            QCheckBox {
                color: #e2e8f0;
                font-size: 11px;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid #203352;
                background-color: #0e1726;
            }
            QCheckBox::indicator:checked {
                background-color: #00d4ff;
                border-color: #00d4ff;
            }
            QTextEdit {
                background-color: #04070d;
                border: 1px solid #141e30;
                border-radius: 8px;
                color: #00f0ff;
                font-family: monospace;
                font-size: 10px;
            }
        """)

        self.init_ui()

        # Live Poller für Port- & Prozessüberwachung (alle 2.5 Sekunden)
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.update_live_status)
        self.poll_timer.start(2500)
        self.update_live_status()

        # Update-Prüfung beim Starten (rein informativ im Hintergrund)
        self.start_github_update_check()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(12)

        # ── 1. HEADER BEREICH ──
        header_layout = QHBoxLayout()
        
        # Icon
        self.logo_lbl = QLabel()
        if ICON_PATH.exists():
            pix = QPixmap(str(ICON_PATH)).scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_lbl.setPixmap(pix)
        header_layout.addWidget(self.logo_lbl)

        # Titel & Subtitel
        title_box = QVBoxLayout()
        title_lbl = QLabel("J.A.R.V.I.S. AI OS")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 900; color: #ffffff; letter-spacing: 1px;")
        sub_lbl = QLabel("SYSTEM ORCHESTRATION & MAINTENANCE CENTER")
        sub_lbl.setStyleSheet("font-size: 9px; font-weight: bold; color: #00d4ff; letter-spacing: 0.5px;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        # Globaler Status Badge
        self.badge_lbl = QLabel("● PRÜFE STATUS...")
        self.badge_lbl.setStyleSheet("""
            background-color: #1a273f;
            color: #94a3b8;
            font-size: 10px;
            font-weight: bold;
            padding: 5px 10px;
            border-radius: 12px;
            border: 1px solid #203352;
        """)
        header_layout.addWidget(self.badge_lbl)
        main_layout.addLayout(header_layout)

        # ── 2. CARD: TELEMETRIE & SUBSYSTEM STATUS ──
        status_card = QFrame()
        status_card.setProperty("class", "card")
        sc_layout = QVBoxLayout(status_card)
        sc_layout.setContentsMargins(14, 12, 14, 12)
        sc_layout.setSpacing(6)

        sc_title = QLabel("SYSTEM-TELEMETRIE & STATUS")
        sc_title.setStyleSheet("font-size: 10px; font-weight: bold; color: #94a3b8; letter-spacing: 0.5px;")
        sc_layout.addWidget(sc_title)

        # Statuszeilen
        self.lbl_backend = QLabel("• Python Live-Backend (Port 8765): Initialisiere...")
        self.lbl_backend.setStyleSheet("font-size: 11px; font-family: monospace;")
        sc_layout.addWidget(self.lbl_backend)

        self.lbl_frontend = QLabel("• Web-HUD Frontend (Port 3000/3005): Initialisiere...")
        self.lbl_frontend.setStyleSheet("font-size: 11px; font-family: monospace;")
        sc_layout.addWidget(self.lbl_frontend)

        self.lbl_workspace = QLabel(f"• Sandbox-Pfad: {get_sandbox_path()}")
        self.lbl_workspace.setStyleSheet("font-size: 10px; color: #64748b; font-family: monospace;")
        sc_layout.addWidget(self.lbl_workspace)

        main_layout.addWidget(status_card)

        # ── 3. CARD: STEUERUNG (START / STOPP / COCKPIT) ──
        ctrl_card = QFrame()
        ctrl_card.setProperty("class", "card")
        cc_layout = QVBoxLayout(ctrl_card)
        cc_layout.setContentsMargins(14, 12, 14, 12)
        cc_layout.setSpacing(10)

        cc_title = QLabel("OPERATIVE STEUERUNG")
        cc_title.setStyleSheet("font-size: 10px; font-weight: bold; color: #94a3b8; letter-spacing: 0.5px;")
        cc_layout.addWidget(cc_title)

        btn_grid = QHBoxLayout()
        btn_grid.setSpacing(8)

        self.btn_start = QPushButton("▶ J.A.R.V.I.S. Starten")
        self.btn_start.setProperty("class", "primary")
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self.action_start_jarvis)
        btn_grid.addWidget(self.btn_start)

        self.btn_stop = QPushButton("⏹ Stoppen")
        self.btn_stop.setProperty("class", "danger")
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.clicked.connect(self.action_stop_jarvis)
        btn_grid.addWidget(self.btn_stop)

        self.btn_browser = QPushButton("🌐 Web-HUD Öffnen")
        self.btn_browser.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browser.clicked.connect(self.action_open_browser)
        btn_grid.addWidget(self.btn_browser)

        cc_layout.addLayout(btn_grid)
        main_layout.addWidget(ctrl_card)

        # ── 4. CARD: AUTOSTART EINSTELLUNG ──
        auto_card = QFrame()
        auto_card.setProperty("class", "card")
        ac_layout = QHBoxLayout(auto_card)
        ac_layout.setContentsMargins(14, 12, 14, 12)

        auto_info_box = QVBoxLayout()
        self.cb_autostart = QCheckBox("Autostart beim Systemstart (KDE Plasma Login)")
        self.cb_autostart.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cb_autostart.setChecked(AUTOSTART_FILE.exists())
        self.cb_autostart.toggled.connect(self.action_toggle_autostart)
        auto_info_box.addWidget(self.cb_autostart)

        self.lbl_autostart_desc = QLabel("Startet J.A.R.V.I.S. automatisch im Hintergrund bei der Anmeldung.")
        self.lbl_autostart_desc.setStyleSheet("font-size: 9px; color: #64748b; margin-left: 22px;")
        auto_info_box.addWidget(self.lbl_autostart_desc)
        ac_layout.addLayout(auto_info_box)

        ac_layout.addStretch()
        self.lbl_auto_badge = QLabel("AKTIV" if AUTOSTART_FILE.exists() else "INAKTIV")
        self.lbl_auto_badge.setStyleSheet(
            "font-size: 9px; font-weight: bold; padding: 3px 8px; border-radius: 6px; " +
            ("background-color: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid #22c55e;" if AUTOSTART_FILE.exists()
             else "background-color: #1a273f; color: #94a3b8; border: 1px solid #203352;")
        )
        ac_layout.addWidget(self.lbl_auto_badge)

        main_layout.addWidget(auto_card)

        # ── 5. CARD: GITHUB UPDATE-ZENTRALE ──
        upd_card = QFrame()
        upd_card.setProperty("class", "card")
        uc_layout = QVBoxLayout(upd_card)
        uc_layout.setContentsMargins(14, 12, 14, 12)
        uc_layout.setSpacing(8)

        uc_header = QHBoxLayout()
        uc_title = QLabel("GITHUB SOFTWARE-STAND & UPDATES")
        uc_title.setStyleSheet("font-size: 10px; font-weight: bold; color: #94a3b8; letter-spacing: 0.5px;")
        uc_header.addWidget(uc_title)

        uc_header.addStretch()

        self.btn_recheck = QPushButton("🔄 Neu prüfen")
        self.btn_recheck.setStyleSheet("font-size: 9px; padding: 3px 8px;")
        self.btn_recheck.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_recheck.clicked.connect(self.start_github_update_check)
        uc_header.addWidget(self.btn_recheck)
        uc_layout.addLayout(uc_header)

        # Update Info Box
        self.lbl_update_status = QLabel("🔍 Prüfe GitHub-Repository (https://github.com/Graba92/webjarvis)...")
        self.lbl_update_status.setStyleSheet("font-size: 11px; color: #00d4ff; font-family: monospace;")
        uc_layout.addWidget(self.lbl_update_status)

        # Update Aktionsleiste
        act_row = QHBoxLayout()
        self.btn_perform_update = QPushButton("⚡ Jetzt Aktualisieren (git pull + setup.sh -u)")
        self.btn_perform_update.setProperty("class", "success")
        self.btn_perform_update.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_perform_update.setEnabled(False)  # Nur aktiv wenn Prüfung fertig
        self.btn_perform_update.clicked.connect(self.action_perform_update)
        act_row.addWidget(self.btn_perform_update)
        uc_layout.addLayout(act_row)

        # Mini Log Konsole
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setFixedHeight(95)
        self.log_console.setPlaceholderText("Live-Prozessprotokoll...")
        uc_layout.addWidget(self.log_console)

        main_layout.addWidget(upd_card)

        # ── 6. FOOTER ──
        footer_layout = QHBoxLayout()
        footer_lbl = QLabel(f"Pfad: {APP_DIR}")
        footer_lbl.setStyleSheet("font-size: 9px; color: #475569; font-family: monospace;")
        footer_layout.addWidget(footer_lbl)
        footer_layout.addStretch()

        close_btn = QPushButton("Schließen")
        close_btn.setStyleSheet("font-size: 10px; padding: 4px 10px;")
        close_btn.clicked.connect(self.close)
        footer_layout.addWidget(close_btn)
        main_layout.addLayout(footer_layout)

    # ── Live-Status Prüfroutine ──
    def update_live_status(self):
        backend_up = is_port_open(8765)
        frontend_3000 = is_port_open(3000)
        frontend_3005 = is_port_open(3005)
        frontend_up = frontend_3000 or frontend_3005

        if backend_up and frontend_up:
            self.badge_lbl.setText("● ONLINE (VOLLSTÄNDIG)")
            self.badge_lbl.setStyleSheet("""
                background-color: rgba(34, 197, 94, 0.2);
                color: #22c55e;
                font-size: 10px;
                font-weight: bold;
                padding: 5px 12px;
                border-radius: 12px;
                border: 1px solid #22c55e;
            """)
        elif backend_up or frontend_up:
            self.badge_lbl.setText("● PARTIELL AKTIV")
            self.badge_lbl.setStyleSheet("""
                background-color: rgba(245, 158, 11, 0.2);
                color: #f59e0b;
                font-size: 10px;
                font-weight: bold;
                padding: 5px 12px;
                border-radius: 12px;
                border: 1px solid #f59e0b;
            """)
        else:
            self.badge_lbl.setText("● OFFLINE")
            self.badge_lbl.setStyleSheet("""
                background-color: #1a273f;
                color: #94a3b8;
                font-size: 10px;
                font-weight: bold;
                padding: 5px 12px;
                border-radius: 12px;
                border: 1px solid #203352;
            """)

        # Backend Text
        if backend_up:
            self.lbl_backend.setText("• Python Live-Backend: 🟢 AKTIV (ws://127.0.0.1:8765)")
            self.lbl_backend.setStyleSheet("font-size: 11px; font-family: monospace; color: #4ade80;")
        else:
            self.lbl_backend.setText("• Python Live-Backend: ⚪ OFFLINE (Port 8765 frei)")
            self.lbl_backend.setStyleSheet("font-size: 11px; font-family: monospace; color: #94a3b8;")

        # Frontend Text
        if frontend_up:
            port_active = 3000 if frontend_3000 else 3005
            self.lbl_frontend.setText(f"• Web-HUD Frontend: 🟢 AKTIV (http://localhost:{port_active})")
            self.lbl_frontend.setStyleSheet("font-size: 11px; font-family: monospace; color: #4ade80;")
        else:
            self.lbl_frontend.setText("• Web-HUD Frontend: ⚪ OFFLINE (Port 3000 frei)")
            self.lbl_frontend.setStyleSheet("font-size: 11px; font-family: monospace; color: #94a3b8;")

    # ── Aktionen ──
    def action_start_jarvis(self):
        self.log_console.append("[*] Starte J.A.R.V.I.S. AI OS im Hintergrund...")
        start_script = APP_DIR / "start.sh"
        if start_script.exists():
            subprocess.Popen(
                ["nohup", str(start_script), "-a"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                cwd=str(APP_DIR), start_new_session=True
            )
            QTimer.singleShot(1500, self.update_live_status)
            QTimer.singleShot(3000, self.update_live_status)
        else:
            self.log_console.append(f"[✗] Fehlendes Startskript: {start_script}")

    def action_stop_jarvis(self):
        self.log_console.append("[*] Fahre Subsysteme herunter (stop.sh)...")
        stop_script = APP_DIR / "stop.sh"
        if stop_script.exists():
            subprocess.run([str(stop_script)], cwd=str(APP_DIR))
            QTimer.singleShot(800, self.update_live_status)
        else:
            self.log_console.append(f"[✗] Fehlendes Stoppskript: {stop_script}")

    def action_open_browser(self):
        port = 3005 if is_port_open(3005) else 3000
        url = f"http://localhost:{port}"
        webbrowser.open(url)

    def action_toggle_autostart(self, checked: bool):
        AUTOSTART_FILE.parent.mkdir(parents=True, exist_ok=True)
        if checked:
            content = f"""[Desktop Entry]
Type=Application
Name=WebJarvis AI OS
Comment=J.A.R.V.I.S. AI OS Autostart
Exec={APP_DIR}/start.sh -a
Icon={ICON_PATH}
Terminal=false
Hidden=false
X-GNOME-Autostart-enabled=true
"""
            AUTOSTART_FILE.write_text(content, encoding="utf-8")
            self.lbl_auto_badge.setText("AKTIV")
            self.lbl_auto_badge.setStyleSheet("font-size: 9px; font-weight: bold; padding: 3px 8px; border-radius: 6px; background-color: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid #22c55e;")
            self.log_console.append(f"[✓] Autostart eingerichtet: {AUTOSTART_FILE}")
        else:
            if AUTOSTART_FILE.exists():
                AUTOSTART_FILE.unlink()
            self.lbl_auto_badge.setText("INAKTIV")
            self.lbl_auto_badge.setStyleSheet("font-size: 9px; font-weight: bold; padding: 3px 8px; border-radius: 6px; background-color: #1a273f; color: #94a3b8; border: 1px solid #203352;")
            self.log_console.append("[✓] Autostart deaktiviert.")

    # ── Update Routine ──
    def start_github_update_check(self):
        self.lbl_update_status.setText("🔍 Frage GitHub ab (https://github.com/Graba92/webjarvis)...")
        self.lbl_update_status.setStyleSheet("font-size: 11px; color: #00d4ff; font-family: monospace;")
        self.btn_recheck.setEnabled(False)

        self.upd_thread = UpdateCheckThread()
        self.upd_thread.check_finished.connect(self.on_github_check_result)
        self.upd_thread.start()

    def on_github_check_result(self, has_update: bool, local_sha: str, remote_sha: str, msg: str):
        self.btn_recheck.setEnabled(True)
        self.btn_perform_update.setEnabled(True)

        if has_update:
            self.lbl_update_status.setText(f"⚠️ UPDATE VERFÜGBAR! Remote: [{remote_sha}] | Lokal: [{local_sha}]")
            self.lbl_update_status.setStyleSheet("font-size: 11px; color: #f59e0b; font-weight: bold; font-family: monospace;")
            self.log_console.append(f"[*] Hinweis: Neuer Commit {remote_sha} auf GitHub gefunden. Klicke auf 'Jetzt Aktualisieren', um zu installieren.")
        else:
            if remote_sha:
                self.lbl_update_status.setText(f"✓ Aktuell: Commit [{local_sha}] entspricht GitHub [{remote_sha}]")
                self.lbl_update_status.setStyleSheet("font-size: 11px; color: #22c55e; font-weight: bold; font-family: monospace;")
            else:
                self.lbl_update_status.setText(f"Status: {msg}")
                self.lbl_update_status.setStyleSheet("font-size: 11px; color: #94a3b8; font-family: monospace;")

    def action_perform_update(self):
        reply = QMessageBox.question(
            self,
            "WebJarvis Update Bestätigung",
            "Möchtest du WebJarvis jetzt auf die neueste Version von GitHub (https://github.com/Graba92/webjarvis) aktualisieren?\n\n"
            "Dabei wird 'git pull' ausgeführt und alle Abhängigkeiten werden über 'setup.sh -u' synchronisiert.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.btn_perform_update.setEnabled(False)
        self.log_console.clear()
        self.perform_thread = PerformUpdateThread()
        self.perform_thread.log_line.connect(self.log_console.append)
        self.perform_thread.update_finished.connect(self.on_update_completed)
        self.perform_thread.start()

    def on_update_completed(self, success: bool, msg: str):
        self.btn_perform_update.setEnabled(True)
        if success:
            QMessageBox.information(self, "Update Abgeschlossen", f"✓ {msg}\nWebJarvis ist nun auf dem neuesten Stand.")
            self.start_github_update_check()
        else:
            QMessageBox.warning(self, "Update Fehler", f"Fehler bei der Aktualisierung:\n{msg}")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Jarvis Manager")
    app.setOrganizationName("Graba92")
    window = JarvisManagerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
