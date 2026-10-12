#!/usr/bin/env python3
import json
import time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = Path(__file__).resolve().parent
DROPZONE = Path(os.environ.get("AGENT_EXCHANGE_DIR", BASE_DIR))

class BridgeHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            target = data.get("target", "ALL_AGENTS")
            text = data.get("text", "")
            
            timestamp = int(time.time())
            filename = DROPZONE / f"operator_msg_{timestamp}.json"
            
            payload = {
                "sender": "OPERATOR",
                "target": target,
                "message": f"Browser-Eingang:\n{text}",
                "timestamp": timestamp
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=4, ensure_ascii=False)
            
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b"OK")
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

if __name__ == '__main__':
    if not DROPZONE.exists():
        DROPZONE.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(('localhost', 8080), BridgeHandler)
    server.serve_forever()
