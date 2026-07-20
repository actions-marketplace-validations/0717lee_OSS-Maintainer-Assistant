from maintainer_agent.eval.run_eval import run_evaluation


def test_eval_metrics_on_bundled_fixtures():
    report = run_evaluation()
    assert report["items_evaluated"] == 9
    # AI-slop detection is the headline feature; it should be perfect on the
    # curated fixtures (this doubles as a regression guard).
    assert report["slop_detection"]["f1"] == 1.0
    assert report["slop_detection"]["precision"] == 1.0
    assert report["slop_detection"]["recall"] == 1.0
    assert report["duplicate_detection"]["accuracy"] == 1.0
    assert report["priority"]["accuracy"] == 1.0
    assert report["label_coverage"]["accuracy"] == 1.0
