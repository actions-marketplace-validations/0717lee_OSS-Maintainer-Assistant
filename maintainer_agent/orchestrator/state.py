"""Shared context passed to every agent during a pipeline run.

Bundling these together keeps agent signatures small and makes it trivial to
give an agent read access to sibling items (for duplicate detection) or the
sandbox (for reproduction).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from ..core.config import RepoConfig
from ..core.llm import BaseLLM, get_llm
from ..core.models import Item
from ..memory.store import TfidfIndex, build_index


@dataclass
class AgentContext:
    config: RepoConfig
    llm: BaseLLM
    index: TfidfIndex
    items_by_number: dict[int, Item]
    sandbox: Optional[Any] = None  # a sandbox.Sandbox, wired only when reproducing

    def item(self, number: int) -> Optional[Item]:
        return self.items_by_number.get(number)


def build_context(
    items: list[Item],
    config: RepoConfig,
    llm: Optional[BaseLLM] = None,
    sandbox: Optional[Any] = None,
) -> AgentContext:
    return AgentContext(
        config=config,
        llm=llm or get_llm(),
        index=build_index(items),
        items_by_number={it.number: it for it in items},
        sandbox=sandbox,
    )
