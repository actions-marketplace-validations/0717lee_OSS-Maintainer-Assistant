"""CI failure analysis agent.

Analyzes GitHub Actions workflow run logs to categorize failure reasons and
suggest likely causes. When an LLM is available, it provides a natural-language
diagnosis; otherwise it uses rule-based log pattern matching.
"""
from __future__ import annotations

import re
from typing import Any, Optional

from ..core.llm import BaseLLM
from ..core.models import Decision, Evidence, AgentResult

# Rule-based failure patterns (used when no LLM).
_PATTERNS: list[tuple[str, str, str]] = [
    ("ImportError|ModuleNotFoundError", "missing-dependency", "Missing or incompatible dependency"),
    ("SyntaxError|IndentationError", "syntax-error", "Python syntax error in the code"),
    (r"AssertionError|assert\s+", "test-failure", "Test assertion failed"),
    ("TimeoutError|timed?\s*out", "timeout", "Build or test timed out"),
    (r"403|401|Unauthorized|Forbidden", "permission", "Permission or authentication error"),
    ("flake8|ruff|eslint|pylint", "lint-failure", "Linting or style check failed"),
    (r"docker.*not\s*found|Cannot\s+connect", "docker", "Docker environment issue"),
    (r"out\s+of\s+memory|OOM|MemoryError", "resource", "Out of memory"),
    ("ConnectionError|ConnectionRefused", "network", "Network connection error"),
    ("FileNotFoundError|ENOENT", "missing-file", "Required file not found"),
]

_FAILURE_CATEGORIES = {
    "missing-dependency": ("Dependency Issue", "danger"),
    "syntax-error": ("Code Error", "danger"),
    "test-failure": ("Test Failure", "warning"),
    "timeout": ("Timeout", "warning"),
    "permission": ("Permission Error", "danger"),
    "lint-failure": ("Lint Failure", "warning"),
    "docker": ("Environment Issue", "warning"),
    "resource": ("Resource Limit", "danger"),
    "network": ("Network Issue", "info"),
    "missing-file": ("Missing File", "warning"),
    "unknown": ("Unknown Failure", "neutral"),
}


def analyze_log(log_text: str, llm: Optional[BaseLLM] = None) -> dict[str, Any]:
    """Analyze a CI log and return categorized failure info.

    Returns dict with: category, label, severity, matched_patterns,
    summary, and (if LLM) diagnosis.
    """
    if not log_text:
        return {"category": "unknown", "label": "No log data", "severity": "neutral", "matched": [], "summary": ""}

    matched: list[dict] = []
    for pattern, key, desc in _PATTERNS:
        finds = re.findall(pattern, log_text, re.IGNORECASE | re.MULTILINE)
        if finds:
            matched.append({"category": key, "description": desc, "count": len(finds)})

    # Pick the most relevant category (first match).
    category = matched[0]["category"] if matched else "unknown"
    label, severity = _FAILURE_CATEGORIES.get(category, _FAILURE_CATEGORIES["unknown"])

    # Extract relevant lines (lines containing 'error', 'failed', 'exception').
    error_lines = [
        line.strip() for line in log_text.split("\n")
        if re.search(r"error|fail|exception|traceback", line, re.IGNORECASE)
    ][:10]

    summary = f"Found {len(matched)} issue pattern(s). Primary: {label}." if matched else "No known failure patterns matched."

    # LLM diagnosis (optional).
    diagnosis = ""
    if llm and llm.available and (matched or error_lines):
        context = "\n".join(error_lines[:8]) if error_lines else log_text[:2000]
        diagnosis = llm.complete(
            f"A CI pipeline failed. Here are the error lines:\n\n{context}\n\n"
            f"Pattern matches: {matched[:3]}\n\n"
            f"In 2-3 sentences, diagnose the most likely root cause and suggest a fix.",
            system="You are a CI/CD expert. Diagnose failures concisely.",
            max_tokens=300,
        ).strip()

    return {
        "category": category,
        "label": label,
        "severity": severity,
        "matched": matched,
        "error_lines": error_lines,
        "summary": summary,
        "diagnosis": diagnosis,
    }
