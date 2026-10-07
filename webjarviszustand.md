# 🌐 WEBJARVIS (J.A.R.V.I.S. AI OS) — VOLLSTÄNDIGE SYSTEM- & ARCHITEKTUR-DOKUMENTATION
> **Single Source of Technical Truth & Entwickler-Referenz**  
> **Stand:** 2026 | **Version:** 2.4.0-Production | **Plattform:** CachyOS / Arch Linux (KDE Plasma 6 Wayland)  
> **Repository:** `github.com/Graba92/webjarvis` | **Entwickelt von:** `@Graba92`

---

## 📑 INHALTSVERZEICHNIS

1. [Systemphilosophie & Kernprinzipien](#1-systemphilosophie--kernprinzipien)
2. [Gesamtsystem-Architektur (ASCII-Übersicht)](#2-gesamtsystem-architektur-ascii-übersicht)
3. [Detaillierte Verzeichnis- & Modulstruktur](#3-detaillierte-verzeichnis--modulstruktur)
4. [Frontend-Architektur (Next.js 15 & Three.js WebGL)](#4-frontend-architektur-nextjs-15--threejs-webgl)
   - 4.1 Holografischer Szenengraph & Settle-on-Equilibrium Physik
   - 4.2 Volumetrische Fresnel- & Warn-Shader (Orphan & Konflikt)
   - 4.3 HUD-Komponenten: BacklogDrawer & WikiInspectorModal
5. [Backend-Architektur & Server-Core](#5-backend-architektur--server-core)
   - 5.1 Asyncio WebSocket RPC-Router & Event-Loop
   - 5.2 Gemini Multimodal Live API Voice-Engine (Bidi-Streaming)
   - 5.3 OpenAPI Schema-Sanitization (`sanitize_schema_for_gemini`)
6. [Data-Layer & Single-Writer Engines](#6-data-layer--single-writer-engines)
   - 6.1 Task Backlog Engine (`backlog.md` Single-Writer)
   - 6.2 Karpathy Knowledge Vault & [[Wiki-Links]]
   - 6.3 3D Graph Persistence (`graph_nodes.json`) & LanceDB Vektorspeicher
7. [Sicherheits- & Sandbox-Architektur](#7-sicherheits--sandbox-architektur)
   - 7.1 Bubblewrap (`bwrap`) OS-Isolation & Hierarchie-Guards
   - 7.2 Hardware Confirmation Gate (Human-in-the-Loop)
   - 7.3 Dynamische AI System-Prompt Synchronisation
8. [Audio- & Voice-Pipeline](#8-audio--voice-pipeline)
   - 8.1 PipeWire Virtual Audio Routing & 16/24-kHz PCM Duplex
   - 8.2 Live Voice Switching & Paranoia-Mute Killswitch
9. [Vollständige WebSocket-Protokoll-Spezifikation](#9-vollständige-websocket-protokoll-spezifikation)
10. [AI Tool- & Action-Matrix](#10-ai-tool--action-matrix)
11. [Entwickler-Leitfaden & Test-Kommandos](#11-entwickler-leitfaden--test-kommandos)

---

## 1. SYSTEMPHILOSOPHIE & KERNPRINZIPIEN

WebJarvis ist kein einfaches Web-Chatbot-Interface, sondern ein **lokales, autonomes Desktop-KI-Betriebssystem** für High-Performance Linux (speziell CachyOS / Arch Linux). Es vereint visuelle 3D-WebGL-Holographie, Vollduplex-Echtzeit-Sprachsteuerung und native Betriebssystem-Interaktion unter strikter Einhaltung von Industriestandards:

* **SPS-Prinzip (Speicherprogrammierbare Steuerung):** Vorhersagbare Zyklen, deterministische Zustandsautomaten und strikte Entkopplung von Ein-, Verarbeitungs- und Ausgabestufen.
* **POSIX-Atomarität & Zero-Data-Loss:** Alle Datei-Mutationen (Aufgaben, Wissensartikel, Backups, Graphendaten) erfolgen atomar über `.tmp`-Zwischenspeicher und `os.replace`. Ein Stromausfall oder Prozessabsturz hinterlässt zu keinem Zeitpunkt korrupte Dateien.
* **Single-Writer Konsistenz:** Kritische Dateien wie `backlog.md` werden ausschließlich über einen thread-sicheren Manager mit Entprellung (SHA-256 Hash-Vergleich) geschrieben, um Race Conditions mit externen Editoren (z.B. Neovim oder Kate) auszuschließen.
* **Red-Team gehärtete Sandbox:** Dateizugriffe und Shell-Operationen der KI sind standardmäßig durch Linux `bubblewrap` isoliert. Pfad-Traversals (`../`) und Symlink-Ausbrüche werden strikt blockiert.
* **Zero-Allocation 60-120 FPS WebGL:** Der Three.js Render-Loop ist vom React-Lifecycle entkoppelt; Scratch-Vektoren verhindern Garbage-Collection-Ruckler während des Renderings.

---

## 2. GESAMTSYSTEM-ARCHITEKTUR (ASCII-ÜBERSICHT)

```
+--------------------------------------------------------------------------------------------------+
|                                    NEXT.JS 15 HUD FRONTEND (PORT 3000)                           |
|                                                                                                  |
|   +-----------------------+   +------------------------------------+   +---------------------+   |
|   |   APEX OVERVIEW       |   |      THREE.JS 3D SCENE GRAPH       |   |    AGENT COCKPIT    |   |
|   |  - Telemetrie-Stats   |   |   - Volumetric Fresnel Hologram    |   |  - Arc Reactor RMS  |   |
|   |  - Category Filter    |   |   - Force-Relaxation (Settled)     |   |  - Voice Mode State |   |
|   |  - Search & Inspector |   |   - [[Wiki-Links]] Spring Edges    |   |  - Paranoia Mute    |   |
|   +-----------+-----------+   |   - Orphan Amber / Conflict Red    |   +----------+----------+   |
|               |               +-----------------+------------------+              |              |
|               |                                 |                                 |              |
|   +-----------v---------------------------------v---------------------------------v----------+   |
|   |                           INTERAKTIVE SCI-FI HUD MODALS & DRAWERS                        |   |
|   |   [BacklogDrawer.tsx]         [WikiInspectorModal.tsx]           [SandboxModal.tsx]      |   |
|   |   - Reorder Up/Down           - Markdown Split Preview           - Path Whitelist        |   |
|   |   - Atomic Checkbox Sync      - Clickable [[Wiki-Links]]         - Full OS Toggle        |   |
|   |   - Priority Badges           - Dirty-State Lock (Ctrl+S)        - Bwrap Fallback Status |   |
|   +---------------------------------------------+--------------------------------------------+   |
|                                                 | (Bidirectional JSON WebSocket RPC)             |
+-------------------------------------------------v------------------------------------------------+
                                                  ^
                                                  | ws://127.0.0.1:8765
                                                  v
+--------------------------------------------------------------------------------------------------+
|                                PYTHON ASYNCIO BACKEND CORE (PORT 8765)                           |
|                                                                                                  |
|   +------------------------------------------------------------------------------------------+   |
|   |                                  FASTAPI / WEBSOCKET ROUTER                              |   |
|   |       RPC-Endpunkte: toggle_task, reorder_tasks, get_wiki_article, save_wiki_article,    |   |
|   |                      get_graph, execute_node_action, trigger_backup, set_sandbox_config  |   |
|   +-------------+---------------------------+---------------------------+--------------------+   |
|                 |                           |                           |                        |
|   +-------------v-------------+ +-----------v-------------+ +-----------v-------------+          |
|   |      TASK MANAGER         | |      WIKI MANAGER       | |      GRAPH MANAGER      |          |
|   |  (Single-Writer Lock)     | |  (Karpathy Vault Engine)| |  (3D Topology Engine)   |          |
|   |  - backlog.md (SPS)       | |  - [[Wiki-Links]] Parse | |  - YAML Title Rendering |          |
|   |  - SHA-256 Anti-Echo      | |  - Conflict Detection   | |  - Orphan Calculation   |          |
|   |  - POSIX Atomic Replace   | |  - LanceDB Embeddings   | |  - graph_nodes.json     |          |
|   +-------------+-------------+ +-----------+-------------+ +-----------+-------------+          |
|                 |                           |                           |                        |
|   +-------------v---------------------------v---------------------------v--------------------+   |
|   |                        GEMINI MULTIMODAL LIVE STREAMING ENGINE                           |   |
|   |  - gemini-2.0-flash-exp / live WebSocket Session mit Duplex Audio (16/24 kHz PCM)        |   |
|   |  - Session Resumption Guard (Code 1008 / GoAway Timeout Auto-Reconnect)                  |   |
|   |  - OpenAPI Schema Sanitization (Pydantic / None-Type Safety)                             |   |
|   |  - Dynamic System Prompt Injection: Untrusted Docs, Active Backlog & Sandbox Paths       |   |
|   +-------------+-------------------------------------------------------+--------------------+   |
|                 |                                                       |                        |
|   +-------------v-------------+                           +-------------v-------------+          |
|   |   HARDENED BWRAP SANDBOX  |                           |  PIPEWIRE AUDIO SUBSYSTEM |          |
|   |  - Path Traversal Block   |                           |  - Virtual Mic/Speaker    |          |
|   |  - Symlink Resolution     |                           |  - Hardware Capture 16kHz |          |
|   |  - Hardware Confirm Gate  |                           |  - Paranoia Zero-Out Mute |          |
|   +---------------------------+                           +---------------------------+          |
+--------------------------------------------------------------------------------------------------+
```

---

## 3. DETAILLIERTE VERZEICHNIS- & MODULSTRUKTUR

```bash
/home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/
├── backend/
│   ├── actions/                       # KI-Tools & Aktionsmodule (Auto-Discovery)
│   │   ├── calendar_manager.py        # SQLite Termin- & Kalender-Matrix mit Wiederholungen
│   │   ├── file_controller.py         # Sandbox-gehärteter Datei-Leser/Schreiber
│   │   ├── graph_manager.py           # 3D-Knotengraph Verwaltung, YAML-Titel & Orphan-Check
│   │   ├── mcp_bridge.py              # Model Context Protocol (JSON-RPC 2.0) Tool-Bridge
│   │   ├── open_app.py                # XDG Desktop & Terminal Anwendungsstarter
│   │   ├── system_monitor.py          # CachyOS Telemetrie (CPU, GPU, RAM, Sensoren)
│   │   ├── task_manager.py            # AI-Tool manage_tasks (list, complete, add, delete)
│   │   ├── undo_manager.py            # 10-Stufen Undo-Stack für destruktive Systemaktionen
│   │   ├── update_agent.py            # Non-destruktiver Git-Self-Updater
│   │   └── wiki_manager.py            # AI-Tool manage_wiki (Karpathy Vault, [[Wiki-Links]])
│   ├── core/                          # Low-Level Systemkerne & Engines
│   │   ├── action_registry.py         # Dynamischer Loader & OpenAPI Schema-Sanitizer
│   │   ├── audio_manager.py           # PipeWire PyAudio Stream-Manager (16/24 kHz)
│   │   ├── backup_manager.py          # Brain Vault: ZIP-Export & Hot-Restore
│   │   ├── cron_engine.py             # Hintergrund-Scheduler & Autonomes Tagesbriefing
│   │   ├── gemini_live.py             # Vollduplex WebSocket Client für Gemini Live
│   │   ├── sandbox.py                 # Bubblewrap (bwrap) Prozessisolation & Pfad-Guards
│   │   ├── task_manager.py            # SPS Single-Writer Task-Engine für backlog.md
│   │   └── undo.py                    # Circular Buffer für reversible Systemmutationen
│   ├── knowledge_base/                # Persistente Wissensspeicher
│   │   ├── graph_nodes.json           # Topologie des 3D Three.js Szenengraphen
│   │   ├── knowledge_map.json         # Metadaten-Mappings für Systemkomponenten
│   │   ├── raw/                       # Unveränderliche Quelltexte (Immutability-Garantie)
│   │   └── wiki/                      # Kuratierte Markdown-Wiki-Seiten mit YAML Frontmatter
│   ├── memory/                        # Gedächtnissysteme
│   │   ├── lancedb_manager.py         # Lokaler LanceDB Vektorspeicher für semantischen Recall
│   │   └── memory_manager.py          # Zwei-Stufen Langzeitgedächtnis (short_term / long_term)
│   ├── backlog.md                     # Single Source of Truth für Aufgaben (- [ ] / - [x])
│   ├── server.py                      # Zentraler WebSocket-Server & Broadcast-Hub (:8765)
│   └── run.sh                         # Venv-Startskript mit automatischem Dependency-Check
├── frontend/                          # Next.js 15 Client-Cockpit
│   ├── app/
│   │   ├── layout.tsx                 # Root Layout & Sci-Fi Font Konfiguration
│   │   └── page.tsx                   # Master-Dashboard (Orchestrierung aller HUD-Panels)
│   ├── components/
│   │   ├── AgentCockpit.tsx           # Arc Reactor, Audio-RMS Visualizer, Killswitch
│   │   ├── ApexOverviewPanel.tsx      # Linke Sidebar: Suche, Telemetrie, Inspector-Trigger
│   │   ├── ApexWorld.tsx              # Three.js 3D WebGL Holographie & Shader-Engine
│   │   ├── BacklogDrawer.tsx          # Interaktive Aufgaben-Matrix (Reorder, Filter, Edit)
│   │   ├── BackupModal.tsx            # Brain Vault Backup- & Restore-Center
│   │   ├── BottomDock.tsx             # Untere Steuerungsleiste & Orphan-Warn-Pill
│   │   ├── CalendarModal.tsx          # Interaktiver Terminkalender mit Zeithorizonten
│   │   ├── ConfirmBanner.tsx          # Hardware Confirmation Gate für sensible Aktionen
│   │   ├── DevConsole.tsx             # Verschiebbare Live-Log Konsole mit Log-Filtern
│   │   ├── JarvisChatWindow.tsx       # Verschiebbares & skalierbares Chat-Fenster
│   │   ├── SandboxModal.tsx           # Sandbox-Konfiguration & Freigegebene Verzeichnisse
│   │   └── WikiInspectorModal.tsx     # Split-Markdown Viewer, [[Wiki-Links]], Dirty-Lock
│   ├── lib/
│   │   ├── graphData.ts               # Farbdefinitionen & Standardknoten
│   │   ├── types.ts                   # TypeScript Interfaces (GraphNode, WikiArticle, etc.)
│   │   └── websocket.ts               # Singleton WebSocket-Manager mit Auto-Reconnect
│   └── package.json                   # Next.js 15, Three.js, Lucide-React, Tailwind CSS
├── posting.md                         # Community- & Social-Media-Vorlagen (Reddit, Discord)
├── posting-win.md                     # Windows/Cross-Platform Kurzreferenz
└── webjarviszustand.md                # Vorliegende Gesamtspezifikation
```

---

## 4. FRONTEND-ARCHITEKTUR (NEXT.JS 15 & THREE.JS WEBGL)

### 4.1 Holografischer Szenengraph & Settle-on-Equilibrium Physik
In [`frontend/components/ApexWorld.tsx`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/frontend/components/ApexWorld.tsx) wird das dreidimensionale Hologramm berechnet.
- **Entkoppelter Lifecycle:** Der WebGL-Renderer und die Animationsschleife (`requestAnimationFrame`) laufen isoliert von React-Rerendern in stabilen `useRef`-Strukturen.
- **Settle-on-Equilibrium Algorithmus:** Anstatt rechenintensive Force-Directed Physik jedes Frame auf der CPU zu berechnen ($O(N^2)$ Flaschenhals), führt WebJarvis beim Laden des Graphen eine **90-Schritt-Relaxation** mit geometrischer Abkühlung (`cooling = 0.965`) und kollisionsgeschütztem Mindestabstand durch:
  1. *Coulomb-Repulsion mit Kollisionsschutz:* Knoten stoßen sich ab ($dist < 210$), wobei Mindestabstände (75 für Hubs, 52 für Standardknoten) Text- und Label-Überlappungen in dichten Clustern verhindern.
  2. *Hooke-Spring Attraction:* Über `[[Wiki-Links]]` verbundene Knoten ziehen sich auf eine elastische Ruhedistanz an.
  3. *Cluster-Zentrierung:* Knoten werden harmonisch in ihre Kategoriensphäre (Cyan = Skills/Tools, Blau = Wiki/Suites, Orange = Concepts/Worlds) gezogen.
  4. Nach Erreichen des Gleichgewichts friert die Topologie ein (`settled = true`). Dies garantiert **konstante 120 FPS** ohne GPU/CPU-Überlastung.
- **High-Definition Billboard-Typografie (1024×256) & Gestaffeltes Entfernungs-LOD:**
  - Knotenbeschriftungen werden auf einem hochauflösenden 1024×256 Canvas mit Sci-Fi Eck-Brackets und abgedunkeltem Glassmorphism-Pill-Hintergrund gerendert.
  - Groß-Hubs, isolierte Orphan-Knoten und Widerspruchs-Knoten sind dauerhaft sichtbar beschriftet.
  - Standardknoten zeigen ihre Beschriftung adaptiv bei Nah- und Mittel-Zoom (`cameraDist < 650`), um eine aufgeräumte, futuristische Galaxie-Optik zu wahren.

### 4.2 Volumetrische Fresnel- & Warn-Shader
Jeder Knoten wird durch einen spezialisierten GLSL-Shader gerendert:
- **Fresnel Rim-Glow:** $\text{rim} = (1.0 - (\vec{N} \cdot \vec{V}))^{2.3}$ für plastische Tiefe.
- **Orphan-Strobe:** Knoten ohne Kanten (`is_orphan` oder Grad 0) schalten auf Neon-Amber (`#ffaa00`) und eine hochfrequente Strobe-Pulsierung.
- **Konflikt-Strobe:** Knoten mit ungelösten Wissenswidersprüchen leuchten im Crimson-Alarmfarbton (`#ff2244`).

### 4.3 HUD-Komponenten: BacklogDrawer & WikiInspectorModal
- **`BacklogDrawer.tsx`:** Floating Glassmorphism-Drawer mit Sofort-Umschaltung von `- [ ]` und `- [x]`, Filtern nach Status und Up/Down-Pfeilen zur Neuanordnung von Prioritäten.
- **`WikiInspectorModal.tsx`:** Wissens-Inspektor für jeden Knoten:
  - Vollständiges Markdown-Rendering mit Live-Extraktion von `[[Wiki-Links]]`. Klick auf einen Querverweis navigiert sofort zum Zielknoten oder zentriert die 3D-Kamera.
  - Erkennung von `> [!WARNING] Widerspruch`-Blöcken als optische Alarm-Banner.
  - Integrierter Editor mit Monospace-Schriftart, Dirty-State-Schutz (`* Ungespeichert`), Tastaturkürzeln (`Ctrl+S`, `Esc`) und POSIX-konformem Speicher-Feedback.

---

## 5. BACKEND-ARCHITEKTUR & SERVER-CORE

### 5.1 Asyncio WebSocket RPC-Router & Event-Loop
[`backend/server.py`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/backend/server.py) bildet den zentralen Kommunikationsknotenpunkt auf Port 8765:
- Vollständig asynchrone Bearbeitung über `websockets.serve`.
- Thread-Pool Entlastung via `asyncio.to_thread` für synchrone Datei- und Backup-Operationen.
- Zustandsübertragung in Echtzeit an alle verbundenen Web-Clients via `broadcast()`.

### 5.2 Gemini Multimodal Live API Voice-Engine
[`backend/core/gemini_live.py`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/backend/core/gemini_live.py) implementiert das Google GenAI SDK (Multimodal Live Bidi-Streaming):
- **Duplex Audio:** Kontinuierlicher 16-kHz PCM Audio-Upstream vom Mikrofon; 24-kHz PCM Audio-Downstream direkt an PipeWire.
- **Session-Resumption:** Automatischer Fang von WebSocket Close-Codes (z.B. Code `1008` / GoAway-Timeout) mit transparenter Sitzungswiederaufnahme ohne Systemneustart.
- **Voice Commands:** Autonome Spracherkennung für Befehle wie *„Jarvis neustart“* (Tool-Reload), *„Jarvis stop“* (Audio-Unterbrechung) und *„Jarvis stumm“* (Paranoia-Mute).

### 5.3 OpenAPI Schema-Sanitization
Gemini Live reagiert empfindlich auf ungültige OpenAPI-Datentypen in Tool-Definitionen. Die Engine bereinigt Schemas über `sanitize_schema_for_gemini`:
- Wandelt komplexe `anyOf`-Union-Typen in saubere Basistypen (`STRING`, `OBJECT`) um.
- Eliminiert `None`-Typen und setzt fehlende Pflichtfelder (`properties`, `items`).

---

## 6. DATA-LAYER & SINGLE-WRITER ENGINES

### 6.1 Task Backlog Engine (`backlog.md` Single-Writer)
[`backend/core/task_manager.py`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/backend/core/task_manager.py) verwaltet Aufgaben nach dem SPS-Prinzip:
- **Speicherort:** `backend/backlog.md` als reines, lesbares Markdown.
- **Thread-Sicherheit:** Mutationen werden durch `threading.RLock()` serialisiert.
- **Atomarität:** Speichern erfolgt immer in `backlog.md.tmp` gefolgt von `os.replace`.
- **Anti-Echo Wächter:** Ein periodischer Wächter prüft den SHA-256 Hash der Datei. Externe Änderungen (z.B. Bearbeiten in Neovim) werden sofort erfasst und ins Frontend gepusht; interne Schreibzugriffe erzeugen keine Echo-Loops.

### 6.2 Karpathy Knowledge Vault & [[Wiki-Links]]
[`backend/actions/wiki_manager.py`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/backend/actions/wiki_manager.py) implementiert das adaptierte Karpathy-Wissensmuster:
- **Isolierter Wiki-Ordner:** `backend/knowledge_base/wiki/*.md`.
- **Immutability-Garantie:** Rohe Benutzereingaben in `backend/knowledge_base/raw/` werden niemals überschrieben.
- **Zero-Data-Loss Konflikt-Erkennung:** Stellt die KI einen inhaltlichen Widerspruch fest, überschreibt sie keine Daten, sondern injiziert einen standardisierten Warnblock:
  ```markdown
  > [!WARNING] Widerspruch erkannt (2026-10-07 17:30:00)
  > **Neuer Input:** Kernel 6.13 benötigt Parameter X
  > **Bisheriger Stand:** Parameter Y war Standard
  > **Status:** Klärung durch Operator ausstehend (Originale unberührt)
  ```
- **Topologie-Kopplung:** Jeder gefundene `[[Wiki-Link]]` erzeugt eine Kante im 3D-Graphen.

### 6.3 3D Graph Persistence & LanceDB Vektoren
- **`graph_nodes.json`:** Speichert Knoten, Kategorien, Kanten und Beschreibungen.
- **LanceDB:** Lokale Vektordatenbank (`backend/memory/lancedb_manager.py`) zur semantischen Volltextsuche und RAG-Injektion in den Gemini-Kontext.

---

## 7. SICHERHEITS- & SANDBOX-ARCHITEKTUR

### 7.1 Bubblewrap (`bwrap`) OS-Isolation & Hierarchie-Guards
[`backend/core/sandbox.py`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/backend/core/sandbox.py) kapselt Shell- und Dateibefehle:
- **Sandbox-Root:** `~/.local/share/webjarvis/backend/sandbox_workspace` (oder explizit freigegebene Verzeichnisse).
- **Prozessisolation:** Aufruf mit `--die-with-parent`, `--new-session`, `--unshare-all`, `--ro-bind /usr /usr`.
- **Path-Traversal Schutz:** Pfade mit `../` oder auflösbare Symlinks außerhalb der Whitelist werden hart blockiert (`PermissionError: Zugriffsverweigerung`).

### 7.2 Hardware Confirmation Gate (Human-in-the-Loop)
Destruktive Systemoperationen (Dateilöschungen, Paketinstallationen, System-Neustarts) werden vor der Ausführung in einer Pending-Queue angehalten. Das Frontend blendet ein priorisiertes Bestätigungsbanner ([`ConfirmBanner.tsx`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/frontend/components/ConfirmBanner.tsx)) ein. Die Aktion wird erst nach manuellem Klick des Benutzers freigegeben.

### 7.3 Dynamische AI System-Prompt Synchronisation
Gemini wird in Echtzeit über seine Sicherheitsbeschränkungen informiert:
- Aktive Pfad-Whitelists werden in den System-Prompt injiziert.
- Ungesicherte Dokumente werden in `<untrusted_document>` Tags gekapselt, um Indirect Prompt Injections abzuwehren.

---

## 8. AUDIO- & VOICE-PIPELINE

```
Mikrofon (16 kHz PCM)  ──>  PyAudio Stream  ──>  Gemini Live WebSocket
                                                       │
Gemini Audio Downstream (24 kHz PCM)  <────────────────┘
       │
       ▼
PipeWire Virtual Sink  ──>  Lautsprecher / Kopfhörer
```

- **PipeWire Low-Latency:** Native Integration über PulseAudio/PipeWire-Kompatibilitätsschicht auf CachyOS.
- **Voice Switching:** Dynamischer Wechsel zwischen `Puck` (männlich) und `Aoede` (weiblich) ohne Serverneustart.
- **Paranoia-Mute:** Physisches Schließen des Mikrofon-Audiostreams bei Betätigung des Mute-Schalters im HUD.

---

## 9. VOLLSTÄNDIGE WEBSOCKET-PROTOKOLL-SPEZIFIKATION

### Client ➔ Server Nachrichten
| Nachrichtentyp | Parameter | Beschreibung |
| :--- | :--- | :--- |
| `get_tasks` | `{}` | Fragt die aktuelle Liste aller Tasks aus `backlog.md` ab. |
| `toggle_task` | `task_id, completed?` | Setzt oder toggled den Erledigt-Status einer Aufgabe. |
| `add_task` | `text, priority?` | Fügt eine neue Aufgabe am Ende von `backlog.md` an. |
| `delete_task` | `task_id` | Entfernt eine Aufgabe POSIX-atomar aus `backlog.md`. |
| `reorder_tasks` | `task_ids: string[]` | Ordnet die Aufgabenreihenfolge anhand der ID-Liste neu an. |
| `get_wiki_article` | `slug, title, path?` | Liest Markdown-Inhalt, Metadaten und `[[Wiki-Links]]`. |
| `save_wiki_article`| `title, content, tags` | Speichert einen Wiki-Artikel atomar & synchronisiert den Graphen. |
| `execute_node_action`| `node_id, path, category` | Führt Standardaktion auf Knoten aus (z.B. Datei oder App öffnen). |
| `set_full_os_access` | `enabled: boolean` | Aktiviert/Deaktiviert unbeschränkten OS-Zugriff temporär. |
| `add_sandbox_path` | `path: string` | Fügt ein Verzeichnis zur Sandbox-Whitelist hinzu. |
| `remove_sandbox_path`| `path: string` | Entfernt ein Verzeichnis von der Sandbox-Whitelist. |
| `set_voice` | `voice: string` | Schaltet die KI-Stimme (`Puck` / `Aoede`) um. |
| `export_brain` | `label, passphrase?` | Erstellt ein vollständiges ZIP-Backup des Brain-Vaults. |
| `import_brain` | `path, passphrase?` | Stellt ein Backup bei laufendem Betrieb wieder her. |

### Server ➔ Client Broadcasts
| Nachrichtentyp | Nutzdaten | Zweck |
| :--- | :--- | :--- |
| `tasks_data` | `tasks: TaskItem[]` | Live-Update aller Aufgaben an alle geöffneten Fenster. |
| `wiki_article_data`| `article: WikiArticle` | Bereitgestellte Artikel-Daten für den Wissens-Inspektor. |
| `wiki_article_saved`| `result: { success, ... }` | Bestätigung über erfolgreiches Speichern eines Artikels. |
| `graph_sync` | `data: GraphData` | Aktualisierte 3D-Knoten und Kanten nach Wiki-Updates. |
| `sandbox_config` | `allowed_paths, full_os_access` | Aktueller Zustand der Sandbox-Sicherheitsmatrix. |
| `telemetry` | `cpu, ram, gpu, temps` | Echtzeit-Systemmetriken für das Apex-HUD. |

---

## 10. AI TOOL- & ACTION-MATRIX

Gemini Live stehen über die Action-Registry folgende autonome Werkzeuge zur Verfügung:

1. **`manage_tasks`:**
   - Parameter: `action` (`list`, `complete`, `add`, `delete`, `toggle`), `task_id`, `text`, `priority`, `status_filter`.
   - Aufgaben autonom planen, erfassen und als erledigt abhaken.
2. **`manage_wiki`:**
   - Parameter: `action` (`read`, `write`, `list`, `flag_conflict`, `search`), `title`, `content`, `tags`, `new_claim`, `existing_claim`.
   - Autonomes Pflegen des Wissenswikis mit Quellenprüfung und Konflikt-Alarm.
3. **`graph_manager`:**
   - Parameter: `action` (`add_node`, `query_graph`, `delete_node`), `title`, `category`, `connections`.
   - Manipulation des 3D Three.js Szenengraphen.
4. **`system_monitor`:**
   - Parameter: `action` (`telemetry`, `top_processes`, `kill_process`).
   - Abfrage von CPU-, Speicher-, Partitions- und Temperaturwerten.
5. **`file_controller`:**
   - Parameter: `action` (`read`, `write`, `list`, `delete`), `path`, `content`.
   - Sichere Dateimanipulation innerhalb der Bubblewrap-Sandbox.
6. **`calendar_manager`:**
   - Parameter: `action` (`list`, `add`, `delete`), `title`, `start_time`, `category`.
   - Terminverwaltung und Abgleich für das morgendliche Briefing.
8. **`show_guide`:**
   - Parameter: `action` (`show`, `close`), `title`, `steps`, `capture_screen`.
   - Blendet eine interaktive Bild-Anleitung mit Pfeilen und Erklärungen im HUD ein (`GuideOverlayModal.tsx`), inklusive 1-Klick JPEG-Download.
9. **`screen_process`:**
   - Parameter: keine.
   - Nimmt den aktuellen Bildschirm via `mss` auf für multimodale Seh-Analysen oder Hintergrund-Guides.

---

## 11. CROSS-PLATFORM & WINDOWS WSL2 INTEGRATION (`run_windows.py` / `run_windows.bat`)

* **WSL 2 Goldstandard (2026):** WebJarvis verzichtet unter Windows vollständig auf ineffiziente Ports (MinGW/Cygwin) und nutzt WSL 2 als native Linux-Engine.
* **TUI-Consent-Architektur (Vektor-7):** Vor tiefgreifenden Host-Eingriffen (`wsl --install`, Paketinstallationen) wird ein klarer Konsens mit Begründung und Systemauswirkung eingeholt.
* **Dynamische Pfad-Konvertierung:** Argumente und Dateipfade werden on-the-fly durch `wslpath -a -u` geschleift, sodass Windows-Dateipfade (`C:\...`) nahtlos in Linux-Pfade übersetzt werden.
* **CRLF-to-LF Sanitizer:** Konvertiert Zeilenumbrüche vor der Übergabe automatisch, um Bash-Syntaxabbrüche (`\r: command not found`) auszuschließen.
* **1-Klick-Starter Batch:** `run_windows.bat` prüft den Python-Hostpfad und leitet direkt an `run_windows.py` weiter.

---

## 12. ENTWICKLER-LEITFADEN & TEST-KOMMANDOS

### 11.1 Schnelle Validierung (One-Liner für Devs)
```bash
# 1. Backend Python-Syntax & Modul-Kompilierung
PYTHONPATH=backend backend/.venv/bin/python3 -m py_compile backend/server.py backend/core/*.py backend/actions/*.py

# 2. Vollständiger Next.js Production-Build
cd frontend && npm run build

# 3. Task- & Wiki-Engine Integrationstest
PYTHONPATH=backend backend/.venv/bin/python3 -c "
from core.task_manager import get_task_manager
from actions.wiki_manager import read_wiki_article, write_wiki_article
tm = get_task_manager()
assert len(tm.get_tasks()) > 0
res = write_wiki_article('DevTest', '# DevTest\n[[Wiki]]', ['test'])
assert res['success'] is True
art = read_wiki_article('DevTest')
assert art['exists'] is True
print('>>> DEV INTEGRATION CHECK: 100% OK <<<')
"
```

### 11.2 Starten des Systems
```bash
# Terminal 1: Backend starten
cd backend && ./run.sh

# Terminal 2: Frontend starten
cd frontend && npm run dev
```

---
*Ende der Spezifikation — Vollständig verifiziert, auditiert und gepflegt für das Entwickler-Portfolio von @Graba92.*
