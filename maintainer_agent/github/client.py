"""Read-only GitHub access.

Two backends behind one interface:

* **Live** (``offline=False``): the public REST API via httpx. Works
  unauthenticated for public repos; a ``GITHUB_TOKEN`` raises the rate limit.
* **Offline** (``offline=True``): bundled JSON fixtures, so the whole project
  runs with zero network and zero credentials.

This module never writes to GitHub. Mutations (if ever enabled) live behind the
approval gate and a separate, explicitly-constructed writer.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional

import httpx

from ..core.models import FileChange, Item, ItemKind
from ..core.paths import FIXTURES_DIR
from ..core.text import extract_linked_issues

API_ROOT = "https://api.github.com"
GRAPHQL_ROOT = "https://api.github.com/graphql"
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

# One round-trip fetches open issues and PRs (with PR diff stats + files).
_ISSUES_PRS_QUERY = """
query($owner:String!,$name:String!,$n:Int!){
  repository(owner:$owner,name:$name){
    issues(first:$n, states:OPEN, orderBy:{field:UPDATED_AT,direction:DESC}){
      nodes{ number title body createdAt updatedAt url comments{totalCount}
             author{login} authorAssociation labels(first:20){nodes{name}} }
    }
    pullRequests(first:$n, states:OPEN, orderBy:{field:UPDATED_AT,direction:DESC}){
      nodes{ number title body createdAt updatedAt url comments{totalCount}
             author{login} authorAssociation additions deletions changedFiles
             labels(first:20){nodes{name}} files(first:100){nodes{path additions deletions}} }
    }
  }
}
"""


class GitHubClient:
    def __init__(
        self,
        token: Optional[str] = None,
        offline: bool = False,
        timeout: float = 15.0,
        use_graphql: Optional[bool] = None,
    ):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.offline = offline
        self.timeout = timeout
        # GraphQL requires auth; enable via arg or MAINTAINER_AGENT_GITHUB_API=graphql.
        if use_graphql is None:
            use_graphql = os.getenv("MAINTAINER_AGENT_GITHUB_API", "").lower() == "graphql"
        self.use_graphql = use_graphql

    # ------------------------------------------------------------------ #
    # Public API                                                          #
    # ------------------------------------------------------------------ #
    def list_items(self, repo: Optional[str] = None, limit: int = 30, state: str = "open") -> list[Item]:
        if self.offline or not repo:
            return self._fixture_items(repo)[:limit]
        if self.use_graphql and self.token:
            return self._live_items_graphql(repo, limit=limit)
        return self._live_items(repo, limit=limit, state=state)

    def get_item(self, repo: Optional[str], number: int) -> Optional[Item]:
        for it in self.list_items(repo, limit=1000):
            if it.number == number:
                return it
        if self.offline or not repo:
            return None
        return self._live_item(repo, number)

    def get_contributing(self, repo: Optional[str]) -> str:
        if self.offline or not repo:
            path = self._fixture_dir(repo) / "contributing.md"
            return path.read_text(encoding="utf-8") if path.exists() else ""
        return self._live_contributing(repo)

    # ------------------------------------------------------------------ #
    # Offline fixtures                                                    #
    # ------------------------------------------------------------------ #
    def _fixture_dir(self, repo: Optional[str]):
        name = repo.split("/")[-1] if repo else "octo-demo"
        candidate = FIXTURES_DIR / name
        return candidate if candidate.exists() else FIXTURES_DIR / "octo-demo"

    def _fixture_items(self, repo: Optional[str]) -> list[Item]:
        path = self._fixture_dir(repo) / "items.json"
        if not path.exists():
            return []
        raw = json.loads(path.read_text(encoding="utf-8"))
        items = [Item(**obj) for obj in raw]
        # Derive linked issues from the body when not stated explicitly.
        for it in items:
            if it.is_pr and not it.linked_issues:
                it.linked_issues = extract_linked_issues(it.body)
        return items

    # ------------------------------------------------------------------ #
    # Live REST                                                           #
    # ------------------------------------------------------------------ #
    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _get(self, client: httpx.Client, path: str, **params):
        resp = client.get(f"{API_ROOT}{path}", params=params or None)
        resp.raise_for_status()
        return resp.json()

    def _live_items(self, repo: str, limit: int, state: str) -> list[Item]:
        items: list[Item] = []
        per_page = min(limit, 50)
        with httpx.Client(headers=self._headers(), timeout=self.timeout) as client:
            issues = self._get(client, f"/repos/{repo}/issues", state=state, per_page=per_page)
            for obj in issues[:limit]:
                items.append(self._map_issue(client, repo, obj))
        return items

    # ------------------------------------------------------------------ #
    # Live GraphQL (requires a token)                                     #
    # ------------------------------------------------------------------ #
    def _graphql(self, query: str, variables: dict) -> dict:
        with httpx.Client(headers=self._headers(), timeout=self.timeout) as client:
            resp = client.post(GRAPHQL_ROOT, json={"query": query, "variables": variables})
            resp.raise_for_status()
            payload = resp.json()
        if payload.get("errors"):
            raise httpx.RequestError(f"GraphQL error: {payload['errors']}")
        return payload["data"]

    def _live_items_graphql(self, repo: str, limit: int) -> list[Item]:
        owner, _, name = repo.partition("/")
        data = self._graphql(
            _ISSUES_PRS_QUERY, {"owner": owner, "name": name, "n": min(limit, 50)}
        )
        node = data.get("repository") or {}
        items: list[Item] = []
        for n in ((node.get("issues") or {}).get("nodes") or []):
            items.append(self._map_gql(n, is_pr=False))
        for n in ((node.get("pullRequests") or {}).get("nodes") or []):
            items.append(self._map_gql(n, is_pr=True))
        items.sort(key=lambda it: (it.updated_at or it.created_at or _EPOCH), reverse=True)
        return items[:limit]

    def _map_gql(self, n: dict, is_pr: bool) -> Item:
        labels = [x["name"] for x in ((n.get("labels") or {}).get("nodes") or [])]
        item = Item(
            number=n["number"],
            kind=ItemKind.PULL_REQUEST if is_pr else ItemKind.ISSUE,
            title=n.get("title") or "",
            body=n.get("body") or "",
            author=(n.get("author") or {}).get("login", ""),
            author_association=n.get("authorAssociation", "NONE"),
            state="open",
            labels=labels,
            created_at=n.get("createdAt"),
            updated_at=n.get("updatedAt"),
            url=n.get("url", ""),
            comments_count=(n.get("comments") or {}).get("totalCount", 0),
        )
        if is_pr:
            item.additions = n.get("additions", 0)
            item.deletions = n.get("deletions", 0)
            item.changed_files = n.get("changedFiles", 0)
            item.files = [
                FileChange(
                    filename=f.get("path", ""),
                    additions=f.get("additions", 0),
                    deletions=f.get("deletions", 0),
                )
                for f in ((n.get("files") or {}).get("nodes") or [])
            ]
            item.linked_issues = extract_linked_issues(item.body)
        return item

    def _live_item(self, repo: str, number: int) -> Optional[Item]:
        with httpx.Client(headers=self._headers(), timeout=self.timeout) as client:
            try:
                obj = self._get(client, f"/repos/{repo}/issues/{number}")
            except httpx.HTTPStatusError:
                return None
            return self._map_issue(client, repo, obj)

    def _map_issue(self, client: httpx.Client, repo: str, obj: dict) -> Item:
        is_pr = "pull_request" in obj
        item = Item(
            number=obj["number"],
            kind=ItemKind.PULL_REQUEST if is_pr else ItemKind.ISSUE,
            title=obj.get("title") or "",
            body=obj.get("body") or "",
            author=(obj.get("user") or {}).get("login", ""),
            author_association=obj.get("author_association", "NONE"),
            state=obj.get("state", "open"),
            labels=[lbl["name"] for lbl in obj.get("labels", []) if isinstance(lbl, dict)],
            created_at=obj.get("created_at"),
            updated_at=obj.get("updated_at"),
            url=obj.get("html_url", ""),
            comments_count=obj.get("comments", 0),
        )
        if is_pr:
            self._enrich_pr(client, repo, item)
        return item

    def _enrich_pr(self, client: httpx.Client, repo: str, item: Item) -> None:
        try:
            pr = self._get(client, f"/repos/{repo}/pulls/{item.number}")
            item.additions = pr.get("additions", 0)
            item.deletions = pr.get("deletions", 0)
            item.changed_files = pr.get("changed_files", 0)
            files = self._get(client, f"/repos/{repo}/pulls/{item.number}/files", per_page=100)
            item.files = [
                FileChange(
                    filename=f.get("filename", ""),
                    additions=f.get("additions", 0),
                    deletions=f.get("deletions", 0),
                    status=f.get("status", "modified"),
                )
                for f in files
            ]
        except httpx.HTTPStatusError:
            pass
        item.linked_issues = extract_linked_issues(item.body)

    def _live_contributing(self, repo: str) -> str:
        import base64

        with httpx.Client(headers=self._headers(), timeout=self.timeout) as client:
            for path in ("CONTRIBUTING.md", ".github/CONTRIBUTING.md", "docs/CONTRIBUTING.md"):
                try:
                    obj = self._get(client, f"/repos/{repo}/contents/{path}")
                except httpx.HTTPStatusError:
                    continue
                if isinstance(obj, dict) and obj.get("content"):
                    return base64.b64decode(obj["content"]).decode("utf-8", errors="replace")
        return ""
