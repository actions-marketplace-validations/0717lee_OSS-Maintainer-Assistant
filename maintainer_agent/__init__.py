"""maintainer-agent: a multi-agent open-source maintainer assistant.

The package is organized around a small set of cooperating agents driven by an
orchestrator (LangGraph when available, linear fallback otherwise):

    triage -> quality (AI-slop) -> reproducer -> responder -> digest

Every agent emits an explainable ``Decision`` (verdict + confidence + evidence)
and optional ``Action`` proposals. Actions are never applied automatically:
they require an explicit ``--apply`` run plus per-action human approval.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
