"""Model-agnostic LLM access with a deterministic offline fallback.

If ``litellm`` is installed and a provider key is configured, agents talk to a
real model. Otherwise a :class:`MockLLM` is returned whose methods yield empty
results, which every agent treats as "no LLM enhancement available" and falls
back to its deterministic heuristics. This keeps demos and CI fully offline and
reproducible while still exercising the real integration when keys are present.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Optional


def extract_json(text: str) -> dict[str, Any]:
    """Best-effort extraction of a JSON object from an LLM response.

    Handles ```json fenced blocks and leading/trailing prose.
    """
    if not text:
        return {}
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
    if candidate is None:
        return {}
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return {}


class BaseLLM:
    """Common interface implemented by both real and mock backends."""

    name: str = "base"
    available: bool = False

    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 900,
    ) -> str:
        raise NotImplementedError

    def json(
        self, prompt: str, system: Optional[str] = None, temperature: float = 0.0
    ) -> dict[str, Any]:
        raise NotImplementedError


class MockLLM(BaseLLM):
    """Offline no-op backend. Signals callers to rely on heuristics."""

    name = "mock"
    available = False

    def complete(self, prompt, system=None, temperature=0.0, max_tokens=900) -> str:  # noqa: D102
        return ""

    def json(self, prompt, system=None, temperature=0.0) -> dict[str, Any]:  # noqa: D102
        return {}


class LiteLLM(BaseLLM):
    """Real backend backed by litellm (OpenAI/Anthropic/local/etc.)."""

    available = True

    def __init__(self, model: str):
        import litellm  # imported lazily; only when actually used

        self._litellm = litellm
        self.name = model
        self.model = model

    def complete(self, prompt, system=None, temperature=0.0, max_tokens=900) -> str:  # noqa: D102
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = self._litellm.completion(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp["choices"][0]["message"]["content"] or ""

    def json(self, prompt, system=None, temperature=0.0) -> dict[str, Any]:  # noqa: D102
        instruction = (
            "Respond with a single valid JSON object and nothing else. "
            "Do not wrap it in prose."
        )
        sys = f"{system}\n\n{instruction}" if system else instruction
        return extract_json(self.complete(prompt, system=sys, temperature=temperature))


_PROVIDER_KEYS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AZURE_API_KEY", "GEMINI_API_KEY")


def _has_provider_key() -> bool:
    return any(os.getenv(k) for k in _PROVIDER_KEYS)


def get_llm() -> BaseLLM:
    """Return a real LLM if configured and importable, else the MockLLM."""
    model = os.getenv("MAINTAINER_AGENT_LLM_MODEL")
    if not model or not _has_provider_key():
        return MockLLM()
    try:
        return LiteLLM(model)
    except Exception:  # litellm missing or misconfigured -> stay offline
        return MockLLM()
