from maintainer_agent.agents.triage import TriageAgent


def _triage(by_number, ctx, number):
    return TriageAgent().run(by_number[number], ctx).decision


def test_duplicate_detection_marks_newer_item(by_number, ctx):
    # #102 is a later-filed duplicate of #101; #101 should not be flagged.
    assert _triage(by_number, ctx, 102).data["duplicate_of"] == 101
    assert _triage(by_number, ctx, 101).data["duplicate_of"] is None


def test_security_issue_is_high_priority(by_number, ctx):
    d = _triage(by_number, ctx, 108)
    assert d.verdict == "security"
    assert d.data["priority"] == "high"


def test_vague_issue_needs_more_info(by_number, ctx):
    d = _triage(by_number, ctx, 106)
    assert d.data["needs_more_info"] is True
    assert "needs-more-info" in d.data["labels"]


def test_good_first_issue_for_newcomer_typo(by_number, ctx):
    d = _triage(by_number, ctx, 105)
    assert d.data["good_first_issue"] is True
    assert "good first issue" in d.data["labels"]
    assert "documentation" in d.data["labels"]


def test_bug_issue_labeled_and_prioritized(by_number, ctx):
    d = _triage(by_number, ctx, 101)
    assert d.verdict == "bug"
    assert d.data["priority"] == "high"
