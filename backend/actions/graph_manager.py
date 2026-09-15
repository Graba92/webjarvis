"""
backend/actions/graph_manager.py — Autonomes 3D-Knotengraph-Management für J.A.R.V.I.S.
Verwaltet Knoten und Kanten persistent in backend/knowledge_base/graph_nodes.json.
Erlaubt Gemini Live und dem Benutzer:
- Neue Knoten und Notizen/Projekte dynamisch im 3D-Raum anzulegen (`add_node`)
- Den Wissensgraphen semantisch und nach Querverbindungen zu durchsuchen (`query_graph`)
- Knoten mit Undo-Unterstützung zu entfernen (`delete_node`)
- Live-Aktualisierungen in Echtzeit per WebSocket an das Three.js Frontend zu streamen.
"""

from __future__ import annotations
import os
import re
import sys
import json
import uuid
from pathlib import Path
from threading import Lock
from typing import Optional, Callable

# Pfade & Importe
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from core.undo import push_undo

GRAPH_STORAGE_PATH = BACKEND_DIR / "knowledge_base" / "graph_nodes.json"
_lock = Lock()

VALID_CATEGORIES = [
    "Router", "Skills", "Tools",
    "Suites", "Wiki", "Files",
    "Concepts", "Worlds", "Notes"
]

# Standard-Initialdaten für den Graphen inklusive nützlicher Systempfade
DEFAULT_GRAPH_DATA = {
    "nodes": [
        {"id": "hub-skill-suites", "name": "Skill Suites", "category": "Suites", "connections": 236, "description": "Zentraler Routing-Knoten aller autonomen Agenten-Skills, Automatisierungsroutinen und Tool-Pipelines.", "path": "backend/actions"},
        {"id": "hub-claude-code", "name": "Claude Code", "category": "Skills", "connections": 48, "description": "Terminal-Agent zur Code-Generierung, Refactoring und statischen AST-Synthese.", "path": "claude"},
        {"id": "hub-gemini-live", "name": "Gemini Live API", "category": "Router", "connections": 112, "description": "Vollduplex-Multimodal-Streaming-Core (gemini-3.1-flash-live-preview) mit 16/24-kHz-Audio.", "path": "backend/core/gemini_live.py"},
        {"id": "hub-ai-workshop", "name": "AI Workshop OS", "category": "Concepts", "connections": 184, "description": "Hauptarchitektur des hybriden Betriebssystems für Linux (CachyOS / Arch).", "path": "."},
        {"id": "hub-youtube-channel", "name": "YouTube Channel", "category": "Concepts", "connections": 64, "description": "Content-Pipeline, Videoskripte, Storyboards und Metadaten-Optimierung.", "path": "https://youtube.com"},
        {"id": "suite-finance", "name": "Finance Suite", "category": "Suites", "connections": 32, "description": "Abrechnungen, Rechnungs-Generierung und Stripe-Schnittstellen.", "path": "backend/actions"},
        {"id": "suite-seo", "name": "SEO Suite", "category": "Suites", "connections": 28, "description": "Suchmaschinenoptimierung, Keyword-Cluster und Content-Scoring.", "path": "backend/actions"},
        {"id": "suite-ads", "name": "Ads Suite", "category": "Suites", "connections": 19, "description": "Werbekampagnen-Steuerung und Performance-Tracking.", "path": "backend/actions"},
        {"id": "tool-vidiq", "name": "vidIQ", "category": "Tools", "connections": 14, "description": "YouTube-Trendanalyse und Keyword-Tracking.", "path": "https://vidiq.com"},
        {"id": "tool-higgsfield", "name": "Higgsfield", "category": "Tools", "connections": 22, "description": "KI-Videogenerierung und Prompt-Orchestrierung.", "path": "https://higgsfield.ai"},
        {"id": "tool-zapier", "name": "Zapier", "category": "Tools", "connections": 38, "description": "Automatisierte Webhook-Verbindungen und Third-Party-Konnektoren.", "path": "https://zapier.com"},
        {"id": "tool-pipewire", "name": "PipeWire Audio", "category": "Tools", "connections": 54, "description": "CachyOS High-Performance Sound-Server mit 16/24-kHz-Streams.", "path": "pavucontrol"},
        {"id": "skill-os-bridge", "name": "OS Bridge Engine", "category": "Skills", "connections": 76, "description": "Direkte Linux-Systemcalls, Pacman/Yay-Paketmanager und PipeWire-Audio-Routing.", "path": "backend/actions/system_monitor.py"},
        {"id": "skill-undo-stack", "name": "Undo Stack", "category": "Skills", "connections": 42, "description": "Umkehrung von bis zu 10 destruktiven Aktionen und Systemmutationen.", "path": "backend/core/undo.py"},
        {"id": "skill-memory-index", "name": "Memory Indexer", "category": "Skills", "connections": 88, "description": "Zweistufiges Langzeitgedächtnis mit Recency-Priorisierung und Keyword-Recall.", "path": "backend/memory/memory_manager.py"},
        {"id": "wiki-cachyos", "name": "CachyOS Optimization", "category": "Wiki", "connections": 29, "description": "Kernel-Optimierungen, BORE-Scheduler und x86-64-v3/v4 Performance-Builds.", "path": "https://wiki.cachyos.org"},
        {"id": "wiki-gemini-live-spec", "name": "Gemini Live Docs", "category": "Wiki", "connections": 34, "description": "Bidirektionale WebSockets, Bidi-Streaming und Tool-Execution-Spezifikationen.", "path": "https://ai.google.dev/api/live"},
        {"id": "world-dev-workspace", "name": "Dev Workspace", "category": "Worlds", "connections": 62, "description": "Arbeitsverzeichnis für Entwicklung, Tests und Container-Orchestrierung.", "path": "."},
        {"id": "world-sysadmin", "name": "Sysadmin Core", "category": "Worlds", "connections": 39, "description": "Systemüberwachung, Backups, Netzwerk- und Kernel-Tools.", "path": "backend"},
        {"id": "note-2026-roadmap", "name": "2026-Roadmap", "category": "Notes", "connections": 16, "description": "Meilensteine für das autonome KI-Betriebssystem und TUI-Widgets.", "path": "backend/knowledge_base/knowledge_map.json"},
        {"id": "note-video-script", "name": "VIDEO-SCRIPT-FULL", "category": "Notes", "connections": 12, "description": "Skript für Vorstellung des CachyOS AI Betriebssystems.", "path": "backend/knowledge_base/knowledge_map.json"},
        {"id": "file-server-py", "name": "backend/server.py", "category": "Files", "connections": 24, "description": "Zentraler WebSocket & Telemetrie-Bridge Server auf Port 8765.", "path": "backend/server.py"},
        {"id": "file-jarvis-core", "name": "backend/core/gemini_live.py", "category": "Files", "connections": 29, "description": "Vollduplex-Audio & Tool-Routing-Controller.", "path": "backend/core/gemini_live.py"}
    ],
    "links": [
        {"source": "hub-ai-workshop", "target": "hub-gemini-live"},
        {"source": "hub-ai-workshop", "target": "hub-skill-suites"},
        {"source": "hub-ai-workshop", "target": "hub-claude-code"},
        {"source": "hub-ai-workshop", "target": "hub-youtube-channel"},
        {"source": "hub-ai-workshop", "target": "world-dev-workspace"},
        {"source": "hub-ai-workshop", "target": "world-sysadmin"},
        {"source": "hub-skill-suites", "target": "skill-os-bridge"},
        {"source": "hub-skill-suites", "target": "skill-undo-stack"},
        {"source": "hub-skill-suites", "target": "skill-memory-index"},
        {"source": "hub-skill-suites", "target": "tool-zapier"},
        {"source": "hub-skill-suites", "target": "suite-finance"},
        {"source": "hub-skill-suites", "target": "suite-seo"},
        {"source": "hub-skill-suites", "target": "suite-ads"},
        {"source": "skill-os-bridge", "target": "tool-pipewire"},
        {"source": "skill-os-bridge", "target": "file-server-py"},
        {"source": "hub-gemini-live", "target": "file-jarvis-core"},
        {"source": "hub-gemini-live", "target": "file-server-py"},
        {"source": "hub-gemini-live", "target": "wiki-gemini-live-spec"},
        {"source": "hub-youtube-channel", "target": "tool-vidiq"},
        {"source": "hub-youtube-channel", "target": "tool-higgsfield"},
        {"source": "hub-youtube-channel", "target": "note-video-script"},
        {"source": "world-sysadmin", "target": "wiki-cachyos"},
        {"source": "world-dev-workspace", "target": "note-2026-roadmap"},
        {"source": "suite-finance", "target": "tool-zapier"}
    ]
}

def _slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "node"

def get_full_graph_data() -> dict:
    """Lädt den vollständigen Graphen thread-sicher aus JSON oder erzeugt die Standarddaten."""
    with _lock:
        if not GRAPH_STORAGE_PATH.exists():
            GRAPH_STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
            GRAPH_STORAGE_PATH.write_text(
                json.dumps(DEFAULT_GRAPH_DATA, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            return json.loads(json.dumps(DEFAULT_GRAPH_DATA))

        try:
            data = json.loads(GRAPH_STORAGE_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "nodes" in data and "links" in data:
                return data
        except Exception as e:
            print(f"[GraphManager] Ladefehler: {e}")

        return json.loads(json.dumps(DEFAULT_GRAPH_DATA))

def _save_graph_data(data: dict):
    """Speichert den Graphen thread-sicher in die JSON-Datei."""
    with _lock:
        GRAPH_STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        GRAPH_STORAGE_PATH.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

def find_node_by_id(node_id: str) -> dict | None:
    data = get_full_graph_data()
    for n in data.get("nodes", []):
        if n.get("id") == node_id:
            return n
    return None

def add_node_internal(
    title: str,
    category: str = "Notes",
    content: str = "",
    connections: int = 1,
    linked_to: str = "",
    path: str = "",
    broadcast_fn: Optional[Callable[[dict], None]] = None
) -> tuple[dict, str]:
    """
    Fügt einen neuen Knoten thread-sicher hinzu, verknüpft ihn und sendet den Broadcast.
    """
    cat_clean = category.strip().capitalize() if category else "Notes"
    if cat_clean not in VALID_CATEGORIES:
        # Beste Übereinstimmung oder Fallback auf Notes
        matching = [c for c in VALID_CATEGORIES if c.lower() == cat_clean.lower()]
        cat_clean = matching[0] if matching else "Notes"

    node_slug = _slugify(title)
    node_id = f"{cat_clean.lower()}-{node_slug}"
    
    data = get_full_graph_data()
    nodes: list[dict] = data.setdefault("nodes", [])
    links: list[dict] = data.setdefault("links", [])

    # Prüfen, ob ID bereits existiert -> eindeutigen Suffix anhängen
    existing_ids = {n["id"] for n in nodes}
    if node_id in existing_ids:
        node_id = f"{node_id}-{uuid.uuid4().hex[:4]}"

    new_node = {
        "id": node_id,
        "name": title.strip(),
        "category": cat_clean,
        "connections": max(1, int(connections or 1)),
        "description": content.strip() or f"Autonom erstellter Eintrag für {title}.",
        "path": path.strip() if path else ""
    }
    nodes.append(new_node)

    # Automatische Verknüpfung
    target_link_id = linked_to.strip()
    if not target_link_id or target_link_id not in existing_ids:
        # Fallback: Mit Kategorie-Hub oder System-Hub verbinden
        category_hubs = {
            "Suites": "hub-skill-suites",
            "Skills": "hub-skill-suites",
            "Tools": "hub-skill-suites",
            "Router": "hub-gemini-live",
            "Concepts": "hub-ai-workshop",
            "Worlds": "hub-ai-workshop",
            "Notes": "hub-ai-workshop",
            "Files": "hub-gemini-live",
            "Wiki": "hub-ai-workshop"
        }
        target_link_id = category_hubs.get(cat_clean, "hub-ai-workshop")

    if target_link_id in existing_ids or target_link_id == "hub-ai-workshop":
        links.append({"source": target_link_id, "target": node_id})

    _save_graph_data(data)

    # Undo-Aktion registrieren
    push_undo(
        label=f"Knoten '{title}' ({cat_clean}) erstellt",
        undo_fn=lambda: _undo_remove_node(node_id)
    )

    # Broadcast ans Next.js / Three.js Frontend
    if broadcast_fn:
        broadcast_fn({
            "type": "graph_update",
            "data": data,
            "action": "add_node",
            "node": new_node
        })

    return new_node, f"Knoten '{title}' [{cat_clean}] erfolgreich angelegt (ID: {node_id}) und mit '{target_link_id}' verknüpft."

def _undo_remove_node(node_id: str) -> str:
    delete_node_internal(node_id)
    return f"Knoten {node_id} rückgängig gemacht."

def delete_node_internal(
    node_id: str,
    broadcast_fn: Optional[Callable[[dict], None]] = None
) -> tuple[bool, str]:
    """
    Entfernt einen Knoten und dessen Verknüpfungen.
    """
    data = get_full_graph_data()
    nodes: list[dict] = data.setdefault("nodes", [])
    links: list[dict] = data.setdefault("links", [])

    target_node = next((n for n in nodes if n.get("id") == node_id), None)
    if not target_node:
        return False, f"Knoten mit ID '{node_id}' existiert nicht im Graphen."

    # Knoten und Links filtern
    data["nodes"] = [n for n in nodes if n.get("id") != node_id]
    removed_links = [l for l in links if l.get("source") == node_id or l.get("target") == node_id]
    data["links"] = [l for l in links if l.get("source") != node_id and l.get("target") != node_id]

    _save_graph_data(data)

    # Undo für Löschung: Wiederherstellung ermöglichen
    push_undo(
        label=f"Knoten '{target_node.get('name')}' gelöscht",
        undo_fn=lambda: _restore_node(target_node, removed_links)
    )

    if broadcast_fn:
        broadcast_fn({
            "type": "graph_update",
            "data": data,
            "action": "delete_node",
            "node_id": node_id
        })

    return True, f"Knoten '{target_node.get('name')}' ({node_id}) wurde aus dem 3D-Graph entfernt."

def _restore_node(node: dict, links: list[dict]) -> str:
    data = get_full_graph_data()
    data.setdefault("nodes", []).append(node)
    data.setdefault("links", []).extend(links)
    _save_graph_data(data)
    return f"Knoten '{node.get('name')}' wiederhergestellt."

# --- Gemini Tool Handler ---

def add_node(
    title: str = "",
    category: str = "Notes",
    content: str = "",
    connections: int = 1,
    linked_to: str = "",
    path: str = "",
    **kwargs
) -> str:
    """Tool-Handler: add_node"""
    if not title:
        return "Abbruch: Kein Titel für den neuen Knoten angegeben."
    
    broadcast_fn = kwargs.get("ws_broadcast")
    node, msg = add_node_internal(
        title=title,
        category=category,
        content=content,
        connections=connections,
        linked_to=linked_to,
        path=path,
        broadcast_fn=broadcast_fn
    )
    return msg

def query_graph(topic: str = "", **kwargs) -> str:
    """Tool-Handler: query_graph (Semantische und Stichwort-Suche)"""
    clean_topic = str(topic or "").strip().lower()
    if not clean_topic:
        return "Bitte geben Sie ein Thema oder einen Suchbegriff an."

    data = get_full_graph_data()
    nodes = data.get("nodes", [])
    links = data.get("links", [])

    results = []
    for n in nodes:
        score = 0
        name = n.get("name", "").lower()
        desc = n.get("description", "").lower()
        cat = n.get("category", "").lower()
        path = n.get("path", "").lower()

        if clean_topic in name:
            score += 5
        if clean_topic in desc:
            score += 3
        if clean_topic in cat:
            score += 2
        if clean_topic in path:
            score += 2

        if score > 0:
            # Nachbar-Knoten ermitteln
            nid = n.get("id")
            neighbors = []
            for l in links:
                s = l.get("source")
                t = l.get("target")
                if s == nid:
                    neighbors.append(t)
                elif t == nid:
                    neighbors.append(s)

            results.append((score, n, neighbors))

    if not results:
        return f"Keine Knoten im 3D-Graph gefunden, die zu '{topic}' passen."

    results.sort(key=lambda r: r[0], reverse=True)
    top_results = results[:6]

    out = [f"Gefundene Knoten im J.A.R.V.I.S. Wissensgraphen für '{topic}':\n"]
    for score, node, neighbors in top_results:
        neigh_str = ", ".join(neighbors[:4]) if neighbors else "Keine"
        path_str = f" | Pfad: {node.get('path')}" if node.get("path") else ""
        out.append(
            f"• **{node.get('name')}** [{node.get('category')}]{path_str}\n"
            f"  Beschreibung: {node.get('description')}\n"
            f"  Verbindungen ({node.get('connections')}): {neigh_str}\n"
        )

    return "\n".join(out)

def delete_node(node_id: str = "", **kwargs) -> str:
    """Tool-Handler: delete_node"""
    if not node_id:
        return "Abbruch: Keine Knoten-ID angegeben."
    broadcast_fn = kwargs.get("ws_broadcast")
    ok, msg = delete_node_internal(node_id, broadcast_fn)
    return msg

# Tool-Deklarationen für Gemini Live
TOOLS = [
    {
        "name": "add_node",
        "description": "Erstellt einen neuen Knoten im interaktiven 3D-Knotengraphen, wenn der Nutzer Notizen diktiert, Ideen festhält oder neue Projekte/Dateien anlegt. Der Knoten wird sofort live im Frontend gerendert.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "title": {
                    "type": "STRING",
                    "description": "Der Name bzw. Titel des Knotens."
                },
                "category": {
                    "type": "STRING",
                    "description": "Die Kategorie des Knotens: 'Router', 'Skills', 'Tools', 'Suites', 'Wiki', 'Files', 'Concepts', 'Worlds', oder 'Notes'."
                },
                "content": {
                    "type": "STRING",
                    "description": "Detaillierte Beschreibung, Notizinhalt oder Zweck des Knotens."
                },
                "connections": {
                    "type": "INTEGER",
                    "description": "Geschätzte Anzahl der Verbindungen oder Relevanzwert (1 bis 50)."
                },
                "linked_to": {
                    "type": "STRING",
                    "description": "Optionale ID des Eltern- oder Zielknotens, mit dem dieser Knoten verknüpft werden soll (z. B. 'hub-ai-workshop' oder 'suite-finance')."
                },
                "path": {
                    "type": "STRING",
                    "description": "Optionaler Datei-, Ordner- oder Programm-Pfad für direkte Betriebssystem-Interaktion."
                }
            },
            "required": ["title", "category"]
        },
        "handler": add_node
    },
    {
        "name": "query_graph",
        "description": "Durchsucht den 3D-Knotengraphen semantisch und gibt verknüpfte Informationen, Querverweise und Beschreibungen zu einem bestimmten Thema zurück.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "topic": {
                    "type": "STRING",
                    "description": "Der Suchbegriff oder das Thema, nach dem im Wissensgraphen gesucht werden soll."
                }
            },
            "required": ["topic"]
        },
        "handler": query_graph
    },
    {
        "name": "delete_node",
        "description": "Entfernt einen Knoten aus dem 3D-Knotengraph und löscht dessen Kanten. Die Aktion wird im Undo-Stack gespeichert.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "node_id": {
                    "type": "STRING",
                    "description": "Die eindeutige ID des zu löschenden Knotens (z. B. 'notes-meine-notiz')."
                }
            },
            "required": ["node_id"]
        },
        "handler": delete_node
    }
]
