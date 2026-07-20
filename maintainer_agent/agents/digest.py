"""Digest agent.

Not a per-item agent: it summarizes a whole batch of pipeline results into a
maintainer-friendly digest (markdown for humans, a stats dict for the API).
The goal is a 30-second read that surfaces what needs attention first.
Bilingual: pass ``lang="zh"`` for a Chinese digest.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from ..core.models import PipelineResult

# Localized strings. Keys are shared across languages.
_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "title": "Maintainer digest",
        "title_for": "Maintainer digest for {repo}",
        "generated": "Generated {now} - {n} open item(s) reviewed.",
        "glance": "At a glance",
        "attention": "Needs attention",
        "duplicates": "Likely duplicates",
        "ready": "Ready to review",
        "good_first": "Good first issues",
        "more_info": "Needs more info",
        "reproduced": "Reproduced bugs",
        "suf_slop": "likely AI slop (score {score})",
        "suf_security": "security, prioritize",
        "suf_dup": "duplicate of #{n}",
        "suf_repro": "reproduced in sandbox",
    },
    "zh": {
        "title": "维护者摘要",
        "title_for": "{repo} 的维护者摘要",
        "generated": "生成于 {now} · 已审阅 {n} 个开放条目。",
        "glance": "一览",
        "attention": "需关注",
        "duplicates": "疑似重复",
        "ready": "待评审",
        "good_first": "适合新手",
        "more_info": "信息不足",
        "reproduced": "已复现的缺陷",
        "suf_slop": "疑似 AI 灌水（评分 {score}）",
        "suf_security": "安全问题，建议优先",
        "suf_dup": "重复于 #{n}",
        "suf_repro": "已在沙箱复现",
    },
}


class DigestAgent:
    name = "digest"

    def stats(self, results: list[PipelineResult]) -> dict[str, Any]:
        buckets = self._bucketize(results)
        return {
            "repo": None,
            "total": len(results),
            "counts": {k: len(v) for k, v in buckets.items()},
        }

    def build(
        self,
        results: list[PipelineResult],
        repo: str = "",
        llm: Optional[Any] = None,
        lang: str = "en",
    ) -> str:
        s = _STRINGS.get(lang, _STRINGS["en"])
        b = self._bucketize(results, lang=lang)
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines: list[str] = []
        title = s["title_for"].format(repo=repo) if repo else s["title"]
        lines.append(f"# {title}")
        lines.append("_" + s["generated"].format(now=now, n=len(results)) + "_")
        lines.append("")

        # Optional one-line LLM summary (no-op offline).
        if llm is not None and getattr(llm, "available", False):
            summary = llm.complete(
                "In one sentence, summarize the state of this issue tracker for a "
                f"maintainer. Counts: {({k: len(v) for k, v in b.items()})}. "
                f"Reply in {'Chinese' if lang == 'zh' else 'English'}.",
                system="You are a concise engineering assistant.",
            ).strip()
            if summary:
                lines += [f"> {summary}", ""]

        lines.append(f"## {s['glance']}")
        for key in ("attention", "duplicates", "ready", "good_first", "more_info"):
            lines.append(f"- {s[key]}: **{len(b[key])}**")
        lines.append("")

        for key in ("attention", "reproduced", "duplicates", "ready", "good_first", "more_info"):
            self._section(lines, s[key], b[key])
        return "\n".join(lines).rstrip() + "\n"

    # ------------------------------------------------------------------ #
    @staticmethod
    def _link(it) -> str:
        title = it.title if len(it.title) <= 80 else it.title[:77] + "..."
        return f"[#{it.number}]({it.url}) {title}" if it.url else f"#{it.number} {title}"

    def _bucketize(self, results: list[PipelineResult], lang: str = "en") -> dict[str, list[str]]:
        s = _STRINGS.get(lang, _STRINGS["en"])
        b: dict[str, list[str]] = {
            "attention": [], "duplicates": [], "ready": [],
            "good_first": [], "more_info": [], "reproduced": [],
        }
        for r in results:
            it = r.item
            tri = r.result_for("triage")
            qual = r.result_for("quality")
            rep = r.result_for("reproducer")
            td = tri.decision.data if tri else {}
            link = self._link(it)

            if qual and qual.decision.verdict == "likely-ai-slop":
                suf = s["suf_slop"].format(score=qual.decision.data.get("slop_score"))
                b["attention"].append(f"{link} - {suf}")
            elif tri and tri.decision.verdict == "security":
                b["attention"].append(f"{link} - {s['suf_security']}")

            if td.get("duplicate_of"):
                b["duplicates"].append(f"{link} - {s['suf_dup'].format(n=td['duplicate_of'])}")
            if td.get("good_first_issue"):
                b["good_first"].append(link)
            if td.get("needs_more_info"):
                b["more_info"].append(link)
            if it.is_pr and qual and qual.decision.verdict == "looks-good":
                b["ready"].append(link)
            if rep and rep.decision.verdict == "reproduced":
                b["reproduced"].append(f"{link} - {s['suf_repro']}")
        return b

    @staticmethod
    def _section(lines: list[str], title: str, items: list[str]) -> None:
        if not items:
            return
        lines.append(f"## {title}")
        lines.extend(f"- {x}" for x in items)
        lines.append("")
