#!/usr/bin/env python3
"""
Second Brain Sentinel (sb_sentinel.py)
Überwacht den Agy-data-pool auf Dateiänderungen und pflegt den Master-Index.
Prinzip: Zero-Data-Loss, inotify-basiert, SQLite-Backend.
Stand: 2026 | Teil der Matze-Graba-Architektur
"""

import os
import sys
import time
import sqlite3
import json
import subprocess
from pathlib import Path

# Konfiguration
BASE_DIR = Path(__file__).resolve().parent
WATCH_DIR = Path(os.environ.get("AGY_DATA_POOL", BASE_DIR / "agy_components" / "data-pool"))
DB_PATH = WATCH_DIR / "MASTER_INDEX.db"
LOG_FILE = WATCH_DIR / "sb_sentinel.log"

class KnowledgeBase:
    def __init__(self, db_path: Path):
        self.db_path = str(db_path)
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path, timeout=5.0)

    def _init_db(self):
        try:
            sys.path.insert(0, str(BASE_DIR / "backend" / "memory"))
            from master_index_init import init_db
            init_db(Path(self.db_path))
        except Exception:
            with self._get_conn() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS knowledge_units (
                        path TEXT PRIMARY KEY,
                        filename TEXT,
                        content_preview TEXT,
                        last_modified REAL,
                        tags TEXT
                    )
                """)
                conn.commit()

    def update_unit(self, file_path: Path):
        if not file_path.is_file() or file_path.suffix not in ['.md', '.txt', '.py']:
            return
        
        try:
            stats = file_path.stat()
            content = ""
            if file_path.suffix == '.md':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(500) # Preview der ersten 500 Zeichen
            
            with self._get_conn() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO knowledge_units 
                    (path, filename, content_preview, last_modified, tags)
                    VALUES (?, ?, ?, ?, ?)
                """, (str(file_path), file_path.name, content, stats.st_mtime, ""))
                conn.commit()
        except Exception as e:
            with open(LOG_FILE, "a") as f:
                f.write(f"[{time.ctime()}] Error updating {file_path}: {e}\n")

def scan_initial(kb: KnowledgeBase):
    """Initialer Scan beim Start."""
    for file in WATCH_DIR.glob("**/*"):
        if file.is_file() and file.suffix in ['.md', '.txt', '.py'] and "MASTER_INDEX.db" not in file.name:
            kb.update_unit(file)

def main():
    print(f"[*] SB-Sentinel startet. Überwachung: {WATCH_DIR}")
    kb = KnowledgeBase(DB_PATH)
    
    # Initialer Scan
    print("[*] Führe initialen Wissens-Scan durch...")
    scan_initial(kb)
    
    # Einfaches Polling als robuster Fallback (inotify-Alternative ohne externe deps)
    last_state = {}
    
    try:
        while True:
            current_files = list(WATCH_DIR.glob("**/*"))
            for f in current_files:
                if f.is_file() and f.suffix in ['.md', '.txt', '.py'] and "MASTER_INDEX.db" not in f.name:
                    mtime = f.stat().st_mtime
                    if f not in last_state or last_state[f] < mtime:
                        print(f"[+] Update erkannt: {f.name}")
                        kb.update_unit(f)
                        last_state[f] = mtime
            time.sleep(10) # Intervall für Second Brain Ingest
    except KeyboardInterrupt:
        print("\n[*] SB-Sentinel sauber beendet.")

if __name__ == "__main__":
    main()
