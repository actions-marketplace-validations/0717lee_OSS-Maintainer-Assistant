"""Thin service layer shared by the CLI and the HTTP API.

Loads items + config from the right source (live repo or offline fixtures) and
exposes a single ``run`` entry point so both front-ends behave identically.
"""
from __future__ import annotations

from typing import Optional

from .core.config import RepoConfig, config_for_repo, load_repo_config
from .core.models import Item
from .github.client import GitHubClient


def load_inputs(
    repo: Optional[str] = None,
    fixtures: bool = False,
    limit: int = 30,
    config_name: Optional[str] = None,
) -> tuple[list[Item], RepoConfig, bool]:
    """Return ``(items, config, offline)``.

    Offline (fixtures) is used when explicitly requested or when no repo is given.
    """
    offline = fixtures or not repo
    client = GitHubClient(offline=offline)
    items = client.list_items(repo, limit=limit)

    if config_name:
        cfg = load_repo_config(config_name)
        if repo:
            cfg.repo = repo
    else:
        cfg = config_for_repo(repo)

    # Fill CONTRIBUTING from the source if the config didn't bundle it.
    if not cfg.contributing:
        try:
            cfg.contributing = client.get_contributing(repo)
        except Exception:
            cfg.contributing = ""
    return items, cfg, offline
