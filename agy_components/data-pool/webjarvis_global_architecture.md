# ASGRAD System Bible: Core Dev-Level Architecture

## 1. System Topology & Logical Data Flow
The ASGRAD system executes a serial workflow based on file dropping in the Agent-Exchange.

### Primary Trigger Chain:
1.  **Event (Brave Browser):** User sends text snippet via extension.
2.  **Trigger (Network):** Extension calls local Brave-Bridge API (HTTP POST on Port 8080).
3.  **Reaction (File System):** `brave_bridge.py` writes data as `task_id.json` into Inbox.
4.  **Audit (Core Logic):** Cypher autonomically scans via `directory_tree`, processes content, and moves the task.

## 2. Directory Anatomy & Hard Paths

```ascii
/home/graba/
├── .local/
│   ├── bin/webjarvis (Main System CLI)
│   └── share/webjarvis/ (Cypher Core Brain - LanceDB)
└── Schreibtisch/
    └── ASGRAD/
        ├── Agy-data-pool/
        │   ├── friday_manifest.md
        │   ├── webjarvis_global_architecture.md
        │   └── ASGRAD_Changelog.md       <-- System logbook
        ├── Agent-Exchange/               <-- Dropzone Infrastructure
        │   ├── inbox/                      <-- Input source for new tasks
        │   ├── payloads/                   <-- Optional heavy data storage
        │   ├── done/                       <-- Processed tasks for auditing
        │   ├── agent_broker.py             <-- Exchange process supervisor
        │   └── brave_bridge.py             <-- HTTP ingestion server
        └── Brave-Extension/              <-- Brave Add-on source code
```

## 3. Data Flow ASCII Chart
```ascii
[Extension] --- POST ---> [Bridge API:8080] -- write --> [Exchange/inbox/]
                                                            |
                                                            V
                                                      [Cypher Core] -- storage --> [Memory Core]
                                                              |
                                                              V
                                                      [Exchange/done/] <-- atomic move task.json
```

## 4. Dependencies
*   If `/Agent-Exchange/` or its subfolders are missing, input ingestion and task move operations will **fail**.
*   Dependency `python-textual python-rich` is required for TUI dashboard operation (Planned).
*   Dependency `rclone` or `rsync` is required for data pool synchronization.
