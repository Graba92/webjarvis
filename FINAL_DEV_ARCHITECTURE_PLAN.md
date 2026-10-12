# 🏛️ FINAL DEV ARCHITECTURE PLAN & SYSTEM COMPARISON (v3.2 Production Ready)

> **Status:** Genehmigt & vollständig harmonisiert mit F.R.I.D.A.Y., Second Brain Masterplan v3.1 und ASGRAD Multi-Agenten-Architektur.  
> **Gültig für:** `WebJarvis Master (Github-Ready / Self-Contained)`  
> **Architektur-Typ:** Autonomes Multi-Agenten- & Second-Brain-Betriebssystem  
> **Roadmap-Abarbeitung:** [`SECOND_BRAIN_ROADMAP_EXECUTION.md`](file://SECOND_BRAIN_ROADMAP_EXECUTION.md)

---

## TEIL 1: SYSTEMVERGLEICH (DELTA-ANALYSE DER 4 AGENTEN)

Ein tiefgreifender, entwicklerischer Vergleich zwischen dem unbearbeiteten Stand vor den Veränderungen und der neuen, konsolidierten Staging-Umgebung:

```
┌───────────────────────────────────────────────┐        ┌────────────────────────────────────────────────┐
│             ORIGINAL (Valhalla)               │   VS   │            KONSOLIDIERTES STAGING              │
│       Single-Daemon WebUI (Monolith)          │        │      Multi-Agent Federation + Second Brain     │
└───────────────────────────────────────────────┘        └────────────────────────────────────────────────┘
```

### 1. Codebase- & Modul-Deltas (Auditor: Agent 1)
* **Neue Subsysteme (+148 Dateien):**
  * `agy_components/`: Vollständige Integration des neutralisierten Persona-Katalogs (`01_Meta_Engineering` bis `18_Wizards`) und des Datenpools inklusive des neuen Leitstands `god_mode_tui.py`.
  * `agent_exchange/`: Vollständiges IPC-Subsystem mit Daemons (`agent_broker.py`, `sb_exchange_sentinel.py`, `agent_intercom.py`, `brave_bridge.py`).
  * `backend/llm/`: Neues hybrides Multi-LLM Gateway (`provider_router.py` und `tool_registry.py`).
* **Backend-Erweiterungen:**
  * `backend/server.py`: Ausgestattet mit der nativen FastAPI-Route `POST /api/chat` (unterstützt SSE-Streaming, Modellauswahl `gemini-2.5-flash`, `qwen2.5-coder` und automatische `SOUL.md`-Injektion).
  * `backend/actions/state_hydration.py` & `agent_manager.py`: Persistierung des globalen Agenten-Zustands und Intent-Routing.
* **Frontend-Erweiterungen:**
  * HUD Activity Monitor und dynamische Agenten-Karten (`SkillMatrix.vue`, `AgentStatusHUD.vue`), die den Live-Heartbeat aller Hintergrunddienste visualisieren.

### 2. Security- & Privacy-Audit (Auditor: Agent 2)
* **Repository-Sanitization (Zero-Leak Garantie):**
  * `.gitignore` wurde gehärtet: Schließt `MASTER_INDEX.db`, `.env`, `*.log`, `dropzone/inbox/*.json` und `dropzone/done/*.json` strikt aus.
  * Reale Datenbanken wurden durch neutrale Templates (`MASTER_INDEX.db.example`, `.env.example`) ersetzt.
* **Bereinigung privater Spuren:**
  * Keine hardcodierten Tailscale-IPs (Thorsten `100.72.56.25`) oder private Jobsuche-Referenzen mehr in den Skripten.
  * Striktes Token- und Quota-Management zur Verhinderung unkontrollierter Cloud-API-Kosten.

### 3. Multi-Agent IPC & Dropzone-Topologie (Auditor: Agent 3)
* **Vom isolierten Web-Server zum verteilten Verbund:**
  * Das Original besaß keinerlei Möglichkeit, mit externen CLIs oder Browser-Extensions zu kommunizieren.
  * Das Staging etabliert ein atomares JSON-Dropzone-Protokoll (`.tmp` -> rename `.json`), das Deadlocks und Race Conditions ausschließt.
  * Vier Daemons sichern den unterbrechungsfreien Betrieb:
    1. `agent_broker.py`: Ringpuffer-Nachrichtenverteiler.
    2. `sb_exchange_sentinel.py`: Background-Watcher für Ingestion und Live-Intercom.
    3. `agent_intercom.py`: TUI- & CLI-Terminalchat.
    4. `brave_bridge.py`: Threading-HTTP-Server auf Port 8080 für Browser-Snippets.

### 4. Pfad-Entkopplung & Knowledge-Graph Audit (Auditor: Agent 4)
* **Graph-Skalierung:**
  * Original: 56 Knotenpunkte (beschränkt auf Basisfunktionen).
  * Staging: 173 Knotenpunkte (vollständige Abbildung des Wissens- und Agenten-Ökosystems).
* **Relative Pfade & Dynamisierung:**
  * Alle 7 Kernpfade in `graph_nodes.json` sowie in sämtlichen Python-Skripten wurden von statischen `/home/graba/...`-Pfaden auf dynamische Auflösung via `Path(__file__).resolve().parent` und `os.getenv()` umgestellt.
  * Das gesamte Repository ist nun auf beliebigen Systemen und unter beliebigen Benutzernamen ohne Codeanpassung lauffähig.

---

## TEIL 2: VOLLSTÄNDIGER ARCHITEKTUR-MASTERPLAN (v3.2)

### 1. Verzeichnisbaum des konsolidierten Systems

```ascii
WebJarvis-Staging/
├── .env.example                     # Neutralisierte Vorlage für alle API-Keys & Ports
├── .gitignore                       # Gehärtete Ausschlussregeln für DBs, Logs und Payloads
├── start.sh / stop.sh               # Dynamisierte Start/Stop-Orchestrierung
├── setup.sh                         # Idempotenter Installer & Updater (-u Guard)
├── FINAL_DEV_ARCHITECTURE_PLAN.md   # Dieses Dokument (Architektur-Masterplan)
├── SECOND_BRAIN_ROADMAP_EXECUTION.md# Abarbeitungs-Roadmap mit Checkboxen
│
├── agent_exchange/                  # Autonomes Multi-Agenten IPC-Subsystem
│   ├── daemons/
│   │   ├── agent_broker.py          # Zentraler JSON-Ringpuffer-Broker
│   │   ├── sb_exchange_sentinel.py  # Hintergrundwächter & Ingestion-Relay
│   │   ├── agent_intercom.py        # TUI/CLI Live-Chat Interface
│   │   └── brave_bridge.py          # Threading HTTP Server (Port 8080)
│   ├── dropzone/
│   │   ├── inbox/                   # Eingehende Agenten-Nachrichten
│   │   └── done/                    # Atomar archivierte Transaktionen
│   └── logs/                        # Isolierte Daemon-Laufzeitlogs
│
├── agy_components/                  # Neutralisierte Antigravity-Assets
│   ├── god_mode_tui.py              # Textual Leitstand & Cockpit (4 Live-Panels)
│   ├── data-pool/
│   │   ├── MASTER_INDEX.db.example  # SQLite Datenbankschema-Vorlage
│   │   ├── friday_manifest.md       # Core-Direktiven für Friday (Cypher)
│   │   └── SECOND_BRAIN_GUIDE.md    # Betriebsanleitung für das Second Brain
│   └── personas/                    # 18 Kategorien spezialisierter KI-Personas
│
├── backend/                         # Kern-Server & Logik
│   ├── server.py                    # FastAPI Backend (:8000) mit /api/chat Route
│   ├── llm/                         # HYBRIDES MULTI-LLM SUBSYSTEM
│   │   ├── provider_router.py       # LLMRouter (Ollama SLMs <-> Cloud Frontier Models)
│   │   └── tool_registry.py         # Standardisiertes Tool-Calling & MCP Interface
│   ├── knowledge_base/
│   │   ├── graph_nodes.json         # Dynamisierter Wissensgraph (173 Knoten)
│   │   └── wiki/                    # Karpathy-Style Markdown Dokumente
│   └── actions/                     # Modulare Executor-Module & Graph-Manager
│
└── frontend/                        # Vue 3 / Vite Web-Interface
    └── src/components/              # 3D Node-Graph, SkillMatrix, Activity HUD
```

---

## 2. Hybride Multi-LLM Provider-Matrix & Tool-Orchestrierung

Das System überwindet starre Abhängigkeiten durch eine 2-Tier Architektur:

```ascii
                     +---------------------------------------+
                     |         WebUI / TUI / Intercom        |
                     +-------------------+-------------------+
                                         |
                                         v
                         +-------------------------------+
                         |   LLMRouter (provider_router) |
                         +---------------+---------------+
                                         |
           +-----------------------------+-----------------------------+
           |                                                           |
 [Tier 1: Routine / Zero-Token / Ops]                        [Tier 2: High-Cognition / Deep RAG]
           v                                                           v
  +-----------------+                                         +-----------------+
  |  JARVIS RUNTIME |                                         | FRIDAY RUNTIME  |
  |  (Local SLMs)   |                                         | (Cloud LLMs)    |
  | qwen2.5-coder   |                                         | Claude 3.5 S.   |
  | mistral / llama |                                         | Gemini 2.5 Pro  |
  +--------+--------+                                         +--------+--------+
           |                                                           |
           +-----------------------------+-----------------------------+
                                         |
                                         v
                        +---------------------------------+
                        |  ToolRegistry (tool_registry)   |
                        +----------------+----------------+
                                         |
    +-----------------+------------------+-----------------+------------------+
    |                 |                  |                 |                  |
    v                 v                  v                 v                  v
[Filesystem]     [SQLite/Lance]    [Sandboxed Shell]  [Brave Bridge]     [External MCP]
```

### Rollenmatrix:
1. **J.A.R.V.I.S. (Local System- & Ops-Executor):**
   * Standard: Lokales SLM via Ollama (`qwen2.5-coder:latest`, `mistral:latest`).
   * Aufgabe: Zero-Token Routine, System-Diagnose, Systemd-Steuerung, Ingestion.
2. **F.R.I.D.A.Y. (Meta-Kognitive Wissens- & Graph-Managerin):**
   * Standard: Claude 3.5 Sonnet / Gemini 2.5 Pro (Deep-Reasoning).
   * Aufgabe: Wissenssynthese, 3D-Graph-Refaktorisierung, Konfliktlösung, strategische Planung.

---

## 3. Das God-Mode TUI Cockpit (`god_mode_tui.py`)

Das interaktive Textual-Leitstand-Dashboard vereint alle Subsysteme in einem 2x2 Grid:

* **Panel 1 (Top-Left): Second Brain Suche**
  * Instant-Suche über `MASTER_INDEX.db` (FTS5 Volltext oder schnelles LIKE).
  * Dynamische Vorschau des gewählten Wissensdokuments.
* **Panel 2 (Top-Right): Sentinel & Systemd Live-Logs**
  * Echtzeit-Streaming aus `sentinel.log` mit farblicher Hervorhebung von Status und Fehlern.
* **Panel 3 (Bottom-Left): Agent-Exchange Monitor**
  * Live-Tracking aller ein- und ausgehenden JSON-Nachrichten der Dropzone.
  * Volltextansicht der Payloads bei Tastaturnavigation.
* **Panel 4 (Bottom-Right): System Health & I/O Telemetrie**
  * Visuelle Balken für CPU- und RAM-Last, Load Average.
  * Status der Datenbank (Größe, Zeilenanzahl, WAL-Modus) und PIDs aktiver Daemons.

---

## 4. Update-Sicherheit & Zero-Data-Loss Garantie

Beim Befehl `git pull` gefolgt von `setup.sh -u`:
1. **Kein Überschreiben:** `.env`, reale SQLite-Datenbanken (`MASTER_INDEX.db`) und Logs sind in `.gitignore` eingetragen. Git rührt diese Dateien niemals an.
2. **Setup-Guards:** `setup.sh` prüft vor jedem Kopiervorgang mit `[ ! -f ]`, ob Zieldateien existieren. Bestehende User-Konfigurationen bleiben unberührt.
3. **Dropzone-Isolation:** Nachrichten im `inbox/` und `done/` Verzeichnis werden lokal verarbeitet und sind vom Upstream entkoppelt.

---

## 5. Vollständige Handshake-Historie mit Friday

Im Zuge der Konsolidierung wurden mehrere bilaterale Abstimmungen über die Dropzone durchgeführt:
1. **Graph-Node-Audit:** Friday identifizierte 7 harte Pfade und empfahl relative Pfadauflösung.
2. **Sanitization-Plan:** Vorgabe der `agy_components/`-Struktur und `.example`-Dateien.
3. **Update-Audit:** Bestätigung der Integrität von `.gitignore` und `setup.sh -u`.
4. **Masterplan-Abgleich (v3.1):** Identifikation von Differenzen zwischen Dateisystem und Live-Graph (u.a. PQC-Evaluation, Btrfs/ZFS Snapshotting und Prognostische Ausfallwahrscheinlichkeit).
5. **Multi-LLM & TUI:** Freigabe des modularen `LLMRouter`-Entwurfs und der Entkopplung der TUI.

---

## 6. Bereitstellung & Verifikation

Zur Überprüfung und operativen Weiterarbeit steht die Roadmap bereit:
👉 **[`SECOND_BRAIN_ROADMAP_EXECUTION.md`](file://SECOND_BRAIN_ROADMAP_EXECUTION.md)**
