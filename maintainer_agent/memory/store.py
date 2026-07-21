"""Semantic memory for duplicate detection.

Two interchangeable backends behind one small interface (``add_items`` +
``query_item``):

* :class:`TfidfIndex` (default) - dependency-free TF-IDF cosine, deterministic
  and perfect for offline runs / CI.
* :class:`FaissIndex` (opt-in via ``MAINTAINER_AGENT_VECTORS=faiss``, needs the
  ``[vectors]`` extra) and :class:`ChromaIndex` (``=chroma``, needs ``[chroma]``)
  - real local vector stores. Embeddings come from a deterministic feature-
  hashing bag-of-words function (cosine via inner product on L2-normed vectors),
  so no model download is required and results stay reproducible.

``build_index`` picks the backend from the environment and falls back to TF-IDF
if the chosen backend is unavailable, so callers never need to care which one is
active.
"""
from __future__ import annotations

import hashlib
import math
import os
from collections import Counter
from typing import Iterable, Optional

from ..core.models import Item
from ..core.text import content_tokens


class TfidfIndex:
    backend = "tfidf"

    def __init__(self) -> None:
        self._tf: dict[int, Counter] = {}
        self._meta: dict[int, str] = {}  # id -> short title, for readable results
        self._df: Counter = Counter()
        self._n: int = 0

    def add(self, doc_id: int, text: str, title: str = "") -> None:
        tf = Counter(content_tokens(text))
        self._tf[doc_id] = tf
        self._meta[doc_id] = title
        for term in tf:
            self._df[term] += 1
        self._n += 1

    def add_items(self, items: Iterable[Item]) -> None:
        for it in items:
            self.add(it.number, f"{it.title}\n{it.body}", title=it.title)

    def _idf(self, term: str) -> float:
        # Smoothed IDF so a term present in every doc still contributes a little.
        return math.log((1 + self._n) / (1 + self._df.get(term, 0))) + 1.0

    def _vector(self, tf: Counter) -> dict[str, float]:
        return {t: f * self._idf(t) for t, f in tf.items()}

    @staticmethod
    def _cosine(va: dict[str, float], vb: dict[str, float]) -> float:
        common = set(va) & set(vb)
        num = sum(va[t] * vb[t] for t in common)
        na = math.sqrt(sum(v * v for v in va.values()))
        nb = math.sqrt(sum(v * v for v in vb.values()))
        return num / (na * nb) if na and nb else 0.0

    def query_text(
        self, text: str, exclude_id: Optional[int] = None, top_k: int = 5
    ) -> list[tuple[int, float, str]]:
        """Return ``(doc_id, score, title)`` ranked by similarity."""
        qv = self._vector(Counter(content_tokens(text)))
        scored: list[tuple[int, float, str]] = []
        for did, tf in self._tf.items():
            if did == exclude_id:
                continue
            score = self._cosine(qv, self._vector(tf))
            scored.append((did, score, self._meta.get(did, "")))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def query_item(self, item: Item, top_k: int = 5) -> list[tuple[int, float, str]]:
        return self.query_text(
            f"{item.title}\n{item.body}", exclude_id=item.number, top_k=top_k
        )


def _hashing_embedding(text: str, dim: int = 512) -> list[float]:
    """Deterministic, model-free feature-hashed bag-of-words vector (L2-normed).

    Uses md5 buckets so results are stable across processes (unlike ``hash``).
    """
    vec = [0.0] * dim
    for tok in content_tokens(text):
        bucket = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16) % dim
        vec[bucket] += 1.0
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def get_embedding(text: str, dim: int = 512) -> list[float]:
    """Return an embedding vector for *text*.

    Uses a real embedding model via litellm when
    ``MAINTAINER_AGENT_EMBEDDING_MODEL`` is set and a provider key is available.
    Falls back to deterministic feature-hashing otherwise (no model download,
    no API call, works fully offline).
    """
    model = os.getenv("MAINTAINER_AGENT_EMBEDDING_MODEL", "")
    if not model:
        return _hashing_embedding(text, dim)

    provider_keys = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AZURE_API_KEY",
                      "GEMINI_API_KEY", "DEEPSEEK_API_KEY")
    if not any(os.getenv(k) for k in provider_keys):
        return _hashing_embedding(text, dim)

    try:
        import litellm
        resp = litellm.embedding(model=model, input=[text[:8000]])
        vec = resp["data"][0]["embedding"]
        # L2-normalize so cosine = inner product.
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec
    except Exception:
        return _hashing_embedding(text, dim)


class ChromaIndex:
    """A real Chroma-backed vector index (cosine space)."""

    backend = "chroma"

    def __init__(self, dim: int = 512) -> None:
        import chromadb  # requires the [vectors] extra

        self.dim = dim
        self._client = chromadb.EphemeralClient()
        # Providing embeddings explicitly means the default (model-downloading)
        # embedding function is never invoked.
        self._col = self._client.get_or_create_collection(
            "issues", metadata={"hnsw:space": "cosine"}
        )
        self._count = 0

    def add(self, doc_id: int, text: str, title: str = "") -> None:
        self._col.add(
            ids=[str(doc_id)],
            embeddings=[get_embedding(text, self.dim)],
            metadatas=[{"title": title}],
        )
        self._count += 1

    def add_items(self, items: Iterable[Item]) -> None:
        items = list(items)
        if not items:
            return
        self._col.add(
            ids=[str(it.number) for it in items],
            embeddings=[get_embedding(f"{it.title}\n{it.body}", self.dim) for it in items],
            metadatas=[{"title": it.title} for it in items],
        )
        self._count += len(items)

    def query_text(
        self, text: str, exclude_id: Optional[int] = None, top_k: int = 5
    ) -> list[tuple[int, float, str]]:
        if self._count == 0:
            return []
        n = min(top_k + 1, self._count)
        res = self._col.query(query_embeddings=[get_embedding(text, self.dim)], n_results=n)
        ids = res["ids"][0]
        dists = res["distances"][0]
        metas = res.get("metadatas", [[]])[0] or [{}] * len(ids)
        out: list[tuple[int, float, str]] = []
        for id_str, dist, meta in zip(ids, dists, metas):
            did = int(id_str)
            if did == exclude_id:
                continue
            # cosine distance -> similarity
            out.append((did, 1.0 - float(dist), (meta or {}).get("title", "")))
        return out[:top_k]

    def query_item(self, item: Item, top_k: int = 5) -> list[tuple[int, float, str]]:
        return self.query_text(
            f"{item.title}\n{item.body}", exclude_id=item.number, top_k=top_k
        )


class FaissIndex:
    """A real FAISS-backed vector index (cosine via inner product on L2 vectors)."""

    backend = "faiss"

    def __init__(self, dim: int = 512) -> None:
        import faiss  # requires the [vectors] extra
        import numpy as np

        self._faiss = faiss
        self._np = np
        self.dim = dim
        self._index = faiss.IndexIDMap2(faiss.IndexFlatIP(dim))
        self._meta: dict[int, str] = {}

    def _matrix(self, texts: list[str]):
        return self._np.array(
            [get_embedding(t, self.dim) for t in texts], dtype="float32"
        )

    def add(self, doc_id: int, text: str, title: str = "") -> None:
        self._index.add_with_ids(self._matrix([text]), self._np.array([doc_id], dtype="int64"))
        self._meta[doc_id] = title

    def add_items(self, items: Iterable[Item]) -> None:
        items = list(items)
        if not items:
            return
        texts = [f"{it.title}\n{it.body}" for it in items]
        ids = self._np.array([it.number for it in items], dtype="int64")
        self._index.add_with_ids(self._matrix(texts), ids)
        for it in items:
            self._meta[it.number] = it.title

    def query_text(
        self, text: str, exclude_id: Optional[int] = None, top_k: int = 5
    ) -> list[tuple[int, float, str]]:
        if self._index.ntotal == 0:
            return []
        k = min(top_k + 1, self._index.ntotal)
        scores, ids = self._index.search(self._matrix([text]), k)
        out: list[tuple[int, float, str]] = []
        for score, did in zip(scores[0].tolist(), ids[0].tolist()):
            if did == -1 or did == exclude_id:
                continue
            out.append((int(did), float(score), self._meta.get(int(did), "")))
        return out[:top_k]

    def query_item(self, item: Item, top_k: int = 5) -> list[tuple[int, float, str]]:
        return self.query_text(
            f"{item.title}\n{item.body}", exclude_id=item.number, top_k=top_k
        )


_BACKENDS = {"faiss": FaissIndex, "chroma": ChromaIndex}


def build_index(items: Iterable[Item]):
    """Build the configured index backend, falling back to TF-IDF on any issue."""
    backend = os.getenv("MAINTAINER_AGENT_VECTORS", "tfidf").lower()
    factory = _BACKENDS.get(backend)
    if factory is not None:
        try:
            index = factory()
        except Exception:
            index = TfidfIndex()
    else:
        index = TfidfIndex()
    index.add_items(items)  # type: ignore[attr-defined]
    return index
