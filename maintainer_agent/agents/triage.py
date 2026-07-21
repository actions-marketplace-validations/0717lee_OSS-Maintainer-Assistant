"""Triage agent.

Classifies an item (area label + priority), detects likely duplicates against
the repo's other open items, flags vague reports as needing more info, and spots
good-first-issue candidates. Everything it concludes is backed by explicit
:class:`Evidence` so a maintainer can see exactly why.
"""
from __future__ import annotations

from typing import Optional

from ..core.models import (
    AgentResult,
    ActionType,
    Decision,
    Evidence,
    Item,
    Severity,
)
from ..core.llm import get_agent_llm
from ..core.text import contains_any, word_count
from .base import Agent, clamp, make_action


class TriageAgent(Agent):
    name = "triage"

    def analyze(self, item, ctx, prior) -> AgentResult:
        cfg = ctx.config
        text = f"{item.title}\n{item.body}"
        evidence: list[Evidence] = []
        labels: set[str] = set()

        # 1) Keyword-driven area labels from repo config.
        for rule in cfg.label_rules:
            hit = contains_any(text, rule.keywords)
            if hit:
                labels.add(rule.label)
                evidence.append(
                    Evidence(
                        kind="heuristic",
                        detail=f"matched '{rule.label}' keywords: {', '.join(hit)}",
                        weight=0.2,
                    )
                )

        # 2) Priority.
        priority = self._priority(text, cfg, evidence)

        # 3) Duplicate detection (same-kind, older sibling only).
        duplicate_of, similarity = self._duplicate(item, ctx)
        if duplicate_of is not None:
            labels.add("duplicate")
            evidence.append(
                Evidence(
                    kind="similarity",
                    detail=f"{similarity:.2f} cosine similarity to older #{duplicate_of}",
                    weight=similarity,
                    severity=Severity.MEDIUM,
                )
            )

        # 4) Vague report -> needs more info (issues only).
        needs_info = (
            not item.is_pr
            and word_count(item.body) < 15
            and "```" not in item.body
        )
        if needs_info:
            labels.add("needs-more-info")
            evidence.append(
                Evidence(
                    kind="heuristic",
                    detail="very short report with no reproduction steps or code block",
                    weight=0.3,
                    severity=Severity.LOW,
                )
            )

        # 5) Good first issue (newcomer + small/docs + not high priority).
        good_first = (
            not item.is_pr
            and item.is_newcomer
            and priority != "high"
            and ("documentation" in labels or contains_any(text, ["typo", "spelling"]))
            and not needs_info
        )
        if good_first:
            labels.add("good first issue")
            evidence.append(
                Evidence(
                    kind="heuristic",
                    detail="small, well-scoped task from a newcomer",
                    weight=0.2,
                )
            )

        # 6) Optional LLM augmentation (no-op offline).
        self._llm_augment(item, ctx, labels, evidence)

        verdict = self._verdict(item, labels, needs_info, duplicate_of)
        ordered = self._order_labels(labels, cfg)
        data = {
            "labels": ordered,
            "priority": priority,
            "duplicate_of": duplicate_of,
            "similarity": round(similarity, 3) if duplicate_of else 0.0,
            "needs_more_info": needs_info,
            "good_first_issue": good_first,
        }
        rationale = self._rationale(verdict, ordered, priority, duplicate_of)
        confidence = clamp(0.45 + 0.12 * len(evidence), 0.3, 0.95)

        actions = []
        if ordered:
            actions.append(
                make_action(
                    self.name,
                    item,
                    ActionType.ADD_LABELS,
                    {"labels": ordered},
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
                data=data,
            ),
            actions=actions,
        )

    # ------------------------------------------------------------------ #
    def _priority(self, text: str, cfg, evidence: list[Evidence]) -> str:
        for tier in ("high", "medium", "low"):
            hit = contains_any(text, cfg.priority_keywords.get(tier, []))
            if hit:
                evidence.append(
                    Evidence(
                        kind="heuristic",
                        detail=f"priority={tier} from keywords: {', '.join(hit)}",
                        weight=0.2,
                        severity=Severity.HIGH if tier == "high" else Severity.INFO,
                    )
                )
                return tier
        return "low"

    def _duplicate(self, item: Item, ctx) -> tuple[Optional[int], float]:
        best: Optional[tuple[int, float]] = None
        for did, score, _title in ctx.index.query_item(item, top_k=5):
            if score < ctx.config.duplicate_threshold:
                continue
            other = ctx.items_by_number.get(did)
            if other is None or other.kind != item.kind:
                continue
            if did in item.linked_issues:
                continue
            if self._is_older(other, item) and (best is None or score > best[1]):
                best = (did, score)
        return (best[0], best[1]) if best else (None, 0.0)

    @staticmethod
    def _is_older(other: Item, item: Item) -> bool:
        if other.created_at and item.created_at:
            return other.created_at < item.created_at
        return other.number < item.number

    def _verdict(self, item, labels, needs_info, duplicate_of) -> str:
        if duplicate_of is not None:
            return "duplicate"
        if "security" in labels:
            return "security"
        if "bug" in labels:
            return "bug"
        if "documentation" in labels:
            return "documentation"
        if needs_info:
            return "needs-more-info"
        if item.is_pr:
            return "enhancement"
        body = item.body or ""
        if "?" in body or contains_any(body, ["how do", "how can", "question"]):
            return "question"
        return "needs-triage"

    @staticmethod
    def _order_labels(labels: set[str], cfg) -> list[str]:
        order = {name: i for i, name in enumerate(cfg.labels)}
        return sorted(labels, key=lambda x: order.get(x, len(order)))

    @staticmethod
    def _rationale(verdict, labels, priority, duplicate_of) -> str:
        parts = [f"Classified as '{verdict}' (priority: {priority})."]
        if duplicate_of is not None:
            parts.append(f"Appears to duplicate #{duplicate_of}.")
        if labels:
            parts.append(f"Suggested labels: {', '.join(labels)}.")
        return " ".join(parts)

    def _llm_augment(self, item, ctx, labels: set[str], evidence: list[Evidence]) -> None:
        llm = get_agent_llm("triage")
        if not llm.available:
            return
        prompt = (
            f"Classify this GitHub {item.kind.value} for triage.\n"
            f"Allowed labels: {ctx.config.labels}\n\n"
            f"Title: {item.title}\n\nBody:\n{item.body[:2000]}\n\n"
            'Return JSON: {"labels": [...], "note": "one short sentence"}'
        )
        out = llm.json(prompt, system="You are an expert open-source triager.")
        for lbl in out.get("labels", []) or []:
            if lbl in ctx.config.labels:
                labels.add(lbl)
        note = out.get("note")
        if note:
            evidence.append(Evidence(kind="llm", detail=str(note)[:200], weight=0.1))
