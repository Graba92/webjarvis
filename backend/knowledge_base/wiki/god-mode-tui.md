# God-Mode TUI Cockpit (god_mode_tui.py)

## 1. Übersicht
Die **God-Mode TUI** ist das zentrale 8-Panel Terminal-HUD des Triumvirats, implementiert in Python mittels Textual (776 Zeilen Vollversion, aktiv auf `pts/1`).

## 2. Asymmetrisches 40/60 Layout
Die Architektur basiert auf zwei horizontalen Hauptbereichen:
- **Linke Flanke (40% Breite, 100% Höhe):**
  - **Panel 8 (Triumvirat Chat & Operator Command):**
    - RichLog Verlauf (`#chat-log`) mit Farbkodierung (Agy=Cyan, Friday=Magenta, Operator=Gold).
    - Status-Container (`#status-container`) mit 100ms animiertem Spinner (`⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏`).
    - Gemini-Label dauerhaft statisch und rot als `OFFLINE (Tokens)` deklariert.
    - Eingabeleiste (`#input-container`).
- **Rechte Flanke (60% Breite):**
  - Geordnetes 2x4-Grid (`#right-dashboard-grid`):
    - *Panel 1:* Agy Engine Telemetrie (CPU, RAM, [[uds-ipc-protokoll|UDS-Status]]).
    - *Panel 2:* Friday Cognitive Core Metriken.
    - *Panel 3:* Agy System Logs.
    - *Panel 4:* Friday Thought Stream.
    - *Panel 5:* Dropzone Matrix (DataTable aller JSON-Events aus [[agent-exchange-protocol]]).
    - *Panel 6:* [[second-brain-fts5|Second Brain FTS5 Volltextsuche]] (`MASTER_INDEX.db`).
    - *Panel 7:* Live Workstream (Queue `Aufgaben_user_to_ki` + Live-Subprozesse).

## 3. Textual-Markup Härtung
Alle eckigen Klammern in Agenten-Labels sind im Quelltext als `\[Agy]`, `\[Friday]`, `\[Gemini]` escaped, um BBCode-Parsing-Fehler in Textual auszuschließen.

## 4. Verknüpfungen
- [[sentinel-architektur]]
- [[agent-exchange-protocol]]
- [[second-brain-fts5]]
- [[audio-stack-zustaendigkeiten]]
