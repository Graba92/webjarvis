"""
backend/memory/lancedb_manager.py — LanceDB Vektorgedächtnis für J.A.R.V.I.S. AI OS.
Verwaltet persistente Vektor-Embeddings für Notizen, Recherchen, Code-Snippets und Systemfakten.
Ermöglicht semantische Ähnlichkeitssuche mit strikter Begrenzung auf die Top-3 relevantesten Fakten.
"""

from __future__ import annotations
import os
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import numpy as np

try:
    import lancedb
    import pyarrow as pa
except ImportError:
    lancedb = None
    pa = None

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "memory" / "lancedb_data"
EMBEDDING_DIM = 128
TABLE_NAME = "jarvis_memories"

_db_instance = None
_table_instance = None

def _compute_dense_embedding(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """
    Erzeugt einen deterministischen, dichten 128-dimensionalen Embedding-Vektor
    mittels Subword- und Token-Hashing mit L2-Normalisierung.
    Garantiert extrem schnelle (Sub-Millisekunden), lokale und robuste Vektorisierung.
    """
    vec = np.zeros(dim, dtype=np.float32)
    clean_text = text.lower().strip()
    if not clean_text:
        return vec.tolist()

    # 1. Wort-Tokens hashen
    words = clean_text.split()
    for w in words:
        h = int(hashlib.md5(w.encode("utf-8")).hexdigest()[:8], 16)
        idx = h % dim
        sign = 1.0 if (h >> 3) & 1 else -1.0
        vec[idx] += sign * (1.0 + len(w) * 0.1)

    # 2. 3-Gramme hashen für semantische Teilwort-Ähnlichkeit
    for i in range(len(clean_text) - 2):
        trigram = clean_text[i:i+3]
        h = int(hashlib.sha256(trigram.encode("utf-8")).hexdigest()[:8], 16)
        idx = h % dim
        sign = 1.0 if (h >> 2) & 1 else -1.0
        vec[idx] += sign * 0.5

    # L2-Normalisierung
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm

    return vec.tolist()

def get_table():
    """Gibt das LanceDB Table-Objekt zurück (Lazy Initialization)."""
    global _db_instance, _table_instance
    if not lancedb or not pa:
        return None

    if _table_instance is not None:
        return _table_instance

    DB_DIR.mkdir(parents=True, exist_ok=True)
    _db_instance = lancedb.connect(str(DB_DIR))

    schema = pa.schema([
        pa.field("id", pa.string()),
        pa.field("text", pa.string()),
        pa.field("category", pa.string()),
        pa.field("source", pa.string()),
        pa.field("updated_at", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), EMBEDDING_DIM))
    ])

    if TABLE_NAME in _db_instance.table_names():
        _table_instance = _db_instance.open_table(TABLE_NAME)
    else:
        # Initialen Basis-Eintrag anlegen
        seed_record = [{
            "id": "seed-system-cachyos",
            "text": "J.A.R.V.I.S. AI OS läuft nativ auf CachyOS (Arch Linux) mit KDE Plasma Desktop, PipeWire Audio und Pacman.",
            "category": "system",
            "source": "bootstrap",
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "vector": _compute_dense_embedding("J.A.R.V.I.S. CachyOS Arch Linux KDE Plasma PipeWire")
        }]
        _table_instance = _db_instance.create_table(TABLE_NAME, seed_record, schema=schema)

    return _table_instance

def store_vector_memory(text: str, category: str = "note", source: str = "user", memory_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Speichert eine Notiz, Recherche oder Fakt mit Vektor-Embedding in LanceDB.
    """
    clean_text = str(text or "").strip()
    if not clean_text:
        return {"success": False, "error": "Text darf nicht leer sein."}

    table = get_table()
    if table is None:
        return {"success": False, "error": "LanceDB nicht verfügbar."}

    record_id = memory_id or f"mem_{uuid.uuid4().hex[:10]}"
    vector = _compute_dense_embedding(clean_text)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    record = {
        "id": record_id,
        "text": clean_text,
        "category": category,
        "source": source,
        "updated_at": timestamp,
        "vector": vector
    }

    table.add([record])
    return {
        "success": True,
        "id": record_id,
        "category": category,
        "text": clean_text[:80] + ("..." if len(clean_text) > 80 else ""),
        "timestamp": timestamp
    }

def search_vector_memories(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Führt eine semantische Vektorsuche in LanceDB durch und liefert strikt die Top-N relevantesten Einträge.
    """
    clean_query = str(query or "").strip()
    if not clean_query:
        return []

    table = get_table()
    if table is None:
        return []

    query_vec = _compute_dense_embedding(clean_query)

    try:
        # LanceDB Vektorsuche
        results = table.search(query_vec).limit(limit).to_list()
        formatted = []
        for r in results:
            dist = r.get("_distance", 0.0)
            # Relevanz-Score approximieren (1 / (1 + distance))
            relevance = round(1.0 / (1.0 + float(dist)), 3) if dist is not None else 1.0
            formatted.append({
                "id": r.get("id"),
                "text": r.get("text"),
                "category": r.get("category", "note"),
                "source": r.get("source", "unknown"),
                "updated_at": r.get("updated_at", ""),
                "score": relevance
            })
        return formatted
    except Exception as e:
        print(f"[LanceDB] Fehler bei Vektorsuche: {e}")
        return []

def get_stats() -> Dict[str, Any]:
    """Liefert Statistikdaten über die Vektordatenbank."""
    table = get_table()
    if table is None:
        return {"online": False, "records": 0}
    try:
        count = len(table)
        return {"online": True, "records": count, "dimension": EMBEDDING_DIM, "db_path": str(DB_DIR)}
    except Exception:
        return {"online": True, "records": "aktiv", "dimension": EMBEDDING_DIM}
