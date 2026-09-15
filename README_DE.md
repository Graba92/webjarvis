[🇩🇪 Zur deutschen Dokumentation wechseln](README_DE.md) | [🇬🇧 Switch to English Documentation](README.md)

# J.A.R.V.I.S. AI OS — Desktop WebGL Edition (Cypher)

<p align="center">
  <img src="preview_hud.png" alt="J.A.R.V.I.S. WebGL HUD Preview" width="900">
</p>

[![GitHub](https://img.shields.io/badge/GitHub-Graba92%2Fwebjarvis-blue?logo=github)](https://github.com/Graba92/webjarvis)
[![OS](https://img.shields.io/badge/OS-CachyOS%20%7C%20Arch%20Linux%20%7C%20Generic-blue?logo=archlinux)](https://cachyos.org)
[![Python](https://img.shields.io/badge/Python-3.11%2B-yellow?logo=python)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-15%20(App%20Router)-black?logo=next.js)](https://nextjs.org)
[![Three.js](https://img.shields.io/badge/3D%20WebGL-Three.js-cyan?logo=threedotjs)](https://threejs.org)
[![Gemini Live](https://img.shields.io/badge/Gemini-Live%20API-brightgreen?logo=google)](https://aistudio.google.com)
[![PipeWire](https://img.shields.io/badge/Audio-PipeWire%20Virtueller%20Sink-blue)](https://pipewire.org)
[![MCP](https://img.shields.io/badge/Protokoll-MCP%20JSON--RPC%202.0-purple)](#-mcp-ökosystem-model-context-protocol)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **J.A.R.V.I.S. (Codename: Cypher)** ist ein autonomes, schlankes und multimodales Desktop-KI-Betriebssystem, optimiert für CachyOS und Arch Linux. Es vereint bidirektionales Audio-Streaming über Gemini Live (WebSockets), dediziertes PipeWire-Audio-Routing, ein physisches Hardware-Sicherheits-Gate, eine hermetische Bubblewrap-Sandbox, proaktive Heartbeat-Briefings, integrierte SQLite-Terminverwaltung, CachyOS-Paketaktualisierung und ein interaktives 3D-WebGL-Hologramm-HUD (Three.js & Next.js 15).

---

## 📑 Inhaltsverzeichnis
1. [Systemarchitektur & Datenfluss](#-systemarchitektur--datenfluss)
2. [Identitäts- & Konfigurations-Dreiklang (`SOUL.md`, `MEMORY.md`, `HEARTBEAT.md`)](#-identitäts--konfigurations-dreiklang)
3. [Native CachyOS Skills & Scheduler](#-native-cachyos-skills--scheduler)
4. [Performance, Audio-Routing & Privatsphäre](#-performance-audio-routing--privatsphäre)
5. [Entwickler-Tools, Backup & Personality Wizard](#-entwickler-tools-backup--personality-wizard)
6. [3D-WebGL-HUD & Theme-Engine](#-3d-webgl-hud--theme-engine)
7. [MCP-Ökosystem (Model Context Protocol)](#-mcp-ökosystem-model-context-protocol)
8. [Schnellstart in unter 2 Minuten](#-schnellstart-in-unter-2-minuten)
9. [Master-Orchestrator (`start.sh`)](#-master-orchestrator-startsh)
10. [Lizenz & Autor](#-lizenz--autor)

---

## 🏛️ Systemarchitektur & Datenfluss

```
                                  ┌────────────────────────┐
                                  │   Google Gemini Live   │
                                  │  Bidirektionaler Stream│
                                  └───────────▲────────────┘
                                              │ (Audio in/out & Function Calls)
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
               │ CachyOS Skills    ││  Hybrid Memory    ││  MCP Gateway      │
               │ - update_agent.py ││ - calendar.db     ││ (Brave Search,    │
               │ - calendar_mgr.py ││ - LanceDB Vector  ││  Fetch, Custom    │
               │ - confirm.py Gate ││ - long_term.json  ││  JSON-RPC 2.0)    │
               └───────────────────┘└───────────────────┘└───────────────────┘
                         │                    │                    │
                         ▼                    ▼                    ▼
               ┌───────────────────┐┌───────────────────┐┌───────────────────┐
               │ PipeWire Audio    ││ Proaktiver Cron   ││ 1-Click Backup    │
               │ Dedizierter Sink  ││ Morning Briefing  ││ ZIP Exporter /    │
               │ Paranoia Kill     ││ Focus Mode Pause  ││ Restore Manager   │
               └───────────────────┘└───────────────────┘└───────────────────┘
                                              │
                                              │ Echtzeit-Telemetrie, Live-Audio-RMS,
                                              │ Ungefilterte dev_log & Graph Events
                                              ▼
                                  ┌────────────────────────┐
                                  │   Next.js 15 App HUD   │
                                  │  Three.js WebGL Engine │
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

## 🐧 Native CachyOS Skills & Scheduler

- **CachyOS Update Agent (`backend/actions/update_agent.py`):**
  Prüft Paketupdates via `checkupdates` und `yay -Qu`. Identifiziert kritische Systemkomponenten (`linux`, `linux-cachyos`, `systemd`, `glibc`, `nvidia`, `mesa`, `openssl`). Führt Systemaktualisierungen niemals unbestätigt aus, sondern leitet sie ausnahmslos über das physische Bestätigungs-Gate (`confirm.py`).
- **Kalender- & Terminverwaltung (`backend/actions/calendar_manager.py`):**
  Lokale SQLite-Datenbank (`backend/memory/calendar.db`) mit vollen CRUD-Möglichkeiten und Parser für natürliche Sprache ("Erinnere mich zwei Tage vorher an das Meeting").
- **Proaktives Morning Briefing (`backend/core/cron_engine.py`):**
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

## 🛠️ Entwickler-Tools, Backup & Personality Wizard

- **Live Dev-Console (`DevConsole.tsx`):**
  Einklappbares HUD-Terminal, das ungefilterte System-Logs, Fehler, Werkzeugaufrufe und Tracebacks live über WebSockets (`dev_log`) streamt.
- **1-Click Brain Backup (`backup_manager.py` & `BottomDock.tsx`):**
  Packt Gedächtnis (`long_term.json`, `calendar.db`, LanceDB-Vektoren, `SOUL.md` und `mcp_servers.json`) in ein komprimiertes `.zip`-Archiv.
- **Personality Wizard (`PersonalityWizardModal.tsx`):**
  Interaktiver Assistent im Frontend zur Konfiguration von Rolle, Tonfall, Humor und ethischen Grenzen mit Direktspeicherung in `SOUL.md`.

---

## 🌐 3D-WebGL-HUD & Theme-Engine

- **Three.js Wissensgraph (`ApexWorld.tsx`):**
  Interaktiver 3D-Graph mit mehrfarbigen Datenfluss-Partikeln (`0x00d4ff`, `0x00ff88`, `0xa855f7`), reaktivem Puls und geschwungenen Bézier-Kanten.
- **Zentrale Farbpalette (`frontend/theme.json`):**
  Einheitliche Design-Tokens für Arch- und CachyOS-Ricing.

---

## 🔌 MCP-Ökosystem (Model Context Protocol)

Unterstützt standardisierte MCP JSON-RPC 2.0 Server (`backend/config/mcp_servers.json`):
- **`brave_search`:** Datenschutzfreundliche Websuche als Ersatz für Legacy-Scraper.
- **`fetch`:** Schneller Webseitenabruf und automatische Markdown-Konvertierung.
- **MCP GUI:** Ein- und Ausschalten von MCP-Werkzeugen direkt im HUD über die Skills-Matrix.

---

## ⚡ Schnellstart in unter 2 Minuten

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
# Trage deinen GEMINI_API_KEY in backend/.env ein
```

### 3. Starten
```bash
./start.sh
# Wähle Option 1 (Nativ Fullstack) oder Option 4 (Docker Compose)
```

---

## 📜 Lizenz & Autor

- **Autor:** Graba92
- **Lizenz:** MIT License (Open Source)
