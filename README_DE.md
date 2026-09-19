[🇩🇪 Zur deutschen Dokumentation wechseln](README_DE.md) | [🇬🇧 Switch to English Documentation](README.md)

# J.A.R.V.I.S. AI OS — Desktop WebGL Edition (Cypher)

<p align="center">
  <img src="preview_hud.png" alt="J.A.R.V.I.S. WebGL HUD Vorschau" width="900">
  <br><br>
  <img src="preview_devconsole.png" alt="J.A.R.V.I.S. Live Dev-Konsole & Stream Engine Vorschau" width="900">
</p>

[![GitHub](https://img.shields.io/badge/GitHub-Graba92%2Fwebjarvis-blue?logo=github)](https://github.com/Graba92/webjarvis)
[![OS](https://img.shields.io/badge/OS-CachyOS%20%7C%20Arch%20Linux%20%7C%20Generic-blue?logo=archlinux)](https://cachyos.org)
[![Python](https://img.shields.io/badge/Python-3.11%2B-yellow?logo=python)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-15%20(App%20Router)-black?logo=next.js)](https://nextjs.org)
[![Three.js](https://img.shields.io/badge/3D%20WebGL-Three.js-cyan?logo=threedotjs)](https://threejs.org)
[![Gemini Live](https://img.shields.io/badge/Gemini-Live%20API-brightgreen?logo=google)](https://aistudio.google.com)
[![PipeWire](https://img.shields.io/badge/Audio-PipeWire%20Dedicated%20Sink-blue)](https://pipewire.org)
[![MCP](https://img.shields.io/badge/Protocol-MCP%20JSON--RPC%202.0-purple)](#-mcp-ökosystem-model-context-protocol)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **J.A.R.V.I.S. (Codename: Cypher)** ist ein autonomes, modulares und multimodales Desktop-KI-Betriebssystem für CachyOS und Arch Linux. Es kombiniert bidirektionales Audio-Streaming mit extrem niedriger Latenz via Gemini Live (WebSockets), dediziertes PipeWire-Audio-Routing, dynamische KI-Identitätsverwaltung, eine relationale Kalender-Engine mit Konversations-Slot-Filling, deterministisches Action-Auditing mit Backend-Empfangsbestätigungen, resilienten WebSocket-Reconnection-Backoff, ein physisches Hardware-Bestätigungs-Gate, konsistente `VACUUM INTO` Live-SQLite-Backups, eine hermetische Bubblewrap-Sandbox und ein futuristisches 3D-WebGL-Hologramm-HUD (Three.js & Next.js 15).

---

## 📑 Inhaltsverzeichnis
1. [Systemarchitektur & Datenfluss](#-systemarchitektur--datenfluss)
2. [Identitäts- & Konfigurations-Dreiklang (`SOUL.md`, `MEMORY.md`, `HEARTBEAT.md`)](#-identitäts--konfigurations-dreiklang)
3. [Dynamische KI-Identität & Live-HUD-Parität](#-dynamische-ki-identität--live-hud-parität)
4. [Bidirektionale Kalender-Engine & Dialog-Slot-Filling](#-bidirektionale-kalender-engine--dialog-slot-filling)
5. [Action-Auditing, Backend Receipts & Telemetrie-Drosselung](#-action-auditing-backend-receipts--telemetrie-drosselung)
6. [Native CachyOS Skills & Tool-Matrix](#-native-cachyos-skills--tool-matrix)
7. [Performance, Audio-Routing & Privatsphäre](#-performance-audio-routing--privatsphäre)
8. [Datenintegrität, atomare Schreibvorgänge & VACUUM INTO Backups](#-datenintegrität-atomare-schreibvorgänge--vacuum-into-backups)
9. [Entwickler-Tools, Live Dev-Konsole & Personality Wizard](#-entwickler-tools-live-dev-konsole--personality-wizard)
10. [3D-WebGL-HUD & Theme-Engine](#-3d-webgl-hud--theme-engine)
11. [MCP-Ökosystem (Model Context Protocol)](#-mcp-ökosystem-model-context-protocol)
12. [Schnellstart & Master Orchestrator (`start.sh`)](#-schnellstart--master-orchestrator-startsh)
13. [Lizenz & Autor](#-lizenz--autor)

---

## 🏛️ Systemarchitektur & Datenfluss

```
                                  ┌────────────────────────┐
                                  │   Google Gemini Live   │
                                  │  Bidirektionaler Stream│
                                  └───────────▲────────────┘
                                              │ (Audio in/out & Tool Calls)
                                              ▼
                                  ┌────────────────────────┐
                                  │   Python Core Server   │
                                  │      (server.py)       │
                                  │   Port 8765 (WebSocket)│
                                  └───────────▲────────────┘
                                              │
                         ┌────────────────────┼────────────────────┐
                         │                    │                    │
                         ▼                    ▼                    ▼
               ┌───────────────────┐┌───────────────────┐┌───────────────────┐
               │ CachyOS Skills    ││  Hybrides Memory  ││  MCP Gateway      │
               │ - update_agent.py ││ - calendar.db     ││ (Brave Search,    │
               │ - calendar_mgr.py ││   (WAL + Relational││  Fetch, Custom    │
               │ - confirm.py Gate ││ - LanceDB Vector  ││  JSON-RPC 2.0)    │
               │ - ActionDispatch  ││ - long_term.json  ││                   │
               └───────────────────┘└───────────────────┘└───────────────────┘
                         │                    │                    │
                         ▼                    ▼                    ▼
               ┌───────────────────┐┌───────────────────┐┌───────────────────┐
               │ PipeWire Audio    ││ Proaktiver Cron   ││ VACUUM INTO Backup│
               │ Dedizierter Sink  ││ Morning Briefing  ││ Online Snapshot / │
               │ Paranoia Kill     ││ Focus Mode Pause  ││ Restore Manager   │
               └───────────────────┘└───────────────────┘└───────────────────┘
                                              │
                                              │ 60Hz Telemetrie-Drosselung, RMS,
                                              │ CALENDAR_SYNC, ACTION_RECEIPT,
                                              │ SYSTEM_INIT & dev_log Events
                                              ▼
                                  ┌────────────────────────┐
                                  │   Next.js 15 App HUD   │
                                  │  Three.js WebGL Engine │
                                  │  ActionAuditor Tracker │
                                  │  Port 3000 (React 19)  │
                                  └────────────────────────┘
```

---

## 🧬 Identitäts- & Konfigurations-Dreiklang

J.A.R.V.I.S. wird transparent über drei zentrale Markdown-Dokumente in `backend/` gesteuert:

1. **`SOUL.md` (Persona, Tonfall & Verhaltensrichtlinien):**
   Definiert Identität, trockenen Humor, technische Präzision und Verhaltensgrenzen. Kann manuell oder im laufenden Betrieb über den **Personality Wizard** im HUD modifiziert werden.
2. **`MEMORY.md` (Langzeitgedächtnis & Fakten):**
   Speichert Nutzerpräferenzen, Workflows, Hardware-Spezifikationen und Gelerntes ohne statisch festverdrahtete Annahmen.
3. **`HEARTBEAT.md` (Autonome periodische Routinen):**
   Regelt autonome Hintergrundprüfungen (z.B. Systemprüfungen, Kalender-Scans, Paketprüfungen und das morgendliche Briefing).

---

## 🎭 Dynamische KI-Identität & Live-HUD-Parität

- **Single Source of Truth (`SOUL.md` / `config.py`):**
  Der Name der KI (`ai_name`) wird zentral aus `SOUL.md` oder der Umgebungsvariable `JARVIS_AI_NAME` geladen.
- **Echtzeit-Synchronisation via WebSocket:**
  Beim Verbindungsaufbau (`init` / `SYSTEM_INIT`) sowie bei jeder Modifikation im Personality Wizard (`save_personality`) wird der aktuelle Name sofort an alle Frontends übertragen.
- **Reaktives Arc-Reactor-Badge & Dev-Konsole:**
  Der kreisrunde Arc-Reactor im HUD (`AgentCockpit.tsx`) und der Header der Entwicklerkonsole (`DevConsole.tsx`) aktualisieren ihren Text und die Schriftlaufweite im laufenden Betrieb ohne Reload.

---

## 📅 Bidirektionale Kalender-Engine & Dialog-Slot-Filling

- **Relationales SQLite-Schema (`calendar_events`):**
  Verwaltet Termine mit eindeutigen UUIDs, ISO-Zeitstempeln, Wiederholungsregeln (`DAILY`, `WEEKLY`, `MONTHLY`) und strukturierten Mehrfach-Erinnerungsstrategien im JSON-Format (`reminder_strategy`).
- **Deterministisches Dialog-Slot-Filling:**
  Wenn Jarvis per Sprache nach einem Termin gefragt wird, prüft er fehlende Angaben (Datum, Uhrzeit, Wiederholung, Erinnerungsvorlauf), fragt gezielt nach und fasst alle Daten zur Bestätigung zusammen, bevor das Tool `create_calendar_entry` ausgelöst wird.
- **Event-Driven Live-Sync (`CALENDAR_SYNC`):**
  Jede Datenbankänderung (Hinzufügen, Löschen) erzeugt einen sofortigen WebSocket-Broadcast, wodurch die Kalenderliste im HUD ohne Polling in Millisekunden aktualisiert wird.
- **HUD-Kalender-Modal & Tastenkürzel (`Alt+C`):**
  Ein elegantes Cyber-Glass-Dashboard ermöglicht manuelle Termineingaben mit Schnellauswahl ("In 1h", "Morgen 09:00"), Filtern und Ein-Klick-Löschung.

---

## ⚡ Action-Auditing, Backend Receipts & Telemetrie-Drosselung

- **ActionAuditor Engine (`frontend/utils/auditLogger.ts`):**
  Jede Benutzerinteraktion im HUD (Paranoia-Mute, manuelle Termine, Update-Prüfung, Backup) wird mit einer eindeutigen Korrelations-ID versehen und muss vom Python-Backend mit einem `ACTION_RECEIPT` quittiert werden. Verhindert unregistrierte Klicks und Geisterzustände.
- **60 Hz Telemetrie- & RMS-Drosselung:**
  Audiopegel und Telemetrieströme werden auf der WebSocket-Bridge auf ein festes 60-Hz-Budget (~16,6 ms) gedrosselt. Dies schützt den JavaScript-Event-Loop und Three.js vor Render-Rucklern und Garbage-Collection-Spikes.
- **Resilienter WebSocket-Reconnect mit exponentiellem Backoff & Jitter:**
  Verbindungsabbrüche fangen sich sanft ab (`1s * 1.8^n` bis max. 15s) mit zufälligem Jitter (0–500 ms), um Reconnection-Stürme beim Server-Neustart auszuschließen.

---

## 🐧 Native CachyOS Skills & Tool-Matrix

Alle autonomen Werkzeuge liegen unter `backend/actions/` und sind in der Gemini Live Action Registry verankert:

- **CachyOS Update Agent (`update_agent.py`):**
  Prüft Paketupdates via `checkupdates` und `yay -Qu`. Identifiziert kritische Systemkomponenten (`linux`, `linux-cachyos`, `systemd`, `glibc`, `nvidia`, `mesa`, `openssl`). Führt Systemaktualisierungen niemals unbestätigt aus, sondern leitet sie ausnahmslos über das physische Bestätigungs-Gate (`confirm.py`).
- **Hardware Confirmation Gate (`computer_settings.py` & `core/confirm.py`):**
  Destruktive Systembefehle (Herunterfahren, Reboot, Ruhezustand) triggern ein bernsteinfarbenes Bestätigungs-Banner im HUD mit einem 90-Sekunden-Countdown, das eine physische Freigabe erzwingt.
- **Hermetische Bubblewrap Sandbox (`sandboxed_shell.py` & `file_controller.py`):**
  Führt Shell- und Dateibefehle in einem isolierten Namespace (`bwrap`) aus, bindet das Dateisystem read-only ein und beschränkt Schreibzugriffe strikt auf `backend/sandbox_workspace/`.
- **Optimistische Undo-Stack Engine (`undo_action.py` & `core/undo.py`):**
  Ein 10-Ebenen-Transaktionsspeicher mit differentiellen Snapshots ermöglicht das sofortige Rückgängigmachen (`undo_last_action`) versehentlicher Dateiänderungen.
- **Zweistufige Gedächtnissuche (`recall_memory.py` & `memory/memory_manager.py`):**
  Erlaubt On-Demand Keyword-Recherchen im Langzeitgedächtnis, ohne das Kontextfenster des aktiven Sprachdialogs zu überlasten.
- **Desktop Application Launcher (`open_app.py`):**
  Startet native Desktop-Anwendungen unter Wayland und KDE Plasma (z. B. Konsole, Dolphin, Kate, Browser) in losgelösten Sessions.
- **Proaktives Morning Briefing (`core/cron_engine.py`):**
  Triggert autonom um 08:00 Uhr oder beim Systemstart, fasst Termine des Tages, anstehende CachyOS-Paketupdates und Systemmetriken zusammen und liest sie via PipeWire vor.

---

## 🔊 Performance, Audio-Routing & Privatsphäre

- **Dedizierter PipeWire-Audio-Sink (`cypher_ai_sink`):**
  Jarvis registriert sich als eigenständiger Audioknoten (`Cypher AI Audio`). Dadurch erscheint Jarvis als separater Lautstärkeregler im KDE Plasma Lautstärkemixer und kann unabhängig von anderen Desktop-Sounds gepegelt werden.
- **Paranoia Killswitch (Mikrofon-Cut auf Hardware-/Treiberebene):**
  Schalter im HUD, der den Mikrofon-Stream auf Treiberebene augenblicklich beendet und freigibt. Bei Deaktivierung leuchtet ein unübersehbarer roter Statusindikator: `PARANOIA MUTED (HARDWARE-OFF)`.
- **Focus Mode (Zero-Interference Gaming & Kompilierung):**
  Pausiert mit einem Klick alle periodischen Hintergrund-Cronjobs und Heartbeats, um maximale Systemressourcen für Gaming, Kernel-Kompilierung oder Benchmarks bereitzustellen.

---

## 🛡️ Datenintegrität, atomare Schreibvorgänge & VACUUM INTO Backups

- **Konsistente Live-Backups via `VACUUM INTO`:**
  Vor dem Packen von `calendar.db` wird das Write-Ahead-Log geflusht (`PRAGMA wal_checkpoint(TRUNCATE);`) und ein sperrfreier Snapshot via `VACUUM INTO` in ein temporäres Verzeichnis exportiert. Verhindert korrupte Archive durch laufende Transaktionen.
- **SQLite Concurrency Hardening:**
  Verbindungen nutzen `PRAGMA journal_mode=WAL;`, `PRAGMA synchronous=NORMAL;`, `busy_timeout=10000;` und einen sauberen Kontextmanager (`get_db()`), wodurch parallele Lese- und Schreibzugriffe kollisionsfrei bleiben.
- **Atomare Gedächtnis-Persistenz:**
  Änderungen an `long_term.json` werden über temporäre Pufferdateien (`NamedTemporaryFile`), explizites `os.fsync` und `os.replace` atomar geschrieben, um Datenverlust bei abruptem Stromausfall oder SIGKILL abzuwenden.

---

## 🛠️ Entwickler-Tools, Live Dev-Konsole & Personality Wizard

- **Live Dev-Console (`DevConsole.tsx`):**
  Einklappbares HUD-Terminal, das ungefilterte System-Logs, Fehler, Werkzeugaufrufe und Tracebacks live über WebSockets (`dev_log`) streamt.
- **1-Click Brain Backup (`backup_manager.py` & `BottomDock.tsx`):**
  Packt Gedächtnis (`long_term.json`, `calendar.db`, LanceDB-Vektoren, `SOUL.md` und `mcp_servers.json`) in ein verschlüsseltes oder unverschlüsseltes `.zip`-Archiv.
- **Personality Wizard (`PersonalityWizardModal.tsx`):**
  Interaktiver Assistent im Frontend zur Konfiguration von Rolle, Tonfall, Humor und ethischen Grenzen mit Direktspeicherung in `SOUL.md`.

---

## 🌐 3D-WebGL-HUD & Theme-Engine

- **Three.js Wissensgraph (`ApexWorld.tsx`):**
  Interaktiver 3D-Graph mit mehrfarbigen Datenfluss-Partikeln (`0x00d4ff`, `0x00ff88`, `0xa855f7`), reaktivem Puls und geschwungenen Bézier-Kanten inklusive sauberem `.dispose()`-Speicher-Cleanup beim Unmount.
- **Zentrale Farbpalette (`frontend/theme.json`):**
  Einheitliche Design-Tokens für Arch- und CachyOS-Ricing.

---

## 🔌 MCP-Ökosystem (Model Context Protocol)

Unterstützt standardisierte MCP JSON-RPC 2.0 Server (`backend/config/mcp_servers.json`):
- **`brave_search`:** Datenschutzfreundliche Websuche als Ersatz für Legacy-Scraper.
- **`fetch`:** Schneller Webseitenabruf und automatische Markdown-Konvertierung.
- **MCP GUI:** Ein- und Ausschalten von MCP-Werkzeugen direkt im HUD über die Skills-Matrix.

---

## ⚡ Schnellstart & Master Orchestrator (`start.sh`)

### 1. Klonen & Setup
```bash
git clone https://github.com/Graba92/webjarvis.git
cd webjarvis
chmod +x setup.sh start.sh terminate_jarvis.sh
./setup.sh
```

### 2. API-Key eintragen
```bash
cp backend/.env.example backend/.env
# Trage deinen GEMINI_API_KEY in backend/.env ein (oder interaktiv via ./start.sh)
```

### 3. Start-Optionen

#### Option A: Interaktiver Master Orchestrator
```bash
./start.sh
```
Menü-Auswahl:
* `1)` **Gesamtsystem starten**: Startet Backend (Python Gemini Live WebSocket) und Frontend (Next.js 15 HUD) parallel.
* `2)` **Nur Python Backend starten**: Startet den WebSocket-Server auf `ws://127.0.0.1:8765`.
* `3)` **Nur Next.js Frontend starten**: Startet das Three.js WebGL HUD auf `http://localhost:3000`.
* `4)` **Hardware- & Systemprüfung ausführen**: Prüft PipeWire, ALSA, Bubblewrap Sandbox und Node/Python-Abhängigkeiten.
* `5)` **Gemini API Key konfigurieren**: Interaktive, persistente Eingabe- und Speicherhilfe.
* `6)` **Beenden**: Beendet alle Subsysteme geordnet.

#### Option B: Direkte Befehlszeilen-Steuerung (Headless & Automatisierung)
```bash
./start.sh --all        # Startet Gesamtsystem direkt
./start.sh --backend    # Startet nur das WebSocket Backend
./start.sh --frontend   # Startet nur das Next.js Frontend
./start.sh --check      # Führt alle Validierungs-Gates aus
./terminate_jarvis.sh   # Stoppt alle Hintergrundprozesse sauber und gibt die Ports 8765 / 3000 frei
```

#### Option C: Docker Compose (Isolierte Container)
```bash
./docker-start.sh       # Baut und startet Backend & Frontend in Docker-Containern
./docker-logs.sh        # Zeigt Live-Container-Logs an
./docker-stop.sh        # Fährt Docker-Container herunter
```

---

## 📜 Lizenz & Autor

- **Autor:** Graba92
- **Lizenz:** MIT License (Open Source)
