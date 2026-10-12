# 🧠 Second Brain Roadmap & Execution Cockpit (v3.2 Production Ready)

> **Zweck:** Schritt-für-Schritt Abarbeitungsdokument für Operator (Matze) und KI-Agenten (Agy / Friday).  
> **Prinzip:** Zero-Hallucination, Zero-Data-Loss, atomare Commits, strikte Checkboxen (`[x]`).  
> **Basis:** Abgleich von `second_brain_masterplan_final (3) last.md` mit Fridays Live-Graph.  
> **Stand:** 2026 | ASGRAD Ökosystem

---

## 0. Protokoll- & Sicherheitsregeln für die KI

1. **Persona-Aktivierung:** Vor Beginn jedes Blocks MUSS die in der Box genannte Persona aus `~/Schreibtisch/ASGRAD/FÜRJARVIS/Optimierte-PERSONAS/` geladen und in der TODO-Liste angezeigt werden.
2. **Aufgabe 0 Pflicht:** Vor Code-Änderungen MUSS der Live-Zustand des Systems per Terminal/Dateisystem geprüft werden.
3. **Clean-Context Notbremse:** Bei drohendem Token-Limit sofort mit dem Warnhinweis pausieren:
   > 🛑 *"WARNUNG: Kontext-Limit erreicht / Risiko von Halluzinationen. Bitte starte ein neues Chatfenster und übergib mir erneut den Masterplan."*
4. **Git-Schutz (Zero-Leak):** Niemals `MASTER_INDEX.db`, `.env` oder private User-Daten comitten!
5. **Erfolgs-Signal:** Nach jedem abgeschlossenen Meilenstein wird das Erfolgs-Signal (`universfield-new-notification-026-380249.mp3`) abgespielt.

---

## Phase 0: System-Audit, Caches & Realabgleich (IST-Status)
**Persona:** `01_Meta_Engineering` & `02_Logic_Reasoning`

- [x] **P0.1: Verzeichnis-Topologie & Sandbox-Entkopplung**
  - [x] Pfad 1: `agy_components/data-pool/` (aktiver Arbeits-Pool)
  - [x] Pfad 2: `~/.local/share/webjarvis/` (Live-System / WebDAV-Basis)
  - [x] Pfad 3: `GIT-Projekte/Eigene/Github-Ready/webjarvis/` (Master GitHub-Release)
- [x] **P0.2: SQLite-Zustand & DB-Audit**
  - [x] Tabellenstruktur von `knowledge_units` verifiziert (2.716 Einträge im Live-System)
  - [x] Neutralisierungs-Vorlage `MASTER_INDEX.db.example` im Staging etabliert
  - [ ] WAL-Modus aktivieren (`PRAGMA journal_mode=WAL;`) für nebenläufige Zugriffe ohne Lock-Deadlocks
- [ ] **P0.3: Cache- und Temp-Dateien bereinigen**
  - [ ] Beseitigung verwaister temporärer Pufferdateien (`*.tmp`, `.tbcache`)
  - [ ] Ausschluss redundanter KDE-Caches (`recently-used.xbel`) aus Ingest-Regeln

---

## Phase 1: WebDAV-Synchronisation & Safe Storage Bridge
**Persona:** `07_Development` (Full Feature Dev) & `08_Security` (BSI-Hardening)

- [ ] **P1.1: WebDAV-Synchronisations-Architektur definieren**
  - [ ] Modus: Bidirektionaler Sync mit Kollisionserkennung via SHA-256 Hashes und `mtime`
  - [ ] Primärquelle: `~/.local/share/webjarvis/` <-> Pool: `Agy-data-pool/`
  - [ ] Zero-Overwrite-Garantie: Wenn Quell- und Zieldatei voneinander abweichen, Erstellung von `.conflict_[timestamp]` statt Überschreiben
- [ ] **P1.2: Skript `sb_webdav_bridge.py` implementieren**
  - [ ] Idempotente Sync-Routine (CLI-Flags: `--dry-run`, `--sync-once`, `--daemon`)
  - [ ] Automatische Protokollierung in `sync_log.txt` mit Zeitstempel und Hash-Differenz
  - [ ] Watchdog-Modus: Polling mit 15s Debounce oder inotify-Trigger
- [ ] **P1.3: Integration in `sb_sentinel.py`**
  - [ ] Auto-Ingest neu synchronisierter WebDAV-Dokumente direkt in `MASTER_INDEX.db`

---

## Phase 2: SQLite MASTER_INDEX.db Optimierung & FTS5-Suche
**Persona:** `07_Development` (Full Feature Dev)

- [ ] **P2.1: Volltextsuche (FTS5) Schema-Migration**
  - [ ] Erstellung der virtuellen Tabelle `knowledge_units_fts USING fts5(path, filename, content, tags)`
  - [ ] Automatische Trigger (`AFTER INSERT`, `AFTER UPDATE`, `AFTER DELETE`) zur Synchronisation von Index und Rohdaten
- [ ] **P2.2: Chunking & Content-Ingestion erweitern**
  - [ ] Bisherige 500-Zeichen Preview-Begrenzung ablösen
  - [ ] Markdown-Dateien bis 50KB vollständig indexieren; größere Dokumente in semantische Chunks zerlegen
- [ ] **P2.3: Hub-Suchfunktion (`[b]`) reparieren & testen**
  - [ ] SQLite-Fehlerbehandlung (`sqlite3.OperationalError` abfangen)
  - [ ] Formatierte Ergebnisdarstellung mit Treffer-Kontext und WebDAV-Pfad-Auflösung

---

## Phase 3: God-Mode TUI Cockpit (`god_mode_tui.py`)
**Persona:** `07_Development` & `12_System_Maintenance`

- [x] **P3.1: Portierung & Dynamisierung der TUI**
  - [x] Quellcode nach `WebJarvis-Staging/agy_components/god_mode_tui.py` überführt
  - [x] Dynamische Pfadauflösung (via `os.getenv` und `Path(__file__)`, keine harten `/home/graba` Pfade)
- [ ] **P3.2: Vollständige Panel-Aktivierung**
  - [ ] **Panel 1 (Top-Left):** Second Brain FTS5 / LIKE SQLite Suche mit Instant-Preview
  - [ ] **Panel 2 (Top-Right):** Sentinel & Systemd Daemon Live-Logs
  - [ ] **Panel 3 (Bottom-Left):** Agent-Exchange Dropzone Live-Monitor (Intercom-Feed)
  - [ ] **Panel 4 (Bottom-Right):** System Health & I/O Telemetrie (CPU, RAM, DB-Größe, aktive IPC-Locks)

---

## Phase 4: Hybrides Multi-LLM Routing & Tool-Orchestrierung
**Persona:** `09_Agent_Orchestration` & `13_Data_Privacy`

- [ ] **P4.1: Multi-Provider LLM Gateway (`LLMRouter`)**
  - [ ] Lokale SLMs via Ollama (Qwen2.5-Coder, Mistral, Llama 3.2) für Offline-Routine & Zero-Token-Betrieb
  - [ ] Cloud Frontier Models (Gemini 2.5 Flash, Claude 3.5 Sonnet, GPT-4o) via Unified Adapter
  - [ ] Dynamisches Routing basierend auf Intent, Token-Cost und Privacy-Klasse
- [ ] **P4.2: Tool-Orchestrierung & MCP-Standard**
  - [ ] Standardisiertes JSON-RPC / MCP Interface für Werkzeuge (Filesystem, WebSearch, SQLite, Terminal)
  - [ ] Strict Enforcement durch Persona `tool_calling_orchestrator`
- [ ] **P4.3: Rollenteilung J.A.R.V.I.S. vs. F.R.I.D.A.Y.**
  - [ ] **J.A.R.V.I.S.:** Lokaler Host-Executor, TUI-Leitstand, Systemd-Steuerung, Ingestion
  - [ ] **F.R.I.D.A.Y.:** Meta-Kognitive Wissens-Orchestrierung, LanceDB/Graph-Memory, Root-Cause-Fixing

---

## Phase 5: Brave Browser Extension Bridge (Web-to-Local)
**Persona:** `08_Security` & `07_Development`

- [x] **P5.1: Lokaler HTTP-Ingest Webhook**
  - [x] ThreadingHTTPServer auf Port 8080 (`agent_exchange/daemons/brave_bridge.py`)
  - [x] Systemd User-Service `brave-bridge.service`
  - [x] CORS-Header für Browser-Kompatibilität
- [ ] **P5.2: Manifest V3 Extension & Autorisierung**
  - [ ] Bearer-Token Absicherung gegen unbefugte lokale Aufrufe
  - [ ] Kontextmenü: "An Second Brain senden" -> Atomarer Push in Dropzone & SQLite

---

## Phase 6: Manuelle Operator-Validierung (End-to-End Test)
**Operator (Matze):**

- [ ] **T1:** Sentinel & Bridge prüfen (`systemctl --user status brave-bridge`)
- [ ] **T2:** Test-Datei anlegen:
  ```bash
  echo "# Test Notiz\nErfolgreicher Testlauf des Second Brain Ingest." > agy_components/data-pool/test_knowledge.md
  ```
- [ ] **T3:** Index-Wachstum prüfen: `sqlite3 agy_components/data-pool/MASTER_INDEX.db "SELECT * FROM knowledge_units WHERE filename='test_knowledge.md';"`
- [ ] **T4:** TUI starten (`python agy_components/god_mode_tui.py`) und Suche ausführen
- [ ] **T5:** Signalton abspielen:
  ```bash
  pw-play universfield-new-notification-026-380249.mp3
  ```
