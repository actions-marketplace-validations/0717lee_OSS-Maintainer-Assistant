"""Filesystem locations for bundled data and runtime artifacts.

Everything is resolved relative to the installed package so the project works
whether it is run from source or installed as a wheel.
"""
from __future__ import annotations

from pathlib import Path

# maintainer_agent/core/paths.py -> parents[1] == maintainer_agent/
PACKAGE_ROOT: Path = Path(__file__).resolve().parents[1]
REPO_ROOT: Path = PACKAGE_ROOT.parent

# Bundled, read-only data.
CONFIGS_DIR: Path = PACKAGE_ROOT / "configs"
FIXTURES_DIR: Path = PACKAGE_ROOT / "github" / "fixtures"
EVAL_DIR: Path = PACKAGE_ROOT / "eval"
STATIC_DIR: Path = PACKAGE_ROOT / "api" / "static"

# Writable runtime artifacts (audit logs, cached indexes, run outputs).
RUNTIME_DIR: Path = REPO_ROOT / ".runtime"
AUDIT_DIR: Path = RUNTIME_DIR / "audit"


def ensure_runtime_dirs() -> None:
    """Create the writable runtime directories if they do not yet exist."""
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
