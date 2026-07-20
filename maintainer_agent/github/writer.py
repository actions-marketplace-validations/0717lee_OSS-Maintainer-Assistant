"""Optional GitHub *write* path, used only behind the approval gate.

Two callables with the same signature ``(action, item) -> None``:

* :class:`SimulatedWriter` (default): prints what *would* happen. Safe; never
  touches GitHub. This is what the demo uses.
* :class:`GitHubWriter`: performs the real REST mutation. Only wired in when the
  user passes ``--apply --allow-write`` with a token on a live repo.

Keeping writes isolated here means the rest of the system is provably read-only.
"""
from __future__ import annotations

import os
from typing import Callable, Optional

import httpx

from ..core.models import Action, ActionType, Item

API_ROOT = "https://api.github.com"

Printer = Callable[[str], None]


class SimulatedWriter:
    def __init__(self, printer: Printer = print):
        self._print = printer

    def __call__(self, action: Action, item: Item) -> None:
        self._print(f"[SIMULATED WRITE] {action.type.value} on #{item.number}: {action.payload}")


class GitHubWriter:
    """Real mutations. Constructed only when explicitly allowed."""

    def __init__(self, repo: str, token: Optional[str] = None, timeout: float = 15.0):
        self.repo = repo
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GitHubWriter requires a GITHUB_TOKEN")
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": f"Bearer {self.token}",
        }

    def __call__(self, action: Action, item: Item) -> None:
        with httpx.Client(headers=self._headers(), timeout=self.timeout) as client:
            if action.type == ActionType.ADD_LABELS:
                resp = client.post(
                    f"{API_ROOT}/repos/{self.repo}/issues/{item.number}/labels",
                    json={"labels": action.payload.get("labels", [])},
                )
            elif action.type == ActionType.COMMENT:
                resp = client.post(
                    f"{API_ROOT}/repos/{self.repo}/issues/{item.number}/comments",
                    json={"body": action.payload.get("body", "")},
                )
            elif action.type == ActionType.CLOSE:
                resp = client.patch(
                    f"{API_ROOT}/repos/{self.repo}/issues/{item.number}",
                    json={"state": "closed", "state_reason": "not_planned"},
                )
            else:
                return
            resp.raise_for_status()
