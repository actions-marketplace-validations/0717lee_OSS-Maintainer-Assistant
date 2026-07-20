from maintainer_agent.github.client import GitHubClient


def test_map_gql_pull_request():
    client = GitHubClient(offline=True)
    node = {
        "number": 5,
        "title": "Fix bug",
        "body": "Fixes #3",
        "author": {"login": "alice"},
        "authorAssociation": "CONTRIBUTOR",
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-02T00:00:00Z",
        "url": "https://github.com/o/r/pull/5",
        "comments": {"totalCount": 2},
        "additions": 10,
        "deletions": 2,
        "changedFiles": 2,
        "labels": {"nodes": [{"name": "bug"}]},
        "files": {"nodes": [{"path": "src/x.py", "additions": 8, "deletions": 2}]},
    }
    it = client._map_gql(node, is_pr=True)
    assert it.is_pr and it.number == 5
    assert it.author == "alice" and it.author_association == "CONTRIBUTOR"
    assert it.labels == ["bug"]
    assert it.additions == 10 and it.changed_files == 2
    assert it.files[0].filename == "src/x.py"
    assert it.linked_issues == [3]


def test_map_gql_issue_without_author():
    client = GitHubClient(offline=True)
    node = {"number": 9, "title": "Q", "body": "", "author": None, "labels": {"nodes": []}}
    it = client._map_gql(node, is_pr=False)
    assert not it.is_pr and it.number == 9 and it.author == ""


def test_graphql_enabled_by_env(monkeypatch):
    monkeypatch.setenv("MAINTAINER_AGENT_GITHUB_API", "graphql")
    assert GitHubClient(offline=True).use_graphql is True


def test_graphql_disabled_by_default(monkeypatch):
    monkeypatch.delenv("MAINTAINER_AGENT_GITHUB_API", raising=False)
    assert GitHubClient(offline=True).use_graphql is False
