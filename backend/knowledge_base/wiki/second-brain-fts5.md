# Second Brain & FTS5 Wissensspeicher (MASTER_INDEX.db)

## 1. Übersicht
Das Gedächtnis des ASGRAD-Triumvirats ruht auf zwei synchronisierten Pfeilern:
1. **LanceDB Vektorspeicher:** Serverlose Vektordatenbank mit 768-dimensionalen Embeddings für semantische Ähnlichkeitssuche (`jarvis_memories.lance`).
2. **SQLite FTS5 Volltext-Graph (`MASTER_INDEX.db`):** Strukturierter Volltext- und Metadaten-Index.

## 2. Kanonische Wahrheitsquelle
- **Autoritativer Pfad:**
  `/home/graba/.local/share/webjarvis/agy_components/data-pool/MASTER_INDEX.db`
  (121 Knowledge-Units, 52 Metadaten-Einträge, vollständiges FTS5-Indexschema).
- **Resolver-Reihenfolge:**
  1. Umgebungsvariable `AGY_DATA_POOL`
  2. Standardpfad `agy_components/data-pool/MASTER_INDEX.db`
- **Nutzung:**
  - `server.py`: Real-time RAG Grounding mit Volltext-Matching (`knowledge_units_fts MATCH ?`).
  - `god_mode_tui.py`: Read-only Panel 6 Volltextsuche für den Operator.

## 3. Entkoppelte Standalone-Instanz
Die Datei in `/home/graba/Schreibtisch/ASGRAD/Agy-data-pool/MASTER_INDEX.db` (999.424 Bytes, 2.716 Einträge) wird exklusiv von Standalone-Desktop-Tools genutzt und besitzt kein FTS5-Schema.

## 4. Verknüpfungen
- [[god-mode-tui]]
- [[system-architecture-map]]
- [[masterplan-phasen]]
