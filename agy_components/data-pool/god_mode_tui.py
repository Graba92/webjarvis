from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input, DataTable
from textual.binding import Binding
import sqlite3
from pathlib import Path

# Datenbankpfad
DB_PATH = Path("GIT-Projekte/Eigene/Github-Ready/webjarvis/agy_components/data-pool/MASTER_INDEX.db")

class GodModeApp(App):
    """Das interaktive God-Mode Dashboard für J.A.R.V.I.S."""
    
    CSS = """
    #dashboard-grid {
        layout: grid;
        grid-size: 2 2;
        grid-columns: 1fr 1fr;
        grid-rows: 1fr 1fr;
        height: 100%;
    }
    
    .panel {
        background: $boost;
        border: solid green;
        margin: 1;
        padding: 1;
        color: green;
    }
    
    .panel-center {
        content-align: center middle;
        text-style: bold;
    }
    
    #panel-top-left {
        column-span: 1;
        row-span: 1;
        layout: vertical;
    }
    
    #search-input {
        margin: 1 0;
    }
    
    #panel-top-right {
        column-span: 1;
        row-span: 1;
    }
    
    #panel-bottom-left {
        column-span: 1;
        row-span: 1;
    }
    
    #panel-bottom-right {
        column-span: 1;
        row-span: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Shutdown"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Static(id="dashboard-grid"):
            # Oben Links: Second Brain Suche
            with Static(id="panel-top-left", classes="panel"):
                yield Input(placeholder="Second Brain Suche...", id="search-input")
                yield DataTable(id="search-results")
            
            # Andere Platzhalter
            yield Static("Sentinel Live-Logs (Standby)", id="panel-top-right", classes="panel panel-center")
            yield Static("Agent-Exchange Monitor (Standby)", id="panel-bottom-left", classes="panel panel-center")
            yield Static("I/O & System-Wächter (Standby)", id="panel-bottom-right", classes="panel panel-center")
        yield Footer()

    def on_mount(self) -> None:
        """DataTable initialisieren."""
        table = self.query_one("#search-results", DataTable)
        table.add_columns("ID", "Dateiname", "Pfad", "Vorschau")
        table.cursor_type = "row"

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Suche ausführen, wenn Input im Suchfeld bestätigt wird."""
        if event.input.id != "search-input":
            return
            
        search_term = event.value.strip()
        table = self.query_one("#search-results", DataTable)
        table.clear()

        if not search_term:
            self.notify("Bitte Suchbegriff eingeben.")
            return

        if not DB_PATH.exists():
            self.notify(f"Datenbank nicht gefunden unter: {DB_PATH}", severity="error")
            return

        try:
            conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
            cursor = conn.cursor()
            
            # Query auf knowledge_units unter Nutzung der rowid
            cursor.execute("""
                SELECT rowid, filename, path, content_preview 
                FROM knowledge_units 
                WHERE filename LIKE ? OR content_preview LIKE ?
                LIMIT 100
            """, (f"%{search_term}%", f"%{search_term}%"))
            
            results = cursor.fetchall()
            conn.close()

            if results:
                for row in results:
                    # ID, filename, path, content_preview
                    table.add_row(str(row[0]), row[1], row[2], (row[3][:50] + "...") if row[3] else "Keine Vorschau")
                self.notify(f"{len(results)} Treffer für '{search_term}'")
            else:
                self.notify(f"Keine Treffer für '{search_term}'")

        except Exception as e:
            self.notify(f"Datenbankfehler: {str(e)}", severity="error")

if __name__ == "__main__":
    app = GodModeApp()
    app.run()
