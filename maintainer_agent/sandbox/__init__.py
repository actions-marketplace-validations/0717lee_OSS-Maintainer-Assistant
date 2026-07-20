"""Sandboxed execution for bug reproduction (Docker-backed, safety-first)."""
from .docker_runner import Sandbox, SandboxResult

__all__ = ["Sandbox", "SandboxResult"]
