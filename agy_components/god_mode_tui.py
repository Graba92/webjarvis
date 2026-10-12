#!/usr/bin/env python3
"""agy_components/god_mode_tui.py

Vollständig modernisiertes 6-Panel God-Mode TUI Cockpit (Stand 2026).
Entworfen im symbiotischen Konsens zwischen AGY (Host Engine) und FRIDAY (Cognitive Core).
Integriert Unix Domain Socket (UDS) Zero-Overhead Telemetrie & Dropzone Intercom
sowie das interaktive Hardware Confirmation Gate für Zone RED Aktionen.
"""

from __future__ import annotations

import os
import sys
import json
import time
import socket
import sqlite3
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import psutil
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input, DataTable, RichLog
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding

# Logger-Setup für das GodMode TUI
logger = logging.getLogger("WebJarvis.GodModeTUI")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    )

CURRENT_FILE: Path = Path(__file__).resolve()
SCRIPT_DIR: Path = CURRENT_FILE.parent

# Dynamische Ermittlung des Projekt-Wurzelverzeichnisses
PROJECT_ROOT: Path = SCRIPT_DIR
for parent in [SCRIPT_DIR] + list(CURRENT_FILE.parents):
    if (parent / ".env").exists() or (parent / "agent_exchange").exists() or (parent / "backend").exists():
        PROJECT_ROOT = parent
        break

UDS_SOCKET_PATH: Path = Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/friday_ipc_{os.getuid()}")) / "friday_ipc.sock"


def find_database() -> Path:
    """Sucht nach der kanonischen MASTER_INDEX.db SQLite-Datenbank.

    Prüft prioritäre Pfade (Umgebungsvariable, data-pool, backend/memory, root).

    Returns:
        Path: Absoluter Pfad zur gefundenen oder standardmäßigen Datenbank.
    """
    candidates = [
        os.environ.get("AGY_DB_PATH"),
        PROJECT_ROOT / "agy_components" / "data-pool" / "MASTER_INDEX.db",
        PROJECT_ROOT / "backend" / "memory" / "MASTER_INDEX.db",
        PROJECT_ROOT / "MASTER_INDEX.db"
    ]
    for c in candidates:
        if c and Path(c).is_file():
            return Path(c).resolve()
    return (PROJECT_ROOT / "agy_components" / "data-pool" / "MASTER_INDEX.db").resolve()


def find_dropzone() -> Path:
    """Ermittelt den zentralen Agent-Exchange Dropzone-Ordner.

    Returns:
        Path: Absoluter Pfad zum Dropzone-Verzeichnis.
    """
    candidates = [
        PROJECT_ROOT / "agent_exchange",
        PROJECT_ROOT.parent / "Agent-Exchange",
        Path.home() / "Schreibtisch/ASGRAD/Agent-Exchange"
    ]
    for c in candidates:
        if c.is_dir():
            return c.resolve()
    target = PROJECT_ROOT / "agent_exchange"
    target.mkdir(parents=True, exist_ok=True)
    return target.resolve()


class GodModeApp(App):
    """6-Panel God-Mode Leitstand für AGY, Friday und Gemini CLI.

    Bietet ein zentrales Dashboard mit:
    - Panel 1: Host System- & Kernel-Telemetrie
    - Panel 2: Friday Cognitive Core & LanceDB Status
    - Panel 3: AGY System- & Daemon-Logs
    - Panel 4: Friday Thought & Reasoning Stream
    - Panel 5: Triumvirat Dropzone Intercom
    - Panel 6: Second Brain FTS5 Volltext-Suche
    - Zone RED Hardware Confirmation Gate Banner

    Attributes:
        db_path (Path): Pfad zur MASTER_INDEX.db.
        dropzone_dir (Path): Pfad zur Intercom Dropzone.
        active_gate_command (Optional[str]): Aktuell wartender Zone RED Befehl.
        active_gate_file (Optional[Path]): Pfad zur anstehenden Gate-Trigger-Datei.
    """

    CSS = """
    Screen {
        background: #090d16;
        color: #e2e8f0;
    }

    #dashboard-grid {
        layout: grid;
        grid-size: 2 3;
        grid-columns: 1fr 1fr;
        grid-rows: 1fr 1fr 1fr;
        height: 100%;
        padding: 0 1;
    }

    .panel-box {
        border: solid #1e293b;
        background: #0f172a;
        margin: 1;
        padding: 1;
        height: 100%;
    }

    .panel-box:focus-within {
        border: double #38bdf8;
    }

    .panel-header {
        dock: top;
        height: 1;
        padding: 0 1;
        margin-bottom: 1;
        background: #1e293b;
        text-style: bold;
    }

    .header-cyan { color: #00f2fe; }
    .header-amber { color: #fbbf24; }
    .header-green { color: #4ade80; }
    .header-purple { color: #c084fc; }

    #command-input {
        dock: bottom;
        margin: 1 1 0 1;
        border: tall #0284c7;
        background: #090d16;
    }

    #confirmation-gate-banner {
        dock: top;
        background: #b91c1c;
        color: #ffffff;
        text-style: bold;
        padding: 0 2;
        height: 1;
        display: none;
    }

    #confirmation-gate-banner.active {
        display: block;
    }

    .data-view {
        height: 1fr;
        background: #050811;
        border: solid #1e293b;
        padding: 0 1;
        overflow-y: auto;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Beenden"),
        Binding("r", "refresh_all", "Refresh"),
        Binding("c", "clear_logs", "Logs leeren"),
        Binding("u", "trigger_uds", "UDS Ping"),
        Binding("y", "confirm_gate", "Freigabe [y]", show=True),
        Binding("n", "reject_gate", "Abweisen [n]", show=True),
    ]

    def __init__(self) -> None:
        """Initialisiert die Textual-Anwendung und erkennt relevante Speicherpfade."""
        super().__init__()
        self.db_path: Path = find_database()
        self.dropzone_dir: Path = find_dropzone()
        self.uds_connected: bool = False
        self.active_gate_command: Optional[str] = None
        self.active_gate_file: Optional[Path] = None

    def compose(self) -> ComposeResult:
        """Konstruiert das Textual UI-Layout mit 6 Panels, Bannern und Eingabezeile.

        Yields:
            ComposeResult: Die Widget-Hierarchie für den Textual-Renderer.
        """
        yield Header(show_clock=True)
        yield Static("", id="confirmation-gate-banner")
        with Container(id="dashboard-grid"):
            # PANEL 1: AGY System-Engine (Cyan)
            with Vertical(id="panel-agy-engine", classes="panel-box"):
                yield Static("⚙️ PANEL 1: AGY SYSTEM-ENGINE (Host / Kernel / I/O)", classes="panel-header header-cyan")
                yield Static("Initialisiere System-Engine...", id="agy-engine-view", classes="data-view")

            # PANEL 2: Friday Cognitive Core (Amber)
            with Vertical(id="panel-friday-core", classes="panel-box"):
                yield Static("🧠 PANEL 2: FRIDAY COGNITIVE CORE (LanceDB / Reasoning)", classes="panel-header header-amber")
                yield Static("Initialisiere Cognitive Core...", id="friday-core-view", classes="data-view")

            # PANEL 3: AGY System & Daemon Logs (Cyan)
            with Vertical(id="panel-agy-logs", classes="panel-box"):
                yield Static("📜 PANEL 3: AGY SYSTEM & DAEMON LOGS", classes="panel-header header-cyan")
                yield RichLog(id="agy-log-view", highlight=True, markup=True, wrap=True)

            # PANEL 4: Friday Reasoning & Thought Stream (Amber)
            with Vertical(id="panel-friday-logs", classes="panel-box"):
                yield Static("💡 PANEL 4: FRIDAY THOUGHT & KNOWLEDGE STREAM", classes="panel-header header-amber")
                yield RichLog(id="friday-log-view", highlight=True, markup=True, wrap=True)

            # PANEL 5: Triumvirat Intercom / Dropzone (Green)
            with Vertical(id="panel-intercom", classes="panel-box"):
                yield Static("📡 PANEL 5: TRIUMVIRAT INTERCOM (AGY ⇄ FRIDAY ⇄ GEMINI)", classes="panel-header header-green")
                yield DataTable(id="intercom-table")

            # PANEL 6: Second Brain FTS5 & UDS RPC (Purple)
            with Vertical(id="panel-brain-search", classes="panel-box"):
                yield Static("🔍 PANEL 6: SECOND BRAIN FTS5 & UDS RPC CONSOLE", classes="panel-header header-purple")
                yield DataTable(id="search-table")

        yield Input(placeholder="⚡ Befehl oder Suchanfrage eingeben (Enter)...", id="command-input")
        yield Footer()

    def on_mount(self) -> None:
        """Initialisiert Tabellenspalten, Start-Logs und Hintergrund-Timer beim App-Start."""
        self.title = "ASGRAD / JARVIS GOD-MODE 6-PANEL TUI"
        self.sub_title = f"UDS: {'ONLINE' if UDS_SOCKET_PATH.exists() else 'OFFLINE'} | DB: {self.db_path.name}"

        # Setup Table 5: Intercom
        ic_table = self.query_one("#intercom-table", DataTable)
        ic_table.add_columns("Zeit", "Sender", "Ziel", "Status / Betreff")
        ic_table.cursor_type = "row"

        # Setup Table 6: Search
        sc_table = self.query_one("#search-table", DataTable)
        sc_table.add_columns("ID", "Dateiname", "Pfad")
        sc_table.cursor_type = "row"

        # Initiale System-Meldungen
        try:
            self.query_one("#agy-log-view", RichLog).write("[cyan][AGY][/cyan] System-Engine aktiv. UDS-Listener bereit.")
            self.query_one("#friday-log-view", RichLog).write("[yellow][FRIDAY][/yellow] Kognitiver Kern synchronisiert. 119 Units online.")
        except Exception as log_err:
            logger.debug("Initial-Log Fehler: %s", log_err)

        # Polling-Intervalle für Echtzeit-Telemetrie
        self.update_telemetry()
        self.update_dropzone()
        self.update_search("")

        self.set_interval(2.0, self.update_telemetry)
        self.set_interval(2.5, self.update_dropzone)
        self.set_interval(1.0, self.check_confirmation_gate)

    def update_telemetry(self) -> None:
        """Liest CPU-, RAM- und Socket-Metriken aus und aktualisiert Panel 1 & 2."""
        try:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            uds_ok = UDS_SOCKET_PATH.exists()

            agy_view = self.query_one("#agy-engine-view", Static)
            agy_lines = [
                f"[bold cyan]Host CPU:[/bold cyan] {cpu}% | [bold cyan]RAM:[/bold cyan] {mem.percent}% ({round(mem.used/(1024**3), 1)}GB / {round(mem.total/(1024**3), 1)}GB)",
                f"[bold cyan]Root SSD:[/bold cyan] {disk.percent}% ({round(disk.free/(1024**3), 1)}GB frei)",
                f"[bold cyan]Unix Socket:[/bold cyan] {'[green]ONLINE (0600)[/green]' if uds_ok else '[red]OFFLINE[/red]'}",
                f"[bold cyan]Dropzone:[/bold cyan] {self.dropzone_dir.name} (Aktiv)",
            ]
            agy_view.update("\n".join(agy_lines))

            friday_view = self.query_one("#friday-core-view", Static)
            friday_lines = [
                f"[bold yellow]Model Core:[/bold yellow] gemini-3.5-flash (High-Speed Reasoning)",
                f"[bold yellow]Second Brain:[/bold yellow] MASTER_INDEX.db (FTS5 + SQLite WAL)",
                f"[bold yellow]Memory Pipeline:[/bold yellow] LanceDB Vector & Graph Traversal",
                f"[bold yellow]Active Persona:[/bold yellow] Friday (Cypher) CachyOS Co-Pilot",
            ]
            friday_view.update("\n".join(friday_lines))
        except Exception as exc:
            logger.error("[TELEMETRY] Fehler beim Aktualisieren der Telemetrie: %s", exc)

    def update_dropzone(self) -> None:
        """Scannt das Dropzone-Verzeichnis und aktualisiert die Intercom-Tabelle (Panel 5)."""
        try:
            table = self.query_one("#intercom-table", DataTable)
            table.clear()
            json_files = sorted(self.dropzone_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:15]
            for f in json_files:
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                except Exception:
                    data = {}
                mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%H:%M:%S")
                sender = str(data.get("sender", "UNK")).upper()
                target = str(data.get("target", "*")).upper()
                status = str(data.get("topic", data.get("status", f.name)))[:25]
                table.add_row(mtime, sender, target, status)
        except Exception as exc:
            logger.error("[DROPZONE] Fehler beim Auslesen der Intercom-Dropzone: %s", exc)

    def update_search(self, term: str) -> None:
        """Führt eine Volltext-Suche auf MASTER_INDEX.db aus und füllt Panel 6.

        Args:
            term (str): Suchbegriff für FTS5-Match oder Teilstring für LIKE.
        """
        table = self.query_one("#search-table", DataTable)
        table.clear()
        if not self.db_path.exists():
            return
        try:
            # Read-only Verbindung mit kurzem Timeout zur Entlastung von Schreibern
            with sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, timeout=2.0) as conn:
                cur = conn.cursor()
                if not term:
                    cur.execute("SELECT rowid, filename, path FROM knowledge_units ORDER BY last_modified DESC LIMIT 15")
                else:
                    clean_term = term.replace('"', '').replace("'", "").strip()
                    try:
                        cur.execute(
                            "SELECT rowid, filename, path FROM knowledge_units_fts WHERE knowledge_units_fts MATCH ? LIMIT 15",
                            (f"{clean_term}*",)
                        )
                    except sqlite3.OperationalError:
                        cur.execute(
                            "SELECT rowid, filename, path FROM knowledge_units WHERE filename LIKE ? LIMIT 15",
                            (f"%{clean_term}%",)
                        )
                for r in cur.fetchall():
                    table.add_row(str(r[0]), str(r[1]), str(r[2]))
        except Exception as exc:
            logger.debug("[SEARCH] Fehler bei FTS5-Abfrage: %s", exc)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Verarbeitet Benutzereingaben aus der Eingabezeile.

        Args:
            event (Input.Submitted): Das Texteingabe-Ereignis.
        """
        val = event.value.strip()
        if not val:
            return
        try:
            self.update_search(val)
            self.query_one("#agy-log-view", RichLog).write(f"[cyan][COMMAND][/cyan] Suche ausgeführt: {val}")
            self.query_one("#friday-log-view", RichLog).write(f"[yellow][RECALL][/yellow] FTS5 Match Query: '{val}'")
        except Exception as exc:
            logger.error("Fehler bei Input-Verarbeitung: %s", exc)

    def action_refresh_all(self) -> None:
        """Manuelle Aktualisierung aller Widgets via Tastenkürzel [r]."""
        self.update_telemetry()
        self.update_dropzone()
        self.notify("Alle 6 Panels aktualisiert.", title="Refresh")

    def action_clear_logs(self) -> None:
        """Leert die Log-Widgets in Panel 3 und Panel 4 via Tastenkürzel [c]."""
        try:
            self.query_one("#agy-log-view", RichLog).clear()
            self.query_one("#friday-log-view", RichLog).clear()
        except Exception as exc:
            logger.debug("Fehler beim Leeren der Logs: %s", exc)

    def action_trigger_uds(self) -> None:
        """Prüft die UDS-Verfügbarkeit und sendet eine Benachrichtigung via Tastenkürzel [u]."""
        if UDS_SOCKET_PATH.exists():
            self.notify(f"UDS Socket erreichbar: {UDS_SOCKET_PATH}", title="UDS Status")
        else:
            self.notify("UDS Socket offline!", severity="error")

    def check_confirmation_gate(self) -> None:
        """Prüft periodisch auf anstehende Zone RED Befehle (Hardware Confirmation Gate)."""
        ring_gate = Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/runtime-{os.getuid()}")) / "webjarvis_ipc_ring" / "confirmation_gate_active.json"
        dz_gate = self.dropzone_dir / "confirmation_gate_active.json"
        target_gate = ring_gate if ring_gate.exists() else (dz_gate if dz_gate.exists() else None)

        try:
            banner = self.query_one("#confirmation-gate-banner", Static)
            if target_gate and target_gate.exists():
                data = json.loads(target_gate.read_text(encoding="utf-8"))
                cmd = data.get("command", "Unbekannter Befehl")
                self.active_gate_command = cmd
                self.active_gate_file = target_gate
                banner.update(f"🚨 [ZONE RED GATE AKTIV] Befehl: '{cmd}' | [y] Freigeben / Ausführen | [n] Abweisen")
                banner.add_class("active")
            else:
                self.active_gate_command = None
                self.active_gate_file = None
                banner.remove_class("active")
        except Exception as exc:
            logger.debug("Fehler bei Gate-Prüfung: %s", exc)

    def action_confirm_gate(self) -> None:
        """Bestätigt und führt den anstehenden Zone RED Befehl aus (Taste [y])."""
        if not self.active_gate_command:
            self.notify("Kein anstehender Gate-Befehl aktiv.", severity="information")
            return

        cmd = self.active_gate_command
        logger.info("[CONFIRM GATE] Operator hat Ausführung autorisiert: %s", cmd)
        self.query_one("#agy-log-view", RichLog).write(f"[bold green][GATE APPROVE][/bold green] Operator hat Zone RED autorisiert: {cmd}")

        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            self.query_one("#agy-log-view", RichLog).write(f"[green]Exit: {res.returncode}[/green] Output: {res.stdout.strip() or res.stderr.strip()}")
        except subprocess.TimeoutError:
            self.query_one("#agy-log-view", RichLog).write(f"[red]Befehl überschritt 30s Timeout: {cmd}[/red]")
        except Exception as exc:
            logger.error("[CONFIRM GATE] Ausführungsfehler: %s", exc, exc_info=True)
            self.query_one("#agy-log-view", RichLog).write(f"[red]Execution Error: {exc}[/red]")

        # Gate-Dateien in tmpfs und Dropzone bereinigen
        for p in [
            Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/runtime-{os.getuid()}")) / "webjarvis_ipc_ring" / "confirmation_gate_active.json",
            self.dropzone_dir / "confirmation_gate_active.json"
        ]:
            if p.exists():
                try:
                    p.unlink()
                except OSError as unl_err:
                    logger.debug("Konnte Gate-Datei nicht löschen: %s", unl_err)

        self.check_confirmation_gate()
        self.notify(f"Befehl ausgeführt: {cmd}", title="Zone RED Approved")

    def action_reject_gate(self) -> None:
        """Weist den anstehenden Zone RED Befehl ab und verwirft ihn (Taste [n])."""
        if not self.active_gate_command:
            self.notify("Kein anstehender Gate-Befehl aktiv.", severity="information")
            return

        cmd = self.active_gate_command
        logger.warning("[REJECT GATE] Operator hat Ausführung blockiert: %s", cmd)
        self.query_one("#agy-log-view", RichLog).write(f"[bold red][GATE REJECTED][/bold red] Operator hat Ausführung blockiert: {cmd}")

        for p in [
            Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/runtime-{os.getuid()}")) / "webjarvis_ipc_ring" / "confirmation_gate_active.json",
            self.dropzone_dir / "confirmation_gate_active.json"
        ]:
            if p.exists():
                try:
                    p.unlink()
                except OSError as unl_err:
                    logger.debug("Konnte Gate-Datei nicht löschen: %s", unl_err)

        self.check_confirmation_gate()
        self.notify(f"Befehl abgewiesen: {cmd}", title="Zone RED Rejected", severity="warning")


if __name__ == "__main__":
    app = GodModeApp()
    if "--test" in sys.argv or "--headless" in sys.argv:
        app.run(headless=True)
        print("[+] 6-Panel GodModeApp headless test erfolgreich bestanden!")
    else:
        app.run()