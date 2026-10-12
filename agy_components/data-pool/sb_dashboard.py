#!/usr/bin/env python3
"""
ASGRAD Second Brain - TUI Leitstand
Modernes Textual-Dashboard zur Überwachung von Knowledge-Units und Inter-Agent-Tasks.
"""

import sqlite3
import json
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, RichLog, Static
from textual.containers import Horizontal, Vertical

# --- HARD-PATHS ---
DB_PATH = Path("GIT-Projekte/Eigene/Github-Ready/webjarvis/agy_components/data-pool/MASTER_INDEX.db")
EXCHANGE_DIR = Path("agent_exchange")

class SBDashboard(App):
    CSS = """
    Screen { background: #0f172a; }
    DataTable { height: 1fr; border: solid #38bdf8; background: #1e293b; }
    RichLog { height: 1fr; border: solid #a855f7; background: #1e293b; }
    #stats { width: 30%; border: solid #10b981; padding: 1 2; background: #064e3b; }
    """
    
    BINDINGS = [
        ("q", "quit", "Beenden"), 
        ("r", "refresh_data", "Manuell Aktualisieren")
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            yield Static(id="stats")
            with Vertical():
                yield DataTable(id="task_table")
                yield RichLog(id="log_view", highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        self.title = "ASGRAD Second Brain & Agent-Exchange Leitstand"
        table = self.query_one("#task_table", DataTable)
        table.add_columns("Task ID", "Sender", "Receiver", "Action", "Status")
        
        self.action_refresh_data()
        self.set_interval(5.0, self.action_refresh_data)
        
        log = self.query_one("#log_view", RichLog)
        log.write("[bold green]System online.[/bold green] Überwache Dropzone und Datenbank...")

    def action_refresh_data(self) -> None:
        log = self.query_one("#log_view", RichLog)
        table = self.query_one("#task_table", DataTable)
        stats = self.query_one("#stats", Static)
        
        db_count = 0
        if DB_PATH.exists():
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    db_count = conn.execute("SELECT COUNT(*) FROM knowledge_units").fetchone()[0]
            except Exception as e:
                log.write(f"[red]DB Error: {e}[/red]")
        
        inbox_p = EXCHANGE_DIR / "inbox"
        done_p = EXCHANGE_DIR / "done"
        
        inbox_count = len(list(inbox_p.glob("*.json"))) if inbox_p.exists() else 0
        done_count = len(list(done_p.glob("*.json"))) if done_p.exists() else 0

        stats.update(
            f"[bold cyan]⚡ SYSTEM STATUS[/bold cyan]\n\n"
            f"[white]Wissens-Einheiten:[/white] [bold green]{db_count}[/bold green]\n\n"
            f"[white]Inbox Tasks (Pending):[/white] [bold yellow]{inbox_count}[/bold yellow]\n"
            f"[white]Erledigte Tasks (Done):[/white] [bold blue]{done_count}[/bold blue]\n\n"
            f"[dim]Dropzone: {EXCHANGE_DIR.name}[/dim]"
        )

        table.clear()
        for folder in ["inbox", "done"]:
            p = EXCHANGE_DIR / folder
            if p.exists():
                for f in p.glob("*.json"):
                    try:
                        with open(f, "r", encoding="utf-8") as json_file:
                            data = json.load(json_file)
                            status_color = "[bold green]" if folder == "done" else "[bold yellow]"
                            table.add_row(
                                data.get("task_id", "-"), 
                                data.get("sender", "-"), 
                                data.get("receiver", "-"), 
                                data.get("action", "-"), 
                                f"{status_color}{data.get('status', folder)}[/]"
                            )
                    except Exception as e:
                        log.write(f"[red]Lese-Fehler bei {f.name}: {e}[/red]")

if __name__ == "__main__":
    app = SBDashboard()
    app.run()
