"""Quality / AI-slop agent -- the project's headline feature.

Rather than a single opaque score, it accumulates *explainable* signals (each a
weighted :class:`Evidence`) evaluated against the repo's CONTRIBUTING guidance
(the "job description"), then maps the total to a verdict:

    slop_score >= slop_threshold   -> "likely-ai-slop"
    slop_score >= 0.3              -> "needs-work"
    otherwise                      -> "looks-good"

Signals include generic AI phrasing, missing linked issue, sweeping many-file
diffs, missing tests for code changes, and unfilled/empty descriptions. Positive
signals (linked issue, tests, small focused diff) reduce the score.
"""
from __future__ import annotations

from ..core.models import AgentResult, ActionType, Decision, Evidence, Item, Severity
from ..core.text import word_count
from .base import Agent, clamp, make_action

# Phrases commonly seen in low-effort, LLM-generated contributions.
AI_PHRASES = [
    "as an ai language model",
    "in summary",
    "it is important to note",
    "certainly,",
    "overall code quality",
    "improves the overall",
    "enhance the overall",
    "enhances functionality",
    "best practices",
    "robust and future-proof",
    "future-proof",
    "for better readability",
    "delve into",
    "seamlessly",
    "cutting-edge",
    "state-of-the-art",
]

_CODE_EXT = (
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".rb", ".rs",
    ".c", ".cc", ".cpp", ".h", ".hpp", ".cs", ".php", ".kt", ".swift",
)
_DOC_EXT = (".md", ".rst", ".txt", ".adoc")


def _is_test_file(name: str) -> bool:
    low = name.lower()
    return "test" in low or "spec" in low or "/tests/" in low or low.startswith("tests/")


def _is_code_file(name: str) -> bool:
    return name.lower().endswith(_CODE_EXT) and not _is_test_file(name)


def _is_doc_file(name: str) -> bool:
    low = name.lower()
    return low.endswith(_DOC_EXT) or low.startswith("docs/") or "/docs/" in low


class QualityAgent(Agent):
    name = "quality"

    def analyze(self, item, ctx, prior) -> AgentResult:
        if not item.is_pr:
            # Quality/slop review targets pull requests.
            return AgentResult(
                agent=self.name,
                decision=Decision(
                    agent=self.name,
                    verdict="not-applicable",
                    confidence=0.9,
                    rationale="Quality review applies to pull requests only.",
                    data={"slop_score": 0.0, "labels": []},
                ),
            )

        cfg = ctx.config
        body = item.body or ""
        body_low = body.lower()
        evidence: list[Evidence] = []
        score = 0.0

        # --- negative-quality signals (increase slop score) ---------------- #
        hits = [p for p in AI_PHRASES if p in body_low]
        if hits:
            w = min(0.10 * len(hits), 0.4)
            score += w
            evidence.append(
                Evidence(
                    kind="heuristic",
                    detail=f"generic AI-style phrasing ({len(hits)}): "
                    + ", ".join(f'"{h}"' for h in hits[:4]),
                    weight=w,
                    severity=Severity.MEDIUM,
                )
            )

        if not item.linked_issues:
            score += 0.2
            evidence.append(
                Evidence(
                    kind="heuristic",
                    detail="no linked issue (CONTRIBUTING asks PRs to reference one)",
                    weight=0.2,
                    severity=Severity.MEDIUM,
                )
            )

        tc = item.total_changes
        if item.changed_files >= 10 or tc >= 800:
            score += 0.25
            evidence.append(
                Evidence(
                    kind="heuristic",
                    detail=f"sweeping change: {item.changed_files} files, {tc} lines "
                    "(CONTRIBUTING prefers small, focused PRs)",
                    weight=0.25,
                    severity=Severity.HIGH,
                )
            )
        elif item.changed_files >= 6 or tc >= 400:
            score += 0.12
            evidence.append(
                Evidence(
                    kind="heuristic",
                    detail=f"sizable change: {item.changed_files} files, {tc} lines",
                    weight=0.12,
                    severity=Severity.LOW,
                )
            )

        code_files = [f for f in item.files if _is_code_file(f.filename)]
        test_files = [f for f in item.files if _is_test_file(f.filename)]
        if code_files and not test_files:
            score += 0.2
            evidence.append(
                Evidence(
                    kind="heuristic",
                    detail=f"touches code ({len(code_files)} file(s)) but adds no tests "
                    "(CONTRIBUTING requires tests for behavior changes)",
                    weight=0.2,
                    severity=Severity.MEDIUM,
                )
            )

        template = ("- [ ]" in body) or ("<!--" in body)
        if template or word_count(body) < 20:
            w = 0.2 if template else 0.15
            score += w
            evidence.append(
                Evidence(
                    kind="heuristic",
                    detail="description is an unfilled template"
                    if template
                    else "description is very short / lacks motivation",
                    weight=w,
                    severity=Severity.MEDIUM,
                )
            )

        # --- positive-quality signals (decrease slop score) ---------------- #
        if item.linked_issues:
            score -= 0.15
            evidence.append(
                Evidence(
                    kind="heuristic",
                    detail=f"references issue(s): {', '.join('#' + str(n) for n in item.linked_issues)}",
                    weight=-0.15,
                )
            )
        if code_files and test_files:
            score -= 0.1
            evidence.append(
                Evidence(
                    kind="heuristic",
                    detail=f"includes tests ({len(test_files)} file(s))",
                    weight=-0.1,
                )
            )
        if item.changed_files <= 3 and tc < 150:
            score -= 0.15
            evidence.append(
                Evidence(
                    kind="heuristic",
                    detail="small, focused diff",
                    weight=-0.15,
                )
            )

        # Optional LLM refinement (no-op offline).
        score = self._llm_refine(item, ctx, score, evidence)

        score = clamp(score)
        verdict, labels = self._verdict(score, cfg.slop_threshold)
        rationale = self._rationale(score, verdict)
        confidence = clamp(0.5 + 0.1 * len(evidence), 0.3, 0.95)

        actions = []
        if labels:
            actions.append(
                make_action(
                    self.name,
                    item,
                    ActionType.ADD_LABELS,
                    {"labels": labels},
                    reason=rationale,
                )
            )

        return AgentResult(
            agent=self.name,
            decision=Decision(
                agent=self.name,
                verdict=verdict,
                confidence=confidence,
                rationale=rationale,
                evidence=evidence,
                data={
                    "slop_score": round(score, 3),
                    "labels": labels,
                    "signals": [e.detail for e in evidence],
                },
            ),
            actions=actions,
        )

    # ------------------------------------------------------------------ #
    @staticmethod
    def _verdict(score: float, threshold: float) -> tuple[str, list[str]]:
        if score >= threshold:
            return "likely-ai-slop", ["likely-ai-slop", "needs-work"]
        if score >= 0.3:
            return "needs-work", ["needs-work"]
        return "looks-good", []

    @staticmethod
    def _rationale(score: float, verdict: str) -> str:
        if verdict == "likely-ai-slop":
            tail = "Multiple low-effort signals suggest this may be AI-generated slop; recommend human review before merge."
        elif verdict == "needs-work":
            tail = "Some quality gaps; likely needs changes before merge."
        else:
            tail = "Meets the basic contribution bar."
        return f"Quality/slop score {score:.2f}. {tail}"

    def _llm_refine(self, item, ctx, score: float, evidence: list[Evidence]) -> float:
        if not ctx.llm.available:
            return score
        contributing = (ctx.config.contributing or "")[:1500]
        prompt = (
            "You review pull requests for an open-source project. Using the "
            "project's CONTRIBUTING guidance, rate how likely this PR is "
            "low-effort or AI-generated 'slop' from 0 (great) to 1 (clear slop).\n\n"
            f"CONTRIBUTING:\n{contributing}\n\n"
            f"PR title: {item.title}\nPR body:\n{item.body[:2000]}\n\n"
            'Return JSON: {"slop_score": 0.0, "reason": "one sentence"}'
        )
        out = ctx.llm.json(prompt, system="You are a meticulous, fair PR reviewer.")
        llm_score = out.get("slop_score")
        if isinstance(llm_score, (int, float)):
            blended = (score + float(llm_score)) / 2
            evidence.append(
                Evidence(
                    kind="llm",
                    detail=f"LLM slop estimate {float(llm_score):.2f}: "
                    + str(out.get("reason", ""))[:160],
                    weight=float(llm_score) - score,
                )
            )
            return blended
        return score
