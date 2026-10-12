---
title: "Kontext & Stabilität"
updated: "2026-10-09 05:23:32"
tags: []
wiki_links_count: 0
---

# Systemkontext & Gedächtnisstabilität

Protokollierung der Maßnahmen zur Amnesie-Prävention und Kontextwiederherstellung.

### Verwendete Mechanismen
- **State Node**: Ein dedizierter Knoten im 3D-Graph (`notes-state-node-controller`), der vor kritischen Ereignissen (Restart/Shutdown) den aktuellen Task- und Gesprächskontext speichert.
- **LanceDB Vektorgedächtnis**: Permanente Speicherung von Langzeitfakten und Notizen.
- **MEMORY.md**: Synchronisationsquelle für das Langzeitgedächtnis.
