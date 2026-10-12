import json
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Friday Exchange Konfiguration
WATCH_DIR = "agent_exchange/"

class FridaySentinelHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith('.json'):
            return
        
        time.sleep(0.5) # HDD Race Condition Schutz
        
        try:
            with open(event.src_path, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return

        if data.get("sender") != "OPERATOR":
            return
            
        target = data.get("target", "").upper()
        if target in ["WEBJARVIS", "FRIDAY", "ALL_AGENTS"]:
            print(f"[Sentinel] Task für Friday erkannt: {event.src_path}")
            
            # Hier würde die Weiterleitung an das WebJarvis Backend erfolgen.
            # Als Platzhalter schreiben wir eine Quittung zurück.
            
            response_filename = f"friday_response_{int(time.time())}.json"
            response_path = os.path.join(WATCH_DIR, response_filename)
            
            response_data = {
                "sender": "FRIDAY",
                "target": "OPERATOR",
                "status": "received",
                "triggered_by": os.path.basename(event.src_path),
                "message": "Task empfangen und in Verarbeitung."
            }
            
            with open(response_path, 'w') as f:
                json.dump(response_data, f, indent=2)
            print(f"[Sentinel] Quittung geschrieben: {response_path}")

if __name__ == "__main__":
    if not os.path.exists(WATCH_DIR):
        os.makedirs(WATCH_DIR)
        
    event_handler = FridaySentinelHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()
    print(f"[Sentinel] Überwache {WATCH_DIR}...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
