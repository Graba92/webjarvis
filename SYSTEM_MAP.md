# 🗺️ J.A.R.V.I.S. SYSTEM ARCHITECTURE & DIRECTORY MAP (Mental Map)
<!-- 
  DOKUMENTATION & KOGNITIVER SYSTEMATLAS FÜR DIE KI SELBST
  Ablageort: backend/config/SYSTEM_MAP.md
  Zugriff für Jarvis:
    1. Tool 'manage_wiki(action="read", title="system_architecture_map")'
    2. Tool 'file_controller(action="read_file", path="config/SYSTEM_MAP.md")'
    3. Tool 'manage_agents(action="consult", id="backend", query="Architektur...")'
-->

---

## 🏛️ 1. Systemübersicht & Gesamtarchitektur

WebJarvis ist ein autonomes, echtzeitfähiges Cybernetic AI OS für CachyOS / Arch Linux.
Es operiert über eine strikt entkoppelte Client-Server-Architektur:
- **Frontend:** Next.js (App Router), React, TypeScript, Tailwind HUD, WebSockets.
- **Backend:** Python 3 (FastAPI, Uvicorn, Asyncio, Google GenAI Live SDK).
- **Audio Pipeline:** PipeWire Hardware-In/Out mit isolierten Virtual Sinks (`audio_streamer.py`).
- **Tool Execution:** Dynamische Action-Registry (`action_loader.py`) + Model Context Protocol (MCP via stdio/SSE) + Sandboxed Shell (`sandbox.py`).

```
[Mikrofon / PipeWire] ──> [audio_streamer.py] ──> [gemini_live.py (Bi-directional Audio)]
                                                          │
                                         ┌────────────────┴────────────────┐
                                         ▼                                 ▼
                              [Audio Stream zurück]              [Tool Calls (Function)]
                                         │                                 │
                                         ▼                                 ▼
                              [PipeWire Lautsprecher]             [action_loader.py]
                                                                           │
                                              ┌────────────────────────────┼────────────────────────────┐
                                              ▼                            ▼                            ▼
                                      [actions/*.py]               [core/mcp_client]            [agent_manager]
                                              │                            │                            │
                                              └────────────────────────────┼────────────────────────────┘
                                                                           ▼
                                                                  [server.py (WebSocket)]
                                                                           │
                                                                           ▼
                                                             [Next.js HUD (Port 3000/8080)]
```

---

## 📂 2. Vollständiger Verzeichnisbaum & Komponenten-Verortung

### 🖥️ A. Root-Ebene (`~/.local/share/webjarvis/` bzw. `/home/graba/Schreibtisch/webjarvis/`)
```text
webjarvis/
├── assets/                     # Grafiken, HUD-Icons, Sounds und statische Assets
├── backend/                    # Python-Backend (FastAPI, Core, Actions, Memory)
│   ├── .venv/                  # Isolierte Python 3.14 virtuelle Umgebung
│   ├── actions/                # Ausführbare Python-Aktionen (Tools für das LLM)
│   ├── backups/                # Verschlüsselte Brain-Backups (.zip)
│   ├── config/                 # Konfigurationen, API-Keys, Agenten & System-Maps
│   ├── core/                   # Kernel-Module (Audio, Gemini Live, MCP, Sandboxing)
│   ├── knowledge_base/         # Karpathy-Wiki & 3D Knowledge Graph
│   ├── memory/                 # LanceDB Vektordaten, SQLite Kalender & Langzeit-JSON
│   ├── sandbox_workspace/      # Isolierter Ausführungsordner für Shell-Befehle
│   ├── backlog.md              # Task-Backlog (offene/abgeschlossene Aufgaben)
│   ├── HEARTBEAT.md            # Periodische Checkliste für Scheduler-Routinen
│   ├── MEMORY.md               # Kuratiertes Langzeitgedächtnis (Systemprompterweiterung)
│   ├── SOUL.md                 # Primäre Persönlichkeitsdatei & Verhaltensregeln
│   └── server.py               # Hauptserver (FastAPI, WebSocket-Hub, Lifecycle)
├── data/                       # Persistente Docker-/Laufzeitdaten
├── frontend/                   # Next.js React Dashboard (Cyberpunk HUD)
│   ├── app/                    # Next.js App Router (Layouts, Pages)
│   ├── components/             # HUD-Komponenten (Cockpit, Modals, 3D Graph, Panels)
│   ├── lib/                    # TypeScript Schnittstellen (WebSockets, GraphData, Types)
│   ├── theme.json              # HUD-Farbpalette, CSS-Variablen und Glaseffekte
│   └── package.json            # Node-Abhängigkeiten
├── manager.py                  # PyQt6 Desktop Kontrollzentrum (System Tray, TUI/GUI Starter)
├── run.sh / start.sh           # Shell-Starter für Backend und Frontend
├── stop.sh / terminate_jarvis  # Harter und weicher Shutdown aller Jarvis-Prozesse
└── .env                        # Umgebungsvariablen (API-Keys, Ports, Audio-Devices)
```

---

## 🔍 3. Detaillierte Modul-Landkarte (Wo ist was?)

### 1. Kognition, Prompts & Identität
| Datei / Ordner | Zweck & Funktion | Zugriffsmethode für die KI |
| :--- | :--- | :--- |
| `backend/SOUL.md` | Die aktive Persönlichkeit (Cypher/Friday), Tonfall, Grenzen, Humor. | Automatisch geladen beim Start; änderbar via `save_personality`. |
| `backend/config/agents/` | Spezialisten-Agenten (`frontend`, `backend`, `mcp_api`, `reasoning_core`). | Tool `manage_agents(action="list"/"toggle"/"consult")`. |
| `backend/config/agents_registry.json` | Status aller Spezialisten (aktiv/inaktiv). | Tool `manage_agents` oder `config.py`. |
| `backend/MEMORY.md` | Manuell kuratiertes Langzeitgedächtnis (Wichtige Fakten über den Nutzer). | Eingebunden in System-Instruction als `<untrusted_document>`. |
| `backend/HEARTBEAT.md` | Checkliste für periodische Hintergrund-Routinen (Temp, RAM, Pakete). | Automatisch vom Scheduler (`cron_engine.py`) abgearbeitet. |
| `backend/backlog.md` | Aufgaben-Backlog für laufende Tasks. | Tool `manage_tasks(action="list"/"add"/"done")`. |

### 2. Core-Kernel (`backend/core/`)
| Modul | Hauptaufgabe |
| :--- | :--- |
| `gemini_live.py` | Baut WebSocket-Session zur Gemini Live API auf, injiziert Prompts, empfängt Audio- und Tool-Calls. |
| `action_loader.py` | Durchsucht `actions/*.py` nach `TOOL`/`TOOLS`, validiert Pydantic-Schemas und führt Handler aus. |
| `audio_streamer.py` | PipeWire Audio I/O (16kHz PCM Input, 24kHz PCM Output) mit Echo-Cancellation & Paranoia-Mute. |
| `config.py` | Lädt `.env`, Systemprompts, Stimmen (`Puck`, `Charon` etc.) und aktive Agenten-Direktiven. |
| `mcp_client.py` | Zentraler Client für externe MCP-Server via JSON-RPC 2.0 (stdio/SSE). |
| `sandbox.py` | Ausführungsschutz: Blockiert zerstörerische Befehle (`rm -rf /`, `mkfs`) und erzwingt Workspace-Isolierung. |
| `cron_engine.py` | Autonome Hintergrund-Cronjobs basierend auf `backend/config/cron_jobs.json`. |
| `backup_manager.py` | Erstellt verschlüsselte Backups aller Gehirndaten nach `backend/backups/`. |

### 3. Ausführbare Aktionen & Tools (`backend/actions/`)
- `agent_manager.py` ➜ Aktiviert/deaktiviert Sub-Agenten (`frontend`, `backend`, `mcp_api`, `reasoning_core`).
- `manage_mcp.py` ➜ Status, Healthcheck und Toggles für Model Context Protocol Server.
- `wiki_manager.py` ➜ Liest/schreibt kuratierte Markdown-Artikel mit `[[Wiki-Links]]` im Karpathy-Format.
- `graph_manager.py` ➜ Verwaltet Wissensknoten im interaktiven 3D Three.js Graphen (`graph_nodes.json`).
- `sandboxed_shell.py` ➜ Führt Shell-Befehle sicher in `sandbox_workspace/` aus.
- `file_controller.py` ➜ Liest, schreibt und editiert Dateien auf dem Dateisystem.
- `calendar_manager.py` ➜ Verwaltet Termine und Erinnerungen in der SQLite-Datenbank (`memory/calendar.db`).
- `system_monitor.py` ➜ Liest CPU-, RAM-, Disk- und Temperaturwerte des CachyOS-Hosts aus.
- `system_cleaner.py` ➜ Bereinigt Pacman-, Yay-, Pip- und Browser-Caches auf Nutzeranweisung.
- `task_manager.py` ➜ Erfasst und hakt Aufgaben in `backlog.md` ab.
- `jarvis_control.py` ➜ Steuert Neustart (`restart_tool`), Mute, Stop und Self-Update.

### 4. Wissensspeicher & Memory (`backend/memory/` & `backend/knowledge_base/`)
- `knowledge_base/wiki/` ➜ Kuratierte Markdown-Wissensseiten (vom Wiki-Manager verwaltet).
- `knowledge_base/raw/` ➜ Unveränderliche Rohdaten und importierte Quelltexte (Immutability-Prinzip).
- `knowledge_base/graph_nodes.json` ➜ Node- und Edge-Definitionen für das 3D-Frontend.
- `memory/calendar.db` ➜ SQLite-Datenbank für Termine (mit WAL-Modus für Zero-Data-Loss).
- `memory/lancedb_data/` ➜ Vektorspeicher für semantische Ähnlichkeitssuche.
- `memory/long_term.json` ➜ Episodische Chat-Historie und gelernte Fakten.

### 5. Frontend & HUD (`frontend/`)
- `frontend/components/ApexWorld.tsx` ➜ Der interaktive 3D Three.js Wissensgraph.
- `frontend/components/AgentCockpit.tsx` ➜ Status-Anzeige, Filter-Controls, Mute & System-Metriken.
- `frontend/components/PersonalityWizardModal.tsx` ➜ GUI zum Wechseln und Anpassen der Persona (`SOUL.md`).
- `frontend/components/DevConsole.tsx` ➜ Echtzeit-Terminal für Logs, Subprozess-Ausgaben und Debugging.
- `frontend/components/BottomDock.tsx` ➜ Die untere Cyberpunk-Leiste mit Schnellzugriffen.
- `frontend/lib/websocket.ts` ➜ Zentraler Client-WebSocket-Manager mit automatischem Reconnect.

---

## 🆘 4. Notfall- & Recovery-Routen (Sollte etwas sein)

| Fehlerszenario | Ursache | Diagnose & Behebung |
| :--- | :--- | :--- |
| **Tool bricht mit Fehler ab** | Schema-Inkonsistenz oder fehlendes Argument. | Prüfe `backend/actions/<tool>.py` auf `TOOL["parameters"]`. Führe `py_compile` im Backend aus. |
| **MCP-Server antwortet nicht** | Node/Python-Paket fehlt oder API-Key fehlt. | Prüfe `backend/config/mcp_servers.json` und `.env`. Führe `manage_mcp(action="status", id="<mcp>")` aus. |
| **Frontend zeigt "Offline"** | WebSocket getrennt oder Port 8080 blockiert. | Prüfe `server.py` Prozess. Starte Backend via `bash run.sh` oder `~/.local/bin/webjarvis`. |
| **Audio stumm / kein Ton** | PipeWire Sink blockiert oder Paranoia-Mute aktiv. | Führe `jarvis_control(action="unmute")` aus oder prüfe `pactl list sinks short`. |
| **Persönlichkeit verloren** | `SOUL.md` korrumpiert oder leer. | Wiederherstellen aus `backend/config/SOUL.md` oder Backup via `backup_manager.py restore`. |

---

## 🤖 5. Wie greift die KI auf diese Datei zu?

1. **Autonomes Nachschlagen bei Desorientierung:**  
   Die KI kann diese Datei jederzeit über das Tool `file_controller` lesen:
   ```json
   {
     "action": "read_file",
     "path": "config/SYSTEM_MAP.md"
   }
   ```
2. **Über die Wiki-Engine:**  
   Da dieser Inhalt auch im Wiki hinterlegt ist, kann Jarvis jederzeit abfragen:
   ```json
   {
     "action": "read",
     "title": "system_architecture_map"
   }
   ```
3. **Bei Agenten-Aktivierung:**  
   Wenn einer der 4 Spezialisten (`frontend`, `backend`, `mcp_api`, `reasoning_core`) aktiv ist, nutzt er die exakten Pfade dieser Map für millimetergenaue Wartungsarbeiten.
