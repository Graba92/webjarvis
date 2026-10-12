from textual.app import App, ComposeResult
from textual.widgets import Input, DataTable, Header, Footer
from textual.binding import Binding
import sqlite3
from pathlib import Path

# Datenbankpfad
DB_PATH = Path("GIT-Projekte/Eigene/Github-Ready/webjarvis/agy_components/data-pool/MASTER_INDEX.db")

class SecondBrainApp(App):
    """Eine Textual App zur Suche im Second Brain Knowledge Graphen."""
    
    CSS = """
    Input {
        dock: top;
        margin: 1 0;
    }
    DataTable {
        height: 1fr;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Input(placeholder="Suchbegriff eingeben und Enter drücken...")
        yield DataTable()
        yield Footer()

    def on_mount(self) -> None:
        """DataTable initialisieren."""
        table = self.query_one(DataTable)
        table.add_columns("ID", "Dateiname", "Pfad", "Vorschau")
        table.cursor_type = "row"

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Suche ausführen, wenn Input bestätigt wird."""
        search_term = event.value.strip()
        table = self.query_one(DataTable)
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
    app = SecondBrainApp()
    app.run()
