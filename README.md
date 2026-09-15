[🇩🇪 Zur deutschen Dokumentation wechseln](README_DE.md) | [🇬🇧 Switch to English Documentation](README.md)

# J.A.R.V.I.S. AI OS — Desktop WebGL Edition (Cypher)

<p align="center">
  <img src="preview_hud.png" alt="J.A.R.V.I.S. WebGL HUD Preview" width="900">
</p>

[![GitHub](https://img.shields.io/badge/GitHub-Graba92%2Fwebjarvis-blue?logo=github)](https://github.com/Graba92/webjarvis)
[![OS](https://img.shields.io/badge/OS-Linux%20(CachyOS%20%7C%20Arch%20%7C%20Generic)-blue?logo=linux)](https://cachyos.org)
[![Python](https://img.shields.io/badge/Python-3.11%2B-yellow?logo=python)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-15%20(App%20Router)-black?logo=next.js)](https://nextjs.org)
[![Three.js](https://img.shields.io/badge/3D%20WebGL-Three.js-cyan?logo=threedotjs)](https://threejs.org)
[![Gemini Live](https://img.shields.io/badge/Gemini-3.1%20Flash%20Live-brightgreen?logo=google)](https://aistudio.google.com)
[![MCP](https://img.shields.io/badge/Protocol-MCP%20JSON--RPC%202.0-purple)](#-mcp-ecosystem-model-context-protocol)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **J.A.R.V.I.S. (Codename: Cypher)** is an autonomous, multimodal desktop AI Operating System for Linux. It combines bi-directional full-duplex voice streaming via Google's `gemini-3.1-flash-live-preview` (WebSockets), a hermetic Bubblewrap sandbox, proactive cron heartbeats, hardware safety gates, an extensible MCP plugin architecture, and a reactive 3D WebGL holographic HUD (Three.js & Next.js 15).

---

## 📑 Table of Contents
1. [System Architecture & Data Flow](#-system-architecture--data-flow)
2. [Quickstart in under 2 minutes](#-quickstart-in-under-2-minutes)
3. [Master Orchestrator (`start.sh`)](#-master-orchestrator-startsh)
4. [Backend Architecture & Core Subsystems](#-backend-architecture--core-subsystems)
   - [Gemini Live Controller & Audio Engine](#gemini-live-controller--audio-engine)
   - [Security Architecture (Bubblewrap & Safety Gate)](#security-architecture)
   - [Undo Stack & Rollback System](#undo-stack--rollback-system)
   - [Memory & Vector Engine (LanceDB + Hybrid Store)](#memory--vector-engine)
   - [Proactive Cron Engine & Heartbeat Scheduler](#proactive-cron-engine)
   - [Action Registry](#action-registry)
   - [Multi-Platform Bridges (Discord & WhatsApp)](#multi-platform-bridges)
5. [Frontend Architecture & Holographic HUD](#-frontend-architecture--holographic-hud)
   - [3D WebGL Constellation Knowledge Graph (`ApexWorld`)](#3d-webgl-constellation-knowledge-graph-apexworld)
   - [Apex Reactor Cockpit (`AgentCockpit`)](#apex-reactor-cockpit-agentcockpit)
   - [Telemetry & Category Filter (`ApexOverviewPanel`)](#telemetry--category-filter)
   - [Interactive Dock & Terminal (`BottomDock`)](#interactive-dock--terminal)
   - [Hardware Confirmation Banner (`ConfirmBanner`)](#hardware-confirmation-banner)
6. [Frontend Button Audit: Real Functions vs. Visual Controls](#-frontend-button-audit-real-functions-vs-visual-controls)
7. [MCP Ecosystem (Model Context Protocol)](#-mcp-ecosystem-model-context-protocol)
8. [Top 3 Recommended Backend & Frontend Optimizations](#-top-3-recommended-backend--frontend-optimizations)
9. [License & Author](#-license--author)

---

## 🏛️ System Architecture & Data Flow

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

## ⚡ Quickstart in under 2 minutes

### 1. Clone the repository
```bash
git clone https://github.com/Graba92/webjarvis.git
cd webjarvis
```

### 2. Run automated setup
The failsafe installer automatically sets up system tools, Python virtual environment, dependencies, and template configurations:
```bash
chmod +x setup.sh start.sh terminate_jarvis.sh
./setup.sh
```

### 3. Launch the AI OS
```bash
./start.sh
```
*On first startup, the orchestrator will prompt for your free [Google Gemini API Key](https://aistudio.google.com/app/apikey).*

---

## 🚀 Master Orchestrator (`start.sh`)

| Option / Flag | Description |
|---|---|
| `-a`, `--all` | Starts the complete system (Python Backend, WhatsApp Gateway, Discord Bot & Next.js Frontend). |
| `-b`, `--backend` | Starts only the Python Gemini Live WebSocket Backend (`ws://127.0.0.1:8765`). |
| `-f`, `--frontend` | Starts only the Three.js WebGL HUD Frontend (`http://localhost:3000`). |
| `-w`, `--whatsapp` | Starts the Baileys WhatsApp Gateway Bridge (`http://127.0.0.1:3001`). |
| `-d`, `--discord` | Starts the Discord Gateway Bridge. |
| `-c`, `--check` | Runs hardware diagnostics & dependency verification. |
| `./terminate_jarvis.sh` | Safely terminates all running subsystems and releases occupied ports. |

---

## ⚙️ Backend Architecture & Core Subsystems

### Gemini Live Controller & Audio Engine
* **Core Modules**: `backend/core/gemini_live.py` & `backend/core/audio_streamer.py`.
* **Full-Duplex Audio**: 16 kHz Mono Input (Microphone via `sounddevice`), 24 kHz Mono Output via PipeWire.
* **Audio-Reactive Visualization**: Computes live RMS volume at 60 FPS and broadcasts it via WebSockets to synchronize the 3D Arc Reactor pulse.
* **Seamless Session Resumption**: Transparently handles WebSocket reconnects (Code 1008 / GoAway) via sliding window context compression.

### Security Architecture
* **Bubblewrap Sandbox (`backend/core/sandbox.py`)**:
  * Generated shell commands execute inside hardened Linux namespaces (`--unshare-pid`, `--unshare-ipc`).
  * System directories (`/usr`, `/lib`, `/bin`) are strictly mounted **Read-Only**; the host home directory remains completely invisible.
  * Only the dedicated `backend/sandbox_workspace/` directory is writable.
* **Hardware Confirmation Gate (`backend/core/confirm.py`)**:
  * Intercepts dangerous or irreversible operations (shutdown, reboot, network disconnects).
  * Requires physical human confirmation via an amber HUD banner with a 90-second timeout.

### Undo Stack & Rollback System (`backend/core/undo.py`)
* Maintains an in-memory stack of the last 10 mutating operations (file changes, volume/brightness adjustments).
* Reverses mistakes instantly via voice command ("undo") or HUD click.

### Memory & Vector Engine (`backend/memory/`)
* **LanceDB Vector Store (`lancedb_manager.py`)**: 128-dimensional dense vectors for semantic similarity retrieval.
* **Structured Long-Term JSON (`long_term.json`)**: Persistent storage of system facts, user preferences, and configuration.
* **Core Trio Markdown Directives**: `SOUL.md` (Persona), `MEMORY.md` (Long-term facts), and `HEARTBEAT.md` (Cron checklist).

### Action Registry (`backend/actions/`)
* `computer_settings.py`: Controls volume (`pactl`), brightness (`brightnessctl`), and WiFi (`nmcli`).
* `file_controller.py`: File operations with safe trash recovery (`send2trash`).
* `screen_processor.py`: Desktop screen capture (`mss`) with multimodal Gemini vision analysis.
* `system_monitor.py`: Real-time hardware telemetry (`psutil` CPU, RAM, GPU, temperatures).
* `web_search.py`: Live DuckDuckGo web search & BeautifulSoup scraping.

---

## 🖥️ Frontend Architecture & Holographic HUD

### 3D WebGL Constellation Knowledge Graph (`ApexWorld.tsx`)
* Native Three.js canvas featuring force-directed physics.
* Quadratic Bézier curves with animated "data pearls" visualizing continuous information flow.
* Spheres pulse organically in sync with the assistant's voice (WebSocket RMS feed).
* Contextual node actions: Open in Terminal (*Konsole*/*Alacritty*), File Manager (*Dolphin*), Editor (*Kate*), Browser, or AI summarization.

### Apex Reactor Cockpit (`AgentCockpit.tsx`)
* Holographic central core with animated SVG rings and live state badges (`ONLINE`, `THINKING`, `SPEAKING`, `RECONNECTING`, `OFFLINE`).
* Quick `INTERRUPT` button to instantly mute the AI speech output.
* Microphone toggle and modal for on-the-fly Gemini API key updates.

### Telemetry & Category Filter (`ApexOverviewPanel.tsx`)
* Live gauges for system hardware metrics (1 Hz refresh rate).
* Sliders for simulation physics (repel force and link length).
* 9-category filter matrix to isolate specific domains in the 3D graph.

---

## 🎛️ Frontend Button Audit: Real Functions vs. Visual Controls

| Component | Button / Control | Status | Actual System Behavior |
|---|---|---|---|
| **AgentCockpit** | **Category Filters** (9 Pills) | ✅ **Real** | Filters nodes in the 3D canvas in real time (`activeFilter`). |
| **AgentCockpit** | **INTERRUPT** (Red Pulse) | ✅ **Real** | Sends `interrupt` via WebSocket to immediately silence Gemini Live. |
| **AgentCockpit** | **GEMINI 3.1 LIVE** (Key Icon) | ✅ **Real** | Opens API Key modal to update credentials without server restart. |
| **AgentCockpit** | **Microphone Toggle** (Mute) | ✅ **Real** | Physically mutes/unmutes the host microphone stream in Python. |
| **AgentCockpit** | **View Switcher** (`RING`/`CUBE`/`FACE`)| 🟡 **Visual** | Toggles HUD reactor visualization between SVG ring, 3D cube, and eye. |
| **AgentCockpit** | **Sensor EYES** | ✅ **Real** | Triggers desktop screen capture and vision analysis via WebSocket. |
| **AgentCockpit** | **Sensor WATCH** | ✅ **Real** | Enables proactive system monitoring mode. |
| **AgentCockpit** | **Sensor HOLO** | ✅ **Real** | Toggles visual holographic display mode. |
| **AgentCockpit** | **Sensor FOCUS** | ✅ **Real** | Directs AI attention to prioritize deep reasoning and code accuracy. |
| **BottomDock** | **Handsfree (Ear Icon)** | ✅ **Real** | Toggles backend microphone mode via WebSocket. |
| **BottomDock** | **Content Studio (Feather)** | ✅ **Real** | Opens node composer modal to add knowledge to `graph_nodes.json`. |
| **BottomDock** | **Device Bridge (Folder)** | ✅ **Real** | Opens hardware control panel (audio, brightness, WiFi, telemetry). |
| **BottomDock** | **Prompt Input & Send** | ✅ **Real** | Dispatches text commands directly to Gemini Live. |
| **BottomDock** | **Quick Reminder (Bell)** | ✅ **Real** | Creates an automated 10-minute reminder. |
| **BottomDock** | **Deep Reasoning (Bulb)** | ✅ **Real** | Commands the AI to perform autonomous graph cluster reasoning. |
| **BottomDock** | **Sync / Refresh (Arrows)** | ✅ **Real** | Triggers the `system_status` backend action. |
| **ApexOverview** | **Fit / Target Reset** | ✅ **Real** | Re-centers camera or fits entire constellation into view. |
| **ApexOverview** | **2D / 3D Mode Toggle** | ✅ **Real** | Projects graph onto a 2D plane (`z=0`) or unfolds 3D space. |
| **ApexWorld** | **Node Context Menu** | ✅ **Real** | Launches Terminal, Dolphin, Kate, Browser, or deletes node. |
| **ConfirmBanner** | **Confirm / Cancel** | ✅ **Real** | Resolves pending action in the Hardware Safety Gate. |
| **DeviceControl** | **Sliders & Toggles** | ✅ **Real** | Controls system hardware via `pactl`, `brightnessctl`, and `nmcli`. |

---

## 🔌 MCP Ecosystem (Model Context Protocol)

The backend includes a production-ready **JSON-RPC 2.0 Stdio Client (`backend/core/mcp_client.py`) adhering to the official 2024-11-05 specification**.

### Why MCP Completes J.A.R.V.I.S.:
1. **Dynamic Skills (Install & Remove without Code Changes)**:
   * Add any community MCP server (GitHub, SQLite, Docker, Home Assistant, Brave Search) by adding an entry in `backend/config/mcp_servers.json`.
   * Gemini Live gains immediate typed access to new tools.
   * To deactivate, simply set `"enabled": false`.
2. **Deterministic Tool Execution**:
   * Strict JSON schemas prevent parameter hallucination.
3. **Sandboxed Subprocess Isolation**:
   * MCP servers run as independent processes that can be confined inside Bubblewrap namespaces.

---

## 💡 Top 3 Recommended Backend & Frontend Optimizations

### Backend
1. **Gemini `text-embedding-004` Integration**: Native semantic embeddings in LanceDB to replace trigram hashing for conceptual synonym search.
2. **DesktopAdapter Abstraction**: Dynamic detection of GNOME, Sway, and Wayland (`wpctl`) for universal Linux portability.
3. **Dedicated Worker Pool**: Offload heavy vision/file tasks to dedicated worker threads to guarantee jitter-free 24 kHz audio streaming.

### Frontend
1. **Three.js `InstancedMesh`**: Collapse hundreds of individual draw calls into a single call for 120 FPS performance with 1,000+ nodes.
2. **Web Audio API Browser Streaming**: Optional browser-level microphone/speaker handling for remote tablet/mobile HUD access.
3. **3D Drag-and-Drop Editor**: Interactive node positioning and relation linking via Three.js `DragControls`.

---

## 📄 License & Author

Developed by **Matthias Haase ([@Graba92](https://github.com/Graba92))**.

Released under the [MIT License](LICENSE).
