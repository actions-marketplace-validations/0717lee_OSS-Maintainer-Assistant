---
title: maintainer-agent
emoji: "🤖"
colorFrom: yellow
colorTo: gray
sdk: docker
app_port: 8000
pinned: true
license: mit
---

# maintainer-agent 🤖

A multi-agent assistant that helps open-source maintainers fight AI slop.

**What it does:**
- 🔍 Triages issues and PRs (labels, priority, duplicate detection)
- 🚩 Flags low-effort AI-generated submissions with explainable scores
- 🐛 Reproduces bug reports in a locked-down Docker sandbox
- ✍️ Drafts respectful replies for each situation
- 📊 Generates a 30-second maintainer digest

**Try it:** Enter any public GitHub repo (e.g. `pallets/flask`) and click Analyze. No token needed.

**How it works:** A team of cooperating agents, orchestrated with LangGraph, processes each issue/PR. Every decision carries a verdict, confidence score, and weighted evidence. Read-only by design — nothing is ever posted without your approval.

**Tech stack:** Python 3.11 · LangGraph · FastAPI · React/Vite · Tailwind · Docker · litellm (optional LLM)

**Links:**
- [GitHub](https://github.com/0717lee/OSS-Maintainer-Assistant)
- [Documentation](https://github.com/0717lee/OSS-Maintainer-Assistant#readme)
