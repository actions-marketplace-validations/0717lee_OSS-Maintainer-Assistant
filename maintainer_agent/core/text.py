"""Small, dependency-free text utilities shared by the memory index and agents.

Everything here is deterministic so offline runs and the eval harness are
reproducible.
"""
from __future__ import annotations

import math
import re
from collections import Counter

_WORD = re.compile(r"[a-zA-Z0-9_]+")

# A compact English stopword list; enough to de-noise similarity/keyword checks.
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "else", "for", "of", "to",
    "in", "on", "at", "by", "is", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those", "it", "its", "as", "with", "from", "into",
    "i", "you", "we", "they", "he", "she", "my", "our", "your", "their", "me",
    "so", "not", "no", "do", "does", "did", "have", "has", "had", "can", "could",
    "would", "should", "will", "just", "about", "when", "which", "what", "how",
}


def tokenize(text: str) -> list[str]:
    return [t for t in (m.group(0).lower() for m in _WORD.finditer(text or "")) if len(t) >= 2]


def content_tokens(text: str) -> list[str]:
    return [t for t in tokenize(text) if t not in _STOPWORDS]


def bag_of_words(text: str) -> Counter:
    return Counter(content_tokens(text))


def cosine(a: str, b: str) -> float:
    """Bag-of-words cosine similarity in ``[0, 1]``."""
    ca, cb = bag_of_words(a), bag_of_words(b)
    if not ca or not cb:
        return 0.0
    common = set(ca) & set(cb)
    num = sum(ca[t] * cb[t] for t in common)
    da = math.sqrt(sum(v * v for v in ca.values()))
    db = math.sqrt(sum(v * v for v in cb.values()))
    return num / (da * db) if da and db else 0.0


def contains_any(text: str, needles: list[str]) -> list[str]:
    """Return the subset of ``needles`` that appear (case-insensitively)."""
    low = (text or "").lower()
    return [n for n in needles if n.lower() in low]


_LINK_RE = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)", re.IGNORECASE
)


def extract_linked_issues(text: str) -> list[int]:
    """Pull issue numbers from 'fixes #123' / 'closes #45' style references."""
    return sorted({int(m.group(1)) for m in _LINK_RE.finditer(text or "")})


def word_count(text: str) -> int:
    return len(tokenize(text))


_FENCE_RE = re.compile(r"```([a-zA-Z0-9_+-]*)\n(.*?)```", re.DOTALL)


def extract_code_blocks(text: str, lang: str | None = None) -> list[str]:
    """Return fenced code blocks. When ``lang`` is given, only matching blocks.

    For ``lang='python'`` both ``py`` and ``python`` fences match; unlabeled
    fences (e.g. pasted tracebacks) are intentionally skipped.
    """
    wanted: set[str] = set()
    if lang == "python":
        wanted = {"python", "py"}
    elif lang:
        wanted = {lang.lower()}
    blocks: list[str] = []
    for m in _FENCE_RE.finditer(text or ""):
        label = (m.group(1) or "").lower()
        if lang is None or label in wanted:
            blocks.append(m.group(2))
    return blocks
