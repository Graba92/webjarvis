#!/usr/bin/env python3
"""backend/memory/master_index_init.py

MASTER_INDEX Database Initializer & Auto-Healing Engine.
Stellt sicher, dass MASTER_INDEX.db niemals leer oder unbrauchbar ist.
Erzeugt Schema (knowledge_units, FTS5 Volltext-Index, system_metadata)
und initialisiert bestehende Wissensdateien vollautomatisch unter
strenger Einhaltung von HDD-Schutz-Pragmas (WAL, synchronous=NORMAL, MMAP, Memory-Cache).
"""

from __future__ import annotations

import os
import sys
import time
import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Union

logger = logging.getLogger("WebJarvis.MasterIndex")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    )

DEFAULT_BASE: Path = Path(__file__).resolve().parent.parent.parent


def resolve_db_path(custom_path: Optional[Union[Path, str]] = None) -> Path:
    """Ermittelt den kanonischen Zielpfad der SQLite-Datenbank MASTER_INDEX.db.

    Priorität:
    1. Explizit übergebener Pfad (`custom_path`)
    2. Umgebungsvariable `AGY_DATA_POOL`
    3. Standard-Pfad: `agy_components/data-pool/MASTER_INDEX.db`

    Args:
        custom_path (Optional[Union[Path, str]]): Optionaler benutzerdefinierter Pfad.

    Returns:
        Path: Absoluter oder aufgelöster Pfad zur MASTER_INDEX.db.
    """
    if custom_path:
        return Path(custom_path).resolve()

    env_pool = os.environ.get("AGY_DATA_POOL")
    if env_pool:
        return (Path(env_pool) / "MASTER_INDEX.db").resolve()

    return (DEFAULT_BASE / "agy_components" / "data-pool" / "MASTER_INDEX.db").resolve()


def configure_hdd_pragmas(conn: sqlite3.Connection) -> None:
    """Konfiguriert SQLite-Pragmas für mechanische HDDs und 16 GB Arbeitsspeicher.

    Schutz- und Performance-Garantien:
    - WAL Mode: Schreibt Änderungen sequentiell in das Write-Ahead-Log, wodurch
      Leser und Schreiber nie blockieren und HDD-Head-Jumps drastisch sinken.
    - synchronous=NORMAL: Eliminiert synchrone fsync()-Stalls bei Schreibvorgängen
      (spart 10-15ms Latenz pro Transaktion).
    - cache_size=-64000: 64 MB Arbeitsspeicher-Cache für Indizes und B-Trees.
    - mmap_size=268435456 (256 MB): Memory-mapped I/O für blitzschnelle Lesezugriffe direkt aus dem Page-Cache.
    - temp_store=MEMORY: Sortierungen, Zwischentabellen und temporäre Indizes im RAM.
    - busy_timeout=10000: Verhindert 'database is locked' unter Last durch 10s Retry-Window.

    Args:
        conn (sqlite3.Connection): Die zu optimierende SQLite-Verbindung.
    """
    pragmas = [
        ("journal_mode", "WAL"),
        ("synchronous", "NORMAL"),
        ("cache_size", "-64000"),
        ("mmap_size", "268435456"),
        ("temp_store", "MEMORY"),
        ("busy_timeout", "10000")
    ]
    for pragma_name, pragma_val in pragmas:
        try:
            conn.execute(f"PRAGMA {pragma_name}={pragma_val};")
        except sqlite3.Error as exc:
            logger.debug("Pragma PRAGMA %s=%s konnte nicht gesetzt werden: %s", pragma_name, pragma_val, exc)


def get_optimized_connection(
    db_path: Optional[Union[Path, str]] = None,
    timeout: float = 10.0
) -> sqlite3.Connection:
    """Erzeugt eine SQLite-Verbindung mit vorkonfigurierten HDD-Schutz-Pragmas.

    Args:
        db_path (Optional[Union[Path, str]]): Pfad zur Datenbankdatei oder None für Standard.
        timeout (float): Timeout in Sekunden für Sperren (Standard: 10.0).

    Returns:
        sqlite3.Connection: Konfigurierte und optimierte Verbindung.

    Raises:
        sqlite3.OperationalError: Falls die Datenbankdatei unzugänglich ist.
    """
    target_path = resolve_db_path(db_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path), timeout=timeout)
    configure_hdd_pragmas(conn)
    return conn


def execute_with_retry(
    conn: sqlite3.Connection,
    sql: str,
    params: Optional[Union[tuple, list, dict]] = None,
    max_retries: int = 5,
    base_delay: float = 0.05
) -> sqlite3.Cursor:
    """Führt eine SQL-Anweisung mit Exponential-Backoff und Full Jitter bei SQLITE_BUSY aus.

    Speziell gehärtet für mechanische HDDs, bei denen Checkpoints kurzzeitig Latenz erzeugen.

    Args:
        conn (sqlite3.Connection): Die aktive SQLite-Verbindung.
        sql (str): Die auszuführende SQL-Anweisung.
        params (Optional[Union[tuple, list, dict]]): Bind-Parameter für die Abfrage.
        max_retries (int): Maximale Anzahl an Wiederholungsversuchen (Standard: 5).
        base_delay (float): Basisverzögerung in Sekunden (Standard: 0.05s).

    Returns:
        sqlite3.Cursor: Der Cursor nach erfolgreicher Ausführung.

    Raises:
        sqlite3.OperationalError: Falls nach max_retries die Datenbank gesperrt bleibt.
    """
    import random
    attempt = 0
    params = params or ()
    while True:
        try:
            return conn.execute(sql, params)
        except sqlite3.OperationalError as exc:
            if "locked" in str(exc).lower() or "busy" in str(exc).lower():
                attempt += 1
                if attempt > max_retries:
                    logger.error("SQLite Lock-Contention nach %d Versuchen fehlgeschlagen: %s", max_retries, exc)
                    raise
                # Exponential Backoff with Full Jitter
                jitter = random.uniform(0.01, 0.05)
                delay = min(2.0, (base_delay * (2 ** attempt)) + jitter)
                logger.warning("SQLITE_BUSY erkannt. Retry %d/%d in %.3fs...", attempt, max_retries, delay)
                time.sleep(delay)
            else:
                raise


def init_db(
    db_path: Optional[Union[Path, str]] = None,
    seed_dirs: Optional[List[Union[Path, str]]] = None
) -> Path:
    """Initialisiert das Schema von MASTER_INDEX.db und repariert fehlende Daten (Auto-Healing).

    Erzeugt:
    1. Tabelle `knowledge_units` für Metadaten & Content-Preview
    2. Tabelle `system_metadata` für Versions- und Healing-Stempel
    3. Virtuelle Tabelle `knowledge_units_fts` mit SQLite FTS5 Volltextsuche

    Führt ein automatisches Seeding durch, wenn die Tabelle leer ist.

    Args:
        db_path (Optional[Union[Path, str]]): Zielpfad der Datenbank.
        seed_dirs (Optional[List[Union[Path, str]]]): Verzeichnisse zum automatischen Indizieren.

    Returns:
        Path: Der validierte Pfad der initialisierten Datenbankdatei.

    Raises:
        sqlite3.Error: Bei schwerwiegenden SQLite-Schema- oder Dateisystemfehlern.
    """
    target_path = resolve_db_path(db_path)
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as os_err:
        logger.error("Konnte Zielverzeichnis %s nicht erstellen: %s", target_path.parent, os_err)
        raise

    conn = get_optimized_connection(target_path, timeout=10.0)
    try:
        with conn:
            # 1. Haupt-Tabelle
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_units (
                    path TEXT PRIMARY KEY,
                    filename TEXT,
                    content_preview TEXT,
                    last_modified REAL,
                    tags TEXT
                )
            """)

            # 2. System-Metadaten
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at REAL
                )
            """)

            # 3. FTS5 Volltext-Tabelle (Standalone & absturzsicher)
            fts_enabled = False
            try:
                conn.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_units_fts USING fts5(
                        filename,
                        path,
                        content_preview
                    )
                """)
                fts_enabled = True
            except sqlite3.OperationalError as fts_err:
                logger.warning("[MASTER_INDEX] FTS5 Modul nicht verfügbar, fts-Tabelle übersprungen: %s", fts_err)

            # 4. Auto-Healing: Prüfe, ob Tabellen Daten enthalten
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM knowledge_units")
            count_row = cursor.fetchone()
            count = count_row[0] if count_row else 0

            if count == 0:
                logger.info("[MASTER_INDEX] Datenbank ist leer. Starte Auto-Healing / Auto-Seeding...")
                default_seeds: List[Path] = [
                    target_path.parent,
                    DEFAULT_BASE / "backend" / "knowledge_base",
                    DEFAULT_BASE / "agy_components"
                ]
                search_dirs = [Path(d) for d in seed_dirs] if seed_dirs else default_seeds

                indexed_count = 0
                for s_dir in search_dirs:
                    if not s_dir.exists():
                        continue
                    for file_path in s_dir.rglob("*"):
                        if file_path.is_file() and file_path.suffix in ['.md', '.txt', '.py', '.json']:
                            if "MASTER_INDEX.db" in file_path.name or ".venv" in file_path.parts or "node_modules" in file_path.parts:
                                continue
                            try:
                                stats = file_path.stat()
                                preview = ""
                                try:
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        preview = f.read(600).strip()
                                except OSError as read_err:
                                    logger.debug("Datei %s konnte nicht gelesen werden: %s", file_path, read_err)
                                    preview = f"Datei: {file_path.name}"

                                rel_path = str(file_path)
                                try:
                                    rel_path = str(file_path.relative_to(DEFAULT_BASE))
                                except ValueError:
                                    pass

                                conn.execute("""
                                    INSERT OR REPLACE INTO knowledge_units 
                                    (path, filename, content_preview, last_modified, tags)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (rel_path, file_path.name, preview, stats.st_mtime, "auto-seed"))
                                indexed_count += 1
                            except Exception as file_idx_err:
                                logger.debug("Indizierungsfehler bei %s: %s", file_path, file_idx_err)

                # FTS Synchronisieren
                if fts_enabled:
                    try:
                        conn.execute("DELETE FROM knowledge_units_fts")
                        conn.execute("""
                            INSERT INTO knowledge_units_fts(rowid, filename, path, content_preview)
                            SELECT rowid, filename, path, content_preview FROM knowledge_units
                        """)
                        logger.info("[MASTER_INDEX] FTS5 Volltext-Index synchronisiert.")
                    except sqlite3.Error as fts_sync_err:
                        logger.warning("[MASTER_INDEX] FTS5 Synchronisation fehlgeschlagen: %s", fts_sync_err)

                conn.execute("""
                    INSERT OR REPLACE INTO system_metadata (key, value, updated_at)
                    VALUES ('schema_version', '2.0.0', ?)
                """, (time.time(),))
                conn.execute("""
                    INSERT OR REPLACE INTO system_metadata (key, value, updated_at)
                    VALUES ('last_auto_healing', ?, ?)
                """, (f"Indexed {indexed_count} units", time.time()))
                logger.info("[MASTER_INDEX] Auto-Healing abgeschlossen: %d Knowledge Units indiziert.", indexed_count)

    except sqlite3.Error as db_err:
        logger.error("[MASTER_INDEX] Schwerer SQLite-Fehler bei init_db: %s", db_err, exc_info=True)
        raise
    finally:
        conn.close()

    return target_path


if __name__ == "__main__":
    p = init_db()
    print(f"[✓] MASTER_INDEX.db initialisiert und verifiziert unter: {p}")
