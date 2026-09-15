[🇩🇪 Zur deutschen Dokumentation wechseln](README_DE.md) | [🇬🇧 Switch to English Documentation](README.md)

# J.A.R.V.I.S. AI OS — Desktop WebGL Edition (Cypher)

<p align="center">
  <img src="preview_hud.png" alt="J.A.R.V.I.S. WebGL HUD Vorschau" width="900">
</p>

[![GitHub](https://img.shields.io/badge/GitHub-Graba92%2Fwebjarvis-blue?logo=github)](https://github.com/Graba92/webjarvis)
[![OS](https://img.shields.io/badge/OS-Linux%20(CachyOS%20%7C%20Arch%20%7C%20Generic)-blue?logo=linux)](https://cachyos.org)
[![Python](https://img.shields.io/badge/Python-3.11%2B-yellow?logo=python)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-15%20(App%20Router)-black?logo=next.js)](https://nextjs.org)
[![Three.js](https://img.shields.io/badge/3D%20WebGL-Three.js-cyan?logo=threedotjs)](https://threejs.org)
[![Gemini Live](https://img.shields.io/badge/Gemini-3.1%20Flash%20Live-brightgreen?logo=google)](https://aistudio.google.com)
[![MCP](https://img.shields.io/badge/Protocol-MCP%20JSON--RPC%202.0-purple)](#-das-mcp-ökosystem-model-context-protocol)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **J.A.R.V.I.S. (Codename: Cypher)** ist ein autonomes, multimodales Desktop-KI-Betriebssystem für Linux. Es kombiniert bidirektionales Vollduplex-Sprach-Streaming über Googles `gemini-3.1-flash-live-preview` (WebSockets), eine hermetische Bubblewrap-Sandbox, proaktive Cron-Heartbeats, Hardware-Safety-Gates, eine erweiterbare MCP-Plugin-Architektur und ein hochreaktives 3D-WebGL-Hologramm-HUD (Three.js & Next.js 15).

---

## 📑 Inhaltsverzeichnis
1. [Systemarchitektur & Datenfluss](#-systemarchitektur--datenfluss)
2. [Schnellstart (1-Klick Setup & Start)](#-schnellstart-in-unter-2-minuten)
3. [Master Orchestrator (`start.sh`)](#-master-orchestrator-startsh)
4. [Backend-Architektur & Funktionen im Detail](#-backend-architektur--funktionen-im-detail)
   - [Gemini Live Controller & Audio-Engine](#gemini-live-controller--audio-engine)
   - [Sicherheits-Architektur (Bubblewrap Sandbox & Safety Gate)](#sicherheits-architektur)
   - [Undo-Stack & Rollback-System](#undo-stack--rollback-system)
   - [Gedächtnis- & Vektorsystem (LanceDB + Hybrid Memory)](#gedächtnis---vektorsystem)
   - [Proaktive Cron-Engine & Heartbeat-Scheduler](#proaktive-cron-engine)
   - [Werkzeug-Registry (Action Registry)](#werkzeug-registry-action-registry)
   - [Multi-Plattform-Bridges (Discord & WhatsApp)](#multi-plattform-bridges)
5. [Frontend-Architektur & Visualisierung (HUD)](#-frontend-architektur--visualisierung-hud)
   - [3D WebGL Constellation Knowledge Graph (`ApexWorld`)](#3d-webgl-constellation-knowledge-graph-apexworld)
   - [Apex Reactor & Holographic Cockpit (`AgentCockpit`)](#apex-reactor--holographic-cockpit-agentcockpit)
   - [System-Telemetrie & Filter-Panel (`ApexOverviewPanel`)](#system-telemetrie--filter-panel)
   - [Interaktives Dock & Dynamic Terminal (`BottomDock`)](#interaktives-dock--dynamic-terminal)
   - [Hardware-Bestätigungsdialog (`ConfirmBanner`)](#hardware-bestätigungsdialog-confirmbanner)
6. [Frontend Button-Audit: Echte Funktionen vs. Platzhalter](#-frontend-button-audit-echte-funktionen-vs-platzhalter)
7. [Das MCP-Ökosystem (Model Context Protocol)](#-das-mcp-ökosystem-model-context-protocol)
8. [Top 3 Empfohlene Backend- & Frontend-Erweiterungen](#-top-3-backend---frontend-erweiterungen)
9. [Lizenz & Autor](#-lizenz--autor)

---

## 🏛️ Systemarchitektur & Datenfluss

```
                                  ┌────────────────────────┐
                                  │   Google Gemini Live   │
                                  │ (3.1-flash-live-preview│
                                  └───────────▲────────────┘
                                              │ (Bi-directional Audio /
                                              │  v1alpha WebSocket)
                                              ▼
┌────────────────────────┐        ┌────────────────────────┐        ┌────────────────────────┐
│  WhatsApp Multi-Device │        │   Python Core Server   │        │     Discord Bridge     │
│   Bridge (Baileys)     ├───────►│      (server.py)       │◄───────┤    (discord_bot.py)    │
│    Port 3001 (Node)    │ HTTP   │   Port 8765 (WebSocket)│ WS     │   Commands & Webhooks  │
└────────────────────────┘        └───────────▲────────────┘        └────────────────────────┘
                                              │
                         ┌────────────────────┼────────────────────┐
                         │                    │                    │
                         ▼                    ▼                    ▼
               ┌───────────────────┐┌───────────────────┐┌───────────────────┐
               │  Action Registry  ││  LanceDB Memory   ││  MCP Gateway      │
               │ (Shell, pactl,    ││ (128d Vector DB + ││ (JSON-RPC 2.0     │
               │  mss, bwrap, etc.)││  long_term.json)  ││  Dynamic Plugins) │
               └───────────────────┘└───────────────────┘└───────────────────┘
                                              │
                                              │ WebSocket Telemetry (1 Hz)
                                              │ Audio RMS (60 FPS) & Events
                                              ▼
                                  ┌────────────────────────┐
                                  │   Next.js 15 App HUD   │
                                  │  Three.js WebGL Engine │
                                  │  Port 3000 (React 19)  │
                                  └────────────────────────┘
```

---

## ⚡ Schnellstart in unter 2 Minuten

### 1. Repository klonen
```bash
git clone https://github.com/Graba92/webjarvis.git
cd webjarvis
```

### 2. Automatische Installation ausführen
Der zerstörungssichere Installer richtet Virtual Environments, Systemtools, Node-Abhängigkeiten und Templates automatisch ein:
```bash
chmod +x setup.sh start.sh terminate_jarvis.sh
./setup.sh
```

### 3. Gesamtsystem starten (Nativ)
```bash
./start.sh
```
*Beim ersten Start fordert das Skript zur Eingabe des kostenfreien [Google Gemini API Keys](https://aistudio.google.com/app/apikey) auf.*

---

### 🐳 Alternative: Starten mit Docker (Isoliert & sofort startklar)

Falls du keine lokalen Python- oder Node-Pakete auf deinem Host installieren möchtest, kannst du WebJarvis mit einem einzigen Befehl im Docker-Verbund starten:

```bash
# 1-Klick Start via Hilfsskript
./docker-start.sh

# Oder direkt via Docker Compose:
docker compose up -d
```

* **HUD-Cockpit:** [http://localhost:3005](http://localhost:3005) *(oder Port 3000)*
* **Backend-WebSocket:** `ws://127.0.0.1:8765`
* **Grafische Verwaltung (Portainer):** [https://localhost:9443](https://localhost:9443)
* **Logs ansehen:** `./docker-logs.sh`
* **Stoppen:** `./docker-stop.sh`

## 🚀 Master Orchestrator (`start.sh`)

| Option / Flag | Beschreibung |
|---|---|
| `-a`, `--all` | Startet Gesamtsystem (Python Backend, WhatsApp Gateway, Discord Bot & Next.js Frontend). |
| `-b`, `--backend` | Startet isoliert das Python Gemini Live WebSocket Backend (`ws://127.0.0.1:8765`). |
| `-f`, `--frontend` | Startet das Three.js WebGL HUD Frontend (`http://localhost:3000`). |
| `-w`, `--whatsapp` | Startet die Baileys WhatsApp Gateway Bridge (`http://127.0.0.1:3001`). |
| `-d`, `--discord` | Startet die Discord Gateway Bridge. |
| `-c`, `--check` | Führt Hardwarediagnosen & Dependency-Checks durch. |
| `./terminate_jarvis.sh` | Beendet alle laufenden Subsysteme und gibt Ports frei. |

---

## ⚙️ Backend-Architektur & Funktionen im Detail

### Gemini Live Controller & Audio-Engine
* **Module**: `backend/core/gemini_live.py` & `backend/core/audio_streamer.py`.
* **Audio-Streaming**: 16 kHz Mono Input (Mikrofon via `sounddevice`), 24 kHz Mono Output via PipeWire.
* **Audio-Reaktivität**: Berechnet 60-FPS-RMS-Lautstärkepegel und broadcastet diese an das Frontend zur Animation des Reaktorkerns.
* **Session Resumption**: Erkennt Verbindungsabbrüche und nimmt Sitzungen transparent über Sliding-Window-Kompression wieder auf.

### Sicherheits-Architektur
* **Bubblewrap Sandbox (`backend/core/sandbox.py`)**:
  * Shell-Befehle werden in isolierten Linux-Namespaces ausgeführt (`--unshare-pid`, `--unshare-ipc`).
  * Systemverzeichnisse (`/usr`, `/lib`, `/bin`) sind strikt **Read-Only** gemountet; das Benutzer-Homeverzeichnis bleibt unsichtbar.
  * Beschreibbar ist ausschließlich der isolierte Workspace `backend/sandbox_workspace/`.
* **Hardware Confirmation Gate (`backend/core/confirm.py`)**:
  * Fängt potenziell destruktive Aktionen (Shutdown, Reboot, WiFi-Deaktivierung) ab.
  * Erfordert eine physische Bestätigung über das bernsteinfarbene HUD-Banner (90s Timeout).

### Undo-Stack & Rollback-System (`backend/core/undo.py`)
* Verwaltet die letzten 10 mutierenden Datei- und Systemeinstellungen.
* Ermöglicht das sofortige Rückgängigmachen von Fehlern per Sprachbefehl oder HUD-Klick.

### Gedächtnis- & Vektorsystem (`backend/memory/`)
* **LanceDB Vektor-Speicher (`lancedb_manager.py`)**: 128-Dimensionale Vektoren für semantische Ähnlichkeitssuche.
* **JSON-Langzeitgedächtnis (`long_term.json`)**: Strukturierte Persistenz von Systemfakten und Präferenzen.
* **Core-Trio**: Markdown-Richtlinien über `SOUL.md`, `MEMORY.md` und `HEARTBEAT.md`.

### Werkzeug-Registry (`backend/actions/`)
* `computer_settings.py`: Steuert Lautstärke (`pactl`), Helligkeit (`brightnessctl`) und WiFi (`nmcli`).
* `file_controller.py`: Sichere Dateimanipulation mit Papierkorb-Fallback (`send2trash`).
* `screen_processor.py`: Screenshot-Erstellung via `mss` und Multimodal-Vision mit Gemini.
* `system_monitor.py`: Hardware-Telemetrie via `psutil` (CPU, RAM, GPU, Temperaturen).
* `web_search.py`: Live-Websuche via DuckDuckGo & BeautifulSoup-Extraktion.

---

## 🖥️ Frontend-Architektur & Visualisierung (HUD)

### 3D WebGL Constellation Knowledge Graph (`ApexWorld.tsx`)
* Nativer Three.js-Canvas mit optimierter Force-Directed-Simulation.
* Quadratische Bézier-Kurven mit animierten „Datenperlen“, die Informationsflüsse visualisieren.
* Knoten pulsieren organisch im Rhythmus der KI-Stimme (Echtzeit-Audio-RMS).
* Interaktives Kontextmenü an jedem Knoten: Öffnen im Terminal, Dateimanager, Editor oder Browser sowie KI-Zusammenfassungen.

### Apex Reactor Cockpit (`AgentCockpit.tsx`)
* Holographisches HUD mit animierten SVG-Ringen und Statusanzeige (`ONLINE`, `THINKING`, `SPEAKING`, `RECONNECTING`, `OFFLINE`).
* Sofortiger `INTERRUPT`-Button zum Unterbrechen der Sprachausgabe.
* Mute-Toggle und Modal zur Live-Aktualisierung des Gemini API Keys.

### System-Telemetrie & Filter (`ApexOverviewPanel.tsx`)
* Live-Messanzeigen für Hardware-Metriken (1 Hz Update-Rate).
* Regler für Graphphysik (Abstoßungskraft und Kantenlängen).
* 9-Kategorien-Filter zur Fokussierung spezifischer Wissensgebiete.

---

## 🎛️ Frontend Button-Audit: Echte Funktionen vs. Platzhalter

| Komponente | Button / Element | Status | Tatsächliche Funktion im System |
|---|---|---|---|
| **AgentCockpit** | **Kategorie-Filter** (9 Pills) | ✅ **Echt** | Filtert Knoten im 3D-Canvas in Echtzeit (`activeFilter`). |
| **AgentCockpit** | **INTERRUPT** (Rot, pulsiert) | ✅ **Echt** | Stoppt sofort die Audioausgabe von Gemini Live via WebSocket. |
| **AgentCockpit** | **GEMINI 3.1 LIVE** (Schlüssel) | ✅ **Echt** | Öffnet API-Key-Modal zur Live-Aktualisierung im laufenden Betrieb. |
| **AgentCockpit** | **Mikrofon-Eingabe** (Mute) | ✅ **Echt** | Schaltet das physische Systemmikrofon im Backend stumm/aktiv. |
| **AgentCockpit** | **View Switcher** (`RING`/`CUBE`/`FACE`) | 🟡 **Optisch** | Schaltet zwischen SVG-Reaktor, CSS-Würfel und Auge-Grafik um. |
| **AgentCockpit** | **Sensor EYES** | ✅ **Echt** | Triggert Screenshot- und Screen-Vision-Analyse via WebSocket. |
| **AgentCockpit** | **Sensor WATCH** | ✅ **Echt** | Schaltet proaktiven Überwachungsmodus ein und informiert die KI. |
| **AgentCockpit** | **Sensor HOLO** | ✅ **Echt** | Schaltet visuellen Holo-Modus um. |
| **AgentCockpit** | **Sensor FOCUS** | ✅ **Echt** | Aktiviert Deep-Reasoning-Priorität für die KI. |
| **BottomDock** | **Handsfree (Ohr-Symbol)** | ✅ **Echt** | Steuert das Backend-Mikrofon per Tastendruck. |
| **BottomDock** | **Content Studio (Feder)** | ✅ **Echt** | Öffnet den 3D-Knoten-Editor zum Erstellen neuen Wissens. |
| **BottomDock** | **Device Bridge (Ordner)** | ✅ **Echt** | Öffnet Hardware-Steuerung (Audio, Helligkeit, WiFi, Telemetrie). |
| **BottomDock** | **Prompt Input & Send** | ✅ **Echt** | Sendet Textkommandos direkt in die Live-Sitzung. |
| **BottomDock** | **Quick Reminder (Glocke)** | ✅ **Echt** | Erstellt automatischen 10-Minuten-Timer. |
| **BottomDock** | **Deep Reasoning (Birne)** | ✅ **Echt** | Weist die KI an, Wissensgraph-Cluster autonom zu analysieren. |
| **BottomDock** | **Sync / Refresh (Kreispfeil)**| ✅ **Echt** | Triggert `system_status` im Backend via WebSocket. |
| **BottomDock** | **MCP Skill Matrix (Puzzle)** | ✅ **Echt** | Öffnet das interaktive Skill-Modal: MCP-Server per 1-Klick an-/ausschalten, konfigurieren oder neue Stdio-Server registrieren. |
| **ApexOverview** | **Fit / Target Reset** | ✅ **Echt** | Steuert Three.js-Kamera (Gesamtansicht oder Zentrum). |
| **ApexOverview** | **2D / 3D Mode Toggle** | ✅ **Echt** | Projiziert Knoten auf flache Ebene (`z=0`) oder 3D-Kugelraum. |
| **ApexWorld** | **Node Kontextmenü** | ✅ **Echt** | Startet Terminal, Dolphin, Kate, Browser oder löscht Knoten. |
| **ConfirmBanner** | **Freigeben / Abbrechen** | ✅ **Echt** | Löst das Hardware Safety Gate im Python-Backend auf. |
| **DeviceControl** | **Slider & Toggles** | ✅ **Echt** | Regelt Hardware via `pactl`, `brightnessctl` und `nmcli`. |

---

## 🔌 Das MCP-Ökosystem (Model Context Protocol)

Im Backend existiert mit `backend/core/mcp_client.py` und `backend/config/mcp_servers.json` ein vollwertiger **JSON-RPC 2.0 Stdio-Client nach der offiziellen Spezifikation**, der nahtlos über das Frontend-Cockpit per **Skills-Modal (Puzzle-Icon)** gesteuert werden kann.

### Vorkonfigurierte MCP-Skills (Standardmäßig deaktiviert – im HUD aktivierbar):
1. **`filesystem`**: Sicherer Dateisystem-Zugriff im Workspace (`@modelcontextprotocol/server-filesystem`).
2. **`sqlite`**: Lokale relationale Datenbankabfragen und Tabellenverwaltung (`mcp-server-sqlite`).
3. **`fetch`**: Webseiten, Online-Artikel und Dokumentationen direkt per URL einlesen (`@modelcontextprotocol/server-fetch`).
4. **`github`**: Repositories, Pull Requests, Commits und Issues verwalten (`@modelcontextprotocol/server-github`).
5. **`brave_search`**: Datenschutzfreundliche, werbefreie Websuche (`@modelcontextprotocol/server-brave-search`).
6. **`memory`**: Strukturierter Wissensgraph für persistente Langzeitfakten (`@modelcontextprotocol/server-memory`).
7. **`time`**: Exakte Zeitzonen-, Datums- und Weltzeitberechnungen (`@modelcontextprotocol/server-time`).
8. **`puppeteer`**: Headless-Browser-Automatisierung für dynamisches Web-Rendering und Screenshots (`@modelcontextprotocol/server-puppeteer`).

### Warum MCP J.A.R.V.I.S. abrundet:
1. **Dynamische Skills (Installieren & Entfernen ohne Neustart)**:
   * Neue Fähigkeiten werden einfach im HUD oder in `mcp_servers.json` registriert.
   * Das Tool steht Gemini Live sofort typisiert zur Verfügung.
   * Zum Entfernen genügt der Schiebeschalter im HUD (`"enabled": false`).
2. **Fehlerfreie Tool-Calls ohne Halluzinationen**:
   * Strikte JSON-Schemas zwingen die KI zu exakt typisierten Parameteraufrufen.
3. **Sicherheit durch Prozess-Isolation**:
   * MCP-Server laufen in separaten Subprozessen und können in die Bubblewrap-Sandbox eingebunden werden.

---

## 💡 Top 3 Backend- & Frontend-Erweiterungen

### Backend
1. **Gemini `text-embedding-004` Integration**: Nativer Ersatz für Hashing-Embeddings in LanceDB für tiefe semantische Synonym-Suche.
2. **DesktopAdapter Abstraktion**: Dynamische Erkennung von GNOME, Wayland (`wpctl`) oder Sway für universelle Linux-Kompatibilität.
3. **Priorisierter Worker-Pool**: Entkopplung schwerer Vision-Tasks in dedizierte Threads zur Vermeidung von Audio-Jitter.

### Frontend
1. **Three.js `InstancedMesh`**: Reduzierung von Hunderten Draw-Calls auf einen einzigen für Tausende Knoten bei 120 FPS.
2. **Web Audio API Client-Streaming**: Optionale Mikrofon-/Lautsprecher-Nutzung direkt im Browser für mobile Tablets.
3. **3D Drag-and-Drop Editor**: Manuelles Verschieben und Neuzuordnen von Knoten im Raum via Three.js `DragControls`.

---

## 📄 Lizenz & Autor

Entwickelt von **Matthias Haase ([@Graba92](https://github.com/Graba92))**.

Veröffentlicht unter der [MIT-Lizenz](LICENSE).
