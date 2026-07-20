"""Reliability evaluation.

Runs the full pipeline over the labeled dataset (the bundled fixtures by default)
and reports objective metrics for the parts that have a ground truth:

* AI-slop detection (precision / recall / F1 / accuracy)
* duplicate detection (accuracy, incl. not falsely flagging non-duplicates)
* priority classification (accuracy)
* label coverage (did we suggest the expected labels?)

This turns "the agent seems smart" into numbers a maintainer can trust, and
gives a regression baseline. The bundled set is small and curated, so scores are
high by design; point ``--dataset`` at your own labels for a real measurement.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from ..core.config import config_for_repo
from ..core.models import ActionType, PipelineResult
from ..github.client import GitHubClient
from ..orchestrator.graph import run_pipeline
from ..core.paths import EVAL_DIR


def _prf(tp: int, fp: int, fn: int, tn: int) -> dict[str, float]:
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    total = tp + fp + fn + tn
    accuracy = (tp + tn) / total if total else 1.0
    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "accuracy": round(accuracy, 3),
        "support": total,
    }


def _predicted_labels(result: PipelineResult) -> list[str]:
    for a in result.actions:
        if a.type == ActionType.ADD_LABELS:
            return a.payload.get("labels", [])
    return []


def load_dataset(path: Optional[Path]) -> list[dict[str, Any]]:
    path = path or (EVAL_DIR / "dataset.jsonl")
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def run_evaluation(dataset: Optional[Path] = None) -> dict[str, Any]:
    rows = load_dataset(dataset)
    items = GitHubClient(offline=True).list_items(limit=1000)
    cfg = config_for_repo("octocat/octo-demo")
    results = {r.item.number: r for r in run_pipeline(items, cfg)}

    # AI-slop detection.
    tp = fp = fn = tn = 0
    # Duplicate / priority / labels.
    dup_correct = dup_total = 0
    pri_correct = pri_total = 0
    lbl_correct = lbl_total = 0

    for row in rows:
        res = results.get(row["number"])
        if res is None:
            continue
        triage = res.result_for("triage")
        quality = res.result_for("quality")
        td = triage.decision.data if triage else {}

        expected_slop = row.get("expected_slop")
        if expected_slop is not None and quality is not None:
            predicted = quality.decision.verdict == "likely-ai-slop"
            if predicted and expected_slop:
                tp += 1
            elif predicted and not expected_slop:
                fp += 1
            elif not predicted and expected_slop:
                fn += 1
            else:
                tn += 1

        dup_total += 1
        if td.get("duplicate_of") == row.get("expected_duplicate_of"):
            dup_correct += 1

        if row.get("expected_priority") is not None:
            pri_total += 1
            if td.get("priority") == row["expected_priority"]:
                pri_correct += 1

        expected_labels = row.get("expected_labels_contains") or []
        if expected_labels:
            lbl_total += 1
            predicted_labels = set(_predicted_labels(res))
            if set(expected_labels).issubset(predicted_labels):
                lbl_correct += 1

    return {
        "dataset": str(dataset or (EVAL_DIR / "dataset.jsonl")),
        "items_evaluated": len(rows),
        "slop_detection": _prf(tp, fp, fn, tn),
        "duplicate_detection": {
            "accuracy": round(dup_correct / dup_total, 3) if dup_total else 1.0,
            "correct": dup_correct,
            "total": dup_total,
        },
        "priority": {
            "accuracy": round(pri_correct / pri_total, 3) if pri_total else 1.0,
            "correct": pri_correct,
            "total": pri_total,
        },
        "label_coverage": {
            "accuracy": round(lbl_correct / lbl_total, 3) if lbl_total else 1.0,
            "correct": lbl_correct,
            "total": lbl_total,
        },
    }


def main() -> None:  # pragma: no cover - convenience entry point
    import sys

    report = run_evaluation()
    print(json.dumps(report, indent=2))
    # Non-zero exit if slop detection regresses badly (useful in CI).
    if report["slop_detection"]["f1"] < 0.5:
        sys.exit(1)


if __name__ == "__main__":
    main()
