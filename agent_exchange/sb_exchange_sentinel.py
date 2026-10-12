#!/usr/bin/env python3
import os
import json
import time
import requests
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

BASE_DIR = Path(__file__).resolve().parent
DROPZONE = Path(os.environ.get("AGENT_EXCHANGE_DIR", BASE_DIR))
LOG_FILE = DROPZONE / "sentinel.log"
WEBJARVIS_API_URL = "http://127.0.0.1:8000/api/chat"

def log_event(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {msg}"
    print(log_line)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_line + "\n")
    except Exception:
        pass

class ExchangeHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith('.json'):
            return
        
        filepath = Path(event.src_path)
        filename = filepath.name
        
        if filename.startswith("friday_msg_"):
            return
            
        time.sleep(0.5)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            sender = data.get("sender", "UNKNOWN")
            target = data.get("target", "")
            message = data.get("message", "")
            
            if target not in ["FRIDAY", "ALL_AGENTS"]:
                return
                
            log_event(f"[+] Task empfangen von {sender}: {filename}")
            
            friday_response = self.ask_friday(sender, message)
            self.send_response(target=sender, message=friday_response)
            
        except json.JSONDecodeError:
            log_event(f"[!] JSON-Fehler in Datei: {filename}")
        except Exception as e:
            log_event(f"[!] Fehler bei {filename}: {e}")

    def ask_friday(self, sender, prompt):
        log_event("[*] Übergebe Payload an WebJarvis API...")
        try:
            # Kontext-Injection: Friday wird zwingend mitgeteilt, wer spricht!
            context_prompt = f"[System-Info: Diese Nachricht kommt von {sender} via Agent-Exchange]\n\n{prompt}"
            payload = {"message": context_prompt}
            
            response = requests.post(WEBJARVIS_API_URL, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data.get("response", data.get("reply", str(data)))
            
        except Exception as e:
            err = f"SYSTEM-ERROR: WebJarvis API Fehler: {e}"
            log_event(err)
            return err

    def send_response(self, target: str, message: str):
        timestamp = int(time.time())
        response_filename = DROPZONE / f"friday_msg_{timestamp}.json"
        payload = {
            "sender": "FRIDAY",
            "target": target,
            "message": message,
            "timestamp": timestamp
        }
        try:
            with open(response_filename, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=4, ensure_ascii=False)
            log_event(f"[>] LLM-Antwort an {target} gesendet: {response_filename.name}")
        except Exception as e:
            log_event(f"[!] Schreibfehler: {e}")

def main():
    if not DROPZONE.exists():
        DROPZONE.mkdir(parents=True, exist_ok=True)
    event_handler = ExchangeHandler()
    observer = Observer()
    observer.schedule(event_handler, str(DROPZONE), recursive=False)
    try:
        observer.start()
        log_event("[*] Friday Sentinel [LLM-Bridge] aktiv.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    finally:
        observer.join()

if __name__ == "__main__":
    main()
