"""Repository-level configuration.

A repo config is a small YAML file (see ``maintainer_agent/configs/``) that acts
as the agents' policy. It also points at a CONTRIBUTING file whose text is used
as the "job description" the Quality/AI-slop agent evaluates PRs against.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field

from .paths import CONFIGS_DIR, FIXTURES_DIR


class LabelRule(BaseModel):
    """Assign ``label`` when any keyword appears in the title/body."""

    label: str
    keywords: list[str] = Field(default_factory=list)


class RepoConfig(BaseModel):
    repo: str  # "owner/name"
    description: str = ""

    # Where CONTRIBUTING guidance comes from. Either an explicit fixture-relative
    # path or (at runtime) the file is fetched from the live repo.
    contributing_path: str = ""
    contributing: str = ""  # resolved text, filled in by the loader

    # Triage taxonomy.
    labels: list[str] = Field(
        default_factory=lambda: [
            "bug",
            "enhancement",
            "documentation",
            "question",
            "good first issue",
        ]
    )
    label_rules: list[LabelRule] = Field(default_factory=list)
    priority_keywords: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "high": ["crash", "data loss", "security", "regression", "cannot", "broken"],
            "medium": ["error", "fails", "unexpected", "incorrect"],
            "low": ["typo", "docs", "nit", "cosmetic"],
        }
    )
    bug_keywords: list[str] = Field(
        default_factory=lambda: [
            "error",
            "crash",
            "traceback",
            "exception",
            "stack trace",
            "reproduce",
            "steps to reproduce",
        ]
    )

    # Thresholds (0..1).
    slop_threshold: float = 0.6  # >= this -> flag as likely AI slop
    duplicate_threshold: float = 0.35  # >= this same-kind similarity -> likely duplicate

    # Responder tone.
    tone: str = "friendly, concise, respectful, and specific"

    def resolve_contributing(self) -> str:
        """Load CONTRIBUTING text from the configured fixture path, if any."""
        if self.contributing:
            return self.contributing
        if self.contributing_path:
            candidate = FIXTURES_DIR / self.contributing_path
            if candidate.exists():
                self.contributing = candidate.read_text(encoding="utf-8")
        return self.contributing


def _config_path(name_or_path: str) -> Path:
    """Resolve a config reference to a concrete YAML path.

    Accepts a bare name ("octo-demo"), a name with extension, or a full path.
    """
    p = Path(name_or_path)
    if p.suffix in {".yaml", ".yml"} and p.exists():
        return p
    for candidate in (
        CONFIGS_DIR / f"{name_or_path}.yaml",
        CONFIGS_DIR / f"{name_or_path}.yml",
        CONFIGS_DIR / name_or_path,
    ):
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"No repo config found for '{name_or_path}'. "
        f"Looked in {CONFIGS_DIR} and as a direct path."
    )


def load_repo_config(name_or_path: str) -> RepoConfig:
    """Load and fully resolve a repo config (including CONTRIBUTING text)."""
    path = _config_path(name_or_path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    config = RepoConfig(**data)
    config.resolve_contributing()
    return config


def default_config_name() -> str:
    """The demo config shipped with the project."""
    return os.getenv("MAINTAINER_AGENT_CONFIG", "octo-demo")


def config_for_repo(repo: Optional[str]) -> RepoConfig:
    """Best-effort: use a config named after the repo, else the demo config.

    ``repo`` looks like "owner/name"; we try "name" and "owner-name" configs
    before falling back to the bundled demo config (still usable for live repos).
    """
    if repo:
        owner, _, name = repo.partition("/")
        for candidate in (name, f"{owner}-{name}", repo.replace("/", "-")):
            try:
                cfg = load_repo_config(candidate)
                cfg.repo = repo
                return cfg
            except FileNotFoundError:
                continue
    cfg = load_repo_config(default_config_name())
    if repo:
        cfg.repo = repo
    return cfg
