from __future__ import annotations

import hashlib
import os

import faiss
import numpy as np

EMBEDDING_DIM = 384
EMBEDDING_MODEL = "text-embedding-3-small"

_store: dict[str, tuple[faiss.IndexFlatL2, list[str]]] = {}


def _stable_token_bucket(token: str) -> int:
    digest = hashlib.md5(token.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % EMBEDDING_DIM


def _fake_embed(texts: list[str]) -> np.ndarray:
    out = np.zeros((len(texts), EMBEDDING_DIM), dtype="float32")
    for i, text in enumerate(texts):
        for token in text.lower().split():
            out[i, _stable_token_bucket(token)] += 1.0
    norms = np.linalg.norm(out, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return out / norms


async def _openai_embed(texts: list[str]) -> np.ndarray:
    from openai import AsyncOpenAI

    client = AsyncOpenAI()
    resp = await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
        dimensions=EMBEDDING_DIM,
    )
    return np.array([d.embedding for d in resp.data], dtype="float32")


async def embed(texts: list[str]) -> np.ndarray:
    if os.getenv("EMBEDDING_FAKE") == "1" or not os.getenv("OPENAI_API_KEY"):
        return _fake_embed(texts)
    return await _openai_embed(texts)


def _slot(student_id: str) -> tuple[faiss.IndexFlatL2, list[str]]:
    if student_id not in _store:
        _store[student_id] = (faiss.IndexFlatL2(EMBEDDING_DIM), [])
    return _store[student_id]


async def add_memory(student_id: str, text: str) -> None:
    if not text or not text.strip():
        return
    index, texts = _slot(student_id)
    emb = await embed([text])
    index.add(emb)
    texts.append(text)


async def get_memory(student_id: str, query: str, k: int = 5) -> list[str]:
    if student_id not in _store:
        return []
    index, texts = _store[student_id]
    if not texts or not query.strip():
        return []
    emb = await embed([query])
    actual_k = min(k, len(texts))
    _, idx = index.search(emb, actual_k)
    return [texts[i] for i in idx[0] if 0 <= i < len(texts)]


def reset() -> None:
    _store.clear()
