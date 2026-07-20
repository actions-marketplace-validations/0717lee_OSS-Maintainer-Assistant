from maintainer_agent.agents.quality import QualityAgent


def _quality(by_number, ctx, number):
    return QualityAgent().run(by_number[number], ctx).decision


def test_flags_ai_slop_pr(by_number, ctx):
    d = _quality(by_number, ctx, 103)
    assert d.verdict == "likely-ai-slop"
    assert d.data["slop_score"] >= 0.6
    assert d.evidence, "slop verdict must carry explanatory evidence"


def test_good_pr_with_tests_and_linked_issue(by_number, ctx):
    d = _quality(by_number, ctx, 104)
    assert d.verdict == "looks-good"
    assert d.data["slop_score"] == 0.0


def test_docs_only_pr_not_penalized_for_missing_tests(by_number, ctx):
    # #107 changes only a doc file; the "no tests" penalty must not apply.
    d = _quality(by_number, ctx, 107)
    assert d.verdict == "looks-good"


def test_quality_not_applicable_to_issues(by_number, ctx):
    d = _quality(by_number, ctx, 101)
    assert d.verdict == "not-applicable"
    assert d.data["slop_score"] == 0.0


def test_empty_template_pr_flagged(by_number, ctx):
    d = _quality(by_number, ctx, 109)
    assert d.verdict in {"likely-ai-slop", "needs-work"}
    assert d.data["slop_score"] >= 0.3
