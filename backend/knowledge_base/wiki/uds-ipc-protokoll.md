# UDS & IPC Protokoll (uds_ipc_engine.py)

## 1. Übersicht
Die **Unix Domain Socket (UDS) IPC-Engine** stellt eine latenzarme Punkt-zu-Punkt-Kommunikation zwischen der Host-Automation (Agy) und dem kognitiven Backend (Friday) bereit.

## 2. Pfad-Konfiguration & Topologie
- **Autoritativer Pfad:**
  `SOCKET_PATH = Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/friday_ipc_{os.getuid()}")) / "friday_ipc.sock"`
  Unter CachyOS aufgelöst zu: `/run/user/1000/friday_ipc.sock`.
- **Berechtigungen:** Strikt auf `0600` (nur der lokale User `graba` darf lesen/schreiben).
- **Protokoll:** Asynchroner JSON-RPC 2.0 Dispatcher via `asyncio.start_unix_server`.

## 3. Verhältnis zur Dropzone
- Während [[agent-exchange-protocol]] als robuster, asynchroner Dateipuffer auf HDD fungiert, dient die UDS-Engine für unmittelbare In-Memory Event-Signalisierung und Telemetrie-Streaming an das [[god-mode-tui]].
- **Audit-Erkenntnis:** Eine existierende Socket-Datei beweist keine Verbindung; Clients müssen echte Verbindungsversuche unternehmen, um Stale Sockets zu erkennen.

## 4. Verknüpfungen
- [[agent-exchange-protocol]]
- [[god-mode-tui]]
- [[system-architecture-map]]
