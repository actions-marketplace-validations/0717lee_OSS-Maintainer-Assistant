"""Responder agent.

Turns the other agents' decisions into a single, specific, respectful reply
*draft*. It proposes a COMMENT action (and, for clear duplicates, a CLOSE action)
that always requires human approval -- nothing is ever posted automatically.

Offline it uses deterministic, situation-aware templates. With an LLM configured
it rewrites the draft in the repo's configured tone while keeping the same facts.
"""
from __future__ import annotations

from ..core.llm import get_agent_llm
from ..core.models import AgentResult, ActionType, Decision, Item
from .base import Agent, make_action


def _decisions_by_agent(prior: list[AgentResult]) -> dict[str, Decision]:
    return {r.agent: r.decision for r in prior}


class ResponderAgent(Agent):
    name = "responder"

    def analyze(self, item, ctx, prior) -> AgentResult:
        prev = _decisions_by_agent(prior)
        triage = prev.get("triage")
        quality = prev.get("quality")
        repro = prev.get("reproducer")

        blocks: list[str] = []
        actions = []
        situation = "general"

        greeting = (
            f"Hi @{item.author}, thanks for the "
            f"{'pull request' if item.is_pr else 'report'}!"
            if item.author
            else "Thanks for the contribution!"
        )

        dup_of = triage.data.get("duplicate_of") if triage else None
        if dup_of:
            situation = "duplicate"
            blocks.append(
                f"This looks like a duplicate of #{dup_of}. To keep the discussion "
                f"in one place, I'd suggest continuing there -- I'll mark this as a "
                f"duplicate. If you think it's actually different, let us know why and "
                f"we'll reopen."
            )
            actions.append(
                make_action(
                    self.name, item, ActionType.CLOSE,
                    {"reason": f"duplicate of #{dup_of}"},
                    reason=f"Triage found {triage.data.get('similarity')} similarity to #{dup_of}",
                )
            )
        elif triage and triage.verdict == "security":
            situation = "security"
            blocks.append(
                "Thanks for the security report. This looks potentially high impact, "
                "so we'll prioritize it. If the details are sensitive, please avoid "
                "posting a working exploit publicly and consider the project's security "
                "policy for private disclosure."
            )
        elif triage and triage.data.get("needs_more_info"):
            situation = "needs-more-info"
            blocks.append(
                "To help us look into this, could you share a bit more? Specifically: "
                "what you expected vs. what happened, a minimal snippet or exact steps "
                "to reproduce, and your environment (OS, version). That'll let us "
                "reproduce it quickly."
            )
        elif quality and quality.verdict == "likely-ai-slop":
            situation = "likely-ai-slop"
            blocks.append(self._slop_block(quality))
        elif quality and quality.verdict == "needs-work":
            situation = "needs-work"
            blocks.append(
                "Thanks for this! A few things would help us review it: please link the "
                "issue it addresses, describe the motivation, and add tests for any "
                "behavior change (see CONTRIBUTING)."
            )

        # Reproduction result (append when relevant).
        if repro and repro.verdict == "reproduced":
            blocks.append(
                f"I reproduced this in a sandbox (exit code {repro.data.get('exit_code')}). "
                "Confirming as a bug -- thanks for the clear report."
            )
        elif repro and repro.verdict == "not-reproduced":
            blocks.append(
                "I tried the snippet in a clean sandbox and it ran without error, so I "
                "couldn't reproduce it as written. Could you double-check the steps or "
                "share your exact environment?"
            )

        if triage and triage.data.get("good_first_issue"):
            blocks.append(
                "This looks like a great first contribution -- I've tagged it "
                "`good first issue`. Happy to guide you through a PR if you'd like to "
                "take it on!"
            )

        if not blocks:
            blocks.append(
                "Thanks for taking the time to contribute! A maintainer will take a "
                "closer look shortly."
            )

        draft = greeting + "\n\n" + "\n\n".join(blocks)
        # Only use LLM to rewrite when the reply needs nuance (slop/quality concerns).
        # For positive/generic replies the template draft is sufficient — saves a pro-model call.
        if any(kw in situation for kw in ("slop", "needs-work", "needs-more-info", "security", "reproduced")):
            draft = self._llm_rewrite(item, ctx, draft, situation)

        actions.insert(
            0,
            make_action(
                self.name, item, ActionType.COMMENT,
                {"body": draft},
                reason=f"Drafted reply for situation: {situation}",
            ),
        )

        return AgentResult(
            agent=self.name,
            decision=Decision(
                agent=self.name,
                verdict="reply-drafted",
                confidence=0.7,
                rationale=f"Composed a '{situation}' reply from upstream decisions "
                "(requires approval before posting).",
                data={"situation": situation, "draft": draft},
            ),
            actions=actions,
        )

    @staticmethod
    def _slop_block(quality: Decision) -> str:
        signals = quality.data.get("signals", [])[:3]
        bullet = "\n".join(f"- {s}" for s in signals) if signals else ""
        return (
            "Thanks for opening a PR. Before we can review this, it would need to meet "
            "the project's contribution bar (see CONTRIBUTING). A few specific things "
            "stood out:\n\n"
            f"{bullet}\n\n"
            "Could you link the issue this addresses, explain the motivation, keep the "
            "change focused, and add tests? If this was largely auto-generated, please "
            "review it carefully first -- we're happy to help once it's ready."
        )

    def _llm_rewrite(self, item: Item, ctx, draft: str, situation: str) -> str:
        llm = get_agent_llm("responder")
        if not llm.available:
            return draft
        prompt = (
            f"Rewrite the following maintainer reply to be {ctx.config.tone}. "
            "Keep it short, keep all facts and any issue references, do not invent "
            "details, and keep a warm tone even when declining.\n\n"
            f"Situation: {situation}\n\nDraft:\n{draft}"
        )
        out = llm.complete(prompt, system="You write excellent open-source replies.")
        return out.strip() or draft
