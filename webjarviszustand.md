# 🧠 J.A.R.V.I.S. AI OS (Codename: Cypher) — Architektur-, Code- & Zustandsdokumentation

> **Status:** Live & Gehärtet (Produktivzustand)  
> **Zielplattform:** CachyOS / Arch Linux (KDE Plasma 6, Wayland, PipeWire, Bubblewrap)  
> **Maintainer / Blueprint:** Matthias Haase (@Graba92)  
> **Architektur-Reviewer:** Matze (SysOps & Low-Level Backend Architect)  
> **Dokumentationspfad:** `/home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarviszustand.md`  
> **Erstellt am:** 07. Oktober 2026  

---

## 📋 Inhaltsverzeichnis

1. [Executive Summary & Systemphilosophie](#1-executive-summary--systemphilosophie)
2. [High-Level Systemarchitektur (ASCII)](#2-high-level-systemarchitektur-ascii)
3. [End-to-End Daten- & Kontrollflüsse (ASCII)](#3-end-to-end-daten--kontrollflüsse-ascii)
   - [3.1 Vollduplex Audio & Voice-Streaming Pipeline](#31-vollduplex-audio--voice-streaming-pipeline)
   - [3.2 Tool-Call Execution & Confirmation Gate](#32-tool-call-execution--confirmation-gate)
   - [3.3 60Hz Telemetrie- & Shader-Synchronisation](#33-60hz-telemetrie--shader-synchronisation)
4. [Vollständiger Verzeichnis- & Dateibaum](#4-vollständiger-verzeichnis--dateibaum)
5. [Backend Deep-Dive ("Wie, Was, Wo")](#5-backend-deep-dive-wie-was-wo)
   - [5.1 Server & WebSocket Engine (`backend/server.py`)](#51-server--websocket-engine-backendserverpy)
   - [5.2 Gemini Live Controller (`backend/core/gemini_live.py`)](#52-gemini-live-controller-backendcoregemini_livepy)
   - [5.3 Bubblewrap Sandbox & Prozessisolation (`backend/core/sandbox.py`)](#53-bubblewrap-sandbox--prozessisolation-backendcoresandboxpy)
   - [5.4 Dynamische Tool-Discovery & OpenAPI Sanitizer (`backend/core/action_loader.py`)](#54-dynamische-tool-discovery--openapi-sanitizer-backendcoreaction_loaderpy)
   - [5.5 Audio Streamer (`backend/core/audio_streamer.py`)](#55-audio-streamer-backendcoreaudio_streamerpy)
   - [5.6 Brain Vault Backup & Restore (`backend/core/backup_manager.py`)](#56-brain-vault-backup--restore-backendcorebackup_managerpy)
   - [5.7 Hardware Safety Confirmation Gate (`backend/core/confirm.py`)](#57-hardware-safety-confirmation-gate-backendcoreconfirmpy)
   - [5.8 Cron & Reminder Engine (`backend/core/cron_engine.py`)](#58-cron--reminder-engine-backendcorecron_enginepy)
   - [5.9 Model Context Protocol Bridge (`backend/core/mcp_client.py`)](#59-model-context-protocol-bridge-backendcoremcp_clientpy)
   - [5.10 Actions & Werkzeug-Katalog (`backend/actions/`)](#510-actions--werkzeug-katalog-backendactions)
   - [5.11 Multi-Tier Gedächtnissystem (`backend/memory/`)](#511-multi-tier-gedächtnissystem-backendmemory)
6. [Frontend Deep-Dive ("Wie, Was, Wo")](#6-frontend-deep-dive-wie-was-wo)
   - [6.1 Next.js 15 App-Router (`frontend/app/`)](#61-nextjs-15-app-router-frontendapp)
   - [6.2 Three.js Holographischer Szenengraph (`frontend/components/ApexWorld.tsx`)](#62-threejs-holographischer-szenengraph-frontendcomponentsapexworldtsx)
   - [6.3 HUD Komponenten & Fenster-Matrix (`frontend/components/`)](#63-hud-komponenten--fenster-matrix-frontendcomponents)
   - [6.4 WebSocket Client State Machine (`frontend/lib/websocket.ts`)](#64-websocket-client-state-machine-frontendlibwebsocketts)
7. [Desktop Orchestration & Manager](#7-desktop-orchestration--manager)
   - [7.1 PyQt6 Cyberpunk HUD Manager (`manager.py`)](#71-pyqt6-cyberpunk-hud-manager-managerpy)
   - [7.2 Shell-Orchestrierungs-Skripte (`*.sh`)](#72-shell-orchestrierungs-skripte-sh)
8. [Sicherheits- & Sandbox-Matrix](#8-sicherheits--sandbox-matrix)
9. [Entwickler-Leitfaden (Developer How-To)](#9-entwickler-leitfaden-developer-how-to)

---

## 1. Executive Summary & Systemphilosophie

**J.A.R.V.I.S. (Codename: Cypher)** ist kein typischer Wrapper um eine LLM-REST-API, sondern ein vollwertiges, autonomes und multimodales **Desktop-KI-Betriebssystem**, das speziell für Linux (CachyOS und Arch Linux) unter KDE Plasma 6 (Wayland) entwickelt wurde.

### Kernprinzipien:
1. **Voice-First & Zero-Latenz:** Bidirektionales Vollduplex-Audio via Google Gemini Live (`models/gemini-3.1-flash-live-preview`). Audio wird nativ im Python-Backend über PipeWire gestreamt – der Browser bleibt schlank und fungiert als reines Visualisierungs- und Kontroll-HUD.
2. **Emanzipierte Partner-Persona:** Cypher agiert als ebenbürtiger, digitaler Partner mit trockenem, sarkastischem Humor. Keine unterwürfigen Floskeln, sondern messerscharfe Präzision bei System- und Code-Operationen.
3. **Hermetische Sicherheit durch Fail-Safe Sandbox:** Shell- und Dateibefehle laufen isoliert via **Bubblewrap (`bwrap`)**. Absolute Pfad-Whitelist, Traversal-Schutz, symlink-Prüfung, `--die-with-parent`-Prozessisolierung und strikte Verweigerung von unsicheren Host-Fallbacks.
4. **Physisches Hardware-Safety-Gate:** Irreversible oder gefährliche Aktionen (System-Shutdown, Reboot, Massenlöschung) werden nicht blind ausgeführt, sondern erfordern eine explizite Bestätigung über das HUD.
5. **Autonome Persistenz & Brain Vault:** Vollständiges Gedächtnis (Langzeitfakten, SQLite-Kalender mit `VACUUM INTO`, LanceDB Vektordaten, 3D-Wissensgraph `graph_nodes.json`, Identitätsdateien) wird 1-Klick-gesichert und im laufenden Betrieb restauriert.

---

## 2. High-Level Systemarchitektur (ASCII)

```text
+----------------------------------------------------------------------------------------------------+
|                                    LINUX DESKTOP (CachyOS / Wayland)                               |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|   +--------------------------+                         +---------------------------------------+   |
|   |   PyQt6 HUD Manager      |                         |       Next.js 15 WebGL Client         |   |
|   |      (manager.py)        |                         |         (Port 3000 / Chromium)        |   |
|   +-------------+------------+                         +-------------------+-------------------+   |
|                 | (TCP Check / Subprocess)                                 |                       |
|                 |                                                          | (WebSocket JSON / RPC)|
|                 +----------------------------+                             |                       |
|                                              |                             |                       |
|                                              v                             v                       |
|   +------------------------------------------------------------------------+-------------------+   |
|   |                         PYTHON BACKEND CORE (backend/server.py:8765)                       |   |
|   +--------------------------------------------------------------------------------------------+   |
|   |                                                                                            |   |
|   |  +------------------------+  +---------------------------+  +---------------------------+  |   |
|   |  |   Gemini Live Client   |  |     Action Registry       |  |    Audio Streamer (PCM)   |  |   |
|   |  |  (gemini_live.py:SDK)  |  |   (action_loader.py)      |  |    (audio_streamer.py)    |  |   |
|   |  +-----------+------------+  +-------------+-------------+  +-------------+-------------+  |   |
|   |              |                             |                              |                    |   |
|   |              | Tool Calls                  | Dynamischer Dispatch         | 16kHz In / 24kHz Out
|   |              v                             v                              v                    |   |
|   |  +------------------------+  +---------------------------+  +---------------------------+  |   |
|   |  | Hardware Safety Gate   |  |  Bubblewrap (bwrap) Core  |  |   PipeWire Virtual Sinks  |  |   |
|   |  |      (confirm.py)      |  |       (sandbox.py)        |  |    (Microphone / Spk)     |  |   |
|   |  +------------------------+  +-------------+-------------+  +---------------------------+  |   |
|   |                                            |                                               |   |
|   |                                            | Hermetische Isolation                         |   |
|   |                                            v                                               |   |
|   |                             +------------------------------+                               |   |
|   |                             |   14 Modulare Actions        |                               |   |
|   |                             |   (actions/*.py)             |                               |   |
|   |                             +--------------+---------------+                               |   |
|   |                                            |                                               |   |
|   +--------------------------------------------|-----------------------------------------------+   |
|                                                |                                                   |
|                                                v                                                   |
|   +--------------------------------------------------------------------------------------------+   |
|   |                               PERSISTENTES MULTI-TIER GEDÄCHTNIS                           |   |
|   |  - SQLite (calendar.db via WAL / VACUUM)       - LanceDB (Vektor-Embedding / lancedb_data)|   |
|   |  - JSON (long_term.json, graph_nodes.json)     - Agent-Kern (SOUL.md, MEMORY.md)          |   |
|   +--------------------------------------------------------------------------------------------+   |
|                                                |                                                   |
|                                                v                                                   |
|   +--------------------------------------------------------------------------------------------+   |
|   |                     ISOLIERTER DATEISYSTEM- & PROZESS-NAMESPACE (bwrap)                    |   |
|   |  - Read-Only System (/usr, /lib, /bin)         - Writable Whitelist (sandbox_workspace)    |   |
|   |  - Isoliertes /proc, /dev, /tmp                - Subprozess-Schutz (--die-with-parent)     |   |
|   +--------------------------------------------------------------------------------------------+   |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. End-to-End Daten- & Kontrollflüsse (ASCII)

### 3.1 Vollduplex Audio & Voice-Streaming Pipeline

```text
[User spricht]
      │
      ▼
PipeWire / ALSA Mikrofon
      │
      ▼
AudioStreamer._capture_loop() (16 kHz, 16-Bit Mono PCM)
      │
      ├──────────────────────────────────────────────┐
      │ (Audio Frames)                               │ (RMS Pegel berechnet)
      ▼                                              ▼
GeminiLiveController._send_audio_loop()      TelemetryThrottler (60 Hz)
      │                                              │
      ▼ (WSS Realtime Input Blob)                    ▼ (JSON "audio_level")
Google Gemini Live API (3.1 Flash)          Next.js Frontend (ApexWorld.tsx)
      │                                              │
      ▼ (PCM 24 kHz Output Chunks)                   ▼
GeminiLiveController._receive_loop()         Three.js Hologramm & Shader pulsieren
      │
      ▼
AudioStreamer.audio_in_queue
      │
      ▼
PipeWire / SoundDevice Playback (Lautsprecher)
```

---

### 3.2 Tool-Call Execution & Confirmation Gate

```text
Google Gemini Live API
      │
      ▼ tool_call (z.B. "sandboxed_shell" oder "file_controller")
GeminiLiveController._receive_loop()
      │
      ▼ ActionRegistry.run(name, args, ctx)
Action Loader
      │
      ├─► [Ist Aktion destruktiv? (z.B. Reboot, rm -rf)] ──► JA ──┐
      │                                                           │
      │ NEIN                                                      ▼
      │                                              confirm.py (Safety Gate)
      │                                                           │
      │                                                           ├─► Broadcast "confirm_request"
      │                                                           │   an Frontend (ConfirmBanner)
      │                                                           │
      │                                                           ├─► User klickt "BESTÄTIGEN"
      │                                                           │
      │                                                           ▼
      ├◄───────────────────────────────────────────── Rückmeldung erteilt
      │
      ▼
core/sandbox.py: execute_sandboxed()
      │
      ├─► Pfadprüfung via is_path_allowed() (NFC, resolve(), Whitelist)
      │        │
      │        ├─► [Pfad illegal & kein OS-Vollzugriff?] ──► Block mit Exit 1
      │
      ├─► Bubblewrap verfügbar?
      │        │
      │        ├─► [bwrap fehlt?] ─────────────────────────► Abbruch mit Exit 126
      │
      ▼ bwrap --unshare-all --ro-bind / / --bind <allowed> ...
Linux Kernel Namespace (Subprozess)
      │
      ▼ Rückgabe (exit_code, stdout, stderr)
FunctionResponse (types.FunctionResponse)
      │
      ▼ send_tool_response()
Google Gemini Live API
      │
      ▼ Antwort & Synthese im gleichen Voice-Turn
User hört das Ergebnis via Lautsprecher
```

---

### 3.3 60Hz Telemetrie- & Shader-Synchronisation

```text
System-Ressourcen (psutil, /proc, sensors)
      │
      ▼ 1 Hz Loop
actions/system_monitor.py: get_system_telemetry()
      │
      ▼ broadcast({"type": "telemetry", "data": ...})
Next.js Frontend: socketManager
      │
      ├─► DevConsole.tsx: CPU / RAM / GPU / VRAM Balken
      ├─► BottomDock.tsx: Status-Badges & Telemetrie
      └─► ApexWorld.tsx:
            │
            ├─► uGlowIntensity & uPulseRate in Fresnel-Shadern anpassen
            ├─► Partikel-Drift-Geschwindigkeit skalieren
            └─► 60-120 FPS Three.js Render-Loop ohne WebGL-Kontextverlust
```

---

## 4. Vollständiger Verzeichnis- & Dateibaum

```text
webjarvis/
├── assets/                               # Visuelle Assets & Branding
│   ├── jarvis-manager.png                # Icon für PyQt6 Manager (PNG)
│   └── jarvis-manager.svg                # Vektor-Icon für Desktop-Launcher
│
├── backend/                              # Python 3.12+ / 3.14 Backend Core
│   ├── actions/                          # Modulare Tool-Implementierungen
│   │   ├── backup_agent.py               # Tool: Brain-Vault Backups erstellen/listen
│   │   ├── calendar_manager.py           # Tool: SQLite-Kalender Termine & Deadlines
│   │   ├── computer_settings.py          # Tool: Lautstärke, Display-Helligkeit, Audio-Sinks
│   │   ├── file_controller.py            # Tool: Dateien lesen/schreiben/löschen mit Undo
│   │   ├── graph_manager.py              # Tool: 3D-Wissensgraph Knoten & Links pflegen
│   │   ├── jarvis_control.py             # Tool: System-Befehle, Mute, Shutdown, Sleep
│   │   ├── manage_mcp.py                 # Tool: MCP-Server Schnittstelle steuern
│   │   ├── open_app.py                   # Tool: Linux-Programme & .desktop Starter öffnen
│   │   ├── recall_memory.py              # Tool: Langzeitgedächtnis & Fakten abrufen
│   │   ├── reminder.py                   # Tool: Erinnerungen & Timer setzen
│   │   ├── sandboxed_shell.py            # Tool: Isolierte Bash-Befehle via bwrap
│   │   ├── screen_processor.py           # Tool: Screenshots & Desktop-Vision (grim/spectacle)
│   │   ├── system_monitor.py             # Tool: CPU, RAM, GPU, Temperaturen abfragen
│   │   ├── undo_action.py                # Tool: Letzte Datei-Aktion rückgängig machen
│   │   └── update_agent.py               # Tool: Git Self-Update & Release-Prüfung
│   │
│   ├── backups/                          # Lokale Brain Vault ZIP-Archive
│   ├── config/                           # Konfigurationsdateien & Secrets
│   │   ├── api_keys.json                 # Gespeicherte API-Keys & Einstellungen
│   │   ├── api_keys.example.json         # Vorlage für Erstinstallation
│   │   ├── contacts.json                 # Kontaktbuch für Benachrichtigungen
│   │   ├── cron_jobs.json                # Persistierte periodische Hintergrundaufgaben
│   │   ├── mcp_servers.json              # Externe MCP-Server Registrierung
│   │   ├── sandbox_config.json           # Whitelist der erlaubten Sandbox-Verzeichnisse
│   │   └── SOUL.md                       # Primäre KI-Identität & Direktiven
│   │
│   ├── core/                             # Low-Level Systemkerne & Controller
│   │   ├── action_loader.py              # Tool-Discovery & OpenAPI Schema-Sanitizer
│   │   ├── audio_streamer.py             # PipeWire/ALSA Audio I/O & RMS-Messung
│   │   ├── backup_manager.py             # Brain Vault Packer (VACUUM INTO SQLite & ZIP)
│   │   ├── config.py                     # Pfad-, Audio-, Modell- & Environment-Verwaltung
│   │   ├── confirm.py                    # Thread-sicheres Hardware-Safety Gate
│   │   ├── cron_engine.py                # Hintergrund-Scheduler & Proaktive Benachrichtigung
│   │   ├── gemini_live.py                # Google GenAI Live Client & Duplex-Session
│   │   ├── json_repair.py                # Robustes Parsing fehlerhafter LLM-Parameter
│   │   ├── mcp_client.py                 # Model Context Protocol JSON-RPC 2.0 Client
│   │   ├── sandbox.py                    # Bubblewrap Prozessisolation & Pfadhärtung
│   │   └── undo.py                       # Dateioperations-Stack für Rollback
│   │
│   ├── knowledge_base/                   # Wissensnetzwerk
│   │   ├── graph_nodes.json              # Knoten & Kanten für das 3D Three.js Hologramm
│   │   └── knowledge_map.json            # Metadaten-Mapping
│   │
│   ├── memory/                           # Persistente Speicher-Engines
│   │   ├── calendar.db                   # SQLite Datenbank für Termine & Ereignisse
│   │   ├── lancedb_data/                 # LanceDB Vektor-Embeddings (Semantische Suche)
│   │   ├── lancedb_manager.py            # Vektordatenbank-Treiber
│   │   ├── long_term.json                # Explizite Fakten, Präferenzen & Notizen
│   │   └── memory_manager.py             # Gedächtnis-Synchronisation für Prompts
│   │
│   ├── sandbox_workspace/                # Primärer Schreibarbeitsbereich der Sandbox
│   ├── server.py                         # Zentraler WebSocket-Server (Port 8765)
│   ├── requirements.txt                  # Python-Paketabhängigkeiten
│   ├── SOUL.md                           # Fallback-Identitätsdatei
│   ├── MEMORY.md                         # Schneller Notizen- & Kontextspeicher
│   └── HEARTBEAT.md                      # Systemzustands-Checkliste für den Agenten
│
├── frontend/                             # Next.js 15 / React 19 Frontend (Port 3000)
│   ├── app/                              # Next.js App-Router
│   │   ├── globals.css                   # Cyberpunk HUD Theme, Scanlines & Glow-Effekte
│   │   ├── layout.tsx                    # Root Layout & Meta-Tags
│   │   └── page.tsx                      # Zentrale Desktop-Oberfläche & Event-Verdrahtung
│   │
│   ├── components/                       # Reaktive HUD-Komponenten & Modals
│   │   ├── AgentCockpit.tsx              # Agenten-Status, Persona & Schnellbefehle
│   │   ├── ApexOverviewPanel.tsx         # Node-Inspector für ausgewählte Wissensknoten
│   │   ├── ApexWorld.tsx                 # 3D Three.js Hologramm (Fresnel Shader & Rings)
│   │   ├── ApiKeyModal.tsx               # Gemini API Key Eingabe & Validierung
│   │   ├── BackupModal.tsx               # Brain Vault Export/Import & ZIP-Download
│   │   ├── BottomDock.tsx                # macOS/Cyberpunk Dock mit App-Icons & Killswitch
│   │   ├── CalendarModal.tsx             # Relationale Kalender-Matrix (Tag/Woche/Monat)
│   │   ├── ConfirmBanner.tsx             # Physisches Bestätigungs-Gate für Hochrisiko-Aktionen
│   │   ├── ContentStudio.tsx             # Editor für Notizen & Dokumente
│   │   ├── DevConsole.tsx                # Verschiebbare Terminal- & Telemetriekonsole
│   │   ├── DeviceControlPanel.tsx        # System-Lautstärke, Sinks, Display & Audio
│   │   ├── JarvisChatWindow.tsx          # Konversations-Chat mit Transkript & Audiobalken
│   │   ├── PersonalityWizardModal.tsx    # SOUL.md Live-Editor & Stimmenauswahl (Puck/Aoede)
│   │   ├── SandboxModal.tsx              # Whitelist-Manager & OS-Vollzugriff Toggle
│   │   └── SkillsModal.tsx               # MCP- und Action-Katalog
│   │
│   ├── lib/                              # Frontend-Bibliotheken & Typen
│   │   ├── graphData.ts                  # Standard-Knotenfarben & Kategorien
│   │   ├── petEngine.ts                  # Sprite-Animationen für das Desktop-Pet
│   │   ├── petTypes.ts                   # Pet-Konfigurationsschnittstellen
│   │   ├── types.ts                      # TypeScript Schnittstellendefinitionen
│   │   └── websocket.ts                  # WebSocket Manager mit Reconnect-Backoff
│   │
│   ├── public/                           # Statische Web-Assets
│   ├── package.json                      # Node.js Abhängigkeiten & Build-Skripte
│   ├── tailwind.config.ts                # Tailwind-CSS Konfiguration
│   └── tsconfig.json                     # TypeScript Compiler-Optionen
│
├── manager.py                            # Native PyQt6 Desktop Maintenance GUI
├── manager.sh                            # Starter für die PyQt6 GUI
├── run.sh                                # Schneller 1-Click Starter
├── start.sh                              # Linux Master-Orchestrator (Prüfung & Parallelstart)
├── stop.sh                               # Sauberer SIGTERM-Shutdown aller Daemons
├── restart.sh                            # Zero-Reboot Dienst-Neustart
├── setup.sh                              # Systemweiter Paket- & Venv-Installer
├── terminate_jarvis.sh                   # Paranoia-Killswitch (SIGKILL auf alle PIDs)
├── posting.md                            # Release- & Community-Postings (Englisch & Deutsch)
├── posting-win.md                        # Kurz-Vorstellung für Foren & Social Media
├── README.md                             # Internationales Projekthandbuch
└── README_DE.md                          # Ausführliches deutsches Handbuch
```

---

## 5. Backend Deep-Dive ("Wie, Was, Wo")

### 5.1 Server & WebSocket Engine (`backend/server.py`)

- **Netzwerk-Schnittstelle:** Lauscht standardmäßig auf `ws://127.0.0.1:8765` (konfigurierbar via `JARVIS_WS_PORT` und `JARVIS_WS_HOST`).
- **TelemetryThrottler:** Begrenzt ausgehende Telemetrie- und Audiopegel-Broadcasts auf exakt **60 Hz (~16.6 ms Intervall)**. Verhindert Garbage-Collection-Ruckler im Three.js Canvas.
- **Connection Lifecycle:** 
  - Sendet bei Verbindungsaufbau ein `init`-Paket mit dem kompletten Systemzustand: Identität, Whitelist-Pfade, Systemtelemetrie, anstehende Bestätigungen, Kalender-Events, API-Key-Status und MCP-Server.
  - Verarbeitet ein- und ausgehende Nachrichten vollkommen asynchron via `asyncio`.
- **Zentrale WebSocket-Befehle (Inbound):**
  - `text_command`: Manuelle Texteingabe an die Gemini Live Session.
  - `interrupt`: Unterbricht die laufende KI-Sprachausgabe sofort.
  - `toggle_mic` / `mute_toggle`: Schaltet das Mikrofon stumm oder aktiv.
  - `confirm_resolve`: Sendet die Benutzerbestätigung (`accepted: true/false`) an das Safety Gate.
  - `undo`: Führt ein Rollback der letzten Datei-Aktion aus.
  - `set_sandbox_access` / `add_sandbox_path` / `remove_sandbox_path`: Aktualisiert die Sandbox-Rechtematrix und stößt `reload_personality()` an.

---

### 5.2 Gemini Live Controller (`backend/core/gemini_live.py`)

- **SDK:** Verwendet das offizielle `google-genai` SDK mit dem Modell `models/gemini-3.1-flash-live-preview`.
- **Echtzeit-Audio:** 
  - `_send_audio_loop()` zieht Roh-PCM (16 kHz Mono) aus der Audio-Queue und sendet es als Realtime-Input an Google.
  - `_receive_loop()` empfängt kontinuierlich Chunks der synthetisierten Sprachausgabe (24 kHz Mono) und leitet sie direkt an das lokale Audiosystem weiter.
- **Session-Resumption & GoAway (Code 1008):**
  - Fängt Server-GoAway-Nachrichten und Timeouts sauber ab.
  - Verwendet den `resumption_handle`, um Verbindungen ohne Gedächtnisverlust oder spürbare Pause nahtlos wiederherzustellen.
- **Dynamic Personality Hot-Reload:**
  - Wird `reload_personality()` aufgerufen (z. B. nach Bearbeitung von `SOUL.md` oder Änderung der Sandbox-Whitelist), wird die WebSocket-Sitzung transparent neu initiiert, sodass die neuen Direktiven sofort aktiv sind.

---

### 5.3 Bubblewrap Sandbox & Prozessisolation (`backend/core/sandbox.py`)

Die Sandbox ist das sicherheitskritische Herzstück von WebJarvis:

```text
[Befehl an execute_sandboxed()]
             │
             ▼
[1. Pfad-Normalisierung]
- Unicode NFC Normalisierung
- os.path.expanduser()
- Absolute Auflösung via Path.resolve() (Verhindert Symlink-Escapes & Traversal)
             │
             ▼
[2. Whitelist-Abgleich: is_path_allowed()]
- Prüft gegen config/sandbox_config.json
- Verhindert Schreibzugriffe auf /etc, /root, ~/.ssh, Systempfade
             │
             ▼
[3. Bubblewrap Aufruf]
bwrap \
  --unshare-all \             # Trennt IPC, PID, UTS, Cgroup
  --share-net \               # Erlaubt Netzwerk (falls allow_network=True)
  --ro-bind / / \             # Gesamtes System-Root ist schreibgeschützt (read-only)
  --dev /dev \                # Isoliertes Device-Filesystem
  --proc /proc \              # Neuer, isolierter Prozessbaum
  --tmpfs /tmp \              # Flüchiges RAM-basiertes /tmp
  --die-with-parent \         # Tötet Subprozesse sofort bei Abbruch des Backends
  --new-session \             # Eigene Session-ID (keine TTY-Kapern)
  --bind <path> <path> \      # Nur freigegebene Pfade werden beschreibbar gemountet
  --chdir <cwd> \             # Sicheres Arbeitsverzeichnis
  bash -c "<cmd>"
```

- **Fail-Safe Verweigerung:** Wenn `bwrap` fehlt oder fehlschlägt, gibt es **keinen ungesicherten Host-Fallback**. Der Befehl wird mit Exit-Code `126` verweigert.
- **AI-Prompt-Injektion:** Die Funktion `format_sandbox_directive_for_prompt()` formatiert die erlaubten Pfade und Restriktionen in klaren Systemdirektiven, damit Gemini von vornherein weiß, welche Pfade tabu sind.

---

### 5.4 Dynamische Tool-Discovery & OpenAPI Sanitizer (`backend/core/action_loader.py`)

- **Automatische Entdeckung:** Scannt `backend/actions/*.py` nach `TOOL` (einzelnes Tool) oder `TOOLS` (Liste von Tools) Deklarationen.
- **OpenAPI Typbereinigung (`sanitize_schema_for_gemini`):**
  - Die Gemini Live API reagiert extrem empfindlich auf inkompatible JSON-Schema-Felder.
  - Entfernt `$schema`, `$id`, `definitions`, `additionalProperties` und `allOf`.
  - Wandelt komplexe `anyOf`/`oneOf` Typen in saubere OpenAPI Typen (`OBJECT`, `STRING`, `INTEGER`, `NUMBER`, `BOOLEAN`, `ARRAY`) mit `nullable: True` um.
  - Repariert fehlerhaft formatierte Tool-Parameter automatisch via `json_repair.py`.

---

### 5.5 Audio Streamer (`backend/core/audio_streamer.py`)

- **Treiber-Architektur:** Nutzt `sounddevice` / PipeWire.
- **Eingang:** 16.000 Hz, 1 Kanal (Mono), 16-Bit signed integer.
- **Ausgang:** 24.000 Hz, 1 Kanal (Mono), 16-Bit signed integer.
- **RMS-Engine:** Berechnet kontinuierlich die Root-Mean-Square Lautstärke der Ein- und Ausgabe für die reaktive Shader-Pulsierung im Frontend.
- **Paranoia-Mute:** Physischer Hardware-Stummschalter im Backend – verwirft Audio-Frames sofort, bevor sie in irgendeine Queue oder ein Netzwerk gelangen.

---

### 5.6 Brain Vault Backup & Restore (`backend/core/backup_manager.py`)

- **Konsistente SQLite-Snapshots:**
  - Verhindert Inkonsistenzen durch ungeschriebene WAL-Dateien (`calendar.db-wal`).
  - Führt `PRAGMA wal_checkpoint(TRUNCATE);` aus und erstellt mit `VACUUM INTO '<snapshot>'` eine saubere, ungesperrte Kopie.
- **Archiv-Inhalt:**
  - `long_term.json`, `calendar.db`, `lancedb_data/`, `knowledge_base/graph_nodes.json`, `mcp_servers.json`, `SOUL.md`, `MEMORY.md`, `HEARTBEAT.md`.
- **Zip-Slip Schutz beim Restore:**
  - Validiert beim Entpacken jeden Dateipfad strikt auf `target.is_relative_to(extract_dir)`, um Verzeichnis-Überschreibungen durch manipulierte Archive abzuwehren.

---

### 5.7 Hardware Safety Confirmation Gate (`backend/core/confirm.py`)

- Schützt vor unbeabsichtigten Zerstörungen:
  - System herunterfahren (`shutdown`, `poweroff`, `systemctl poweroff`)
  - Neustart (`reboot`)
  - Massenlöschung von Verzeichnissen
- **Ablauf:** Registriert ein asynchrones Future mit einem 90-Sekunden Timeout. Der Backend-Befehl wartet blockierend, bis das Frontend `confirm_resolve` sendet. Verstreicht die Zeit, wird die Aktion sicher verworfen.

---

### 5.8 Cron & Reminder Engine (`backend/core/cron_engine.py`)

- Verwaltet periodische Aufgaben und Erinnerungen aus `config/cron_jobs.json`.
- Ermöglicht dem Agenten, zu festgelegten Zeitpunkten aktiv zu werden (z. B. morgendliches System-Briefing, Terminerinnerungen 15 Minuten vor Beginn).

---

### 5.9 Model Context Protocol Bridge (`backend/core/mcp_client.py`)

- Standardisierte JSON-RPC 2.0 Schnittstelle zur Anbindung externer MCP-Toolserver.
- Liest Server-Definitionen aus `config/mcp_servers.json` und registriert externe Tools automatisch in der `ActionRegistry`.

---

### 5.10 Actions & Werkzeug-Katalog (`backend/actions/`)

| Modul | Registrierte Tools | Zweck / Linux-Befehl |
| :--- | :--- | :--- |
| `sandboxed_shell.py` | `execute_sandboxed_shell` | Führt Shell-Befehle isoliert via `bwrap` aus. |
| `file_controller.py` | `file_controller` | Datei-Operationen (`read`, `write`, `delete`, `move`, `list`, `organize_desktop`). |
| `calendar_manager.py` | `calendar_manager`, `create_calendar_entry` | SQLite Kalenderverwaltung, Termine abfragen, anlegen und löschen. |
| `graph_manager.py` | `get_graph_data`, `add_graph_node`, `delete_graph_node` | Live-Manipulation des 3D Three.js Wissensgraphen. |
| `system_monitor.py` | `get_system_status` | Telemetrie (CPU, RAM, GPU, Temperaturen, Lüfter). |
| `screen_processor.py` | `capture_screen` | Wayland-Screenshots via `grim` / `spectacle` für Desktop-Vision. |
| `computer_settings.py`| `adjust_computer_settings` | Lautstärke (`wpctl`, `amixer`), Helligkeit (`brightnessctl`). |
| `open_app.py` | `open_application` | Startet Programme unprivilegiert (`gtk-launch`, `xdg-open`). |
| `recall_memory.py` | `recall_memory`, `store_memory` | Fakten aus `long_term.json` & LanceDB abrufen/speichern. |
| `reminder.py` | `set_reminder` | Timers und Einmal-Erinnerungen setzen. |
| `backup_agent.py` | `manage_backups` | Brain Vault Exporte auslösen und Backups auflisten. |
| `undo_action.py` | `undo_last_action` | Macht die letzte Dateioperation rückgängig. |
| `update_agent.py` | `check_for_updates`, `perform_self_update` | Git-Synchronisation & Release-Prüfung. |
| `manage_mcp.py` | `manage_mcp_servers` | MCP Server aktivieren, deaktivieren oder abfragen. |

---

### 5.11 Multi-Tier Gedächtnissystem (`backend/memory/`)

1. **Episodisch / Konversation:** Live-Session Kontext im Gemini Live WebSocket Stream.
2. **Deklarativ / Langzeit (`long_term.json`):** Wichtige Fakten über den Nutzer, Hardware-Setup, Vorlieben und Projektzustände.
3. **Relational (`calendar.db`):** SQLite Datenbank mit strukturierter Tabelle für Events, Start-/Endzeit, Priorität und Tags.
4. **Semantisch / Vektor (`lancedb_data/`):** Vektordatenbank für kontextuelle Ähnlichkeitssuche in großen Textmengen und Dokumentationen.
5. **Konzeptionell (`knowledge_base/graph_nodes.json`):** Verknüpfte Wissensknoten für die holografische 3D-Visualisierung.

---

## 6. Frontend Deep-Dive ("Wie, Was, Wo")

### 6.1 Next.js 15 App-Router (`frontend/app/`)

- **Tech-Stack:** Next.js 15, React 19, Tailwind CSS, Lucide Icons.
- **Hydration & SSR:** Das Three.js Canvas wird via `next/dynamic` mit `{ ssr: false }` geladen, um WebGL-Konflikte beim Server-Side Rendering zu verhindern.
- **Theme:** Tiefschwarzer Cyberpunk-Look (`#030712`), Neon-Cyan (`#00f3ff`), Amber-Orange (`#f59e0b`), subtile Scanlines und CRT-Grid Shader.

---

### 6.2 Three.js Holographischer Szenengraph (`frontend/components/ApexWorld.tsx`)

- **Volumetrische Fresnel-Shader:**
  - Knoten leuchten nicht als flache Sprites, sondern als dreidimensionale holografische Sphären mit Glanzkante (`fresnelVertexShader` & `fresnelFragmentShader`).
- **Gyroskop-Ringe:**
  - Jeder Hub-Knoten besitzt zwei rotierende Orbit-Ringe, die sich dynamisch entlang der X- und Y-Achse drehen.
- **Zero-Allocation Raycasting:**
  - Maus-Hover und Selektion nutzen vorinitialisierte Vektoren (`THREE.Raycaster`), um Memory-Leaks und Garbage-Collection Spikes zu eliminieren.
- **Audio-Reaktivität:**
  - Das empfangene `audio_level` pulsiert die Knotengröße und Shader-Frequenz im Takt der Stimme.

---

### 6.3 HUD Komponenten & Fenster-Matrix (`frontend/components/`)

```text
+----------------------------------------------------------------------------------------------------+
| TOP BAR: Systemstatus | Voice-Stimme | CPU: 12% | RAM: 34% | GPU: 42°C | Safety Gate Badge          |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|    +-----------------------------+                               +----------------------------+    |
|    |      DevConsole.tsx         |                               |     JarvisChatWindow.tsx   |    |
|    |  - Live Python Logs         |                               |  - Volle Transkription     |    |
|    |  - Tool Call Ausgaben       |      APEX WORLD (Three.js)    |  - Benutzer- & KI-Turns    |    |
|    |  - Draggable & Resizable    |    Holographischer 3D Graph   |  - Audio Level Meter       |    |
|    |  - Filter: SYS, YOU, ERR    |                               |  - Draggable & Resizable   |    |
|    +-----------------------------+                               +----------------------------+    |
|                                                                                                    |
|    +------------------------------------------------------------------------------------------+    |
|    | ConfirmBanner.tsx: [WARNUNG: Herunterfahren angefordert! BESTÄTIGEN | ABBRECHEN (89s)]   |    |
|    +------------------------------------------------------------------------------------------+    |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
| BOTTOM DOCK: [Mic Toggle] [Chat] [Dev] [Kalender] [Vault] [Sandbox] [Skills] [Settings] [KILLSWITCH] |
+----------------------------------------------------------------------------------------------------+
```

---

### 6.4 WebSocket Client State Machine (`frontend/lib/websocket.ts`)

- **Zustandsautomat (`AssistantState`):**
  - `OFFLINE` ➔ `CONNECTING` ➔ `ONLINE` ➔ `LISTENING` ➔ `THINKING` ➔ `SPEAKING` ➔ `CONFIRM` ➔ `ERROR`.
- **Resilienter Reconnect:**
  - Exponentieller Backoff mit Jitter (Basis 1000 ms bis max. 15.000 ms).
  - Bei Netzwerkabriss versucht der Client automatisch im Hintergrund die Wiederverbindung.

---

## 7. Desktop Orchestration & Manager

### 7.1 PyQt6 Cyberpunk HUD Manager (`manager.py`)

- **Natives Desktop-Kontrollzentrum:**
  - Überwacht Port 8765 (Backend) und Port 3000 (Frontend) in Echtzeit.
  - Ermöglicht 1-Klick Start, Stopp und Neustart des gesamten Stacks.
  - Integriert den Non-Destruktiven GitHub-Update-Checker (prüft Remote-Commits via `git ls-remote`).
  - Schaltet den Linux-Autostart (`~/.config/autostart/webjarvis.desktop`) an oder aus.

---

### 7.2 Shell-Orchestrierungs-Skripte (`*.sh`)

| Skript | Funktion & Verhalten |
| :--- | :--- |
| `run.sh` | Ergonomischer Starter; leitet Argumente an `start.sh` weiter. |
| `start.sh` | Master-Orchestrator: Prüft Venv, Node-Pakete, PipeWire & Ports; startet Backend & Frontend parallel; fängt SIGINT/SIGTERM sauber ab. |
| `stop.sh` | Sendet sauberes `SIGTERM` an Backend- und Frontend-PIDs und räumt temporäre Sockets auf. |
| `restart.sh` | Führt `stop.sh` und anschließend `start.sh` ohne Betriebssystem-Neustart aus. |
| `setup.sh` | Vollständige Erstinstallation: Erstellt Python Venv, installiert Pakete, baut Next.js Abhängigkeiten. |
| `terminate_jarvis.sh` | Not-Aus / Killswitch: Tötet alle WebJarvis-Prozesse augenblicklich via `SIGKILL`. |

---

## 8. Sicherheits- & Sandbox-Matrix

```text
+----------------------+--------------------+--------------------+----------------------------------+
| Ressource / Bereich  | Standard-Modus     | Vollzugriff aktiv  | Schutzmechanismus                |
+----------------------+--------------------+--------------------+----------------------------------+
| Dateisystem (Host)   | READ-ONLY          | READ / WRITE       | bwrap --ro-bind / /              |
| Whitelist-Pfade      | READ / WRITE       | READ / WRITE       | bwrap --bind <allowed> <allowed> |
| Systemverzeichnisse  | GESPERRT (/etc,..) | GESPERRT (/etc,..) | is_path_allowed() & bwrap ro     |
| Subprozesse          | ISOLIERT           | ISOLIERT           | --unshare-all, --die-with-parent |
| Netzwerk             | ERLAUBT            | ERLAUBT            | --share-net                      |
| Destruktive Aktionen | SAFETY-GATE        | SAFETY-GATE        | confirm.py (90s Timeout)         |
| Privilegieneskalation| VERHINDERT         | VERHINDERT         | Unprivileged User Namespace      |
+----------------------+--------------------+--------------------+----------------------------------+
```

---

## 9. Entwickler-Leitfaden (Developer How-To)

### 9.1 Neues Tool / Action hinzufügen

1. Neue Datei `backend/actions/mein_tool.py` erstellen:
```python
"""backend/actions/mein_tool.py"""
from typing import Dict, Any

TOOL = {
    "name": "mein_neues_tool",
    "description": "Erkläre präzise, was das Tool macht.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "parameter_eins": {
                "type": "STRING",
                "description": "Beschreibung des Parameters"
            }
        },
        "required": ["parameter_eins"]
    }
}

def mein_neues_tool(parameters: Dict[str, Any], **kwargs) -> str:
    wert = parameters.get("parameter_eins", "")
    # Logik hier implementieren...
    return f"Erfolg: {wert}"
```
2. Das Tool wird beim nächsten Start durch `action_loader.py` vollautomatisch entdeckt und bei Gemini Live registriert.

### 9.2 Sandbox-Testsuite ausführen

```bash
cd /home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis
PYTHONPATH=backend backend/.venv/bin/python3 -c "
from core.sandbox import is_path_allowed, execute_sandboxed, DEFAULT_SANDBOX_DIR
assert is_path_allowed(DEFAULT_SANDBOX_DIR)
assert not is_path_allowed('/etc/passwd')
code, out, err, is_sb = execute_sandboxed('echo OK')
assert code == 0 and 'OK' in out
print('SANDBOX INTENSIVE CHECK: 100% CLEAN!')
"
```

### 9.3 Manuelle Syntax- und Import-Prüfung

```bash
PYTHONPATH=backend backend/.venv/bin/python3 -m py_compile backend/server.py backend/core/*.py backend/actions/*.py
```

---
*Ende der Dokumentation — Erstellt für das Entwickler- und SysOps-Portfolio von @Graba92.*
