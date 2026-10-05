import importlib
from unittest.mock import patch

import pytest

from maintainer_agent.memory.memory import AgentMemory


@pytest.mark.parametrize(
    ("records", "expected_risk"),
    [
        ([], "unknown"),
        ([{"slop": False}], "low"),
        ([{"slop": True}, {"slop": False}, {"slop": False}, {"slop": False}], "medium"),
        ([{"slop": True}, {"slop": True}], "high"),
    ],
)
def test_contributor_endpoint_reuses_loaded_stats_and_preserves_risk_labels(
    tmp_path, monkeypatch, records, expected_risk
):
    db_path = tmp_path / "memory.db"
    seed = AgentMemory(db_path)
    for item_number, record in enumerate(records, start=1):
        seed.record_result(
            repo="octo/demo",
            item_number=item_number,
            kind="pull_request",
            title=f"PR {item_number}",
            author="alice",
            quality_verdict="likely-ai-slop" if record["slop"] else "clean",
            slop_score=1.0 if record["slop"] else 0.0,
        )
    seed.close()

    lookups = 0
    original_get_stats = AgentMemory.get_contributor_stats

    def counted_get_stats(self, author, repo):
        nonlocal lookups
        lookups += 1
        return original_get_stats(self, author, repo)

    monkeypatch.setattr(AgentMemory, "get_contributor_stats", counted_get_stats)
    with patch("dotenv.load_dotenv", return_value=False):
        server = importlib.import_module("maintainer_agent.api.server")
    monkeypatch.setattr(server, "AgentMemory", lambda: AgentMemory(db_path))

    response = server.api_contributor_memory("octo/demo", "alice")

    assert response["risk"] == expected_risk
    assert lookups == 1
    assert response["author"] == "alice"
    assert response["repo"] == "octo/demo"
    assert response["stats"].get("total_prs", 0) == len(records)

    memory = AgentMemory(db_path)
    try:
        assert memory.get_contributor_risk_label("alice", "octo/demo") == expected_risk
    finally:
        memory.close()
