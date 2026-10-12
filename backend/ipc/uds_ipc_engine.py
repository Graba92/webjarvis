#!/usr/bin/env python3
"""backend/ipc/uds_ipc_engine.py

Hochperformante Unix Domain Socket (UDS) IPC-Engine für das ASGRAD-Triumvirat:
- AGY (Host/Engine)
- FRIDAY (Cognitive Core / Cypher)
- GEMINI CLI (Routine Worker)

Bietet JSON-RPC 2.0 Schnittstellen für Zero-TCP-Overhead und Microsecond-Latency.
Umfasst Hardware-Schutzmechanismen (L1 RAM/tmpfs Ringpuffer) und ein 3-Zonen
Security-Gate für riskante Shell-Operationen.
"""

from __future__ import annotations

import os
import sys
import json
import time
import asyncio
import sqlite3
import logging
import subprocess
from collections import deque
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

# Konfiguration des zentralen IPC-Loggers
logger = logging.getLogger("WebJarvis.UdsIpcEngine")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    )

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
SOCKET_PATH: Path = Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/friday_ipc_{os.getuid()}")) / "friday_ipc.sock"
DROPZONE_DIR: Path = PROJECT_ROOT / "agent_exchange"
L1_RING_DIR: Path = Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/runtime-{os.getuid()}")) / "webjarvis_ipc_ring"


class UdsIpcEngine:
    """Zentrale Unix Domain Socket IPC-Engine für das WebJarvis / ASGRAD Triumvirat.

    Stellt einen asynchronen UDS-Server bereit, der JSON-RPC 2.0 Anfragen
    mit minimalem Overhead abarbeitet und Ereignisse flüchtig im L1 tmpfs Ring
    spiegelt, um Lese-/Schreibzugriffe auf mechanischen Festplatten zu minimieren.

    Attributes:
        socket_path (Path): Pfad zur Unix-Domain-Socket-Datei.
        server (Optional[asyncio.AbstractServer]): Laufende Server-Instanz.
        clients (set[asyncio.StreamWriter]): Aktive verbundene Client-Streams.
        l1_ring (deque): In-Memory FIFO-Puffer für die jüngsten 64 System-Events.
    """

    def __init__(self, socket_path: Path = SOCKET_PATH) -> None:
        """Initialisiert die UDS IPC-Engine und bereitet das L1 tmpfs Verzeichnis vor.

        Args:
            socket_path (Path): Zielpfad des Unix Domain Sockets. Standard ist SOCKET_PATH.
        """
        self.socket_path: Path = socket_path
        self.server: Optional[asyncio.AbstractServer] = None
        self.clients: set[asyncio.StreamWriter] = set()
        self.l1_ring: deque[Dict[str, Any]] = deque(maxlen=64)

        try:
            L1_RING_DIR.mkdir(parents=True, exist_ok=True)
            logger.debug("L1 tmpfs Ringpuffer-Verzeichnis initialisiert: %s", L1_RING_DIR)
        except OSError as exc:
            logger.warning("Konnte L1 tmpfs Verzeichnis %s nicht erstellen: %s", L1_RING_DIR, exc)

    def _resolve_path(self, p: Union[str, Path]) -> Path:
        """Löst einen relativen oder absoluten Pfad gegen das Projekt-Wurzelverzeichnis auf.

        Args:
            p (Union[str, Path]): Pfadangabe als Zeichenkette oder Path-Objekt.

        Returns:
            Path: Absoluter, normalisierter Pfad.
        """
        target = Path(p)
        if not target.is_absolute():
            target = (PROJECT_ROOT / target).resolve()
        return target

    async def l1_ring_push(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """L1 Speicher-Tier: Schreibt ein flüchtiges Event in den RAM- und tmpfs-Ringpuffer.

        Gewährleistet 0 mechanische HDD-Seeks und Microsecond-Latenzen (<0.05ms).
        Alte Einträge werden bei Überschreiten von 64 Elementen zyklisch überschrieben.

        Args:
            event (Dict[str, Any]): Das zu speichernde Ereignis-Dictionary.

        Returns:
            Dict[str, Any]: Statusinformationen inklusive Tier-Bezeichnung und Ringgröße.

        Raises:
            Keine Exceptions nach außen; fehlerhafte Disk-Spiegelungen werden defensiv geloggt.
        """
        try:
            event_entry: Dict[str, Any] = {
                "id": len(self.l1_ring) + 1,
                "timestamp": time.time(),
                "event": event
            }
            self.l1_ring.append(event_entry)

            # Flüchtigen Slot im tmpfs RAM spiegeln
            try:
                slot_index = event_entry["id"] % 64
                slot_file = L1_RING_DIR / f"slot_{slot_index}.json"
                slot_file.write_text(json.dumps(event_entry), encoding="utf-8")

                # Spill-Over Guard: Bei Vollendung eines 64er-Zyklus alten Block in tmpfs spillover.log sichern
                if slot_index == 0 and len(self.l1_ring) >= 64:
                    spillover_file = L1_RING_DIR / "spillover.log"
                    with spillover_file.open("a", encoding="utf-8") as sf:
                        sf.write(json.dumps(event_entry) + "\n")
            except OSError as disk_err:
                logger.debug("Flüchtiges tmpfs Spiegeln fehlgeschlagen (unbedenklich): %s", disk_err)

            return {
                "status": "ok",
                "tier": "L1_TMPFS",
                "ring_size": len(self.l1_ring)
            }
        except Exception as exc:
            logger.error("Unerwarteter Fehler bei l1_ring_push: %s", exc, exc_info=True)
            return {"status": "error", "error": str(exc), "tier": "L1_TMPFS"}

    async def l1_ring_poll(self, limit: int = 10) -> Dict[str, Any]:
        """L1 Speicher-Tier: Holt die letzten Events direkt aus dem RAM ohne Festplattenzugriff.

        Args:
            limit (int): Maximale Anzahl an zurückzugebenden Events (Standard: 10).

        Returns:
            Dict[str, Any]: Ergebnis-Dictionary mit Event-Liste, Anzahl und Tier-Status.
        """
        try:
            safe_limit = max(1, min(limit, 64))
            items = list(self.l1_ring)[-safe_limit:]
            return {
                "status": "ok",
                "tier": "L1_TMPFS",
                "count": len(items),
                "events": items
            }
        except Exception as exc:
            logger.error("Fehler bei l1_ring_poll: %s", exc, exc_info=True)
            return {"status": "error", "error": str(exc), "tier": "L1_TMPFS", "events": []}

    # -------------------------------------------------------------------------
    # Kern-Werkzeuge (JSON-RPC 2.0) mit 3-Zonen Security Matrix
    # -------------------------------------------------------------------------

    async def cli_executor(
        self,
        command: str,
        timeout: int = 30,
        sudo: bool = False
    ) -> Dict[str, Any]:
        """Führt Terminal-Befehle unter strikter Einhaltung der 3-Zonen Security-Matrix aus.

        Befehle der Zone RED (potenziell destruktiv wie rm -rf, Paketmanager-Deinstallation,
        Shutdown) werden sofort blockiert und erfordern eine explizite Hardware-Freigabe
        im 6-Panel God-Mode TUI ([y] Freigeben).

        Args:
            command (str): Auszuführender Bash-Befehl.
            timeout (int): Maximales Ausführungszeitfenster in Sekunden (Standard: 30).
            sudo (bool): Privilegierte Ausführung (wird automatisch als Zone RED gewertet).

        Returns:
            Dict[str, Any]: Ergebnis mit exit_code, stdout, stderr oder Status CONFIRMATION_REQUIRED.
        """
        # Zone RED Prüfliste: Destruktive und privilegierte Systembefehle
        destructive = [
            "rm -rf", "pacman -R", "pacman -S", "reboot", "shutdown",
            "mkfs", "dd if=", "systemctl stop", "systemctl restart"
        ]

        if sudo or any(d in command for d in destructive):
            logger.warning("[ZONE RED DETECTED] Befehl erfordert Hardware Confirmation Gate: %s", command)
            gate_payload = {
                "status": "CONFIRMATION_REQUIRED",
                "zone": "RED",
                "command": command,
                "timestamp": int(time.time()),
                "message": "Befehl erfordert physische Freigabe im 6-Panel God-Mode TUI (Taste [y])"
            }
            try:
                L1_RING_DIR.mkdir(parents=True, exist_ok=True)
                DROPZONE_DIR.mkdir(parents=True, exist_ok=True)
                (L1_RING_DIR / "confirmation_gate_active.json").write_text(
                    json.dumps(gate_payload, indent=2), encoding="utf-8"
                )
                (DROPZONE_DIR / "confirmation_gate_active.json").write_text(
                    json.dumps(gate_payload, indent=2), encoding="utf-8"
                )
            except OSError as disk_err:
                logger.error("Konnte Confirmation Gate Signals nicht schreiben: %s", disk_err)

            return gate_payload

        try:
            logger.debug("[CLI EXECUTOR] Starte Subprozess: %s (Timeout: %ds)", command, timeout)
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(PROJECT_ROOT)
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=float(timeout))
            return {
                "exit_code": proc.returncode,
                "stdout": stdout.decode("utf-8", "replace").strip(),
                "stderr": stderr.decode("utf-8", "replace").strip()
            }
        except asyncio.TimeoutError:
            logger.warning("[CLI EXECUTOR] Timeout nach %ds für Befehl: %s", timeout, command)
            return {"error": f"Command timed out after {timeout}s", "command": command}
        except Exception as exc:
            logger.error("[CLI EXECUTOR] Unerwarteter Ausführungsfehler: %s", exc, exc_info=True)
            return {"error": str(exc), "command": command}

    async def file_ops(
        self,
        action: str,
        path: str,
        content: str = "",
        line_range: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Granulare, sichere Dateimanipulation (read, write, patch, diff).

        Args:
            action (str): Eine von 'read', 'write', 'patch', 'diff'.
            path (str): Zieldateipfad (relativ zum Projekt oder absolut).
            content (str): Zu schreibender oder einzufügender Dateiinhalt.
            line_range (Optional[List[int]]): 2-Element-Liste [start_line, end_line] für 'patch'.

        Returns:
            Dict[str, Any]: Status-Dictionary mit 'status': 'ok' oder 'status': 'error'.
        """
        target = self._resolve_path(path)
        try:
            if action == "read":
                if not target.is_file():
                    alt1 = DROPZONE_DIR / path
                    alt2 = PROJECT_ROOT / "agy_components" / "data-pool" / path
                    if alt1.is_file():
                        target = alt1
                    elif alt2.is_file():
                        target = alt2
                    else:
                        logger.warning("[FILE OPS] Datei nicht gefunden: %s", path)
                        return {"status": "error", "error": f"File not found: {path}"}
                txt = target.read_text(encoding="utf-8", errors="replace")
                return {"status": "ok", "path": str(target), "content": txt, "size": len(txt)}

            elif action == "write":
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                logger.info("[FILE OPS] Datei erfolgreich geschrieben: %s (%d Bytes)", target, len(content))
                return {"status": "ok", "path": str(target), "bytes": len(content)}

            elif action == "patch":
                if not target.is_file():
                    return {"status": "error", "error": f"File not found: {path}"}
                lines = target.read_text(encoding="utf-8").splitlines()
                if line_range and len(line_range) == 2:
                    start, end = line_range
                    if start < 0 or end > len(lines) or start > end:
                        return {"status": "error", "error": f"Invalid line range indices: {line_range}"}
                    new_lines = lines[:start] + content.splitlines() + lines[end:]
                    target.write_text("\n".join(new_lines), encoding="utf-8")
                    logger.info("[FILE OPS] Patch erfolgreich auf %s angewendet", target)
                    return {"status": "ok", "path": str(target)}
                return {"status": "error", "error": "Invalid line_range for patch"}

            elif action == "diff":
                if not target.is_file():
                    return {"status": "error", "error": f"File not found: {path}"}
                return {"status": "ok", "path": str(target), "exists": True, "size": target.stat().st_size}

            logger.error("[FILE OPS] Unbekannte Aktion: %s", action)
            return {"status": "error", "error": f"Unknown action: {action}"}
        except Exception as exc:
            logger.error("[FILE OPS] Fehler bei Aktion '%s' auf '%s': %s", action, path, exc, exc_info=True)
            return {"status": "error", "error": str(exc)}

    async def db_query(
        self,
        query: str,
        params: Optional[List[Any]] = None,
        db_path: str = "MASTER_INDEX.db"
    ) -> Dict[str, Any]:
        """Führt optimierte SQLite-Abfragen mit HDD-Schonungs-Pragmas aus.

        Nutzt WAL-Modus, memory-mapped I/O und Cache-Pragmas zur Minimierung
        mechanischer Schreib-/Leseköpfe auf HDDs.

        Args:
            query (str): Auszuführendes SQL-Statement.
            params (Optional[List[Any]]): Parameterliste für Prepared Statements.
            db_path (str): Datenbankpfad (Standard: 'MASTER_INDEX.db').

        Returns:
            Dict[str, Any]: Ergebnis mit Zeilenliste ('rows') oder betroffenen Zeilen ('rows_affected').
        """
        params = params or []
        try:
            from memory.master_index_init import resolve_db_path, configure_hdd_pragmas
            default_db = resolve_db_path()
        except Exception:
            default_db = PROJECT_ROOT / "agy_components" / "data-pool" / "MASTER_INDEX.db"
            configure_hdd_pragmas = None

        if db_path == "MASTER_INDEX.db":
            db_target = default_db
        else:
            db_target = self._resolve_path(db_path)
            if not db_target.is_file():
                db_target = default_db

        try:
            with sqlite3.connect(str(db_target), timeout=5.0) as conn:
                if configure_hdd_pragmas:
                    try:
                        configure_hdd_pragmas(conn)
                    except Exception as p_err:
                        logger.debug("Fehler beim Anwenden der HDD-Pragmas: %s", p_err)
                else:
                    try:
                        conn.execute("PRAGMA journal_mode=WAL;")
                        conn.execute("PRAGMA synchronous=NORMAL;")
                        conn.execute("PRAGMA cache_size=-64000;")
                        conn.execute("PRAGMA mmap_size=268435456;")
                        conn.execute("PRAGMA temp_store=MEMORY;")
                    except Exception:
                        pass

                try:
                    from memory.master_index_init import execute_with_retry
                    cur = execute_with_retry(conn, query, params)
                except Exception:
                    cur = conn.cursor()
                    cur.execute(query, params)

                if query.strip().upper().startswith("SELECT"):
                    rows = cur.fetchall()
                    return {"rows": rows, "count": len(rows), "db": str(db_target.name)}
                conn.commit()
                return {"rows_affected": cur.rowcount, "db": str(db_target.name)}
        except Exception as exc:
            logger.error("[DB QUERY] SQL-Fehler auf %s: %s", db_target, exc)
            return {"error": str(exc), "db": str(db_target)}

    async def lance_memory_search(
        self,
        query: str,
        top_k: int = 5,
        filter_tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Durchsucht das Gedächtnis via FTS5-Volltextindex mit robustem LIKE-Fallback.

        Args:
            query (str): Suchbegriff oder Freitext.
            top_k (int): Maximale Trefferanzahl (Standard: 5).
            filter_tags (Optional[List[str]]): Optionale Filter-Tags (zukünftige Erweiterung).

        Returns:
            Dict[str, Any]: Suchergebnisse mit Treffern und Quellenangabe ('fts5' oder 'like_fallback').
        """
        clean_q = query.replace('"', '').replace("'", "").strip()
        if not clean_q:
            return {"status": "ok", "source": "empty", "results": []}

        try:
            fts_res = await self.db_query(
                "SELECT filename, path, content_preview FROM knowledge_units_fts WHERE knowledge_units_fts MATCH ? LIMIT ?",
                [f'"{clean_q}"*', top_k]
            )
            if "rows" in fts_res and fts_res["rows"]:
                return {
                    "status": "ok",
                    "source": "fts5",
                    "results": [{"filename": r[0], "path": r[1], "preview": r[2]} for r in fts_res["rows"]]
                }
        except Exception as fts_err:
            logger.warning("[MEMORY SEARCH] FTS5 Match fehlgeschlagen, nutze LIKE: %s", fts_err)

        # Fallback auf Standard SQL LIKE
        try:
            like_res = await self.db_query(
                "SELECT filename, path, content_preview FROM knowledge_units WHERE filename LIKE ? OR content_preview LIKE ? LIMIT ?",
                [f"%{clean_q}%", f"%{clean_q}%", top_k]
            )
            rows = like_res.get("rows", [])
            return {
                "status": "ok",
                "source": "like_fallback",
                "results": [{"filename": r[0], "path": r[1], "preview": r[2]} for r in rows]
            }
        except Exception as exc:
            logger.error("[MEMORY SEARCH] Fehler bei Gedächtnissuche: %s", exc)
            return {"status": "error", "error": str(exc), "results": []}

    async def agent_exchange_send(
        self,
        target: str,
        payload: Optional[Any] = None,
        message: Optional[str] = None,
        priority: str = "normal",
        exclude_writer: Optional[asyncio.StreamWriter] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Schreibt eine Nachricht in die Dropzone und benachrichtigt verbundene Clients per UDS.

        Args:
            target (str): Empfänger-Agent (z. B. 'FRIDAY', 'AGY', 'GEMINI').
            payload (Optional[Any]): Nutzdaten (Dictionary, String oder Objekt).
            message (Optional[str]): Optionale Kurznachricht.
            priority (str): Prioritätsstufe ('normal', 'high', 'urgent').
            exclude_writer (Optional[asyncio.StreamWriter]): Client-Stream, der nicht benachrichtigt werden soll.
            **kwargs (Any): Zusätzliche Parameter für den Nachrichten-Payload.

        Returns:
            Dict[str, Any]: Bestätigung mit Dateiname der erzeugten Dropzone-Nachricht.
        """
        try:
            DROPZONE_DIR.mkdir(parents=True, exist_ok=True)
            ts = int(time.time())
            msg_file = DROPZONE_DIR / f"ipc_msg_{ts}.json"

            final_payload = payload if payload is not None else {}
            if isinstance(final_payload, str):
                final_payload = {"text": final_payload}
            elif not isinstance(final_payload, dict):
                final_payload = {"data": str(final_payload)}

            if message:
                final_payload["message"] = message
            for k, v in kwargs.items():
                final_payload[k] = v

            full_data: Dict[str, Any] = {
                "sender": kwargs.get("sender", "UDS_ENGINE"),
                "target": target,
                "priority": priority,
                "payload": final_payload,
                "timestamp": ts
            }

            msg_file.write_text(json.dumps(full_data, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.debug("[AGENT EXCHANGE] Nachricht hinterlegt: %s für %s", msg_file.name, target)

            # Broadcast an alle ANDEREN verbundenen UDS-Clients
            broadcast_msg = json.dumps({"type": "dropzone_event", "file": str(msg_file.name), "data": full_data}) + "\n"
            broadcast_bytes = broadcast_msg.encode("utf-8")

            for w in list(self.clients):
                if exclude_writer and w == exclude_writer:
                    continue
                try:
                    w.write(broadcast_bytes)
                    await w.drain()
                except Exception as client_err:
                    logger.debug("[AGENT EXCHANGE] Fehler bei Broadcast an Client: %s", client_err)
                    self.clients.discard(w)

            return {"status": "sent", "file": str(msg_file.name)}
        except Exception as exc:
            logger.error("[AGENT EXCHANGE] Fehler bei agent_exchange_send: %s", exc, exc_info=True)
            return {"status": "error", "error": str(exc)}

    # -------------------------------------------------------------------------
    # UDS Server Lifecycle & RPC Dispatcher
    # -------------------------------------------------------------------------

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Verarbeitet eingehende Client-Verbindungen und delegiert JSON-RPC 2.0 Aufrufe.

        Args:
            reader (asyncio.StreamReader): Eingehender Stream-Reader des UDS-Clients.
            writer (asyncio.StreamWriter): Ausgehender Stream-Writer des UDS-Clients.
        """
        self.clients.add(writer)
        client_peer = "UDS_Client"
        logger.debug("[UDS SERVER] Neuer Client verbunden (%s)", client_peer)

        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                try:
                    req = json.loads(line.decode("utf-8").strip())
                    req_id = req.get("id")
                    method = req.get("method")
                    params = req.get("params", {})

                    result: Any = None
                    if method == "cli_executor":
                        result = await self.cli_executor(**params)
                    elif method == "file_ops":
                        result = await self.file_ops(**params)
                    elif method == "db_query":
                        result = await self.db_query(**params)
                    elif method == "lance_memory_search":
                        result = await self.lance_memory_search(**params)
                    elif method == "agent_exchange_send":
                        result = await self.agent_exchange_send(exclude_writer=writer, **params)
                    elif method == "l1_ring_push":
                        result = await self.l1_ring_push(**params)
                    elif method == "l1_ring_poll":
                        result = await self.l1_ring_poll(**params)
                    else:
                        result = {"error": f"Unknown method: {method}"}

                    resp = {"jsonrpc": "2.0", "id": req_id, "result": result}
                    writer.write((json.dumps(resp) + "\n").encode("utf-8"))
                    await writer.drain()
                except json.JSONDecodeError as jde:
                    logger.warning("[UDS SERVER] Ungültiges JSON empfangen: %s", jde)
                    err_resp = {"jsonrpc": "2.0", "id": None, "error": f"Parse error: {str(jde)}"}
                    writer.write((json.dumps(err_resp) + "\n").encode("utf-8"))
                    await writer.drain()
                except Exception as ex:
                    logger.error("[UDS SERVER] RPC-Verarbeitungsfehler: %s", ex, exc_info=True)
                    err_resp = {"jsonrpc": "2.0", "id": None, "error": str(ex)}
                    writer.write((json.dumps(err_resp) + "\n").encode("utf-8"))
                    await writer.drain()
        except asyncio.CancelledError:
            pass
        except Exception as sock_err:
            logger.debug("[UDS SERVER] Client-Verbindung beendet oder Fehler: %s", sock_err)
        finally:
            self.clients.discard(writer)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            logger.debug("[UDS SERVER] Client getrennt.")

    async def start(self) -> None:
        """Startet den Unix Domain Socket Server und setzt sichere Datei-Berechtigungen (0600).

        Raises:
            OSError: Wenn der Socket nicht gebunden oder erstellt werden kann.
        """
        try:
            self.socket_path.parent.mkdir(parents=True, exist_ok=True)
            if self.socket_path.exists():
                self.socket_path.unlink()

            self.server = await asyncio.start_unix_server(self.handle_client, path=str(self.socket_path))
            # Höchste Sicherheit: Nur Owner darf lesen/schreiben (0600)
            os.chmod(self.socket_path, 0o600)
            logger.info("[*] Unix Domain Socket aktiv unter: %s (Berechtigungen: 0600)", self.socket_path)
        except Exception as exc:
            logger.critical("[UDS SERVER] Start fehlgeschlagen: %s", exc, exc_info=True)
            raise

    async def stop(self) -> None:
        """Beendet den UDS Server geordnet und bereinigt den Socket-Pfad."""
        logger.info("[!] Fahre UDS IPC Engine herunter...")
        if self.server:
            self.server.close()
            try:
                await self.server.wait_closed()
            except Exception as close_err:
                logger.warning("Fehler beim Schließen des Servers: %s", close_err)

        for w in list(self.clients):
            try:
                w.close()
            except Exception:
                pass
        self.clients.clear()

        if self.socket_path.exists():
            try:
                self.socket_path.unlink()
                logger.info("[*] Socket-Datei erfolgreich bereinigt.")
            except OSError as unl_err:
                logger.warning("Konnte Socket-Datei nicht löschen: %s", unl_err)


if __name__ == "__main__":
    engine = UdsIpcEngine()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(engine.start())
        print("[+] UDS Engine läuft. Warte auf Anfragen...")
        loop.run_forever()
    except KeyboardInterrupt:
        print("\n[!] UDS Engine wird heruntergefahren.")
        loop.run_until_complete(engine.stop())
    finally:
        loop.close()
