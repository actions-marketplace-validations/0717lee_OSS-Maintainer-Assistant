"""Persistent agent memory across runs (SQLite).

Stores contributor profiles (slop history, PR counts) and item analysis history
so agents can reason about patterns over time — "this contributor's last 3 PRs
were all flagged as AI slop" or "this issue was already triaged last week".

SQLite is in the Python standard library, so this works with zero extra deps.
The database lives in the runtime directory (``.runtime/memory.db`` by default).
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from ..core.paths import RUNTIME_DIR

DB_PATH = RUNTIME_DIR / "memory.db"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgentMemory:
    """Cross-run persistent memory backed by SQLite."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.path = db_path or DB_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS contributor_stats (
                author     TEXT NOT NULL,
                repo       TEXT NOT NULL,
                total_prs       INTEGER DEFAULT 0,
                total_issues    INTEGER DEFAULT 0,
                slop_count      INTEGER DEFAULT 0,
                avg_slop_score  REAL DEFAULT 0,
                last_verdict    TEXT,
                last_seen       TEXT,
                PRIMARY KEY (author, repo)
            );

            CREATE TABLE IF NOT EXISTS item_history (
                repo         TEXT NOT NULL,
                number       INTEGER NOT NULL,
                kind         TEXT,
                title        TEXT,
                author       TEXT,
                triage_verdict   TEXT,
                quality_verdict  TEXT,
                slop_score       REAL,
                confidence       REAL,
                analyzed_at      TEXT,
                PRIMARY KEY (repo, number)
            );
            """
        )
        self._conn.commit()

    def record_result(
        self,
        repo: str,
        item_number: int,
        kind: str,
        title: str,
        author: str,
        triage_verdict: str = "",
        quality_verdict: str = "",
        slop_score: float = 0.0,
        confidence: float = 0.0,
    ) -> None:
        """Record (or update) an analysis result for a single item."""
        now = _now()

        # Upsert item history.
        self._conn.execute(
            """
            INSERT INTO item_history
                (repo, number, kind, title, author, triage_verdict,
                 quality_verdict, slop_score, confidence, analyzed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(repo, number) DO UPDATE SET
                kind=excluded.kind, title=excluded.title, author=excluded.author,
                triage_verdict=excluded.triage_verdict,
                quality_verdict=excluded.quality_verdict,
                slop_score=excluded.slop_score,
                confidence=excluded.confidence,
                analyzed_at=excluded.analyzed_at
            """,
            (repo, item_number, kind, title, author, triage_verdict,
             quality_verdict, slop_score, confidence, now),
        )

        # Update contributor stats.
        is_pr = kind == "pull_request"
        is_slop = quality_verdict == "likely-ai-slop"

        row = self._conn.execute(
            "SELECT total_prs, total_issues, slop_count, avg_slop_score FROM contributor_stats WHERE author=? AND repo=?",
            (author, repo),
        ).fetchone()

        if row:
            total_prs = row["total_prs"] + (1 if is_pr else 0)
            total_issues = row["total_issues"] + (0 if is_pr else 1)
            slop_count = row["slop_count"] + (1 if is_slop else 0)
            # Running average: blend old avg with new score.
            n = total_prs + total_issues
            old_avg = row["avg_slop_score"]
            new_avg = (old_avg * (n - 1) + slop_score) / n if n > 0 else slop_score

            self._conn.execute(
                """
                UPDATE contributor_stats SET
                    total_prs=?, total_issues=?, slop_count=?,
                    avg_slop_score=?, last_verdict=?, last_seen=?
                WHERE author=? AND repo=?
                """,
                (total_prs, total_issues, slop_count, new_avg,
                 quality_verdict or triage_verdict, now, author, repo),
            )
        else:
            self._conn.execute(
                """
                INSERT INTO contributor_stats
                    (author, repo, total_prs, total_issues, slop_count,
                     avg_slop_score, last_verdict, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (author, repo,
                 1 if is_pr else 0,
                 0 if is_pr else 1,
                 1 if is_slop else 0,
                 slop_score,
                 quality_verdict or triage_verdict,
                 now),
            )

        self._conn.commit()

    def get_contributor_stats(self, author: str, repo: str) -> dict[str, Any]:
        """Return a contributor's profile for a repo, or empty dict if unknown."""
        row = self._conn.execute(
            "SELECT * FROM contributor_stats WHERE author=? AND repo=?",
            (author, repo),
        ).fetchone()
        if not row:
            return {}
        return dict(row)

    def get_contributor_risk_label(self, author: str, repo: str) -> str:
        """Quick risk assessment: 'high', 'medium', 'low', or 'unknown'."""
        stats = self.get_contributor_stats(author, repo)
        if not stats:
            return "unknown"
        slop_count = stats.get("slop_count", 0)
        total = stats.get("total_prs", 0) + stats.get("total_issues", 0)
        if total == 0:
            return "unknown"
        slop_rate = slop_count / total
        if slop_rate >= 0.5 and total >= 2:
            return "high"
        if slop_rate >= 0.25:
            return "medium"
        return "low"

    def get_item_history(self, repo: str, number: int) -> dict[str, Any]:
        """Return the last analysis record for an item, or empty dict."""
        row = self._conn.execute(
            "SELECT * FROM item_history WHERE repo=? AND number=?",
            (repo, number),
        ).fetchone()
        if not row:
            return {}
        return dict(row)

    def get_repo_summary(self, repo: str) -> dict[str, Any]:
        """Aggregate stats for a repo."""
        total = self._conn.execute(
            "SELECT COUNT(*) as n FROM item_history WHERE repo=?", (repo,)
        ).fetchone()["n"]
        slop = self._conn.execute(
            "SELECT COUNT(*) as n FROM item_history WHERE repo=? AND quality_verdict='likely-ai-slop'",
            (repo,),
        ).fetchone()["n"]
        contributors = self._conn.execute(
            "SELECT COUNT(DISTINCT author) as n FROM item_history WHERE repo=?", (repo,)
        ).fetchone()["n"]
        return {
            "repo": repo,
            "total_analyzed": total,
            "total_slop": slop,
            "unique_contributors": contributors,
        }

    def close(self) -> None:
        self._conn.close()
