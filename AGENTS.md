# AGENTS.md — working on maintainer-agent

Navigation entrypoint for coding agents. Read this first, then open the linked
files for detail. Keep changes small, focused, and explainable — the same bar
this tool applies to others (see [CONTRIBUTING.md](CONTRIBUTING.md)).

## What this is

A multi-agent assistant that helps OSS maintainers triage issues/PRs, flag
likely AI slop, reproduce bugs in a sandbox, and draft replies — **read-only and
human-in-the-loop by default**. Python 3.11 orchestrated with LangGraph (linear
fallback), a FastAPI service, and a React/Vite + Tailwind dashboard. It runs
**fully offline** out of the box (bundled fixtures + a deterministic MockLLM).

Full context: [README.md](README.md) · design rationale: [docs/WRITEUP.md](docs/WRITEUP.md).

## Where to work (directory route)

| Path | Owns | Start here when… |
| --- | --- | --- |
| `maintainer_agent/agents/` | The agents: `triage`, `quality` (AI-slop), `reproducer`, `responder`, `digest`, `ci_failure` | Changing what an agent decides or the evidence it emits |
| `maintainer_agent/orchestrator/` | `graph.py` (LangGraph) + `state.py` shared context | Changing the pipeline / how agents are wired |
| `maintainer_agent/core/` | `models.py`, `config.py`, `llm.py` (per-agent LLM), `approval.py`, `audit.py` | Cross-cutting types, config, LLM abstraction, gates |
| `maintainer_agent/github/` | `client.py` (read-only fetch), `writer.py` (gated writes), `fixtures/` | Anything touching GitHub I/O |
| `maintainer_agent/memory/` | `store.py` (TF-IDF/vector dup index), `memory.py` (SQLite cross-run) | Duplicate detection or contributor memory |
| `maintainer_agent/sandbox/` | `docker_runner.py` (locked-down snippet runner) | Bug reproduction / sandbox behavior |
| `maintainer_agent/api/` | `server.py` (FastAPI) + `static/` (built dashboard) | HTTP endpoints, webhook, approve/ask/CI-analyze |
| `maintainer_agent/eval/` | `dataset.jsonl` + `run_eval.py` (precision/recall/F1) | Reliability metrics / regression dataset |
| `maintainer_agent/configs/` | Per-repo YAML policy (`octo-demo.yaml`) | Label taxonomy, priority keywords, thresholds |
| `web/src/` | React/Vite + Tailwind dashboard (highest-churn area) | Any dashboard/UI change |
| `tests/` | pytest suite (incl. `test_eval.py` regression guard) | Add/adjust Python tests |

Entrypoints: CLI `maintainer_agent/cli.py` (typer, `maintainer-agent …`);
service `maintainer_agent/service.py`; dashboard `web/src/main.jsx`.

## High-risk areas — change with care

- **`maintainer_agent/github/writer.py`** — the *only* code that writes to
  GitHub. The default GitHub client is read-only; never make the default path
  write. New side effects must go through `GitHubWriter`.
- **`maintainer_agent/core/approval.py`** — the human-in-the-loop `ApprovalGate`.
  Default mode is `DRY_RUN` (actions stay `PROPOSED`, only logged); the default
  approver rejects everything. Real posting needs `--apply --allow-write` + a
  token. Keep every write behind this gate and audited.
- **`maintainer_agent/sandbox/docker_runner.py`** — runs untrusted snippets.
  Preserve isolation: `--network none`, all caps dropped, read-only FS,
  memory/CPU/PID limits, timeout, and graceful "skipped" when Docker is absent.
- **`action.yml`** — the published GitHub Action / Marketplace surface. `name`
  must be unique on the Marketplace and `description` must be **< 125 chars**.
- **`maintainer_agent/api/static/`** — the *built* dashboard bundle, generated
  from `web/`. Do not hand-edit; rebuild from `web/` (see below) so the served
  bundle matches source, or call out the drift.

## Setup, run, validate

```bash
# Setup (Python 3.11+)
pip install -e ".[dev]"     # core + pytest + ruff
pip install -e ".[all]"     # optional: langgraph, litellm, faiss

# Run offline (no token / API key needed)
maintainer-agent run --fixtures
maintainer-agent serve                 # dashboard on http://127.0.0.1:8000

# Dashboard from source
cd web && npm ci && npm run dev        # dev server (proxies /api); npm run build to bundle
```

### Validate your change (route by area)

| You changed… | Run |
| --- | --- |
| Python (`maintainer_agent/**`) | `pytest -q` (includes the eval regression guard) |
| Python style | `ruff check .` (currently **non-blocking** in CI — still fix locally) |
| Frontend (`web/src/**`) | `cd web && npm ci && npm run build` (gated in CI) |

Both routes run in [`.github/workflows/ci.yml`](.github/workflows/ci.yml) on push
and PR. `pytest` runs `tests/test_eval.py`, which asserts the AI-slop / duplicate
/ priority / label metrics on the bundled fixtures — treat it as a regression
guard, not a demo.

## Conventions & gotchas (keep this list growing)

- **Offline-first.** Zero credentials must still work. Heavy integrations
  (`litellm`, `langgraph`, `chromadb`, `faiss`) are import-guarded and optional —
  don't turn them into hard dependencies.
- **Explainable decisions.** Every agent verdict carries a `confidence` and a
  list of weighted `Evidence`. Preserve that shape when adding signals; don't
  return a bare label/score.
- **Read-only by default, dry-run by default.** New actions are *proposed*, not
  applied. Route all GitHub writes through `GitHubWriter` + `ApprovalGate`.
- **Everything is audited** to `.runtime/audit/audit.jsonl`. Keep new
  decisions/actions auditable.
- **Rebuild the dashboard** after `web/src` changes so `maintainer_agent/api/static/`
  stays in sync with source.
- **Per-repo config** lives in `maintainer_agent/configs/*.yaml`; the CLI also
  targets any live repo via `--repo owner/name`.

## Deeper docs

[README.md](README.md) · [README.zh-CN.md](README.zh-CN.md) ·
[CONTRIBUTING.md](CONTRIBUTING.md) · [docs/WRITEUP.md](docs/WRITEUP.md)
