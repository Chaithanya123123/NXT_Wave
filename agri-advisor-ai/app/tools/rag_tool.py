import os
import pathlib

import chromadb
from chromadb.utils import embedding_functions

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge_base", "chroma_store")
DOCS_DIR = pathlib.Path(os.path.join(os.path.dirname(__file__), "..", "knowledge_base", "docs"))

_client = None
_collection = None


def _get_collection():
    global _collection, _client
    if _collection is not None:
        return _collection
    _client = chromadb.PersistentClient(path=os.path.normpath(CHROMA_DIR))
    # Local all-MiniLM ONNX embeddings — consistent vectors, no API key,
    # works offline. (Google's embedding EF needs the legacy SDK and would
    # produce vectors incompatible with the existing store.)
    ef = embedding_functions.DefaultEmbeddingFunction()
    _collection = _client.get_or_create_collection("crop_advisory", embedding_function=ef)
    return _collection


def _chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        # Prefer breaking at sentence boundaries
        if end < len(text):
            dot = text.rfind(". ", start, end)
            if dot > start + chunk_size // 2:
                end = dot + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap if end < len(text) else end
    return chunks


def ingest_docs() -> int:
    """Load all .txt/.md/.pdf-extracted docs from knowledge_base/docs into ChromaDB."""
    col = _get_collection()
    count = 0
    for path in sorted(DOCS_DIR.glob("*")):
        if path.suffix.lower() not in {".txt", ".md"}:
            continue
        existing = col.get(where={"source": str(path.name)})
        if existing["ids"]:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        crop, topic = "", ""
        name_stem = path.stem.replace("_", " ").lower()
        for known in ("rice", "wheat", "tomato", "cotton", "groundnut", "maize", "sugarcane", "onion", "potato"):
            if known in name_stem:
                crop = known.title()
                break
        blocks = len(col.get()["ids"])
        for i, chunk in enumerate(_chunk_text(text)):
            col.add(
                ids=[f"{path.name}::{i}"],
                documents=[chunk],
                metadatas=[{"source": path.name, "crop": crop}],
            )
        count += len(col.get()["ids"]) - blocks
    return count


def rag_crop_advisory(query: str, crop: str = "", top_k: int = 3) -> list[dict]:
    """
    Retrieve top-k expert advisory passages for a crop/question.
    Returns list of {'text', 'doc', 'crop', 'score'}.
    """
    col = _get_collection()
    if col.count() == 0:
        ingest_docs()
    if col.count() == 0:
        return []

    where = {"crop": crop} if crop else None
    try:
        res = col.query(query_texts=[query], n_results=top_k, where=where)
    except Exception:
        res = col.query(query_texts=[query], n_results=top_k)

    out = []
    for i, doc in enumerate(res["documents"][0]):
        meta = res["metadatas"][0][i] if res.get("metadatas") else {}
        dist = res["distances"][0][i] if res.get("distances") else 1.0
        out.append({
            "text": doc,
            "doc": meta.get("source", ""),
            "crop": meta.get("crop", ""),
            "score": round(1.0 - min(dist, 1.0), 3),
        })
    return out
