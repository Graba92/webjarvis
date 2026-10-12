# J.A.R.V.I.S. (Friday) UI Architecture & Deep-Dive Handbook

## Part 1: Frontend & UI Components

### ASCII Wireframe
```ascii
+-------------------------------------------------------------+
| [HUBS & FORCES] |      3D GRAPH INTERFACE          | [FILTERS] |
| - Workshop      |                                  | - System   |
| - Gemini Live   |      (Center Interaction)        | - Tools    |
| - Suites        |                                  | - Skills   |
|                 |                                  |            |
|-----------------|----------------------------------|------------|
| Status Panel    | [DEV CONSOLE / CHAT INPUT]      | Mode Matrix|
+-------------------------------------------------------------+
```

### Module Descriptions
*   **Sensor / Mode Matrix:** Reactive panel displaying system telemetry (CPU/RAM/Temp) and active AI modes (e.g., Focus, Autonomous Task Audit).
*   **OS-Zugriff Status:** Indicator showing if Cypher has active host execution privileges. Red means restricted, Green means temporal full access.
*   **Skill & Tool Matrix Overlay:** A dedicated view (🧩 Puzzle Icon trigger) to manage Model Context Protocol (MCP) server statuses.

### Interaction Logic
*   **Node Click:** Emits event to backend asking for metadata and connections. Triggers `open_nodes` MCP call for RAG context hydration.
*   **Filtering:** Modifies visibility parameter in the Center 3D Graph, querying memory with altered parameters.

## Part 2: Backend & Data Pipelines

### Data Synchronization
The graph in the frontend listens to a WebSocket stream from the Python backend, which pushes node changes directly from SQLite (semantic relations) and LanceDB (vector facts) whenever an `add_node` or `delete_node` tool is called.

### Chat & Console Communication
Text input in the bottom console is routed to the FastAPI `/chat` endpoint. If an action is required, the Agent Broker dispatcher dynamically loads the necessary action module or MCP tool.

## Part 3: AI Logic, Workflows & Rulebook

### Active Pipelines
1.  **System Heartbeat:** Cyclic check of system health, dropzone ingest, and update status.
2.  **Ingest Loop:** Autonomous verification of inbox tasks (e.g., from Brave Bridge).
3.  **Auto-Node Extraction:** Logic defining how incoming web snippet tasks are chunked and converted into graph nodes.

### Trigger Logic
*   **Active Job Mode:** Triggered by user command or pending inbox tasks identified by heartbeat.
*   **Self-Healing/Quarantine:** Executed when missing folders or corrupt JSON tasks are detected during monitoring loops.
