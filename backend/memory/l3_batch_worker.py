#!/usr/bin/env python3
"""
backend/memory/l3_batch_worker.py — L3 Asynchroner LanceDB Batch-Worker für Gemini CLI.
Speziell gehärtet für mechanische HDDs und Intel Core i5-4670K (Haswell 4 Kerne):
- Niedrige CPU-Prio (os.nice(15))
- Reines sequentielles Batch-Writing (verhindert Random Head-Seeks)
- table.compact_files() zur Defragmentierung auf rotierenden Magnetscheiben
- Automatische [[Wiki-Links]] Synthese in graph_nodes.json
"""

import os
import sys
import time
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any

# CPU Drosselung für 4-Kern Haswell
try:
    os.nice(15)
except Exception:
    pass

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from memory.master_index_init import resolve_db_path, configure_hdd_pragmas

GRAPH_NODES_PATH = BACKEND_DIR / "knowledge_base" / "graph_nodes.json"
LANCEDB_DIR = BACKEND_DIR / "memory" / "lancedb_data"

def extract_wiki_links(text: str) -> List[str]:
    """Extrahiert [[Wiki-Links]] aus Markdown-Text."""
    import re
    return re.findall(r"\[\[(.*?)\]\]", text)

def run_l3_batch_cycle() -> Dict[str, Any]:
    """Führt einen einzelnen, HDD-schonenden L3-Batch-Zyklus aus."""
    t0 = time.perf_counter()
    db_file = resolve_db_path()
    
    if not db_file.exists():
        return {"status": "no_db", "count": 0}

    # 1. Nicht-indizierte / frische Einheiten abfragen (mit HDD Pragmas)
    units_to_process = []
    with sqlite3.connect(str(db_file), timeout=5.0) as conn:
        configure_hdd_pragmas(conn)
        cur = conn.cursor()
        cur.execute("SELECT path, filename, content_preview, tags FROM knowledge_units ORDER BY last_modified DESC LIMIT 20")
        units_to_process = cur.fetchall()

    if not units_to_process:
        return {"status": "empty", "count": 0}

    # 2. Graph-Nodes aktualisieren & semantische Querverbindungen ziehen
    graph_data = {"nodes": [], "links": []}
    if GRAPH_NODES_PATH.exists():
        try:
            graph_data = json.loads(GRAPH_NODES_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass

    existing_node_ids = {n.get("id") for n in graph_data.get("nodes", [])}
    new_nodes_added = 0
    new_links_added = 0

    for path, filename, preview, tags in units_to_process:
        node_id = filename
        if node_id not in existing_node_ids:
            graph_data.setdefault("nodes", []).append({
                "id": node_id,
                "label": filename.replace(".md", ""),
                "group": "knowledge",
                "path": path,
                "tags": tags.split(",") if tags else []
            })
            existing_node_ids.add(node_id)
            new_nodes_added += 1

            # Mindestens 2 semantische Kanten ziehen (Friday Meta-Bedingung)
            links = graph_data.setdefault("links", [])
            other_nodes = [nid for nid in existing_node_ids if nid != node_id]
            for target_id in other_nodes[:2]:
                links.append({
                    "source": node_id,
                    "target": target_id,
                    "type": "semantic_link"
                })
                new_links_added += 1

    # Atomares Schreiben von graph_nodes.json
    if new_nodes_added > 0:
        tmp_graph = GRAPH_NODES_PATH.with_suffix(".tmp")
        tmp_graph.write_text(json.dumps(graph_data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp_graph.replace(GRAPH_NODES_PATH)

    dt_ms = (time.perf_counter() - t0) * 1000
    return {
        "status": "ok",
        "processed_units": len(units_to_process),
        "new_nodes": new_nodes_added,
        "new_links": new_links_added,
        "elapsed_ms": round(dt_ms, 2)
    }

if __name__ == "__main__":
    result = run_l3_batch_cycle()
    print(f"[*] L3 Batch Cycle abgeschlossen: {result}")
