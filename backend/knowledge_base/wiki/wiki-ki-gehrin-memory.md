---
title: J.A.R.V.I.S. KI-OS Memory & Knowledge Core
category: Brain
tags:
  - brain
  - consciousness
  - context
  - memory
  - first-principles
created_at: '2026-10-09T13:10:00'
updated_at: '2026-10-09T13:10:00'
confidence: 1.0
status: verified
summary: Dieses Dokument definiert die kognitiven Standards und Speicherarchitektur für das J.A.R.V.I.S. Betriebssystem zur Vermeidung von Kontextverlust und alzheimerartigen Zuständen.
---

# 🧠 J.A.R.V.I.S. Memory & Knowledge Core

Um die kognitive Stabilität des Systems zu gewährleisten, müssen strikte Prinzipien eingehalten werden.

## 1. Amnesie-Prävention durch Re-Hydration
Bei jedem Initialisierungs-Prozess oder nach Kontext-Timeouts müssen operative Zustände aus dem `backlog.md` und dem 3D-Graph (`State Nodes`) re-hydriert werden. Niemals darf ahnungslos nach laufenden Tasks gefragt werden.

## 2. Strukturierter Wissensgraphen-Support
Notizen, Fakten und Systemzusammenhänge dürfen nicht als lose Markdown-Dateien existieren. Sie sind zwingend in diesem Wiki zu strukturieren und über semantische Querverweise ([[Wiki-Links]]) mit dem 3D-Knotengraphen zu synchronisieren.

## 3. First-Principles Thinking
Problemanalysen dürfen sich nicht auf Analogien stützen. Jedes logische Problem ist in fundamentale Wahrheiten zu zerlegen.

## 4. Speicher-Topologie
- **Vektor-Gedächtnis**: LanceDB (semantische Suche via `recall_memory`).

- **Strukturiertes Wissen**: Dieses Wiki (`backend/knowledge_base/wiki/`).
- **Episodischer Zustand**: 3D-Graph Knotendaten & `SOUL.md`/`MEMORY.md` im Core.
