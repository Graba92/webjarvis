import json
import time
import os
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
WATCH_DIR = str(Path(os.environ.get("AGENT_EXCHANGE_DIR", BASE_DIR)))
AGY_CMD_TEMPLATE = "fish -c \"agy --prompt '{}'\""

class AgentExchangeHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith('.json'):
            return
        
        # Sicherstellen, dass die Datei vollständig geschrieben ist (gegen HDD Race Conditions)
        time.sleep(0.5) 
        
        try:
            with open(event.src_path, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[Broker] Fehler beim Lesen von {event.src_path}: {e}")
            return

        # Endlosschleifen-Schutz & Target-Validierung
        if data.get("sender") != "OPERATOR":
            return
            
        target = data.get("target", "").upper()
        if target in ["AGY", "ALL_AGENTS", "GEMINI"]:
            prompt = data.get("message")
            if not prompt:
                return

            print(f"[Broker] Triggere AGY für: {event.src_path}")
            
            try:
                # Führe subprocess aus und fange stdout
                result = subprocess.run(AGY_CMD_TEMPLATE.format(prompt), shell=True, capture_output=True, text=True, check=True)
                response_text = result.stdout.strip()
            except subprocess.CalledProcessError as e:
                response_text = f"Fehler bei AGY Ausführung: {e.stderr}"

            # Response schreiben
            response_filename = f"agy_response_{int(time.time())}.json"
            response_path = os.path.join(WATCH_DIR, response_filename)
            
            response_data = {
                "sender": "AGY",
                "target": "OPERATOR",
                "response": response_text,
                "triggered_by": os.path.basename(event.src_path)
            }
            
            with open(response_path, 'w') as f:
                json.dump(response_data, f, indent=2)
            print(f"[Broker] Response geschrieben: {response_path}")

if __name__ == "__main__":
    if not os.path.exists(WATCH_DIR):
        os.makedirs(WATCH_DIR)
        
    event_handler = AgentExchangeHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()
    print(f"[Broker] Überwache {WATCH_DIR}...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
