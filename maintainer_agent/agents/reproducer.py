"""Reproducer agent.

For bug reports, it extracts the first Python snippet from the issue and runs it
in the Docker sandbox to check whether the reported failure actually reproduces.
A non-zero exit (traceback) is treated as "reproduced"; a clean exit as
"not-reproduced". When no snippet exists or the sandbox is unavailable, it
degrades to an explicit "skipped" verdict -- it never blocks the pipeline.
"""
from __future__ import annotations

from ..core.models import AgentResult, Decision, Evidence, Item, Severity
from ..core.text import extract_code_blocks
from .base import Agent, clamp


def _tail(text: str, n: int = 600) -> str:
    text = (text or "").strip()
    return text[-n:]


class ReproducerAgent(Agent):
    name = "reproducer"

    def analyze(self, item, ctx, prior) -> AgentResult:
        if item.is_pr:
            return self._skip("reproduction targets issues, not PRs", applicable=False)

        snippets = extract_code_blocks(item.body, lang="python")
        if not snippets:
            return self._skip("no runnable Python snippet found in the report")

        sandbox = ctx.sandbox
        if sandbox is None:
            return self._skip("sandbox not enabled (pass --reproduce to run)")

        code = snippets[0]
        result = sandbox.run_python(code)

        data = {
            "status": None,
            "exit_code": result.exit_code,
            "timed_out": result.timed_out,
            "stderr_tail": _tail(result.stderr),
            "stdout_tail": _tail(result.stdout),
            "snippet": code[:500],
        }
        evidence: list[Evidence] = []

        if not result.ran:
            data["status"] = "skipped"
            return AgentResult(
                agent=self.name,
                decision=Decision(
                    agent=self.name,
                    verdict="skipped",
                    confidence=0.3,
                    rationale=f"Could not run the snippet: {result.reason}.",
                    data=data,
                ),
            )

        if result.timed_out:
            data["status"] = "timeout"
            verdict, rationale, conf = (
                "inconclusive",
                "Snippet timed out; reproduction inconclusive.",
                0.4,
            )
        elif result.crashed:
            data["status"] = "reproduced"
            verdict, rationale, conf = (
                "reproduced",
                f"Snippet crashed (exit {result.exit_code}); the reported bug reproduces.",
                0.85,
            )
            evidence.append(
                Evidence(
                    kind="sandbox",
                    detail="stderr: " + _tail(result.stderr, 200),
                    weight=0.85,
                    severity=Severity.HIGH,
                )
            )
        else:
            data["status"] = "not-reproduced"
            verdict, rationale, conf = (
                "not-reproduced",
                "Snippet ran cleanly (exit 0); could not reproduce as written.",
                0.6,
            )
            evidence.append(
                Evidence(
                    kind="sandbox",
                    detail="stdout: " + _tail(result.stdout, 200),
                    weight=-0.2,
                )
            )

        return AgentResult(
            agent=self.name,
            decision=Decision(
                agent=self.name,
                verdict=verdict,
                confidence=clamp(conf),
                rationale=rationale,
                evidence=evidence,
                data=data,
            ),
        )

    def _skip(self, reason: str, applicable: bool = True) -> AgentResult:
        return AgentResult(
            agent=self.name,
            decision=Decision(
                agent=self.name,
                verdict="not-applicable" if not applicable else "skipped",
                confidence=0.3,
                rationale=reason[0].upper() + reason[1:] + ".",
                data={"status": "skipped"},
            ),
        )
