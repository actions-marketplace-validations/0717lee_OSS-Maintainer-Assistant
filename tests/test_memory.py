import math

from maintainer_agent.memory.store import build_index, _hashing_embedding


def test_default_backend_is_tfidf(items):
    idx = build_index(items)
    assert getattr(idx, "backend", None) == "tfidf"


def test_duplicate_ranks_across_backends(items, by_number, monkeypatch):
    # Backend-agnostic: #101 must be a top neighbour of its duplicate #102.
    # (faiss path falls back to tfidf if faiss-cpu is not installed.)
    for backend in ("tfidf", "faiss"):
        monkeypatch.setenv("MAINTAINER_AGENT_VECTORS", backend)
        idx = build_index(items)
        top = [did for did, _score, _title in idx.query_item(by_number[102], top_k=3)]
        assert 101 in top


def test_hashing_embedding_is_l2_normalized():
    v = _hashing_embedding("crash zero division average three", dim=64)
    assert abs(math.sqrt(sum(x * x for x in v)) - 1.0) < 1e-6
