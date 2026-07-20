from maintainer_agent.core.models import ActionStatus, ActionType
from maintainer_agent.orchestrator.graph import (
    LANGGRAPH_AVAILABLE,
    _run_langgraph,
    _run_linear,
    run_pipeline,
)
from maintainer_agent.orchestrator.state import build_context


def test_pipeline_produces_core_agents_for_all(items, config):
    results = run_pipeline(items, config)
    assert len(results) == len(items)
    for r in results:
        agents = {x.agent for x in r.results}
        assert {"triage", "quality", "responder"}.issubset(agents)


def test_duplicate_gets_close_action(items, config):
    results = {r.item.number: r for r in run_pipeline(items, config)}
    assert any(a.type == ActionType.CLOSE for a in results[102].actions)


def test_labels_are_aggregated_into_single_action(items, config):
    results = {r.item.number: r for r in run_pipeline(items, config)}
    label_actions = [a for a in results[109].actions if a.type == ActionType.ADD_LABELS]
    assert len(label_actions) == 1
    labels = set(label_actions[0].payload["labels"])
    assert {"documentation", "likely-ai-slop"}.issubset(labels)


def test_dry_run_leaves_actions_proposed(items, config):
    for r in run_pipeline(items, config):
        for a in r.actions:
            assert a.status == ActionStatus.PROPOSED


def test_backend_parity_triage_and_quality(items, config):
    if not LANGGRAPH_AVAILABLE:
        return  # linear-only environment; nothing to compare
    ctx = build_context(items, config)
    for it in items:
        lin = {x.agent: x.decision.verdict for x in _run_linear(it, ctx)}
        lg = {x.agent: x.decision.verdict for x in _run_langgraph(it, ctx)}
        assert lin["triage"] == lg["triage"]
        assert lin["quality"] == lg["quality"]
