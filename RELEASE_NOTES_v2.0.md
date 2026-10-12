# 🚀 WebJarvis v2.0 — Release Notes

**Codename:** Triumvirat Ascendance (Self-Contained Multi-Agent Architecture)  
**Release Date:** Oktober 2026  
**License:** MIT  

---

## 🌟 Übersicht

WebJarvis v2.0 markiert den bisher größten Meilenstein im System: Der vollständige Übergang zu einer **100 % in sich geschlossenen (Self-Contained) Multi-Agenten-Architektur**. Alle Abhängigkeiten, Kommunikationskanäle (Dropzone IPC, UDS), Datenbank-Schemas und Benutzeroberflächen wurden gekapselt, gehärtet und portabel aufbereitet.

---

## 🔑 Kern-Upgrades & Neue Features

### 1. 🛡️ 100 % Self-Contained & Absolute-Path Eradication
- **Vollständige Kapselung:** Sämtliche Subsysteme (`agent_exchange`, `agy_components`, `backend/ipc`, `backend/llm`) befinden sich physisch im WebJarvis-Projektstamm.
- **Dynamische Pfadauflösung:** Keine hardgecodeten Pfade (`/home/...`) mehr im Codebase. Alle Module verwenden relative Pfad-Resolution via `Path(__file__).resolve()` und projektweite Root-Referenzen.
- **Portabilität:** Direkt clonable und auf jedem Linux/Arch/CachyOS-System ohne Pfadkonflikte lauffähig.

### 2. ⚡ High-Speed UDS-IPC Engine (Unix Domain Socket)
- **Zero-TCP-Overhead:** Inter-Agenten-Kommunikation zwischen Friday, AGY und Gemini CLI via `/run/user/1000/friday_ipc.sock`.
- **Sub-Millisekunden-Latenz:** < 1 ms Ausführungszeit für Agenten-RPCs im JSON-RPC 2.0 Standard.
- **Sicherheits-Härtung:** POSIX-Berechtigung `0600` (nur der lokale Systembenutzer hat Zugriff).
- **5 Kern-Werkzeuge integriert:**
  - `cli_executor`: Kontrollierte Befehlsausführung im Benutzerkontext.
  - `file_ops`: Sicheres Lesen, Schreiben und Anhängen von Wissensdateien.
  - `db_query`: Direkte Abfrage der SQLite Knowledge Base.
  - `lance_memory_search`: Semantische Vektorsuche im Langzeitgedächtnis.
  - `agent_exchange_send`: Asynchrone Nachrichtenübermittlung über die Dropzone.

### 3. 🎛️ 6-Panel God-Mode TUI Cockpit (`god_mode_tui.py`)
- **Triumvirat-Überblick auf einen Blick:**
  - **Panel 1 (Top-Left):** AGY Core Engine Status & Host-Telemetrie.
  - **Panel 2 (Top-Right):** Friday Reasoning & Meta-Kognition.
  - **Panel 3 (Mid-Left):** AGY Live Activity Logs.
  - **Panel 4 (Mid-Right):** Friday Wissensgraph & Memory Stream.
  - **Panel 5 (Bottom-Left):** Triumvirat Dropzone Monitor (AGY / Friday / Gemini CLI).
  - **Panel 6 (Bottom-Right):** FTS5 & UDS High-Speed Wissenssuche mit Live-Preview.
- **Interaktiver Command Prompt:** Direkte Steuerung und Prompt-Übergabe an alle drei Agenten.

### 4. 🧠 FTS5 Self-Healing & SQLite Master-Index (`master_index_init.py`)
- **Automatisches Self-Healing:** Bei fehlender, leerer oder korrupter Datenbank rekonstruiert WebJarvis das Tabellenschema (`knowledge_units` und Volltext-Index `knowledge_units_fts`) vollautomatisch beim Server-Start.
- **LIKE-Fallback:** Höchste Zuverlässigkeit selbst auf minimalistischen SQLite-Installationen ohne FTS5-Modul.
- **119+ Wissenseinheiten:** Initialer Wissensbestand (Bible, Architektur, Workflows, Personas) sofort volltextdurchsuchbar.

### 5. 🌐 Brave Browser Web-to-Local Bridge
- **Rechtsklick-Clipping:** Web-Snippets per Browser-Extension direkt in das Second Brain übergeben – ohne Kontextverlust oder LLM-Token-Verbrauch.
- **Port-Entkopplung:** Dedizierter Endpoint `POST /api/brave_clip` auf Port 8000 (FastAPI), wodurch Port 8080 frei für POS-/Haussysteme bleibt.
- **Sofortige Indexierung:** Jeder Clip wird als Markdown-Datei in `agy_components/data-pool/clips/` abgelegt, in `MASTER_INDEX.db` registriert und an die Agenten-Dropzone gemeldet.

### 6. 🤖 Triumvirat-Orchestrierung (Friday, AGY & Gemini CLI)
- **Klare Rollenteilung:**
  - 🧠 **FRIDAY (Cypher):** Meta-Kognitive Strategin, Wissensgraph, semantische Kohärenz.
  - ⚙️ **AGY (Antigravity):** System-Architekt, Core Engine, CachyOS/Host-Automation, IPC & TUI.
  - ⚡ **GEMINI CLI („Der Kleine“):** Fokussierter Fast-Path Routine-Worker für Formatierung, Logging und Statusprüfungen mit dediziertem Memory (`GEMINI.md`).

---

## 📦 Upgrade & Installation

```bash
# Repo klonen / aktualisieren
git pull origin main

# Backend-Umgebung starten
cd backend
source .venv/bin/activate
uvicorn server:app --host 127.0.0.1 --port 8000

# God-Mode TUI Cockpit starten
python3 agy_components/god_mode_tui.py
```
