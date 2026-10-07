"""
backend/actions/wiki_manager.py — Karpathy-Muster Wissenspflege & Wiki-Engine für J.A.R.V.I.S.
- Autonomes Wiki in backend/knowledge_base/wiki/*.md mit YAML Frontmatter.
- Immutability für rohe Quellen in backend/knowledge_base/raw/.
- [[Wiki-Links]] Extraktion & automatische bidirektionale Verknüpfung im 3D-Graphen.
- Widerspruchs-Erkennung (Conflict Resolution): Niemals stillschweigend überschreiben!
- Automatischer Sync in den 3D Three.js Graph (graph_nodes.json) & LanceDB Vektorspeicher.
"""

from __future__ import annotations
import os
import re
import json
import uuid
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

BACKEND_DIR = Path(__file__).resolve().parent.parent
WIKI_DIR = BACKEND_DIR / "knowledge_base" / "wiki"
RAW_DIR = BACKEND_DIR / "knowledge_base" / "raw"
GRAPH_FILE = BACKEND_DIR / "knowledge_base" / "graph_nodes.json"

WIKI_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Regex für [[Wiki-Links]] und YAML Frontmatter
_WIKI_LINK_RE = re.compile(r"\[\[(.*?)\]\]")
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

TOOL = {
    "name": "manage_wiki",
    "description": (
        "Verwaltet das strukturierte Karpathy-Wissenswiki (backend/knowledge_base/wiki/). "
        "Ermöglicht das Anlegen und Aktualisieren von kuratierten Markdown-Seiten mit [[Wiki-Links]], "
        "das Erkennen und Kennzeichnen von Widersprüchen (Conflict Flagging) ohne Datenverlust, "
        "das Lesen und Durchsuchen des Wikis sowie die automatische Synchronisation mit dem 3D-Graphen."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "Die Wiki-Aktion: 'read', 'write', 'list', 'flag_conflict', 'search'.",
                "enum": ["read", "write", "list", "flag_conflict", "search"]
            },
            "title": {
                "type": "STRING",
                "description": "Titel des Wiki-Artikels (z.B. 'CachyOS Kernel Tuning' oder 'Audio Pipeline Architecture')."
            },
            "content": {
                "type": "STRING",
                "description": "Der Markdown-Inhalt des Artikels inklusive möglicher [[Wiki-Links]]."
            },
            "tags": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": "Schlagworte / Tags für den Artikel (z.B. ['linux', 'kernel', 'sched-ext'])."
            },
            "new_claim": {
                "type": "STRING",
                "description": "Bei 'flag_conflict': Der neu erfasste, widersprüchliche Fakt."
            },
            "existing_claim": {
                "type": "STRING",
                "description": "Bei 'flag_conflict': Der bisherige Wissensstand, der im Widerspruch steht."
            },
            "query": {
                "type": "STRING",
                "description": "Suchbegriff für 'search'."
            }
        },
        "required": ["action"]
    }
}

def _slugify(text: str) -> str:
    s = str(text).strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    return s.strip("-") or "wiki-page"

def _extract_wiki_links(text: str) -> List[str]:
    links = []
    for match in _WIKI_LINK_RE.findall(text):
        target = match.split("|")[0].strip()
        if target and target not in links:
            links.append(target)
    return links

def _parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    fm_match = _FRONTMATTER_RE.match(content)
    metadata = {}
    body = content
    if fm_match:
        raw_fm = fm_match.group(1)
        body = content[fm_match.end():]
        for line in raw_fm.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and ":" in line:
                k, v = line.split(":", 1)
                metadata[k.strip().lower()] = v.strip().strip("'\"")
    return metadata, body

def _sync_to_graph_and_lancedb(title: str, content: str, links: List[str], has_conflict: bool = False, broadcast_fn = None):
    slug = _slugify(title)
    node_id = f"wiki-{slug}"

    # 1. 3D-Graph (graph_nodes.json) aktualisieren
    try:
        from actions.graph_manager import get_full_graph_data, save_graph_data
        data = get_full_graph_data()
        nodes = data.setdefault("nodes", [])
        graph_links = data.setdefault("links", [])

        # Existierenden Knoten suchen oder neu erstellen
        existing_node = next((n for n in nodes if n["id"] == node_id), None)
        status_val = "conflict" if has_conflict else "active"

        # Kurze Beschreibung für den Graphen
        desc_lines = [l for l in content.splitlines() if l.strip() and not l.startswith("#") and not l.startswith("---")]
        short_desc = desc_lines[0][:140] if desc_lines else f"Kuratierter Wiki-Artikel: {title}"

        if existing_node:
            existing_node["name"] = title
            existing_node["description"] = short_desc
            existing_node["status"] = status_val
            existing_node["connections"] = max(existing_node.get("connections", 1), len(links) + 1)
        else:
            nodes.append({
                "id": node_id,
                "name": title,
                "category": "Wiki",
                "connections": max(1, len(links) + 1),
                "description": short_desc,
                "status": status_val,
                "path": str(WIKI_DIR / f"{slug}.md")
            })

        # Links für [[Wiki-Links]] anlegen
        for target_title in links:
            target_slug = _slugify(target_title)
            # Zielknoten finden (Wiki oder bestehender Knoten)
            target_node = next((n for n in nodes if _slugify(n["name"]) == target_slug or n["id"] == target_slug or n["id"] == f"wiki-{target_slug}"), None)
            target_id = target_node["id"] if target_node else f"wiki-{target_slug}"
            
            # Prüfen ob Link bereits existiert
            link_exists = any(
                (l.get("source") == node_id and l.get("target") == target_id) or
                (l.get("source") == target_id and l.get("target") == node_id)
                for l in graph_links
            )
            if not link_exists:
                graph_links.append({
                    "source": node_id,
                    "target": target_id,
                    "value": 2,
                    "type": "wiki"
                })

        save_graph_data(data)
        if broadcast_fn:
            broadcast_fn({
                "type": "graph_updated",
                "graph_data": data
            })
    except Exception as e:
        print(f"[WIKI_MANAGER] Fehler beim 3D-Graph Sync: {e}")

    # 2. LanceDB Vektor-Embedding aktualisieren
    try:
        from memory.lancedb_manager import store_vector_memory
        store_vector_memory(
            text=f"Wiki: {title}\n{content}",
            category="wiki",
            source=f"wiki/{slug}.md"
        )
    except Exception as e:
        print(f"[WIKI_MANAGER] Fehler beim LanceDB Sync: {e}")

def manage_wiki(parameters: Dict[str, Any], **kwargs) -> str:
    action = str(parameters.get("action", "list")).lower().strip()
    title = parameters.get("title", "")
    content = parameters.get("content", "")
    tags = parameters.get("tags", [])
    new_claim = parameters.get("new_claim", "")
    existing_claim = parameters.get("existing_claim", "")
    query = parameters.get("query", "")

    ctx = kwargs.get("ctx", {})
    broadcast_fn = ctx.get("ws_broadcast")

    if action == "list":
        pages = list(WIKI_DIR.glob("*.md"))
        if not pages:
            return "Das Wiki (backend/knowledge_base/wiki/) ist aktuell leer. Es wurden noch keine Artikel kuratiert."
        
        result_lines = [f"Kuratierte Wiki-Artikel ({len(pages)} Seiten):"]
        for p in pages:
            text = p.read_text(encoding="utf-8")
            meta, _ = _parse_frontmatter(text)
            title_display = meta.get("title", p.stem.replace("-", " ").title())
            links = _extract_wiki_links(text)
            has_conflict = "> [!WARNING] Widerspruch" in text
            status_tag = " ⚠️ [WIDERSPRUCH]" if has_conflict else ""
            result_lines.append(f"  • {title_display} ({len(links)} Links){status_tag} [Pfad: wiki/{p.name}]")
        return "\n".join(result_lines)

    elif action == "read":
        if not title:
            return "Fehler: 'title' muss zum Lesen einer Wiki-Seite angegeben werden."
        slug = _slugify(title)
        page_path = WIKI_DIR / f"{slug}.md"
        if not page_path.exists():
            # Fallback: Suche nach ähnlichem Dateinamen
            matches = list(WIKI_DIR.glob(f"*{slug}*.md"))
            if matches:
                page_path = matches[0]
            else:
                return f"Wiki-Seite '{title}' ({slug}.md) existiert noch nicht."

        text = page_path.read_text(encoding="utf-8")
        return text

    elif action == "write":
        if not title or not content:
            return "Fehler: 'title' und 'content' müssen zum Erstellen/Aktualisieren einer Wiki-Seite angegeben werden."
        
        slug = _slugify(title)
        page_path = WIKI_DIR / f"{slug}.md"
        now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        links = _extract_wiki_links(content)
        tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)

        # YAML Frontmatter generieren / erhalten
        frontmatter = (
            f"---\n"
            f"title: \"{title}\"\n"
            f"updated: \"{now_iso}\"\n"
            f"tags: [{tags_str}]\n"
            f"wiki_links_count: {len(links)}\n"
            f"---\n\n"
        )
        
        # Falls der Content noch kein Frontmatter hat, voranstellen
        if not content.startswith("---"):
            full_markdown = frontmatter + content.strip() + "\n"
        else:
            full_markdown = content.strip() + "\n"

        has_conflict = "> [!WARNING] Widerspruch" in full_markdown

        # Atomar speichern via Tempfile
        temp_file = page_path.with_suffix(".tmp")
        temp_file.write_text(full_markdown, encoding="utf-8")
        os.replace(temp_file, page_path)

        # Synchronisation mit 3D-Graph und Vektordatenbank
        _sync_to_graph_and_lancedb(title, full_markdown, links, has_conflict=has_conflict, broadcast_fn=broadcast_fn)

        link_info = f" ({len(links)} [[Wiki-Links]] verknüpft: {', '.join(links)})" if links else ""
        return f"Wiki-Artikel '{title}' erfolgreich gespeichert unter 'wiki/{slug}.md'{link_info}. 3D-Graph und LanceDB synchronisiert."

    elif action == "flag_conflict":
        if not title or not new_claim:
            return "Fehler: 'title' und 'new_claim' müssen zum Kennzeichnen eines Widerspruchs angegeben werden."
        
        slug = _slugify(title)
        page_path = WIKI_DIR / f"{slug}.md"
        if not page_path.exists():
            return f"Wiki-Seite '{title}' existiert nicht. Bitte erstelle den Artikel zuerst, bevor ein Widerspruch vermerkt wird."

        current_text = page_path.read_text(encoding="utf-8")
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conflict_block = (
            f"\n\n> [!WARNING] Widerspruch erkannt ({now_str})\n"
            f"> **Neuer Input:** {new_claim}\n"
            f"> **Bisheriger Stand:** {existing_claim or 'Siehe vorherigen Abschnitt'}\n"
            f"> **Status:** Klärung durch Operator ausstehend (Originale unberührt)\n\n"
        )

        updated_text = current_text.rstrip() + conflict_block
        page_path.write_text(updated_text, encoding="utf-8")

        links = _extract_wiki_links(updated_text)
        _sync_to_graph_and_lancedb(title, updated_text, links, has_conflict=True, broadcast_fn=broadcast_fn)

        return (
            f"Widerspruch in Wiki-Seite '{title}' erfolgreich markiert (Zero-Data-Loss). "
            f"Knoten im 3D-Graphen wurde als 'conflict' geflaggt."
        )

    elif action == "search":
        if not query:
            return "Fehler: 'query' für die Wiki-Suche muss angegeben werden."
        
        clean_q = query.lower().strip()
        hits = []
        for p in WIKI_DIR.glob("*.md"):
            txt = p.read_text(encoding="utf-8")
            if clean_q in txt.lower() or clean_q in p.name.lower():
                meta, body = _parse_frontmatter(txt)
                t = meta.get("title", p.stem.replace("-", " ").title())
                # Snippet finden
                snippet = ""
                for line in body.splitlines():
                    if clean_q in line.lower():
                        snippet = line.strip()[:120]
                        break
                hits.append(f"• **{t}** (wiki/{p.name}): \"{snippet}\"")

        if hits:
            return f"Gefundene Wiki-Artikel für '{query}' ({len(hits)} Treffer):\n" + "\n".join(hits)
        
        # LanceDB semantische Suche als Fallback
        try:
            from memory.lancedb_manager import search_vector_memory
            vec_hits = search_vector_memory(query, limit=3)
            wiki_vec_hits = [h for h in vec_hits if h.get("category") == "wiki"]
            if wiki_vec_hits:
                lines = [f"Semantische Vektortreffer für '{query}':"]
                for vh in wiki_vec_hits:
                    lines.append(f"• {vh.get('source', 'Wiki')}: \"{vh.get('text', '')[:120]}...\"")
                return "\n".join(lines)
        except Exception:
            pass

        return f"Keine Wiki-Artikel gefunden für '{query}'."

    return f"Unbekannte Aktion '{action}'."
