"""Pydantic data models shared across agents.

These are intentionally transport-agnostic: the GitHub client maps API payloads
(or offline fixtures) into an :class:`Item`, agents read the ``Item`` and emit
:class:`Decision` / :class:`Action` objects, and the orchestrator collects them
into a :class:`PipelineResult`.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Inputs                                                                       #
# --------------------------------------------------------------------------- #
class ItemKind(str, Enum):
    ISSUE = "issue"
    PULL_REQUEST = "pull_request"


class FileChange(BaseModel):
    filename: str
    additions: int = 0
    deletions: int = 0
    status: str = "modified"


class Item(BaseModel):
    """A unified view over a GitHub issue or pull request."""

    number: int
    kind: ItemKind
    title: str
    body: str = ""
    author: str = ""
    # OWNER | MEMBER | COLLABORATOR | CONTRIBUTOR | FIRST_TIME_CONTRIBUTOR | NONE
    author_association: str = "NONE"
    state: str = "open"
    labels: list[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    url: str = ""
    comments_count: int = 0

    # Pull-request specific fields (zero/empty for issues).
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    files: list[FileChange] = Field(default_factory=list)
    diff: str = ""
    linked_issues: list[int] = Field(default_factory=list)

    @property
    def is_pr(self) -> bool:
        return self.kind == ItemKind.PULL_REQUEST

    @property
    def total_changes(self) -> int:
        return self.additions + self.deletions

    @property
    def is_newcomer(self) -> bool:
        return self.author_association in {"NONE", "FIRST_TIME_CONTRIBUTOR", "CONTRIBUTOR"}


# --------------------------------------------------------------------------- #
# Explainable decisions                                                        #
# --------------------------------------------------------------------------- #
class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Evidence(BaseModel):
    """A single, human-readable reason contributing to a decision."""

    kind: str  # "heuristic" | "llm" | "similarity" | "sandbox"
    detail: str
    weight: float = 0.0  # signed contribution to the agent's score
    severity: Severity = Severity.INFO


class Decision(BaseModel):
    agent: str
    verdict: str  # agent-specific, e.g. "likely-ai-slop", "duplicate", "bug"
    confidence: float = 0.0  # 0..1
    rationale: str = ""
    evidence: list[Evidence] = Field(default_factory=list)
    # Structured, machine-readable outputs (labels, priority, slop_score, ...).
    data: dict[str, Any] = Field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Proposed actions (always human-gated)                                        #
# --------------------------------------------------------------------------- #
class ActionType(str, Enum):
    ADD_LABELS = "add_labels"
    COMMENT = "comment"
    CLOSE = "close"
    ASSIGN = "assign"
    NONE = "none"


class ActionStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    SKIPPED = "skipped"


class Action(BaseModel):
    id: str
    type: ActionType
    payload: dict[str, Any] = Field(default_factory=dict)
    reason: str = ""
    requires_approval: bool = True
    status: ActionStatus = ActionStatus.PROPOSED


class AgentResult(BaseModel):
    agent: str
    decision: Decision
    actions: list[Action] = Field(default_factory=list)
    error: Optional[str] = None
    duration_ms: int = 0


class PipelineResult(BaseModel):
    """Everything produced for a single item across all agents."""

    item: Item
    results: list[AgentResult] = Field(default_factory=list)
    actions: list[Action] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None

    def result_for(self, agent: str) -> Optional[AgentResult]:
        for r in self.results:
            if r.agent == agent:
                return r
        return None

    @property
    def slop_score(self) -> float:
        r = self.result_for("quality")
        return float(r.decision.data.get("slop_score", 0.0)) if r else 0.0
