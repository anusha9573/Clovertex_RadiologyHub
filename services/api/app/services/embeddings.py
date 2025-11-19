# services/api/app/services/embeddings.py
"""
Embeddings utilities using sentence-transformers and FAISS.

Functions:
 - embed_texts(list[str]) -> ndarray
 - build_faiss_index(resource_profiles: List[dict], model_name=...) -> (index, ids_list)
 - save/load index & cache
 - query_faiss(index, query_embedding, top_k=5) -> (scores, ids)
"""
import logging
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Tuple

import faiss
import numpy as np

logger = logging.getLogger(__name__)

# optional heavy imports
try:
    import faiss
    from sentence_transformers import SentenceTransformer

    ST_AVAILABLE = True
except Exception:
    ST_AVAILABLE = False

# default model
EMB_MODEL_NAME = os.getenv("EMB_MODEL", "all-MiniLM-L6-v2")
CACHE_DIR = Path(os.getenv("EMB_CACHE_DIR", "infra/mysql_init/embeddings_cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH = CACHE_DIR / "faiss.index"
IDS_PATH = CACHE_DIR / "ids.pkl"
EMB_CACHE_PATH = CACHE_DIR / "embeddings.pkl"


def _get_model():
    if not ST_AVAILABLE:
        raise RuntimeError("sentence-transformers or faiss not installed")
    model = SentenceTransformer(EMB_MODEL_NAME)
    return model


def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Compute embeddings for a list of texts and return a (N, D) numpy array.
    """
    model = _get_model()
    emb = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    # ensure dtype float32 for faiss
    if emb.dtype != np.float32:
        emb = emb.astype(np.float32)
    return emb


def build_resource_profiles(
    resources: List[Dict[str, Any]],
) -> Tuple[List[str], List[str]]:
    """
    Convert resource dicts into profile strings and return (ids, profile_texts)
    """
    ids = []
    texts = []
    for r in resources:
        rid = r.get("resource_id")
        ids.append(rid)
        parts = [
            r.get("name", ""),
            r.get("specialty", ""),
            f"skill:{r.get('skill_level','')}",
            f"cases:{r.get('total_cases_handled','')}",
        ]
        texts.append(" | ".join(parts))
    return ids, texts


def build_faiss_index(
    resources: List[Dict[str, Any]], rebuild: bool = False
) -> Tuple[Any, List[str]]:
    """
    Build or update a FAISS index from resource profiles.
    Returns (index, ids_list)
    Index and ids are saved to CACHE_DIR.
    """
    if not ST_AVAILABLE:
        raise RuntimeError("sentence-transformers or faiss not installed")

    ids, texts = build_resource_profiles(resources)
    embeddings = embed_texts(texts)  # (N, D)
    dim = embeddings.shape[1]

    # create index
    index = faiss.IndexFlatIP(
        dim
    )  # inner product (cosine-like if embeddings normalized)
    # normalize for IP similarity (optional)
    faiss.normalize_L2(embeddings)
    index.add(embeddings)

    # persist
    faiss.write_index(index, str(INDEX_PATH))
    with open(IDS_PATH, "wb") as f:
        pickle.dump(ids, f)
    with open(EMB_CACHE_PATH, "wb") as f:
        pickle.dump(
            {"ids": ids, "texts": texts, "embeddings_shape": embeddings.shape}, f
        )

    return index, ids


def load_faiss_index():
    if not ST_AVAILABLE:
        raise RuntimeError("sentence-transformers or faiss not installed")
    if not INDEX_PATH.exists() or not IDS_PATH.exists():
        raise FileNotFoundError("FAISS index or ids file not found. Build index first.")

    index = faiss.read_index(str(INDEX_PATH))
    with open(IDS_PATH, "rb") as f:
        ids = pickle.load(f)
    return index, ids


def query_faiss_by_text(query: str, top_k: int = 5):
    if not ST_AVAILABLE:
        raise RuntimeError("sentence-transformers or faiss not installed")
    model = _get_model()
    q_emb = model.encode([query], convert_to_numpy=True)
    if q_emb.dtype != np.float32:
        q_emb = q_emb.astype(np.float32)
    faiss.normalize_L2(q_emb)
    index, ids = load_faiss_index()
    D, I = index.search(q_emb, top_k)
    # I is shape (1, k)
    results = []
    for score, idx in zip(D[0].tolist(), I[0].tolist()):
        if idx < 0:
            continue
        results.append({"id": ids[idx], "score": float(score)})
    return results
