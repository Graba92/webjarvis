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
[![PipeWire](https://img.shields.io/badge/Audio-PipeWire%20Dedicated%20Sink-blue)](https://pipewire.org)
[![MCP](https://img.shields.io/badge/Protocol-MCP%20JSON--RPC%202.0-purple)](#-mcp-ecosystem-model-context-protocol)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **J.A.R.V.I.S. (Codename: Cypher)** is an autonomous, lean, multimodal desktop AI Operating System specifically tailored for CachyOS and Arch Linux. It features bi-directional low-latency voice streaming via Gemini Live (WebSockets), dedicated PipeWire virtual audio sink routing, a hardware safety confirmation gate, a hermetic Bubblewrap sandbox, proactive heartbeat briefings, SQLite calendar management, native CachyOS kernel/package updates, and a 3D WebGL holographic HUD (Three.js & Next.js 15).

---

## 📑 Table of Contents
1. [System Architecture & Data Flow](#-system-architecture--data-flow)
2. [Identity & Configuration Triad (`SOUL.md`, `MEMORY.md`, `HEARTBEAT.md`)](#-identity--configuration-triad)
3. [Native CachyOS Skills & Scheduler](#-native-cachyos-skills--scheduler)
4. [Performance, Audio Routing & Privacy](#-performance-audio-routing--privacy)
5. [Developer Tools, Backup & Personality Wizard](#-developer-tools-backup--personality-wizard)
6. [3D WebGL Holographic HUD & Theme Engine](#-3d-webgl-holographic-hud--theme-engine)
7. [MCP Ecosystem (Model Context Protocol)](#-mcp-ecosystem-model-context-protocol)
8. [Quickstart in under 2 minutes](#-quickstart-in-under-2-minutes)
9. [Master Orchestrator (`start.sh`)](#-master-orchestrator-startsh)
10. [License & Author](#-license--author)

---

## 🏛️ System Architecture & Data Flow

```
                                  ┌────────────────────────┐
                                  │   Google Gemini Live   │
                                  │  Bi-directional Stream │
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
               │ PipeWire Audio    ││ Proactive Cron    ││ 1-Click Backup    │
               │ Dedicated Sink    ││ Morning Briefing  ││ ZIP Exporter /    │
               │ Paranoia Kill     ││ Focus Mode Pause  ││ Restore Manager   │
               └───────────────────┘└───────────────────┘└───────────────────┘
                                              │
                                              │ Real-time Telemetry, Live Audio RMS,
                                              │ Unfiltered dev_log & Graph Events
                                              ▼
                                  ┌────────────────────────┐
                                  │   Next.js 15 App HUD   │
                                  │  Three.js WebGL Engine │
                                  │  Port 3000 (React 19)  │
                                  └────────────────────────┘
```

---

## 🧬 Identity & Configuration Triad

J.A.R.V.I.S. is driven by three transparent Markdown configuration documents located in `backend/`:

1. **`SOUL.md` (Persona, Tone & Core Behavioral Directives):**
   Defines the identity, concise and dry communication style, technical precision, and behavioral boundaries. Can be edited manually or live via the **Personality Wizard** in the HUD.
2. **`MEMORY.md` (Long-Term User Models & Epistemic Facts):**
   Maintains user preferences, workflows, hardware specs, and persistent knowledge without hardcoded identities.
3. **`HEARTBEAT.md` (Autonomous Periodic Scheduler):**
   Governs autonomous background routines (e.g. system health checks, calendar sweeps, CachyOS package scans, and morning briefings).

---

## 🐧 Native CachyOS Skills & Scheduler

- **CachyOS Update Agent (`backend/actions/update_agent.py`):**
  Monitors pending package upgrades via `checkupdates` and `yay -Qu`. Specifically isolates critical system components (`linux`, `linux-cachyos`, `systemd`, `glibc`, `nvidia`, `mesa`, `openssl`). Never executes unconfirmed package upgrades: strictly routes through the Hardware Confirmation Gate (`confirm.py`).
- **Calendar & Appointment Manager (`backend/actions/calendar_manager.py`):**
  Embedded SQLite engine (`backend/memory/calendar.db`) providing full CRUD capabilities and natural-language scheduling ("Erinnere mich zwei Tage vorher an das Release").
- **Proactive Morning Briefing (`backend/core/cron_engine.py`):**
  Autonomously triggers at 08:00 or system boot, summarizing appointments, pending package updates, and system metrics via PipeWire voice playback.

---

## 🔊 Performance, Audio Routing & Privacy

- **Dedicated PipeWire Virtual Sink (`cypher_ai_sink`):**
  Jarvis registers as an independent audio node (`Cypher AI Audio`) within PipeWire and PulseAudio emulation. It appears as an individual volume slider in the KDE Plasma System Tray Audio Mixer, allowing independent balance without altering system audio.
- **Paranoia Killswitch (Hardware-Level Microphone Cut):**
  A dedicated toggle in the HUD that immediately terminates and closes the ALSA/PipeWire input stream handle. When activated, the HUD displays a bright red `PARANOIA MUTED (HARDWARE-OFF)` alert.
- **Focus Mode (Zero-Interference Gaming & Compilation):**
  Temporarily halts all background cron jobs and heartbeats with a single HUD click, freeing 100% CPU time for gaming, kernel compilation, or benchmark tasks.

---

## 🛠️ Developer Tools, Backup & Personality Wizard

- **Live Dev-Console (`DevConsole.tsx`):**
  A collapsible floating terminal streaming unfiltered backend events, exceptions, tool invocations, and tracebacks directly over WebSockets (`dev_log`).
- **1-Click Brain Backup (`backup_manager.py` & `BottomDock.tsx`):**
  Exports all persistent data (`long_term.json`, `calendar.db`, LanceDB vector indices, `SOUL.md`, and `mcp_servers.json`) into a compressed `.zip` archive.
- **Personality Wizard Modal (`PersonalityWizardModal.tsx`):**
  Interactive in-HUD wizard for configuring persona tone, humor, expertise domain, and ethical guardrails with 1-click live saving to `SOUL.md`.

---

## 🌐 3D WebGL Holographic HUD & Theme Engine

- **Three.js Knowledge Constellation (`ApexWorld.tsx`):**
  Interactive 3D graph with multi-colored data flow particles (`0x00d4ff`, `0x00ff88`, `0xa855f7`), reactive audio pulse scale, and Bezier link routing.
- **Centralized Theme Config (`frontend/theme.json`):**
  Defines standardized color palettes and glowing borders tailored for Arch Linux and CachyOS desktop ricing.

---

## 🔌 MCP Ecosystem (Model Context Protocol)

J.A.R.V.I.S. implements standard Model Context Protocol (MCP) JSON-RPC 2.0 servers configured in `backend/config/mcp_servers.json`:
- **`brave_search`:** Privacy-focused web search replacing legacy scrapers.
- **`fetch`:** Efficient web content retrieval and markdown conversion.
- **Dynamic MCP GUI:** Toggle and configure new MCP servers directly in the HUD via the Skills Matrix.

---

## ⚡ Quickstart in under 2 minutes

### 1. Clone & Setup
```bash
git clone https://github.com/Graba92/webjarvis.git
cd webjarvis
chmod +x setup.sh start.sh terminate_jarvis.sh
./setup.sh
```

### 2. Configure API Key
```bash
cp backend/.env.example backend/.env
# Edit backend/.env and insert your GEMINI_API_KEY
```

### 3. Launch
```bash
./start.sh
# Select option 1 (Native Fullstack) or option 4 (Docker Compose)
```

---

## 📜 License & Author

- **Author:** Graba92
- **License:** MIT License (Open Source)
