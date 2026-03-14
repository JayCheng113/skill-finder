"""Self-contained REST API for skill retrieval. No MCP dependency.

Reads skills from a SQLite database and searches via FAISS vector index.

Environment variables:
    SKILL_DB_PATH    - Path to skills.db (default: ./data/skills.db)
    SKILL_INDEX_DIR  - Path to index directory (default: ./data/index/)
    HOST             - Bind host (default: 0.0.0.0)
    PORT             - Bind port (default: 7860)
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
import uvicorn

logger = logging.getLogger("skill_api")

_db: sqlite3.Connection | None = None
_index: faiss.Index | None = None
_skill_ids: list[str] = []
_model: SentenceTransformer | None = None


def _query_skill(skill_id: str) -> dict | None:
    cur = _db.cursor()
    cur.execute("SELECT * FROM skills WHERE id = ?", (skill_id,))
    row = cur.fetchone()
    if row is None:
        return None
    cols = [d[0] for d in cur.description]
    d = dict(zip(cols, row))
    d["tags"] = json.loads(d.get("tags") or "[]")
    return d


def _search_fts(query: str, limit: int = 10) -> list[dict]:
    cur = _db.cursor()
    tokens = query.strip().split()
    if not tokens:
        return []
    fts_query = " ".join(f'"{t.replace(chr(34), "")}"' for t in tokens)
    try:
        cur.execute(
            "SELECT s.id, s.name, s.description, s.category, s.tags "
            "FROM skills_fts f JOIN skills s ON f.rowid = s.rowid "
            "WHERE skills_fts MATCH ? LIMIT ?",
            (fts_query, limit),
        )
    except sqlite3.OperationalError:
        return []
    results = []
    for row in cur.fetchall():
        results.append({
            "id": row[0], "name": row[1], "description": row[2],
            "category": row[3], "tags": json.loads(row[4] or "[]"),
        })
    return results


# ── API endpoints ───────────────────────────────────────────────────


async def search(request):
    q = request.query_params.get("q", "")
    k = int(request.query_params.get("k", "5"))
    if not q:
        return JSONResponse({"error": "Missing 'q'"}, status_code=400)
    if _index is None or _model is None:
        return JSONResponse({"error": "Index not loaded"}, status_code=503)

    vec = _model.encode([q], normalize_embeddings=True).astype(np.float32)
    scores, indices = _index.search(vec, min(k, _index.ntotal))

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(_skill_ids):
            continue
        skill = _query_skill(_skill_ids[idx])
        if skill:
            results.append({
                "id": skill["id"],
                "name": skill["name"],
                "description": skill["description"],
                "score": round(float(score), 4),
                "category": skill["category"],
                "tags": skill["tags"],
            })
    return JSONResponse(results)


async def get_skill(request):
    skill_id = request.path_params["skill_id"]
    if _db is None:
        return JSONResponse({"error": "Store not loaded"}, status_code=503)
    skill = _query_skill(skill_id)
    if skill is None:
        return JSONResponse({"error": "Skill not found"}, status_code=404)
    return JSONResponse({
        "id": skill["id"],
        "name": skill["name"],
        "description": skill["description"],
        "instructions": skill["instructions"],
        "category": skill["category"],
        "tags": skill["tags"],
        "source": skill["source"],
    })


async def keyword_search(request):
    q = request.query_params.get("q", "")
    limit = int(request.query_params.get("limit", "10"))
    if not q:
        return JSONResponse({"error": "Missing 'q'"}, status_code=400)
    if _db is None:
        return JSONResponse({"error": "Store not loaded"}, status_code=503)
    return JSONResponse(_search_fts(q, limit))


async def categories(request):
    if _db is None:
        return JSONResponse({"error": "Store not loaded"}, status_code=503)
    cur = _db.cursor()
    cur.execute(
        "SELECT category, COUNT(*) as count FROM skills GROUP BY category ORDER BY count DESC"
    )
    return JSONResponse([{"category": r[0], "count": r[1]} for r in cur.fetchall()])


async def health(request):
    count = 0
    if _db:
        cur = _db.cursor()
        cur.execute("SELECT COUNT(*) FROM skills")
        count = cur.fetchone()[0]
    return JSONResponse({
        "status": "ok",
        "skills": count,
        "index": _index is not None,
    })


# ── App factory ─────────────────────────────────────────────────────


def create_app(db_path: str, index_dir: str) -> Starlette:
    global _db, _index, _skill_ids, _model

    db = Path(db_path)
    idx = Path(index_dir)

    if not db.exists():
        raise FileNotFoundError(f"Database not found: {db}")
    _db = sqlite3.connect(f"file:{db}?mode=ro", uri=True, check_same_thread=False)
    cur = _db.cursor()
    cur.execute("SELECT COUNT(*) FROM skills")
    logger.info("store: loaded %d skills from %s", cur.fetchone()[0], db)

    index_path = idx / "index.faiss"
    ids_path = idx / "skill_ids.json"
    if index_path.exists() and ids_path.exists():
        _index = faiss.read_index(str(index_path))
        with open(ids_path) as f:
            meta = json.load(f)
        _skill_ids = meta["skill_ids"]
        model_name = meta.get("embedding", {}).get("model", "all-MiniLM-L6-v2")
        _model = SentenceTransformer(model_name)
        logger.info("index: loaded %d vectors, model=%s", _index.ntotal, model_name)
    else:
        logger.warning("index not found at %s, semantic search disabled", idx)

    return Starlette(routes=[
        Route("/api/search", search),
        Route("/api/skills/{skill_id}", get_skill),
        Route("/api/search/keyword", keyword_search),
        Route("/api/categories", categories),
        Route("/api/health", health),
    ])


def _ensure_data(data_dir: str) -> tuple[str, str]:
    """Download skills DB and index from HuggingFace if not present locally."""
    from huggingface_hub import hf_hub_download

    repo = "zcheng256/skillretrieval-data"
    db_path = os.path.join(data_dir, "skills.db")
    index_dir = os.path.join(data_dir, "index")

    if not os.path.exists(db_path):
        logger.info("Downloading skills.db from HuggingFace...")
        dl = hf_hub_download(repo, "processed/skills.db", repo_type="dataset")
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        os.symlink(dl, db_path)

    idx_subdir = "indices/sentence-transformers/all-MiniLM-L6-v2"
    faiss_path = os.path.join(index_dir, "index.faiss")
    if not os.path.exists(faiss_path):
        logger.info("Downloading index from HuggingFace...")
        os.makedirs(index_dir, exist_ok=True)
        for fname in ("index.faiss", "skill_ids.json"):
            dl = hf_hub_download(repo, f"{idx_subdir}/{fname}", repo_type="dataset")
            dest = os.path.join(index_dir, fname)
            if not os.path.exists(dest):
                os.symlink(dl, dest)

    return db_path, index_dir


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    data_dir = os.environ.get("SKILL_DATA_DIR", "data")
    db_path = os.environ.get("SKILL_DB_PATH", "")
    index_dir = os.environ.get("SKILL_INDEX_DIR", "")
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "7860"))

    if not db_path or not index_dir:
        db_path, index_dir = _ensure_data(data_dir)

    app = create_app(db_path, index_dir)
    uvicorn.run(app, host=host, port=port)
