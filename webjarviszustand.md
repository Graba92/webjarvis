# 🧠 J.A.R.V.I.S. AI OS (Codename: Cypher) — Full-Stack Entwickler- & Architektur-Bibel

> **Dokumententyp:** Vollständige System-, Code- & Architektur-Spezifikation (Wie, Was, Wo)  
> **Architektur-Modell:** SPS-Prinzip der IT (Einmal gebaut, 10 Jahre stabil ohne Bloatware)  
> **Lead Systems Architect:** Matze "Graba" (Lead Systems Architect & Full-Stack Pragmatist)  
> **Zielplattform:** Linux (CachyOS / Arch Linux, Kernel 6.12+, KDE Plasma 6 Wayland, PipeWire)  
> **Dokumentationspfade:**  
> - Primär: `/home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarviszustand.md`  
> - Repository: `/home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/webjarviszustand.md`  
> **Stand:** 07. Oktober 2026 (Live & Gehärtet)  

---

## 📋 Inhaltsverzeichnis

1. [Architektur-Philosophie: Das SPS-Prinzip für Desktop AI OS](#1-architektur-philosophie-das-sps-prinzip-für-desktop-ai-os)
2. [Gesamtsystem-Architektur (Full-Stack ASCII Übersicht)](#2-gesamtsystem-architektur-full-stack-ascii-übersicht)
3. [Interne Interface Definition Language (IDL) & WebSocket-RPC-Protokoll](#3-interne-interface-definition-language-idl--websocket-rpc-protokoll)
4. [End-to-End Datenflüsse & Sequenzdiagramme (ASCII)](#4-end-to-end-datenflüsse--sequenzdiagramme-ascii)
   - [4.1 Vollduplex Audio & Voice-Streaming Pipeline](#41-vollduplex-audio--voice-streaming-pipeline)
   - [4.2 Tool-Call Execution Loop mit Confirmation Gate & Sandbox](#42-tool-call-execution-loop-mit-confirmation-gate--sandbox)
   - [4.3 60Hz Telemetrie- & Shader-Synchronisation](#43-60hz-telemetrie--shader-synchronisation)
5. [Frontend Deep-Dive: Next.js 15 & Three.js WebGL Hologramm](#5-frontend-deep-dive-nextjs-15--threejs-webgl-hologramm)
   - [5.1 Volumetrische Fresnel-Shader & GPU-Pipeline](#51-volumetrische-fresnel-shader--gpu-pipeline)
   - [5.2 Szenengraph, Gyroskop-Ringe & Zero-Allocation Raycasting](#52-szenengraph-gyroskop-ringe--zero-allocation-raycasting)
   - [5.3 HUD-Komponenten- & Fenster-Matrix](#53-hud-komponenten--fenster-matrix)
   - [5.4 Resiliente WebSocket State Machine (`frontend/lib/websocket.ts`)](#54-resiliente-websocket-state-machine-frontendlibwebsocketts)
6. [Backend Deep-Dive: AsyncIO Core & Sicherheit](#6-backend-deep-dive-asyncio-core--sicherheit)
   - [6.1 Server & Connection Pooling (`backend/server.py`)](#61-server--connection-pooling-backendserverpy)
   - [6.2 Gemini Live Voice Controller (`backend/core/gemini_live.py`)](#62-gemini-live-voice-controller-backendcoregemini_livepy)
   - [6.3 Bubblewrap Sandbox & Zero-Escape Isolation (`backend/core/sandbox.py`)](#63-bubblewrap-sandbox--zero-escape-isolation-backendcoresandboxpy)
   - [6.4 Tool-Discovery & OpenAPI Typ-Sanitizer (`backend/core/action_loader.py`)](#64-tool-discovery--openapi-typ-sanitizer-backendcoreaction_loaderpy)
   - [6.5 PipeWire Audio Streamer (`backend/core/audio_streamer.py`)](#65-pipewire-audio-streamer-backendcoreaudio_streamerpy)
   - [6.6 Brain Vault Backup-Engine & SQLite WAL Snapshot (`backend/core/backup_manager.py`)](#66-brain-vault-backup-engine--sqlite-wal-snapshot-backendcorebackup_managerpy)
   - [6.7 Hardware Safety Confirmation Gate (`backend/core/confirm.py`)](#67-hardware-safety-confirmation-gate-backendcoreconfirmpy)
   - [6.8 Multi-Tier Gedächtnissystem (`backend/memory/`)](#68-multi-tier-gedächtnissystem-backendmemory)
7. [Vollständiger Werkzeug-Katalog (Alle 14 Actions im Detail)](#7-vollständiger-werkzeug-katalog-alle-14-actions-im-detail)
8. [Desktop Orchestration & Manager GUI (`manager.py` & Shell)](#8-desktop-orchestration--manager-gui-managerpy--shell)
9. [Vollständiger Verzeichnis- & Dateibaum](#9-vollständiger-verzeichnis--dateibaum)
10. [Sicherheits-, Privilegien- & Sandbox-Matrix](#10-sicherheits--privilegien--sandbox-matrix)
11. [Entwickler-Codex: How-To Guides & Best Practices](#11-entwickler-codex-how-to-guides--best-practices)

---

## 1. Architektur-Philosophie: Das SPS-Prinzip für Desktop AI OS

Die meisten modernen KI-Anwendungen kranken an zwei Extremen:
Entweder sind sie bloße Electron-Bloatware mit 800 MB RAM-Verbrauch im Leerlauf und unkontrollierten Cloud-Abos, oder es sind fragile CLI-Skripte, die beim ersten Syntaxfehler abbrechen.

**WebJarvis folgt dem SPS-Prinzip (Speicherprogrammierbare Steuerung):**
- **Fundament zuerst:** Ein Prozess, der im Hintergrund läuft, darf niemals abstürzen (`try/except/retry`). Fehler im Dateisystem oder in einem Tool werden abgefangen, sauber protokolliert und an das Modell gemeldet – der Server-Daemon läuft unbeeindruckt weiter.
- **Entkopplung von Interface & Core:** Das Python-Backend verwaltet Audio, Gemini Live, Bubblewrap und die Datenbanken autonom. Das Frontend (Next.js 15 / Three.js) ist ein reiner Darstellungs- und Kontroll-Client. Wird der Browser geschlossen, läuft Jarvis im Hintergrund weiter. Wird der Browser neu geladen, synchronisiert ein einzelner `init`-Handshake den Zustand in unter 15 Millisekunden.
- **Zero-Trust für LLM-Tool-Calls:** Die KI erhält niemals ungeprüften Zugriff auf den Host. Jeder Shell-Befehl läuft in einem isolierten Bubblewrap-Container mit Whitelist-Prüfung. Irreversible System-Befehle (Shutdown, Reboot) erfordern ein physisches Hardware-Gate im HUD.
- **Ressourceneffizienz:** Audio wird direkt im C-Space via PipeWire/sounddevice gestreamt. Telemetrie wird auf 60 Hz gedrosselt, um den JavaScript-Event-Loop nicht mit Müll zu fluten.

---

## 2. Gesamtsystem-Architektur (Full-Stack ASCII Übersicht)

```text
+====================================================================================================+
|                                    LINUX DESKTOP (CachyOS / Wayland)                               |
+====================================================================================================+
|                                                                                                    |
|   +------------------------------------+             +-----------------------------------------+   |
|   |        PyQt6 HUD Manager           |             |         Next.js 15 / React 19 Client    |   |
|   |           (manager.py)             |             |            (Port 3000 / Chromium)       |   |
|   |  - TCP Port Monitor (8765 / 3000)  |             |  - Three.js WebGL Hologram (ApexWorld)  |   |
|   |  - Autostart (.config/autostart)   |             |  - Cyberpunk HUD Modals & DevConsole    |   |
|   |  - Non-Destructive Git Updater     |             |  - Audio Level Reactivity (60 FPS)      |   |
|   +-----------------+------------------+             +--------------------+--------------------+   |
|                     |                                                     |                        |
|                     | Subprocess / Socket Check                           | WebSocket JSON / RPC   |
|                     v                                                     v                        |
|   +============================================================================================+   |
|   |                        PYTHON BACKEND CORE (backend/server.py : 8765)                      |   |
|   +============================================================================================+   |
|   |                                                                                            |   |
|   |  +------------------------------+  +-------------------------+  +-----------------------+  |   |
|   |  |     GeminiLiveController     |  |     ActionRegistry      |  |     AudioStreamer     |  |   |
|   |  |   (core/gemini_live.py)      |  |  (core/action_loader)   |  | (core/audio_streamer) |  |   |
|   |  | - google-genai SDK 3.1 Flash |  | - Auto-Discovery        |  | - 16kHz In / 24kHz Out|  |   |
|   |  | - GoAway / Resumption Handle |  | - OpenAPI Sanitizer     |  | - PipeWire Ringbuffer |  |   |
|   |  | - Live Persona Hot-Reload    |  | - json_repair Handler   |  | - Paranoia Killswitch |  |   |
|   |  +--------------+---------------+  +------------+------------+  +-----------+-----------+  |   |
|   |                 |                               |                            |                 |   |
|   |                 | Function Call                 | Tool Dispatch              | PCM Audio Stream|
|   |                 v                               v                            v                 |   |
|   |  +------------------------------+  +-------------------------+  +-----------------------+  |   |
|   |  |    Hardware Safety Gate      |  | Bubblewrap Sandbox Core |  |  PipeWire Audio Sinks |  |   |
|   |  |      (core/confirm.py)       |  |   (core/sandbox.py)     |  |   (wpctl / PulseAudio)|  |   |
|   |  | - 90s Blocking Async Future  |  | - Whitelist Validierung |  |                       |  |   |
|   |  | - UI Bestätigungs-Broadcast  |  | - Zero-Escape Guards   |  |                       |  |   |
|   |  +------------------------------+  +------------+------------+  +-----------------------+  |   |
|   |                                                 |                                              |   |
|   |                                                 v                                              |   |
|   |                                  +------------------------------+                              |   |
|   |                                  |     14 Modulare Actions      |                              |   |
|   |                                  |     (backend/actions/*.py)   |                              |   |
|   |                                  +--------------+---------------+                              |   |
|   |                                                 |                                              |   |
|   +=================================================|==============================================+   |
|                                                     |                                                  |
|                                                     v                                                  |
|   +--------------------------------------------------------------------------------------------+       |
|   |                                PERSISTENTE SPEICHER-SCHICHTEN                              |       |
|   |  - SQLite (calendar.db via PRAGMA wal_checkpoint & VACUUM INTO Snapshot)                   |       |
|   |  - LanceDB (lancedb_data/ Vektordatenbank für semantische Ähnlichkeitssuche)              |       |
|   |  - JSON (long_term.json Fakten, graph_nodes.json 3D-Knoten, sandbox_config.json Whitelist) |       |
|   |  - Systemdirektiven (SOUL.md Identität, MEMORY.md Notizen, HEARTBEAT.md Checkliste)        |       |
|   +--------------------------------------------------------------------------------------------+       |
|                                                     |                                                  |
|                                                     v                                                  |
|   +--------------------------------------------------------------------------------------------+       |
|   |                         ISOLIERTER BUBBLEWRAP (bwrap) NAMESPACE                            |       |
|   |  - Systemdateien: /usr, /lib, /bin (STRIKT READ-ONLY via --ro-bind / /)                    |       |
|   |  - Temporär: RAM-basiertes flüchtiges /tmp (via --tmpfs /tmp)                              |       |
|   |  - Beschreibbar: Ausschließlich Whitelist-Pfade (backend/sandbox_workspace/)              |       |
|   |  - Prozessbaum: Neuer PID- & IPC-Namespace, stirbt automatisch (--die-with-parent)        |       |
|   +--------------------------------------------------------------------------------------------+       |
+====================================================================================================+
```

---

## 3. Interne Interface Definition Language (IDL) & WebSocket-RPC-Protokoll

Die Kommunikation zwischen Next.js Frontend und Python Backend erfolgt über ein strukturiertes, typisiertes JSON-RPC-Protokoll auf Port `8765`.

### 3.1 Client ➔ Server (Frontend Befehle)

| Message Type | Parameter | Zweck / Verhalten im Backend |
| :--- | :--- | :--- |
| `text_command` | `{ text: string }` | Sendet einen Textprompt direkt in den Gemini Live WebSocket Stream. |
| `interrupt` | `{}` | Bricht die laufende KI-Sprachausgabe sofort ab und leert Audio-Puffer. |
| `toggle_mic` | `{ active?: boolean }` | Schaltet das Mikrofon stumm oder aktiv. Broadcastet `mute_state`. |
| `mute_toggle` | `{}` | Invertiert den aktuellen Stummschaltzustand des Mikrofons. |
| `confirm_resolve` | `{ accepted: boolean }` | Löst das anstehende Safety-Gate (`confirm.py`) auf. |
| `undo` | `{}` | Macht die letzte Dateioperation aus dem `undo_stack` rückgängig. |
| `trigger_tool` | `{ tool: string, params: object }` | Manuelle Test-Ausführung eines Tools über die DevConsole. |
| `set_api_key` | `{ key: string }` | Speichert Gemini API Key persistent in `.env` & stößt Neuinitialisierung an. |
| `get_api_key_status` | `{}` | Fordert aktuellen Key-Status an (gibt nur maskierte Version zurück). |
| `set_voice` | `{ voice: string }` | Dynamischer Stimmenwechsel (Puck, Aoede, Charon, Kore, Fenrir) ohne Neustart. |
| `get_graph` | `{}` | Fordert vollständige 3D-Knotendaten (`graph_nodes.json`) an. |
| `add_node` | `{ node: GraphNode }` | Fügt dem 3D-Wissensgraphen einen neuen Knoten hinzu. |
| `delete_node` | `{ node_id: string }` | Entfernt einen Knoten und zugehörige Links aus dem Graphen. |
| `list_backups` | `{}` | Listet alle im Verzeichnis `backend/backups/` vorhandenen ZIP-Dateien auf. |
| `create_backup` | `{ label?: string }` | Erstellt ein transaktionssicheres Brain-Vault Backup. |
| `download_backup` | `{ filename: string }` | Sendet die Backup-ZIP Base64-codiert für den Browser-Download. |
| `delete_backup` | `{ filename: string }` | Löscht ein altes Backup-Archiv von der Festplatte. |
| `restore_backup` | `{ filename: string }` | Stellt das System aus einem lokalen Backup-Archiv wieder her. |
| `upload_restore_brain` | `{ filename: string, data_base64: string }` | Lädt eine externe ZIP hoch und führt einen Hot-Restore durch. |
| `get_calendar_events` | `{}` | Holt anstehende Kalender-Ereignisse aus `calendar.db`. |
| `create_calendar_event` | `{ title, start_time, ... }` | Trägt ein neues Ereignis in die relationale SQLite-Tabelle ein. |
| `delete_calendar_event` | `{ event_id: number }` | Löscht ein Ereignis aus der Datenbank. |
| `trigger_briefing` | `{}` | Triggert das autonome Tages-Briefing der KI. |
| `get_sandbox_config` | `{}` | Fragt Whitelist-Pfade und OS-Vollzugriff-Status ab. |
| `set_full_os_access` | `{ enabled: boolean }` | Toggled temporären Vollzugriff & stößt `reload_personality()` an. |
| `add_sandbox_path` | `{ path: string }` | Fügt einen Host-Pfad zur Whitelist hinzu & aktualisiert Systemprompt. |
| `remove_sandbox_path` | `{ path: string }` | Entfernt einen Pfad aus der Whitelist & aktualisiert Systemprompt. |

---

### 3.2 Server ➔ Client (Backend Broadcasts)

| Message Type | Payload-Struktur | Taktung / Auslöser |
| :--- | :--- | :--- |
| `init` | `{ ai_name, state, actions, telemetry, graph_data, sandbox_config, ... }` | Einmalig bei jedem neuen WebSocket Connect. |
| `telemetry` | `{ data: TelemetryData, can_undo: bool, undo_peek: str, actions: [] }` | Gedrosselt auf 1 Hz (psutil CPU/RAM/GPU). |
| `audio_level` | `{ level: number, speaking: boolean }` | **Gedrosselt auf 60 Hz** via `TelemetryThrottler` (~16.6 ms). |
| `state` | `{ state: "OFFLINE" \| "ONLINE" \| "LISTENING" \| "THINKING" \| ... }` | Zustandswechsel der Gemini Live Session. |
| `chat_message` | `{ speaker: "YOU" \| "JARVIS", text: string, ts: string }` | Nach jedem abgeschlossenen Turn (Sprache/Text). |
| `log` | `{ speaker: "SYS" \| "YOU" \| "JARVIS" \| "ERR", text: string, ts: string }` | Live-Stream für DevConsole und Audit-Log. |
| `confirm_request` | `{ key: string, label: string, detail: string, timeout: number }` | Ausgelöst durch `confirm.py` bei Hochrisiko-Aktionen. |
| `confirm_resolved`| `{ accepted: boolean, executed: boolean }` | Bestätigung oder Abbruch des Safety-Gates. |
| `graph_updated` | `{ graph_data: GraphData }` | Nach Hinzufügen/Löschen von Knoten im Wissensnetz. |
| `calendar_events_updated` | `{ events: CalendarEvent[] }` | Nach Terminerstellung oder -löschung. |
| `sandbox_config_updated` | `{ allowed_paths: string[], full_os_access: boolean }` | Nach jeder Pfadänderung in der Sandbox-Matrix. |

---

## 4. End-to-End Datenflüsse & Sequenzdiagramme (ASCII)

### 4.1 Vollduplex Audio & Voice-Streaming Pipeline

```text
User Stimme ──► Mikrofon
                    │
                    ▼
          sounddevice.InputStream (16 kHz, 16-Bit Mono PCM)
                    │
                    ├─────────────────────────────────────────────────┐
                    │ Raw PCM Frames                                  │ RMS Lautstärke
                    ▼                                                 ▼
        AudioStreamer.audio_out_queue                       TelemetryThrottler (60 Hz)
                    │                                                 │
                    ▼                                                 ▼ (ws_broadcast)
        GeminiLiveController._send_audio_loop()             Next.js Frontend (ApexWorld)
                    │                                                 │
                    ▼ (types.Blob mime="audio/pcm")                   ▼
        Google Gemini Live WebSocket                       Shader Glow & Particles pulsieren
                    │
                    ▼ Model Synthese (24 kHz PCM)
        GeminiLiveController._receive_loop()
                    │
                    ▼
        AudioStreamer.audio_in_queue
                    │
                    ▼
          sounddevice.OutputStream (24 kHz, 16-Bit Mono PCM)
                    │
                    ▼
          PipeWire / ALSA Lautsprecher ──► User hört Antwort
```

---

### 4.2 Tool-Call Execution Loop mit Confirmation Gate & Sandbox

```text
Google Gemini Live API
      │
      ▼ (ToolCall: name="execute_sandboxed_shell", args={command: "cat /etc/shadow"})
GeminiLiveController._receive_loop()
      │
      ▼ ActionRegistry.run(name, args, ctx)
ActionLoader (core/action_loader.py)
      │
      ├─► [Ist Aktion destruktiv? (z.B. Shutdown / Reboot)]
      │        │
      │        ├─► JA ──► confirm.py (Safety Gate) ──► ConfirmBanner im Frontend
      │        │                │
      │        │                ├─► User klickt "BESTÄTIGEN" ──► Fortfahren
      │        │                └─► User klickt "ABBRECHEN"  ──► Abbruch
      │        │
      │        └─► NEIN ──► Direkt weiter
      │
      ▼
actions/sandboxed_shell.py
      │
      ▼ execute_sandboxed(command, cwd)
core/sandbox.py:
      │
      ├─► is_path_allowed(cwd)
      │        │
      │        ├─► [Pfad nicht in Whitelist & kein OS-Vollzugriff?]
      │        │        │
      │        │        ▼
      │        │   Hart blockiert: Exit-Code 1 ("⛔ Sandbox-Schutz verweigert")
      │        │
      │        └─► [Pfad erlaubt?] ──► Fortfahren
      │
      ├─► shutil.which("bwrap")
      │        │
      │        ├─► [bwrap fehlt?] ──► Hart blockiert: Exit-Code 126 (KEIN Host-Fallback!)
      │        │
      │        └─► [bwrap vorhanden]
      │                 │
      │                 ▼
      │            bwrap --unshare-all --ro-bind / / --bind <allowed> ...
      │                 │
      │                 ▼
      │            Linux Kernel Container Namespace
      │                 │
      │                 ▼
      │            Befehl ausgeführt (Exit-Code, Stdout, Stderr)
      │
      ▼ types.FunctionResponse(name, response={"result": str})
GeminiLiveController.send_tool_response()
      │
      ▼
Google Gemini Live API ──► Sprachliche Zusammenfassung im selben Voice-Turn
```

---

### 4.3 60Hz Telemetrie- & Shader-Synchronisation

```text
Linux Kernel (/proc/stat, psutil, sensors)
      │
      ▼ 1 Hz Loop (backend/server.py: telemetry_loop)
actions/system_monitor.py: get_system_telemetry()
      │
      ▼ Broadcast {"type": "telemetry", "data": ...}
Next.js Client (lib/websocket.ts: socketManager)
      │
      ├─► DevConsole.tsx: Telemetrie-Balken (CPU Cores, RAM GB, GPU Watt)
      ├─► BottomDock.tsx: Status-Ampel & Ressourcen-Badges
      │
AudioStreamer RMS Pegel (backend/core/audio_streamer.py)
      │
      ▼ 60 Hz Loop (TelemetryThrottler: 16.6ms Frame-Budget)
Broadcast {"type": "audio_level", "level": float}
      │
      ▼ Next.js Client: onAudioLevel(level)
ApexWorld.tsx (Three.js WebGL Renderloop)
      │
      ├─► uGlowIntensity = baseGlow + audioLevel * 1.5
      ├─► uPulseRate = basePulse + audioLevel * 3.0
      ├─► Gyroskop-Ringe rotieren proportional zu Audio-RMS
      └─► Partikel-Ströme beschleunigen entlang der Bézier-Kurven
```

---

## 5. Frontend Deep-Dive: Next.js 15 & Three.js WebGL Hologramm

Das Frontend (`frontend/`) ist als reaktive, cybernetische Leitstelle konzipiert. Es verbindet Next.js 15 (App-Router) mit einer nativen Three.js WebGL-Szene ohne Zwischenschicht oder Render-Overhead.

### 5.1 Volumetrische Fresnel-Shader & GPU-Pipeline

Im Gegensatz zu standardmäßigen 2D-Canvas-Graphen rendert [`frontend/components/ApexWorld.tsx`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/frontend/components/ApexWorld.tsx) jeden Wissensknoten als echte 3D-Geometrie mit maßgeschneiderten GLSL-Shadern:

```glsl
// Fresnel Vertex Shader (ApexWorld.tsx)
varying vec3 vNormal;
varying vec3 vViewPosition;

void main() {
  vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
  vNormal = normalize(normalMatrix * normal);
  vViewPosition = -mvPosition.xyz;
  gl_Position = projectionMatrix * mvPosition;
}

// Fresnel Fragment Shader (ApexWorld.tsx)
uniform vec3 uColor;
uniform float uTime;
uniform float uPulseRate;
uniform float uGlowIntensity;
varying vec3 vNormal;
varying vec3 vViewPosition;

void main() {
  vec3 normal = normalize(vNormal);
  vec3 viewDir = normalize(vViewPosition);
  float fresnel = dot(normal, viewDir);
  fresnel = clamp(1.0 - fresnel, 0.0, 1.0);
  fresnel = pow(fresnel, 2.5);

  float pulse = sin(uTime * uPulseRate) * 0.5 + 0.5;
  vec3 finalColor = uColor * (fresnel * uGlowIntensity + pulse * 0.25);
  gl_FragColor = vec4(finalColor, fresnel * 0.95);
}
```

**Effekt:** Die Sphären leuchten holografisch an ihren Kanten auf, reagieren in Echtzeit auf den Blickwinkel der Kamera und pulsieren im Rhythmus von Jarvis' Stimme.

---

### 5.2 Szenengraph, Gyroskop-Ringe & Zero-Allocation Raycasting

1. **Gyroskop-Orbitringe:**
   - Jeder Hub-Knoten (`isHub: true`) wird von zwei orthogonalen Torus-Ringen (`THREE.TorusGeometry`) umschlossen.
   - Im Render-Loop werden diese Ringe unabhängig voneinander um die X- und Y-Achse rotiert, was den futuristischen Gyroskop-Effekt erzeugt.
2. **Gekrümmte Bézier-Datenströme:**
   - Verbindungen zwischen Knoten werden nicht als starre Linien gerendert, sondern als `THREE.QuadraticBezierCurve3`.
   - Auf diesen Kurven bewegen sich volumetrische `DataPacket`-Sprites, deren Fluggeschwindigkeit mit der Systemaktivität skaliert.
3. **Zero-Allocation Raycasting:**
   - Beim Bewegen der Maus über den 3D-Raum werden keine neuen `THREE.Vector3` oder `THREE.Raycaster` Instanzen erzeugt.
   - Alle Berechnungen verwenden vorinitialisierte Klassenvariablen – das verhindert Ruckler durch den Browser Garbage Collector selbst bei 144 Hz Bildwiederholrate.

---

### 5.3 HUD-Komponenten- & Fenster-Matrix

Das Interface ist vollständig modular aufgebaut. Alle Fenster sind frei verschiebbar und in der Größe anpassbar:

- **[`DevConsole.tsx`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/frontend/components/DevConsole.tsx):**
  - Live-Stream aller System- und Tool-Aufrufe mit Farbkennzeichnung (`SYS`=Cyan, `YOU`=Grün, `JARVIS`=Gelb, `ERR`=Rot).
  - Integrierte Systemmetriken: Live-Balken für CPU-Cores, RAM, GPU-Auslastung und VRAM.
  - Manuelle Tool-Triggering Schnittstelle zum isolierten Testen einzelner Backend-Actions.
- **[`JarvisChatWindow.tsx`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/frontend/components/JarvisChatWindow.tsx):**
  - Vollständiger Konversationsverlauf zwischen Nutzer und KI mit Zeitstempeln.
  - Visueller Audio-Equalizer, der die aktuelle Sprachaktivität anzeigt.
- **[`BottomDock.tsx`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/frontend/components/BottomDock.tsx):**
  - Zentrale Steuerleiste im Stil eines Cyberpunk-Docks.
  - Mikrofon-Schalter (Handsfree/Mute), Fenster-Umschalter, Status-Ampel (`ONLINE`/`THINKING`) und roter Not-Aus Killswitch.
- **[`CalendarModal.tsx`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/frontend/components/CalendarModal.tsx):**
  - Relationale Kalender-Matrix mit Monats-, Wochen- und Tagesansicht.
  - Farbcodierte Prioritäten, Terminkonflikt-Warnung und Direktverbindung zur `calendar.db`.
- **[`BackupModal.tsx`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/frontend/components/BackupModal.tsx):**
  - Brain Vault Management: 1-Klick Backup-Erstellung mit Labels, ZIP-Download in den Browser, Liste aller archivierten Snapshots und Drag-and-Drop Datei-Upload für Hot-Restores.
- **[`SandboxModal.tsx`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/frontend/components/SandboxModal.tsx):**
  - Sicherheitsmatrix: Verwalten der erlaubten Pfade (Hinzufügen, Entfernen) und Schalter für temporären OS-Vollzugriff mit optischer Warnanzeige.
- **[`ConfirmBanner.tsx`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/frontend/components/ConfirmBanner.tsx):**
  - Hardware Safety Gate: Blockierender Banner bei gefährlichen Aktionen mit Live-Countdown (90s).

---

### 5.4 Resiliente WebSocket State Machine (`frontend/lib/websocket.ts`)

Der `JarvisSocketManager` ist ein robuster Singleton, der den Verbindungsstatus verwaltet:

```text
[OFFLINE] ──► connect() ──► [CONNECTING] ──► onopen ──► [ONLINE]
    ▲                             │                         │
    │                             ▼ onerror                 ├─► [LISTENING] (User spricht)
    │                        [ERROR]                        ├─► [THINKING]  (Tool läuft)
    │                             │                         ├─► [SPEAKING]  (Audio läuft)
    └────────── onclose ──────────┴◄── scheduleReconnect() ─┴─► [CONFIRM]   (Gate aktiv)
```

**Exponential Backoff mit Jitter:**
- Basisverzögerung: `1000 ms`, Maximalverzögerung: `15.000 ms`.
- Bei jedem Fehlversuch multipliziert mit `1.8^factor` plus Zufalls-Jitter (0–500 ms).
- Verhindert Verbindungsstürme auf dem lokalen Port.

---

## 6. Backend Deep-Dive: AsyncIO Core & Sicherheit

Das Backend (`backend/`) ist in modernem Python 3.12+ / 3.14 rein asynchron auf Basis von `asyncio` und `websockets` implementiert.

### 6.1 Server & Connection Pooling (`backend/server.py`)

- **Host & Port:** `127.0.0.1:8765` (konfigurierbar via `JARVIS_WS_HOST` und `JARVIS_WS_PORT`).
- **TelemetryThrottler:**
  ```python
  class TelemetryThrottler:
      def __init__(self, target_hz: int = 60):
          self.interval = 1.0 / target_hz  # ~16.6 ms
          self.last_sent = 0.0

      def should_send(self, now: float) -> bool:
          if (now - self.last_sent) >= self.interval:
              self.last_sent = now
              return True
          return False
  ```
- **Connection Handshake:** Jeder neue Client erhält sofort das aggregierte Begrüßungspaket mit allen verfügbaren Tools, Kalenderdaten, Wissensknoten und Sicherheitsgrenzen.

---

### 6.2 Gemini Live Voice Controller (`backend/core/gemini_live.py`)

- **Modell:** `models/gemini-3.1-flash-live-preview` über das offizielle `google-genai` SDK.
- **Vollduplex-Audio:**
  - `_send_audio_loop()` holt Chunks aus der Audio-Out-Queue und sendet sie als `types.Blob(mime_type="audio/pcm")`.
  - `_receive_loop()` nimmt synthetisierte 24 kHz Audio-Frames entgegen und legt sie in die Wiedergabe-Queue.
- **Session-Resumption & GoAway (Code 1008):**
  - Fängt Google GoAway-Signale und Session-Timeouts sauber ab.
  - Übernimmt den `resumption_handle`, um die Konversation unterbrechungsfrei fortzusetzen.
- **Live Hot-Reload:**
  - Wird `reload_personality()` aufgerufen, bricht der Controller die alte WebSocket-Verbindung ab und initialisiert die Session mit dem aktualisierten Systemprompt transparent neu.

---

### 6.3 Bubblewrap Sandbox & Zero-Escape Isolation (`backend/core/sandbox.py`)

Die Bubblewrap-Integration riegelt das Dateisystem und den Prozessbaum hermetisch ab:

```text
Whitelist-Verwaltung:
config/sandbox_config.json
  ├── Optimierte-PERSONAS
  ├── FÜRJARVIS
  ├── jarvistestlauf
  └── backend/sandbox_workspace (Standard-Schreibordner)
```

**Sicherheitsregeln in `core/sandbox.py`:**
1. **Pfad-Normalisierung:** Pfade werden mit Unicode-NFC normalisiert, per `os.path.expanduser()` aufgelöst und mit `Path.resolve()` geprüft. Symlink-Escapes und relative Traversal (`../../etc`) werden unweigerlich erkannt.
2. **Strikte Verweigerung ohne Host-Fallback:** Wenn `bwrap` nicht installiert ist oder fehlschlägt, gibt es **keinen ungesicherten Host-Fallback**. Der Befehl wird mit Exit-Code `126` hart abgebrochen.
3. **Arbeitsverzeichnis-Prüfung:** Das übergebene `cwd` muss zwingend innerhalb der freigegebenen Whitelist liegen. Ein Aufruf mit `cwd='/etc'` wird mit Exit-Code `1` verweigert.
4. **Subprozess-Isolation:** `--unshare-all`, `--ro-bind / /`, `--tmpfs /tmp`, `--proc /proc`, `--dev /dev`, `--die-with-parent` und `--new-session` verhindern Ausbrüche und verwaiste Prozesse.
5. **AI-Direktiven:** `format_sandbox_directive_for_prompt()` generiert bindende Verhaltensregeln, die direkt in den Gemini-Prompt injiziert werden.

---

### 6.4 Tool-Discovery & OpenAPI Typ-Sanitizer (`backend/core/action_loader.py`)

- Durchsucht das Verzeichnis `backend/actions/` dynamisch nach Modulen mit `TOOL` oder `TOOLS`.
- **`sanitize_schema_for_gemini(schema)`:**
  - Entfernt nicht-konforme Felder wie `$schema`, `$id`, `definitions`, `additionalProperties` und `allOf`.
  - Wandelt Pydantic/OpenAPI `anyOf`/`oneOf` Typen in saubere Basistypen (`OBJECT`, `STRING`, `INTEGER`, `NUMBER`, `BOOLEAN`, `ARRAY`) mit `nullable: True` um.
  - Schützt die Gemini Live API vor Schema-Validierungsfehlern.

---

### 6.5 PipeWire Audio Streamer (`backend/core/audio_streamer.py`)

- Basiert auf `sounddevice` und verbindet sich nativ mit PipeWire / ALSA.
- **Aufnahme:** 16.000 Hz Mono PCM (optimiert für Spracherkennung).
- **Wiedergabe:** 24.000 Hz Mono PCM (Standard-Ausgabe von Gemini Live).
- **Paranoia-Mute:** Physischer Hardware-Stummschalter im Backend – verwirft Audio-Frames sofort, bevor sie in irgendeine Queue oder das Netzwerk gelangen.

---

### 6.6 Brain Vault Backup-Engine & SQLite WAL Snapshot (`backend/core/backup_manager.py`)

- **Konsistente SQLite-Snapshots:**
  - Führt vor dem Backup ein `PRAGMA wal_checkpoint(TRUNCATE);` aus.
  - Erstellt mit `VACUUM INTO '<snapshot>'` eine konsistente, ungesperrte Kopie von `calendar.db`, selbst während Schreiboperationen laufen.
- **Archivierung:**
  - Packt `long_term.json`, `calendar.db`, `lancedb_data/`, `graph_nodes.json`, `mcp_servers.json`, `SOUL.md`, `MEMORY.md` und `HEARTBEAT.md` in ein ZIP-Archiv.
- **Zip-Slip Schutz beim Restore:**
  - Prüft jeden Zielpfad strikt mit `target.is_relative_to(extract_dir)`, um Path-Traversal Angriffe durch manipulierte ZIP-Dateien abzuwehren.

---

### 6.7 Hardware Safety Confirmation Gate (`backend/core/confirm.py`)

- Blockiert irreversible Systemaktionen (z. B. `systemctl poweroff`, `reboot`, rekursive Massenlöschungen).
- Registriert ein asynchrones `asyncio.Future` mit einem 90-Sekunden Timeout.
- Sendet `confirm_request` an das Frontend.
- Erst wenn der Nutzer im `ConfirmBanner` explizit bestätigt, wird die Aktion freigegeben; andernfalls wird sie sicher verworfen.

---

### 6.8 Multi-Tier Gedächtnissystem (`backend/memory/`)

```text
+----------------------------------------------------------------------------------------------------+
| 1. EPISODISCHER SPEICHER: Aktive Gemini Live Konversation (Flüchtig, In-Session)                  |
+----------------------------------------------------------------------------------------------------+
| 2. DEKLARATIVER SPEICHER: backend/memory/long_term.json (Fakten, Hardware, Nutzerpräferenzen)      |
+----------------------------------------------------------------------------------------------------+
| 3. RELATIONALER SPEICHER: backend/memory/calendar.db (SQLite Termine, Start-/Endzeit, Priorität)  |
+----------------------------------------------------------------------------------------------------+
| 4. SEMANTISCHER SPEICHER: backend/memory/lancedb_data/ (LanceDB Vektoren für Ähnlichkeitssuche)    |
+----------------------------------------------------------------------------------------------------+
| 5. STRUKTURELLER SPEICHER: backend/knowledge_base/graph_nodes.json (3D Hologramm Wissensnetz)     |
+----------------------------------------------------------------------------------------------------+
| 6. IDENTITÄTS-SPEICHER: backend/config/SOUL.md, MEMORY.md, HEARTBEAT.md                           |
+----------------------------------------------------------------------------------------------------+
```

---

## 7. Vollständiger Werkzeug-Katalog (Alle 14 Actions im Detail)

| Modul | Registriertes Tool | Parameter | Beschreibung & Systemverhalten |
| :--- | :--- | :--- | :--- |
| [`sandboxed_shell.py`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/backend/actions/sandboxed_shell.py) | `execute_sandboxed_shell` | `command` (str, req), `working_dir` (str, opt) | Führt Shell-Befehle isoliert via Bubblewrap aus. Erzwingt Whitelist-Pfade. Verweigert Host-Fallback. |
| [`file_controller.py`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/backend/actions/file_controller.py) | `file_controller` | `action` (str, req), `path` (str), `content` (str), `destination` (str) | Operationen (`read`, `write`, `delete`, `move`, `list`, `organize_desktop`). Relative Pfade landen in `sandbox_workspace`. Unterstützt Undo. |
| [`calendar_manager.py`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/backend/actions/calendar_manager.py) | `calendar_manager`, `create_calendar_entry` | `action`, `title`, `start_time`, `end_time`, `priority`, `tags` | Verwaltet Termine in `calendar.db`. Erkennt Terminkonflikte und berechnet relative Zeiträume. |
| [`graph_manager.py`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/backend/actions/graph_manager.py) | `get_graph_data`, `add_graph_node`, `delete_graph_node` | `node_id`, `name`, `category`, `description` | Manipuliert das 3D Three.js Wissensnetzwerk live. Synchronisiert sofort mit dem WebGL-Canvas. |
| [`system_monitor.py`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/backend/actions/system_monitor.py) | `get_system_status` | `detailed` (bool, opt) | Fragt Live-Telemetrie ab: CPU pro Kern, RAM, Swap, Festplatte, GPU-Thermals und Sensoren. |
| [`screen_processor.py`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/backend/actions/screen_processor.py) | `capture_screen` | `monitor` (str, opt) | Erstellt Wayland-Screenshots via `grim` oder `spectacle` für die visuelle Analyse durch die KI. |
| [`computer_settings.py`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/backend/actions/computer_settings.py) | `adjust_computer_settings` | `setting_type`, `value` | Steuert System-Lautstärke (`wpctl`), Audio-Sinks und Bildschirm-Helligkeit (`brightnessctl`). |
| [`open_app.py`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/backend/actions/open_app.py) | `open_application` | `app_name` (str, req) | Startet installierte Linux-Programme unprivilegiert via `gtk-launch` oder `xdg-open`. |
| [`recall_memory.py`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/backend/actions/recall_memory.py) | `recall_memory`, `store_memory` | `query`, `fact`, `category` | Liest und speichert Fakten in `long_term.json` und der LanceDB Vektordatenbank. |
| [`reminder.py`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/backend/actions/reminder.py) | `set_reminder` | `message` (str, req), `seconds` (int, req) | Richtet asynchrone Timer und Erinnerungen im Hintergrund ein. |
| [`backup_agent.py`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/backend/actions/backup_agent.py) | `manage_backups` | `action` (`create`, `list`, `restore`), `label` | Steuert das Brain Vault Backup-System direkt über Sprach- oder Textbefehle. |
| [`undo_action.py`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/backend/actions/undo_action.py) | `undo_last_action` | `{}` | Macht die letzte Datei-Aktion (Schreiben, Verschieben, Löschen) sofort rückgängig. |
| [`update_agent.py`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/backend/actions/update_agent.py) | `check_for_updates`, `perform_self_update` | `{}` | Prüft Remote-Git-Commits und führt kontrollierte Self-Updates via Git durch. |
| [`manage_mcp.py`](file:///home/graba/Schreibtisch/ASGRAD/Valhalla/TOOLS/GRABAS_GITHUB/webjarvis/backend/actions/manage_mcp.py) | `manage_mcp_servers` | `action`, `server_id`, `config` | Verwaltet externe Model Context Protocol (MCP) Server und deren Werkzeug-Bridges. |

---

## 8. Desktop Orchestration & Manager GUI (`manager.py` & Shell)

### 8.1 PyQt6 Cyberpunk HUD Manager (`manager.py`)

- **Rolle:** Native Linux Desktop-Leitstelle für System-Maintenance.
- **Port-Auditor:** Prüft non-blocking via TCP-Sockets, ob Port 8765 (Backend) und Port 3000 (Frontend) aktiv sind.
- **Git Self-Update:** Führt einen non-destruktiven Remote-Check durch (`git ls-remote origin main`), vergleicht Commits und bietet sichere Updates per Knopfdruck.
- **Autostart-Integration:** Erstellt oder entfernt die `.desktop`-Datei in `~/.config/autostart/webjarvis.desktop`.
- **Desktop-Pet Anbindung:** Startet und überwacht das native PyQt6 Desktop Companion Pet (`webjarvis_petaddon`).

---

### 8.2 Shell-Orchestrierungs-Skripte

```text
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    run.sh    ├───► │   start.sh   ├───► │   stop.sh    │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
               ┌────────────┴────────────┐
               ▼                         ▼
      Backend Daemon (8765)      Frontend Next.js (3000)
```

- **`start.sh`:** Prüft Venv, Abhängigkeiten, PipeWire und Port-Kollisionen. Startet Backend und Frontend parallel und fängt `EXIT`, `INT` und `TERM` mit einem sauberen Cleanup-Trap ab.
- **`stop.sh`:** Sendet gezielte `SIGTERM`-Signale an die registrierten PIDs und gibt belegte Ports sauber frei.
- **`restart.sh`:** Schneller Dienst-Neustart ohne OS-Reboot.
- **`terminate_jarvis.sh`:** Not-Aus / Killswitch mit `kill -9` auf alle zugehörigen Prozess-Instanzen.

---

## 9. Vollständiger Verzeichnis- & Dateibaum

```text
webjarvis/
├── assets/                               # Visuelle Assets & Branding
│   ├── jarvis-manager.png                # Icon für PyQt6 Manager
│   └── jarvis-manager.svg                # Vektor-Icon für Desktop-Launcher
│
├── backend/                              # Python 3.12+ Backend Core
│   ├── actions/                          # 14 Modulare Action-Werkzeuge
│   │   ├── backup_agent.py               # Brain-Vault Tool
│   │   ├── calendar_manager.py           # SQLite-Kalender Tool
│   │   ├── computer_settings.py          # Lautstärke & Helligkeit Tool
│   │   ├── file_controller.py            # Dateimanager Tool mit Undo
│   │   ├── graph_manager.py              # 3D-Wissensgraph Tool
│   │   ├── jarvis_control.py             # Systembefehle & Mute Tool
│   │   ├── manage_mcp.py                 # MCP Server Tool
│   │   ├── open_app.py                   # Linux App-Starter Tool
│   │   ├── recall_memory.py              # Langzeitgedächtnis Tool
│   │   ├── reminder.py                   # Timer & Erinnerungen Tool
│   │   ├── sandboxed_shell.py            # Bubblewrap Shell Tool
│   │   ├── screen_processor.py           # Screenshot & Vision Tool
│   │   ├── system_monitor.py             # Telemetrie-Tool
│   │   ├── undo_action.py                # Undo-Tool
│   │   └── update_agent.py               # Git Self-Update Tool
│   │
│   ├── backups/                          # Lokale Brain Vault ZIP-Archive
│   ├── config/                           # Konfigurationen & Secrets
│   │   ├── api_keys.json                 # Gespeicherte API-Keys & Settings
│   │   ├── api_keys.example.json         # Vorlage für Installation
│   │   ├── contacts.json                 # Adressbuch
│   │   ├── cron_jobs.json                # Persistierte Hintergrund-Tasks
│   │   ├── mcp_servers.json              # Externe MCP-Server Registrierung
│   │   ├── sandbox_config.json           # Whitelist der erlaubten Sandbox-Pfade
│   │   └── SOUL.md                       # Primäre KI-Identität & Direktiven
│   │
│   ├── core/                             # Systemkerne & Controller
│   │   ├── action_loader.py              # Tool-Discovery & OpenAPI Sanitizer
│   │   ├── audio_streamer.py             # PipeWire/ALSA I/O & RMS-Messung
│   │   ├── backup_manager.py             # Brain Vault Engine (VACUUM INTO)
│   │   ├── config.py                     # Pfad-, Audio- & Environment-Verwaltung
│   │   ├── confirm.py                    # Thread-sicheres Safety Gate (Futures)
│   │   ├── cron_engine.py                # Proaktiver Scheduler
│   │   ├── gemini_live.py                # Google GenAI Live Client (Duplex)
│   │   ├── json_repair.py                # LLM JSON Parser & Repair
│   │   ├── mcp_client.py                 # MCP JSON-RPC 2.0 Bridge
│   │   ├── sandbox.py                    # Bubblewrap Prozessisolation & Guards
│   │   └── undo.py                       # Reversibler Dateioperations-Stack
│   │
│   ├── knowledge_base/                   # Wissensnetzwerk
│   │   ├── graph_nodes.json              # Knoten & Kanten für das 3D Hologramm
│   │   └── knowledge_map.json            # Metadaten-Mapping
│   │
│   ├── memory/                           # Gedächtnisspeicher
│   │   ├── calendar.db                   # SQLite Termindatenbank
│   │   ├── lancedb_data/                 # LanceDB Vektordatenbank
│   │   ├── lancedb_manager.py            # Vektordatenbank Treiber
│   │   ├── long_term.json                # Langzeitfakten & Präferenzen
│   │   └── memory_manager.py             # Kontext-Synchronisation
│   │
│   ├── sandbox_workspace/                # Standard-Schreibarbeitsbereich
│   ├── server.py                         # Zentraler WebSocket-Server (Port 8765)
│   ├── requirements.txt                  # Python Abhängigkeiten
│   ├── SOUL.md                           # Fallback-Identitätsdatei
│   ├── MEMORY.md                         # Notizenspeicher
│   └── HEARTBEAT.md                      # Systemzustands-Checkliste
│
├── frontend/                             # Next.js 15 / React 19 Frontend (Port 3000)
│   ├── app/                              # Next.js App Router
│   │   ├── globals.css                   # Cyberpunk HUD Theme & Scanlines
│   │   ├── layout.tsx                    # Root Layout
│   │   └── page.tsx                      # Zentrale Desktop-Oberfläche
│   │
│   ├── components/                       # Reaktive HUD-Komponenten & Modals
│   │   ├── AgentCockpit.tsx              # Status- & Persona-Panel
│   │   ├── ApexOverviewPanel.tsx         # Wissensknoten Detail-Inspector
│   │   ├── ApexWorld.tsx                 # 3D Three.js Hologramm (Fresnel Shader)
│   │   ├── ApiKeyModal.tsx               # API Key Konfiguration
│   │   ├── BackupModal.tsx               # Brain Vault Export/Restore Center
│   │   ├── BottomDock.tsx                # Cyberpunk Dock mit App-Icons
│   │   ├── CalendarModal.tsx             # Relationale Kalender-Matrix
│   │   ├── ConfirmBanner.tsx             # Hardware Safety Confirmation Gate
│   │   ├── ContentStudio.tsx             # Editor für Notizen & Dokumente
│   │   ├── DevConsole.tsx                # Verschiebbare Terminal- & Telemetriekonsole
│   │   ├── DeviceControlPanel.tsx        # System-Lautstärke & Audio-Sinks
│   │   ├── JarvisChatWindow.tsx          # Konversations-Chat mit Transkript
│   │   ├── PersonalityWizardModal.tsx    # SOUL.md Editor & Stimmenauswahl
│   │   ├── SandboxModal.tsx              # Whitelist-Manager & OS-Vollzugriff Toggle
│   │   └── SkillsModal.tsx               # MCP- und Action-Katalog
│   │
│   ├── lib/                              # Frontend Typen & Bibliotheken
│   │   ├── graphData.ts                  # Knotenfarben & Kategorien
│   │   ├── petEngine.ts                  # Desktop Pet Animationen
│   │   ├── petTypes.ts                   # Pet Typdefinitionen
│   │   ├── types.ts                      # TypeScript Interfaces (IDL)
│   │   └── websocket.ts                  # Resilienter WebSocket Manager
│   │
│   ├── package.json                      # Node.js Abhängigkeiten
│   ├── tailwind.config.ts                # Tailwind-CSS Konfiguration
│   └── tsconfig.json                     # TypeScript Konfiguration
│
├── manager.py                            # PyQt6 Desktop Maintenance GUI
├── manager.sh                            # Starter für die PyQt6 GUI
├── run.sh                                # Ergonomischer 1-Click Starter
├── start.sh                              # Linux Master-Orchestrator
├── stop.sh                               # Sauberer SIGTERM-Shutdown
├── restart.sh                            # Dienst-Neustart ohne OS-Reboot
├── setup.sh                              # Installations- & Setup-Skript
├── terminate_jarvis.sh                   # Not-Aus Paranoia Killswitch
├── posting.md                            # Release- & Community-Postings
├── posting-win.md                        # Kurz-Vorstellung für Foren
├── webjarviszustand.md                   # Entwickler- & Architektur-Bibel
├── README.md                             # Internationales Projekthandbuch
└── README_DE.md                          # Ausführliches deutsches Handbuch
```

---

## 10. Sicherheits-, Privilegien- & Sandbox-Matrix

```text
+-----------------------+--------------------+--------------------+----------------------------------+
| Ressource / Bereich   | Standard-Modus     | Vollzugriff aktiv  | Technische Durchsetzung          |
+-----------------------+--------------------+--------------------+----------------------------------+
| Root-Dateisystem      | READ-ONLY          | READ / WRITE       | bwrap --ro-bind / /              |
| Whitelist-Pfade       | READ / WRITE       | READ / WRITE       | bwrap --bind <allowed> <allowed> |
| Systemverzeichnisse   | GESPERRT (/etc,..) | GESPERRT (/etc,..) | is_path_allowed() & bwrap ro     |
| Prozess-Namespace     | ISOLIERT           | ISOLIERT           | bwrap --unshare-all, --proc /proc|
| Verwaiste Prozesse    | VERHINDERT         | VERHINDERT         | bwrap --die-with-parent          |
| TTY-Kapern            | VERHINDERT         | VERHINDERT         | bwrap --new-session              |
| Destruktive Aktionen  | SAFETY-GATE        | SAFETY-GATE        | confirm.py (90s Timeout)         |
| Ungeprüfter Fallback  | VERWEIGERT (126)   | VERWEIGERT (126)   | Kein Ausführen ohne Isolation    |
| Relative Pfade        | GEKAPSELT          | GEKAPSELT          | Standard: sandbox_workspace/     |
+-----------------------+--------------------+--------------------+----------------------------------+
```

---

## 11. Entwickler-Codex: How-To Guides & Best Practices

### 11.1 Neues Backend-Tool erstellen (Das SPS-Prinzip)

1. Neue Datei `backend/actions/meine_action.py` anlegen.
2. Definiere das Schema strikt nach OpenAPI/Gemini-Regeln:
```python
"""backend/actions/meine_action.py"""
from typing import Dict, Any

TOOL = {
    "name": "meine_neue_action",
    "description": "Erkläre präzise, was die Aktion tut. Keine Romane.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "ziel_parameter": {
                "type": "STRING",
                "description": "Zweck des Parameters"
            }
        },
        "required": ["ziel_parameter"]
    }
}

def meine_neue_action(parameters: Dict[str, Any], **kwargs) -> str:
    ziel = str(parameters.get("ziel_parameter", "")).strip()
    if not ziel:
        return "Fehler: Parameter fehlt."
    try:
        # Robuste Logik implementieren...
        return f"Aktion für '{ziel}' erfolgreich ausgeführt."
    except Exception as e:
        return f"Fehler bei Ausführung: {e}"
```
3. `action_loader.py` erkennt das Modul beim nächsten Start vollautomatisch.

---

### 11.2 Neues Frontend-Modal anbinden

1. Modal in `frontend/components/MeinModal.tsx` erstellen.
2. Event-Listener in `frontend/app/page.tsx` verdrahten:
```tsx
const [isMeinModalOpen, setIsMeinModalOpen] = useState(false);

// Im JSX:
{isMeinModalOpen && (
  <MeinModal onClose={() => setIsMeinModalOpen(false)} />
)}
```
3. Icon im `frontend/components/BottomDock.tsx` ergänzen.

---

### 11.3 Schnelle Validierungs-Kommandos für Entwickler

```bash
# 1. Vollständige Python-Syntaxprüfung
PYTHONPATH=backend backend/.venv/bin/python3 -m py_compile backend/server.py backend/core/*.py backend/actions/*.py

# 2. Sandbox- & Sicherheits-Intensivtest
PYTHONPATH=backend backend/.venv/bin/python3 -c "
from core.sandbox import is_path_allowed, execute_sandboxed, DEFAULT_SANDBOX_DIR
assert is_path_allowed(DEFAULT_SANDBOX_DIR)
assert not is_path_allowed('/etc/passwd')
code, out, err, is_sb = execute_sandboxed('echo OK')
assert code == 0 and 'OK' in out
print('SANDBOX TEST: 100% CLEAN!')
"

# 3. Next.js TypeScript- & Build-Check
cd frontend && npm run build
```

---

## 12. ERWEITERUNGEN: TASK ENGINE, KARPATHY-WIKI & 3D GRAPH INTELLIGENCE

### 12.1 SPS Task Backlog Engine (`backlog.md`)
- **Single Source of Truth:** `backend/backlog.md` als reines Markdown-Format (`- [ ]` und `- [x]`).
- **Single-Writer & Atomarität:** `TaskManager` (`backend/core/task_manager.py`) nutzt `threading.RLock()` und POSIX-atomaren Datei-Austausch (`.tmp` + `os.replace`), um Lost Updates und Dateikorruption auszuschließen.
- **Anti-Echo Watcher:** Entprellung externer Dateiedits (Kate/Neovim) über SHA-256 Checksummenvergleich.
- **Frontend HUD:** `frontend/components/BacklogDrawer.tsx` bietet interaktive Checkboxen, Live-Filter (Alle/Offen/Erledigt), Prioritäts-Badges (`[HIGH]`, `[NORMAL]`, `[LOW]`) und Tastatur-Shortcut `Alt+T`.
- **KI-Tool:** `manage_tasks` (`backend/actions/task_manager.py`) ermöglicht Gemini das autonome Hinzufügen, Abhaken und Löschen von Aufgaben.

### 12.2 Karpathy-Muster Knowledge Vault & [[Wiki-Links]]
- **Kuratierte Wissensbasis:** `backend/knowledge_base/wiki/*.md` mit YAML-Frontmatter (`title:`, `updated:`, `tags:`).
- **Immutability:** Rohe Eingaben und Quelltexte verbleiben unveränderlich in `backend/knowledge_base/raw/`.
- **[[Wiki-Links]] Extraktion:** Regex-Parser erfasst Verweise wie `[[Thema]]` und transformiert sie in gerichtete Kanten im 3D-Graphen.
- **Widerspruchs-Erkennung (Zero Data Loss):** Bei widersprüchlichen Fakten überschreibt Jarvis niemals stillschweigend, sondern injiziert einen standardisierten Warnblock:
  `> [!WARNING] Widerspruch erkannt (Timestamp)`
  `> **Neuer Input:** ...`
  `> **Bisheriger Stand:** ...`
  und markiert den Knoten im Graphen mit dem Status `conflict`.
- **Vektor- & Graph-Synchronisation:** Jeder Wiki-Artikel wird automatisch in `graph_nodes.json` sowie im LanceDB-Vektorspeicher indexiert.

### 12.3 3D Graph Frontmatter-Titel & Orphan-Erkennung
- **YAML Frontmatter Title Rendering:** Knoten im 3D-Graph (`ApexWorld.tsx`) heißen nicht mehr generisch nach dem Dateinamen, sondern erhalten ihren echten Titel aus dem Frontmatter.
- **Orphan-Erkennung:** Knoten mit Grad 0 (ohne Kanten) werden als `is_orphan` markiert.
- **Shader Strobe-Pulse & HUD-Alerts:**
  - Knoten mit `is_orphan`: Neon-Amber Fresnel Strobe Pulse im Vertex-/Fragment-Shader und HUD-Badge `⚡ [ORPHAN]`.
  - Knoten mit `conflict`: Crimson-Warnpulsierung und Billboard-Badge `⚠️ [KONFLIKT]`.
  - HUD-Pill im Dock (`BottomDock.tsx`) zeigt die Anzahl aktiver Orphans an; ein Klick fokussiert die 3D-Kamera direkt auf den unverbundenen Knoten.

---
*Ende der Spezifikation — Dokumentiert für das Linux-, SysOps- und Entwickler-Portfolio von @Graba92.*
