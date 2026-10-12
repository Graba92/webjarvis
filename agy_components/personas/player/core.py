#!/usr/bin/env python3
import sys, os, time, subprocess, threading
import termios, tty, select
from rich.console import Console
from rich.live import Live
from rich.table import Table

console = Console()

class Player:
    def __init__(self, directory):
        self.directory = directory
        self.files = sorted([f for f in os.listdir(directory) if f.endswith(('.mp3', '.wav', '.flac'))])
        self.current_idx = 0
        self.playing = False
        self.process = None

    def play(self):
        if not self.files: return
        self.stop()
        filepath = os.path.join(self.directory, self.files[self.current_idx])
        self.process = subprocess.Popen(['pw-play', filepath], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.playing = True

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process = None
        self.playing = False

    def next(self):
        self.current_idx = (self.current_idx + 1) % len(self.files)
        if self.playing: self.play()

def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        if select.select([sys.stdin], [], [], 0.1)[0]:
            return sys.stdin.read(1)
        return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def render_ui(player):
    table = Table(title="Terminal Music Player (Audit)", show_header=True, header_style="bold green")
    table.add_column("Status", justify="center")
    table.add_column("Datei", justify="left")

    for i, file in enumerate(player.files):
        status = "▶" if i == player.current_idx and player.playing else " "
        style = "green" if i == player.current_idx else "white"
        table.add_row(status, file, style=style)

    ui = f"\n[Steuerung] p: Spiel/Pause | n: Weiter | s: Stop | q: Beenden\n"
    return table

def main():
    player = Player(os.getcwd())
    if not player.files:
        console.print("[red]Keine Musikdateien gefunden.[/red]")
        return

    sys.stdout.write("\033[?25l") # Hide Cursor

    try:
        with Live(render_ui(player), refresh_per_second=4) as live:
            while True:
                live.update(render_ui(player))
                key = get_key()
                if key == 'q':
                    break
                elif key == 'p':
                    if player.playing: player.stop()
                    else: player.play()
                elif key == 'n':
                    player.next()
                elif key == 's':
                    player.stop()

    finally:
        player.stop()
        sys.stdout.write("\033[?25h") # Show Cursor

if __name__ == "__main__":
    main()
