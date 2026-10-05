import math

import pytest

from maintainer_agent.memory import store
from maintainer_agent.memory.store import _hashing_embedding, build_index


def test_default_backend_is_tfidf(items, by_number, monkeypatch):
    monkeypatch.delenv("MAINTAINER_AGENT_VECTORS", raising=False)
    monkeypatch.delenv("MAINTAINER_AGENT_EMBEDDING_MODEL", raising=False)
    idx = build_index(items)
    assert idx.backend == "tfidf"
    top = [did for did, _score, _title in idx.query_item(by_number[102], top_k=3)]
    assert 101 in top


def test_requested_faiss_falls_back_to_tfidf_when_unavailable(items, by_number, monkeypatch):
    monkeypatch.setenv("MAINTAINER_AGENT_VECTORS", "faiss")
    monkeypatch.delenv("MAINTAINER_AGENT_EMBEDDING_MODEL", raising=False)

    def unavailable_faiss():
        raise ImportError("faiss-cpu is unavailable for this test")

    monkeypatch.setitem(store._BACKENDS, "faiss", unavailable_faiss)
    idx = build_index(items)
    assert idx.backend == "tfidf"
    top = [did for did, _score, _title in idx.query_item(by_number[102], top_k=3)]
    assert 101 in top


def test_available_faiss_backend_ranks_duplicates(items, by_number, monkeypatch):
    pytest.importorskip("faiss", reason="faiss-cpu is not installed")
    pytest.importorskip("numpy", reason="numpy is not installed")
    monkeypatch.setenv("MAINTAINER_AGENT_VECTORS", "faiss")
    monkeypatch.delenv("MAINTAINER_AGENT_EMBEDDING_MODEL", raising=False)
    idx = build_index(items)
    assert idx.backend == "faiss"
    top = [did for did, _score, _title in idx.query_item(by_number[102], top_k=3)]
    assert 101 in top


def test_hashing_embedding_is_l2_normalized():
    v = _hashing_embedding("crash zero division average three", dim=64)
    assert abs(math.sqrt(sum(x * x for x in v)) - 1.0) < 1e-6
