"""Pipeline orchestration.

Runs the agents in order for a single item:

    triage -> quality -> [reproducer if it's a reproducible bug] -> responder

then aggregates their proposed actions (merging label suggestions), sends every
action through the human-in-the-loop :class:`ApprovalGate`, and records decisions
to the audit log.

Uses **LangGraph** when installed (a real ``StateGraph`` with a conditional edge
for reproduction) and falls back to an equivalent linear runner otherwise, so
the project works with or without the optional dependency.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, TypedDict

from ..agents.quality import QualityAgent
from ..agents.reproducer import ReproducerAgent
from ..agents.responder import ResponderAgent
from ..agents.triage import TriageAgent
from ..core.approval import ApprovalGate, ApprovalMode, Approver, Writer
from ..core.audit import AuditLog
from ..core.config import RepoConfig
from ..core.llm import BaseLLM
from ..core.models import Action, ActionType, AgentResult, Item, PipelineResult
from ..core.text import extract_code_blocks
from .state import AgentContext, build_context

try:  # optional dependency
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except Exception:  # pragma: no cover - exercised only when langgraph is absent
    LANGGRAPH_AVAILABLE = False


def describe_backend() -> str:
    return "langgraph" if LANGGRAPH_AVAILABLE else "linear"


def _should_reproduce(item: Item, triage: Optional[AgentResult]) -> bool:
    if item.is_pr:
        return False
    if triage and triage.decision.verdict == "bug":
        return True
    return bool(extract_code_blocks(item.body, lang="python"))


# --------------------------------------------------------------------------- #
# Agent runners (two interchangeable backends)                                 #
# --------------------------------------------------------------------------- #
def _run_linear(item: Item, ctx: AgentContext) -> list[AgentResult]:
    results: list[AgentResult] = []
    triage = TriageAgent().run(item, ctx, results)
    results.append(triage)
    results.append(QualityAgent().run(item, ctx, results))
    if _should_reproduce(item, triage):
        results.append(ReproducerAgent().run(item, ctx, results))
    results.append(ResponderAgent().run(item, ctx, results))
    return results


class _GraphState(TypedDict):
    # Only the growing list of results flows through the graph; the item and
    # context are captured via closure in _run_langgraph (simpler + avoids
    # threading immutable inputs through every channel).
    results: list


def _run_langgraph(item: Item, ctx: AgentContext) -> list[AgentResult]:
    def triage_node(state):
        return {"results": state["results"] + [TriageAgent().run(item, ctx, state["results"])]}

    def quality_node(state):
        return {"results": state["results"] + [QualityAgent().run(item, ctx, state["results"])]}

    def reproducer_node(state):
        return {"results": state["results"] + [ReproducerAgent().run(item, ctx, state["results"])]}

    def responder_node(state):
        return {"results": state["results"] + [ResponderAgent().run(item, ctx, state["results"])]}

    def route_after_quality(state):
        triage = next((x for x in state["results"] if x.agent == "triage"), None)
        return "reproduce" if _should_reproduce(item, triage) else "respond"

    graph = StateGraph(_GraphState)
    graph.add_node("triage", triage_node)
    graph.add_node("quality", quality_node)
    graph.add_node("reproducer", reproducer_node)
    graph.add_node("responder", responder_node)
    graph.set_entry_point("triage")
    graph.add_edge("triage", "quality")
    graph.add_conditional_edges(
        "quality", route_after_quality,
        {"reproduce": "reproducer", "respond": "responder"},
    )
    graph.add_edge("reproducer", "responder")
    graph.add_edge("responder", END)

    final = graph.compile().invoke({"results": []})
    return final["results"]


def _run_agents(item: Item, ctx: AgentContext, use_graph: bool) -> list[AgentResult]:
    if use_graph and LANGGRAPH_AVAILABLE:
        try:
            return _run_langgraph(item, ctx)
        except Exception:  # never fail the run because of the graph engine
            return _run_linear(item, ctx)
    return _run_linear(item, ctx)


# --------------------------------------------------------------------------- #
# Action aggregation + approval                                                #
# --------------------------------------------------------------------------- #
def _aggregate_actions(results: list[AgentResult], item: Item) -> list[Action]:
    """Merge all ADD_LABELS proposals into one, keep other actions in order."""
    label_union: list[str] = []
    others: list[Action] = []
    for r in results:
        for a in r.actions:
            if a.type == ActionType.ADD_LABELS:
                for lbl in a.payload.get("labels", []):
                    if lbl not in label_union:
                        label_union.append(lbl)
            else:
                others.append(a)
    merged: list[Action] = []
    if label_union:
        merged.append(
            Action(
                id=f"labels:{item.number}",
                type=ActionType.ADD_LABELS,
                payload={"labels": label_union},
                reason="Aggregated label suggestions from triage + quality",
            )
        )
    return merged + others


def process_item(
    item: Item,
    ctx: AgentContext,
    gate: ApprovalGate,
    use_graph: bool = True,
) -> PipelineResult:
    result = PipelineResult(item=item)
    results = _run_agents(item, ctx, use_graph)
    result.results = results

    if gate.audit is not None:
        gate.audit.record("item_start", item=item.number, kind=item.kind.value, title=item.title)
        for r in results:
            gate.audit.record(
                "decision",
                item=item.number,
                agent=r.agent,
                verdict=r.decision.verdict,
                confidence=round(r.decision.confidence, 3),
                data=r.decision.data,
            )

    actions = _aggregate_actions(results, item)
    result.actions = gate.process_all(actions, item)
    result.finished_at = datetime.now(timezone.utc)
    return result


def run_pipeline(
    items: list[Item],
    config: RepoConfig,
    *,
    mode: ApprovalMode = ApprovalMode.DRY_RUN,
    approver: Optional[Approver] = None,
    writer: Optional[Writer] = None,
    sandbox=None,
    llm: Optional[BaseLLM] = None,
    audit: Optional[AuditLog] = None,
    use_graph: bool = True,
) -> list[PipelineResult]:
    """Process every item, sharing one context (so duplicate detection sees the
    whole corpus) and one approval gate.

    Items are processed concurrently with a thread pool to overlap LLM API
    latency. The serial path is used when there's only one item.
    """
    ctx = build_context(items, config, llm=llm, sandbox=sandbox)
    gate = ApprovalGate(mode=mode, approver=approver, writer=writer, audit=audit)

    if len(items) <= 1:
        return [process_item(it, ctx, gate, use_graph=use_graph) for it in items]

    # Parallel path: overlap I/O-bound LLM calls across items.
    from concurrent.futures import ThreadPoolExecutor

    max_workers = min(len(items), 8)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        results = list(pool.map(lambda it: process_item(it, ctx, gate, use_graph=use_graph), items))
    # Preserve original order (pool.map already preserves order, but be explicit).
    results.sort(key=lambda r: r.item.number)
    return results
