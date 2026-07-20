from maintainer_agent.agents.reproducer import ReproducerAgent
from maintainer_agent.orchestrator.state import build_context
from maintainer_agent.sandbox.docker_runner import SandboxResult


class FakeSandbox:
    """Injectable sandbox so reproduction logic is tested without Docker."""

    def __init__(self, result: SandboxResult):
        self._result = result

    def run_python(self, code: str) -> SandboxResult:
        return self._result


def _ctx(items, config, result):
    return build_context(items, config, sandbox=FakeSandbox(result))


def test_reproduced_when_snippet_crashes(items, config, by_number):
    ctx = _ctx(items, config, SandboxResult(True, 1, "", "ZeroDivisionError: division by zero"))
    d = ReproducerAgent().run(by_number[101], ctx).decision
    assert d.verdict == "reproduced"
    assert d.data["status"] == "reproduced"


def test_not_reproduced_when_snippet_clean(items, config, by_number):
    ctx = _ctx(items, config, SandboxResult(True, 0, "2.0", ""))
    d = ReproducerAgent().run(by_number[101], ctx).decision
    assert d.verdict == "not-reproduced"


def test_skipped_without_sandbox(ctx, by_number):
    # The default ctx fixture has sandbox=None.
    d = ReproducerAgent().run(by_number[101], ctx).decision
    assert d.verdict == "skipped"


def test_not_applicable_for_pr(ctx, by_number):
    d = ReproducerAgent().run(by_number[103], ctx).decision
    assert d.verdict == "not-applicable"


def test_issue_without_snippet_is_skipped(items, config, by_number):
    ctx = _ctx(items, config, SandboxResult(True, 0, "", ""))
    d = ReproducerAgent().run(by_number[102], ctx).decision  # #102 has no code block
    assert d.verdict == "skipped"
