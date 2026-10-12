import json
import time
import subprocess
import os
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, RichLog, Input, Button
from textual.containers import Vertical, Horizontal

# Dynamische Pfadauflösung (Self-Contained)
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
EXCHANGE_DIR = Path(os.environ.get("AGENT_EXCHANGE_DIR", BASE_DIR))
BROKER_SCRIPT = str(BASE_DIR / "agent_broker.py")
SENTINEL_SCRIPT = str(BASE_DIR / "sb_exchange_sentinel.py")
VENV_PYTHON = str(PROJECT_ROOT / "backend" / ".venv" / "bin" / "python3")
if not Path(VENV_PYTHON).exists():
    VENV_PYTHON = sys.executable

class AgentIntercom(App):
    """Operator Broadcast & Chat Monitor inkl. Auto-Daemon Management"""

    CSS = """
    #chat-container {
        height: 1fr;
        border: solid green;
        margin: 1;
    }

    #chat-log {
        height: 100%;
        padding: 0 1;
    }

    #input-container {
        height: 3;
        margin: 0 1 1 1;
    }

    #prompt-input {
        width: 1fr;
        border: tall green;
    }

    #send-btn {
        width: 16;
        margin-left: 1;
        background: $success;
        color: auto;
    }

    #mute-btn {
        width: 6;
        margin-left: 1;
        background: $panel;
    }
    """

    BINDINGS = [("q", "quit", "Beenden")]

    def __init__(self):
        super().__init__()
        self.read_files = set()
        self.is_muted = False
        self.daemons = []
        EXCHANGE_DIR.mkdir(parents=True, exist_ok=True)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            with Vertical(id="chat-container"):
                yield RichLog(id="chat-log", markup=True, wrap=True)

            with Horizontal(id="input-container"):
                yield Input(placeholder="Prompt-Text ODER Dateipfad (z.B. /home/.../prompt.md)...", id="prompt-input")
                yield Button("🔊", id="mute-btn")
                yield Button("🚀 Trigger", id="send-btn")
        yield Footer()

    async def on_mount(self) -> None:
        self.log_widget = self.query_one("#chat-log", RichLog)
        self.log_widget.write("[bold green]=== OPERATOR INTERCOM BEREIT ===[/bold green]")
        self.log_widget.write(f"[dim]Dropzone: {EXCHANGE_DIR}[/dim]\n")

        # Daemons automatisch mit der WebJarvis Venv starten
        self.start_daemons()

        # Scan-Intervall starten
        self.set_interval(1.0, self.scan_dropzone)

    def start_daemons(self) -> None:
        try:
            if not os.path.exists(VENV_PYTHON):
                self.log_widget.write(f"[red][FEHLER] Venv-Python nicht gefunden: {VENV_PYTHON}[/red]")
                return

            # Starte Broker und Sentinel als Subprozesse mit der Venv
            if os.path.exists(BROKER_SCRIPT):
                d1 = subprocess.Popen([VENV_PYTHON, BROKER_SCRIPT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.daemons.append(d1)
            else:
                self.log_widget.write(f"[red][WARNUNG] Broker nicht gefunden: {BROKER_SCRIPT}[/red]")

            if os.path.exists(SENTINEL_SCRIPT):
                d2 = subprocess.Popen([VENV_PYTHON, SENTINEL_SCRIPT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.daemons.append(d2)
            else:
                self.log_widget.write(f"[red][WARNUNG] Sentinel nicht gefunden: {SENTINEL_SCRIPT}[/red]")

            self.log_widget.write("[dim]Hintergrund-Wächter (Broker & Sentinel) online (via Venv).[/dim]\n")
        except Exception as e:
            self.log_widget.write(f"[red][FEHLER] Konnte Wächter nicht starten: {e}[/red]\n")

    async def on_unmount(self) -> None:
        """Wird aufgerufen, wenn die App mit 'q' beendet wird."""
        for d in self.daemons:
            d.terminate()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-btn":
            self.send_broadcast()
        elif event.button.id == "mute-btn":
            self.is_muted = not self.is_muted
            event.button.label = "🔇" if self.is_muted else "🔊"

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "prompt-input":
            self.send_broadcast()

    def play_notification_sound(self) -> None:
        if not self.is_muted:
            try:
                subprocess.Popen(
                    ["paplay", "/usr/share/sounds/freedesktop/stereo/message.oga"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception:
                pass

    def send_broadcast(self) -> None:
        input_widget = self.query_one("#prompt-input", Input)
        raw_input = input_widget.value.strip()

        if not raw_input:
            return

        possible_path = Path(raw_input)
        if possible_path.is_file():
            try:
                with open(possible_path, "r", encoding="utf-8") as f:
                    prompt_text = f.read().strip()
            except Exception as e:
                self.log_widget.write(f"[red][FEHLER] Kann Datei nicht lesen: {e}[/red]")
                return
        else:
            prompt_text = raw_input

        timestamp = int(time.time())
        file_name = f"operator_broadcast_{timestamp}.json"
        file_path = EXCHANGE_DIR / file_name

        payload = {
            "sender": "OPERATOR",
            "target": "ALL_AGENTS",
            "message": prompt_text,
            "timestamp": timestamp
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)

            preview = prompt_text[:80] + "..." if len(prompt_text) > 80 else prompt_text
            self.log_widget.write(f"[bold yellow]<OPERATOR>[/bold yellow] {preview}")
            self.log_widget.write(f"[dim]📁 {file_name} in Dropzone gefeuert![/dim]\n")

            input_widget.value = ""
            self.read_files.add(file_name)

        except Exception as e:
            self.log_widget.write(f"[red][FEHLER] Konnte Broadcast nicht senden: {e}[/red]")

    def scan_dropzone(self) -> None:
        for file_path in sorted(EXCHANGE_DIR.glob("*.*")):
            if file_path.suffix not in [".json", ".md"]:
                continue

            if file_path.name not in self.read_files:
                self.process_file(file_path)

    def process_file(self, file_path: Path) -> None:
        try:
            sender = "UNKNOWN"
            message = ""

            if file_path.suffix == ".json":
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sender = data.get("sender", "SYSTEM").upper()
                message = data.get("message", data.get("task", "Kein Inhalt"))

            elif file_path.suffix == ".md":
                with open(file_path, "r", encoding="utf-8") as f:
                    message = f.read().strip()
                sender = "DATEI"

            if "AGY" in sender:
                color = "cyan"
            elif "FRIDAY" in sender or "WEBJARVIS" in sender:
                color = "magenta"
            elif "OPERATOR" in sender:
                return
            else:
                color = "white"

            self.log_widget.write(f"[{color}][bold]<{sender}>[/bold][/{color}] {message}")
            self.log_widget.write(f"[dim]↳ {file_path.name}[/dim]\n")

            self.read_files.add(file_path.name)

            self.play_notification_sound()

        except Exception:
            pass

if __name__ == "__main__":
    app = AgentIntercom()
    app.run()
