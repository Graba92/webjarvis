---
title: System Architecture & Directory Map
category: Architecture
tags:
  - architecture
  - core
  - actions
  - frontend
  - mcp
  - memory
created_at: '2026-10-08T17:58:00'
updated_at: '2026-10-08T17:58:00'
confidence: 1.0
status: verified
summary: Komplette Architektur- und Verzeichnis-Übersicht von J.A.R.V.I.S. (WebJarvis) zur internen Selbst-Orientierung der KI.
---

# 🗺️ J.A.R.V.I.S. System Architecture & Directory Map

Dieses Dokument dient der internen Selbst-Orientierung von J.A.R.V.I.S. (Cypher/Friday). Bei Unklarheiten über Modulpfade, Tool-Zuständigkeiten oder Dateisystem-Strukturen greift die KI auf diese Seite zu.

## 🏛️ Kern-Architektur
- **[[FastAPI Backend]]**: Liegt in `backend/server.py` und steuert die WebSocket-Kommunikation.
- **[[Next.js Frontend]]**: Liegt in `frontend/` und stellt das reaktive Cyberpunk-HUD bereit.
- **[[Gemini Live Controller]]**: In `backend/core/gemini_live.py` angebunden an Google GenAI Live (Audio + Tools).
- **[[Action Registry]]**: In `backend/core/action_loader.py` scannt dynamisch `backend/actions/`.
- **[[Model Context Protocol]]**: In `backend/core/mcp_client.py` und `backend/config/mcp_servers.json`.
- **[[Spezialisten Agenten]]**: In `backend/config/agents/` gesteuert über `backend/actions/agent_manager.py`.

## 📂 Hauptpfade
- **Prompts & Identität**: `backend/SOUL.md`, `backend/MEMORY.md`, `backend/HEARTBEAT.md`, `backend/backlog.md`
- **Konfigurationen**: `backend/config/` (`agents_registry.json`, `mcp_servers.json`, `cron_jobs.json`)
- **Aktionen (Tools)**: `backend/actions/` (`agent_manager.py`, `manage_mcp.py`, `wiki_manager.py`, `file_controller.py`, `sandboxed_shell.py`, `calendar_manager.py`, `system_monitor.py`)
- **Kernel-Module**: `backend/core/` (`gemini_live.py`, `audio_streamer.py`, `sandbox.py`, `backup_manager.py`)
- **Wissensspeicher**: `backend/knowledge_base/wiki/`, `backend/knowledge_base/raw/`, `backend/memory/calendar.db`, `backend/memory/lancedb_data/`

## 🛠️ Zugriffsmethoden für die KI
1. `manage_wiki(action="read", title="system_architecture_map")`
2. `file_controller(action="read_file", path="config/SYSTEM_MAP.md")`
3. `manage_agents(action="consult", id="backend", query="Verzeichnisstruktur")`
