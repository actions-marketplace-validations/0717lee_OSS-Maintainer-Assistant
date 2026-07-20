"""Append-only JSONL audit log.

Every agent decision and every action (proposed / approved / rejected / applied)
is recorded as one JSON line. This is a core trust feature: a maintainer can
always reconstruct exactly what the system decided and why.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

from .paths import AUDIT_DIR, ensure_runtime_dirs


class AuditLog:
    def __init__(self, path: Optional[Path] = None, run_id: Optional[str] = None):
        ensure_runtime_dirs()
        self.path = path or (AUDIT_DIR / "audit.jsonl")
        self.run_id = run_id or uuid.uuid4().hex[:12]

    def record(self, event_type: str, **fields: Any) -> dict[str, Any]:
        """Append one event and return it."""
        event = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "event": event_type,
            **fields,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
        return event

    def events(self, limit: Optional[int] = None) -> list[dict[str, Any]]:
        """Read events back (most-recent-last), optionally limited."""
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        if limit is not None:
            lines = lines[-limit:]
        out: list[dict[str, Any]] = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out

    def iter_events(self) -> Iterator[dict[str, Any]]:
        yield from self.events()
