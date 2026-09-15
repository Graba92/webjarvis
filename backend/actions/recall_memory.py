"""
backend/actions/recall_memory.py — Semantische Vektorsuche & Speicherung via LanceDB.
Erweitert das Gedächtnis um LanceDB Vektor-Embeddings für Notizen, Recherchen und Fakten.
Gibt streng limitiert nur die drei relevantesten Ergebnisse zurück, um Token im Live-Stream zu sparen.
"""

from __future__ import annotations
from typing import Optional
from memory.lancedb_manager import search_vector_memories, store_vector_memory
from memory.memory_manager import search_memory, remember

def recall_memory_handler(parameters: dict, **kwargs) -> str:
    query = str(parameters.get("query", "")).strip()
    if not query:
        return "Suchbegriff fehlt."

    # 1. Semantische Suche via LanceDB Vektordatenbank (Top 3)
    vector_results = search_vector_memories(query, limit=3)
    if vector_results:
        lines = []
        for i, r in enumerate(vector_results, 1):
            cat = r.get("category", "info").upper()
            score = r.get("score", 1.0)
            text = r.get("text", "").strip()
            lines.append(f"{i}. [{cat}] (Relevanz {score}): {text}")
        return f"Top-3 Gedächtnis-Fakten zu '{query}':\n" + "\n".join(lines)

    # 2. Fallback: Keyword-Suche im statischen long_term Speicher (max 3)
    fallback_res = search_memory(query, limit=3)
    return fallback_res

def store_memory_handler(parameters: dict, **kwargs) -> str:
    text = str(parameters.get("text", "")).strip()
    category = str(parameters.get("category", "note")).lower().strip()
    key = str(parameters.get("key", "")).strip()

    if not text:
        return "Abbruch: Kein Text zum Speichern übergeben."

    # 1. In LanceDB Vektordatenbank indizieren
    res = store_vector_memory(text=text, category=category, source="gemini_live")

    # 2. In Level-2 Key-Value Store & MEMORY.md persistieren
    store_key = key or f"note_{res.get('id', 'item')}"
    remember(key=store_key, value=text, category=category if category in {"identity", "preferences", "projects", "relationships", "wishes", "notes"} else "notes")

    return f"Gedächtniseintrag erfolgreich gespeichert und vektoriell indiziert ({category}): \"{text[:60]}...\""

RECALL_TOOL = {
    "name": "recall_memory",
    "description": "Führt eine semantische Vektorsuche in LanceDB durch und liefert die 3 relevantesten Fakten, Notizen oder Projektdetails (Token-sparend).",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query": {
                "type": "STRING",
                "description": "Suchbegriff, Frage oder Thema (z. B. 'Arch Linux Setup', 'KDE Plasma Shortcuts', 'Projekt J.A.R.V.I.S.')."
            }
        },
        "required": ["query"]
    },
    "handler": recall_memory_handler
}

STORE_TOOL = {
    "name": "store_memory",
    "description": "Speichert neue Notizen, Recherche-Ergebnisse oder Fakten permanent im LanceDB Vektorgedächtnis und der Memory-Datei.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "text": {
                "type": "STRING",
                "description": "Der vollständige Inhalt der Information, Notiz oder Recherche, die gemerkt werden soll."
            },
            "category": {
                "type": "STRING",
                "description": "Kategorie: 'note', 'project', 'system', 'preference', 'research' oder 'contact'."
            },
            "key": {
                "type": "STRING",
                "description": "Optionaler Kurzschlüssel oder Titel für den Eintrag."
            }
        },
        "required": ["text"]
    },
    "handler": store_memory_handler
}

TOOLS = [RECALL_TOOL, STORE_TOOL]
