"""A minimal, safety-first Docker sandbox for running untrusted snippets.

Design choices that matter for running code from strangers' bug reports:

* code is piped over **stdin** (no host volume mounts, no temp files);
* the container has **no network** (``--network none``);
* **all capabilities dropped**, **read-only** root fs, writable ``/tmp`` only;
* memory / CPU / PID limits and a hard wall-clock **timeout**;
* ``--rm`` so nothing is left behind.

If Docker is unavailable or the sandbox is disabled, methods return a result
with ``ran=False`` and a human-readable ``reason`` -- callers degrade gracefully.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class SandboxResult:
    ran: bool
    exit_code: Optional[int]
    stdout: str
    stderr: str
    timed_out: bool = False
    reason: str = ""

    @property
    def crashed(self) -> bool:
        """Non-zero exit typically means a traceback / crash was reproduced."""
        return self.ran and self.exit_code is not None and self.exit_code != 0


class Sandbox:
    def __init__(
        self,
        image: str = "python:3.11-slim",
        timeout: int = 30,
        memory: str = "256m",
        cpus: str = "1.0",
        enabled: bool = True,
    ):
        self.image = image
        self.timeout = timeout
        self.memory = memory
        self.cpus = cpus
        self.enabled = enabled

    @staticmethod
    def docker_available() -> bool:
        return shutil.which("docker") is not None

    def _docker_cmd(self) -> list[str]:
        return [
            "docker", "run", "--rm", "-i",
            "--network", "none",
            "--cap-drop", "ALL",
            "--read-only",
            "--tmpfs", "/tmp:size=16m",
            "--memory", self.memory,
            "--memory-swap", self.memory,  # disallow swap growth
            "--cpus", self.cpus,
            "--pids-limit", "128",
            self.image,
            "python", "-",
        ]

    def run_python(self, code: str) -> SandboxResult:
        if not self.enabled:
            return SandboxResult(False, None, "", "", reason="sandbox disabled")
        if not self.docker_available():
            return SandboxResult(False, None, "", "", reason="docker not available on PATH")
        try:
            proc = subprocess.run(
                self._docker_cmd(),
                input=code,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                False, None, "", "", timed_out=True,
                reason=f"execution exceeded {self.timeout}s",
            )
        except FileNotFoundError:
            return SandboxResult(False, None, "", "", reason="docker not available")
        except Exception as exc:  # pragma: no cover - defensive
            return SandboxResult(False, None, "", "", reason=f"sandbox error: {exc}")
        return SandboxResult(
            ran=True,
            exit_code=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
        )
