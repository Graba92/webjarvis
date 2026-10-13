---
title: "Autonomous Verification Protocol"
updated: "2026-10-08 16:48:37"
tags: []
wiki_links_count: 0
---

# Autonomous Verification Protocol

Um die Effizienz der Interaktion zu steigern, gilt folgende Direktive:

Bevor der Operator gefragt wird, ob eine Änderung am User Interface (HUD, 3D-Graph) oder dem Systemzustand erfolgreich war, muss die KI **autonom** versuchen, dies zu verifizieren.

### Methoden zur Verifizierung:
1. **Visuelle Prüfung:** Nutzung von `screen_process`, um den aktuellen Bildschirminhalt zu analysieren.
2. **Systematische Prüfung:** Nutzung von `query_graph`, `manage_tasks(action='list')`, `file_controller(action='read')` oder MCP-Tools, um den Zustand von Daten oder Dateien zu bestätigen.

Erst wenn diese autonomen Methoden kein eindeutiges Ergebnis liefern, darf der Operator um Bestätigung gebeten werden.
