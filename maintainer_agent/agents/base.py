"""Base agent: timing, error isolation, and small shared helpers."""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

from ..core.models import Action, ActionType, AgentResult, Decision, Item

if TYPE_CHECKING:  # avoid an import cycle; annotations are strings anyway
    from ..orchestrator.state import AgentContext


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def make_action(
    agent: str,
    item: Item,
    action_type: ActionType,
    payload: Optional[dict[str, Any]] = None,
    reason: str = "",
    requires_approval: bool = True,
) -> Action:
    """Build an Action with a stable, human-readable id (deterministic for tests)."""
    return Action(
        id=f"{agent}:{item.number}:{action_type.value}",
        type=action_type,
        payload=payload or {},
        reason=reason,
        requires_approval=requires_approval,
    )


class Agent(ABC):
    name: str = "agent"

    def run(
        self,
        item: Item,
        ctx: "AgentContext",
        prior: Optional[list[AgentResult]] = None,
    ) -> AgentResult:
        prior = prior or []
        start = time.perf_counter()
        try:
            result = self.analyze(item, ctx, prior)
        except Exception as exc:  # never let one agent crash the pipeline
            result = AgentResult(
                agent=self.name,
                decision=Decision(
                    agent=self.name,
                    verdict="error",
                    rationale=f"{type(exc).__name__}: {exc}",
                ),
                error=str(exc),
            )
        result.duration_ms = int((time.perf_counter() - start) * 1000)
        return result

    @abstractmethod
    def analyze(
        self, item: Item, ctx: "AgentContext", prior: list[AgentResult]
    ) -> AgentResult:
        ...
