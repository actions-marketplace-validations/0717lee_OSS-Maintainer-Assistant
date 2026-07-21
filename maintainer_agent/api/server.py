"""HTTP API + bundled dashboard.

Endpoints:
    GET  /api/health                           -> backend / llm / version info
    GET  /api/run                               -> run the pipeline and return results + digest
    GET  /api/audit                             -> recent audit-log events
    GET  /api/memory/{repo}/contributors/{a}    -> contributor cross-run profile
    GET  /api/memory/{repo}/summary             -> repo aggregate memory stats
    POST /api/webhook                           -> GitHub webhook auto-triage (HMAC verified)
    POST /api/approve                           -> execute a proposed action on GitHub
    POST /api/ask                               -> interactive follow-up Q&A with LLM
    POST /api/ci-analyze                         -> CI failure log categorization + LLM diagnosis
    GET  /                                       -> the bundled single-page dashboard

The React/Vite app in ``web/`` consumes the same JSON API; CORS is open so it can
run from the Vite dev server during development.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

from .. import __version__
from ..agents.digest import DigestAgent
from ..core.audit import AuditLog
from ..core.llm import get_llm
from ..core.models import PipelineResult
from ..core.paths import STATIC_DIR
from ..memory.memory import AgentMemory
from ..orchestrator.graph import describe_backend, run_pipeline
from ..service import load_inputs

app = FastAPI(title="maintainer-agent", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _serialize(results: list[PipelineResult]) -> list[dict]:
    return [json.loads(r.model_dump_json()) for r in results]


# Small in-memory TTL cache so a hosted demo survives traffic + GitHub rate limits.
_CACHE_TTL = float(os.getenv("MAINTAINER_AGENT_CACHE_TTL", "120"))
_cache: dict = {}


def _cache_get(key):
    hit = _cache.get(key)
    if hit and hit[0] > time.time():
        return hit[1]
    return None


def _cache_put(key, payload) -> None:
    if _CACHE_TTL > 0:
        _cache[key] = (time.time() + _CACHE_TTL, payload)


@app.get("/api/health")
def health() -> dict:
    llm = get_llm()
    return {
        "version": __version__,
        "backend": describe_backend(),
        "llm": llm.name,
        "llm_available": llm.available,
    }


@app.get("/api/run")
def api_run(
    repo: Optional[str] = Query(None, description="owner/name; omit for the offline demo"),
    fixtures: bool = Query(False, description="force offline bundled fixtures"),
    limit: int = Query(30, ge=1, le=100),
    lang: str = Query("en", description="digest language: en or zh"),
) -> dict:
    lang = lang if lang in ("en", "zh") else "en"
    key = (repo or "", fixtures, limit, lang)
    cached = _cache_get(key)
    if cached is not None:
        return cached
    try:
        items, cfg, offline = load_inputs(repo, fixtures, limit)
    except Exception as e:
        err = str(e)
        if "403" in err or "rate limit" in err.lower():
            raise HTTPException(
                status_code=429,
                detail="GitHub API rate limit exceeded. Set GITHUB_TOKEN in .env to raise the limit (5000 req/hour).",
            )
        raise HTTPException(status_code=502, detail=f"Failed to fetch repository data: {err}")
    llm = get_llm()
    audit = AuditLog()
    try:
        results = run_pipeline(items, cfg, llm=llm, audit=audit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Pipeline error: {e}")

    # Record results to persistent memory for cross-run insights.
    mem = AgentMemory()
    for r in results:
        tri = r.result_for("triage")
        qual = r.result_for("quality")
        tri_v = tri.decision.verdict if tri and tri.decision else ""
        qual_v = qual.decision.verdict if qual and qual.decision else ""
        slop = qual.decision.data.get("slop_score", 0.0) if qual and qual.decision and qual.decision.data else 0.0
        conf = (qual.decision.confidence if qual and qual.decision else 0.0) or 0.0
        mem.record_result(
            repo=cfg.repo,
            item_number=r.item.number,
            kind=r.item.kind.value if hasattr(r.item.kind, "value") else str(r.item.kind),
            title=r.item.title,
            author=r.item.author or "unknown",
            triage_verdict=tri_v,
            quality_verdict=qual_v,
            slop_score=slop,
            confidence=conf,
        )
    mem.close()

    digest = DigestAgent()
    payload = {
        "repo": cfg.repo,
        "offline": offline,
        "backend": describe_backend(),
        "llm": llm.name,
        "run_id": audit.run_id,
        "count": len(results),
        "stats": digest.stats(results),
        "digest_md": digest.build(results, repo=cfg.repo, llm=llm, lang=lang),
        "results": _serialize(results),
    }
    _cache_put(key, payload)
    return payload


@app.get("/api/audit")
def api_audit(limit: int = Query(100, ge=1, le=1000)) -> dict:
    return {"events": AuditLog().events(limit=limit)}


@app.get("/api/memory/{repo}/contributors/{author}")
def api_contributor_memory(repo: str, author: str) -> dict:
    """Return a contributor's cross-run profile for the given repo."""
    mem = AgentMemory()
    stats = mem.get_contributor_stats(author, repo)
    risk = mem.get_contributor_risk_label(author, repo)
    mem.close()
    return {"author": author, "repo": repo, "stats": stats, "risk": risk}


@app.get("/api/memory/{repo}/summary")
def api_repo_memory(repo: str) -> dict:
    """Return aggregate memory stats for a repo."""
    mem = AgentMemory()
    summary = mem.get_repo_summary(repo)
    mem.close()
    return summary


@app.post("/api/webhook")
async def webhook(request: Request) -> dict:
    """Receive a GitHub webhook event, auto-triage the item, return analysis.

    Read-only: never posts comments or labels. Configure
    MAINTAINER_AGENT_WEBHOOK_SECRET to enforce HMAC signature verification.
    """
    body = await request.body()

    # Verify HMAC signature if a secret is configured.
    secret = os.getenv("MAINTAINER_AGENT_WEBHOOK_SECRET", "")
    if secret:
        sig = request.headers.get("X-Hub-Signature-256", "")
        expected = "sha256=" + hmac.new(
            secret.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise HTTPException(status_code=403, detail="Invalid signature")

    event = request.headers.get("X-GitHub-Event", "")
    payload = json.loads(body)

    # Only handle issues and pull_request events.
    if event == "issues":
        action = payload.get("action", "")
        if action not in ("opened", "reopened"):
            return {"status": "ignored", "reason": f"action={action}"}
        number = payload["issue"]["number"]
        kind = "issue"
    elif event == "pull_request":
        action = payload.get("action", "")
        if action not in ("opened", "reopened", "synchronize"):
            return {"status": "ignored", "reason": f"action={action}"}
        number = payload["pull_request"]["number"]
        kind = "pull_request"
    else:
        return {"status": "ignored", "reason": f"event={event}"}

    repo = payload["repository"]["full_name"]

    # Fetch the item and config.
    from ..core.config import config_for_repo
    from ..github.client import GitHubClient

    client = GitHubClient(offline=False)
    item = client.get_item(repo, number)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item #{number} not found in {repo}")

    cfg = config_for_repo(repo)
    if not cfg.contributing:
        try:
            cfg.contributing = client.get_contributing(repo)
        except Exception:
            cfg.contributing = ""

    # Run the pipeline on this single item.
    llm = get_llm()
    audit = AuditLog()
    results = run_pipeline([item], cfg, llm=llm, audit=audit)
    digest = DigestAgent()
    result = results[0]

    return {
        "status": "analyzed",
        "event": event,
        "repo": repo,
        "item_number": number,
        "item_kind": kind,
        "item_title": item.title,
        "result": json.loads(result.model_dump_json()),
        "digest": digest.build(results, repo=repo, llm=llm, lang="en"),
        "run_id": audit.run_id,
    }


@app.post("/api/approve")
async def approve(request: Request) -> dict:
    """Approve and execute a single proposed action on GitHub.

    Requires GITHUB_TOKEN to be configured. Accepts JSON body:
    { repo, item_number, action_type, payload }.
    """
    body = await request.body()
    data = json.loads(body)
    repo = data.get("repo", "")
    item_number = data.get("item_number")
    action_type = data.get("action_type", "")
    payload = data.get("payload", {})
    item_title = data.get("item_title", "")

    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        raise HTTPException(
            status_code=403,
            detail="GITHUB_TOKEN not configured. Set it in .env to enable publishing.",
        )

    from ..core.models import Action, ActionType, Item, ItemKind
    from ..github.writer import GitHubWriter

    # Map action_type string to ActionType enum.
    type_map = {
        "add_labels": ActionType.ADD_LABELS,
        "comment": ActionType.COMMENT,
        "close": ActionType.CLOSE,
    }
    atype = type_map.get(action_type)
    if atype is None:
        raise HTTPException(status_code=400, detail=f"Unknown action type: {action_type}")

    action = Action(id=f"web-{item_number}-{action_type}", type=atype, payload=payload)
    item = Item(number=item_number, title=item_title, kind=ItemKind.ISSUE)

    audit = AuditLog()
    writer = GitHubWriter(repo=repo, token=token)

    try:
        writer(action, item)
        audit.record(
            "action_applied",
            item=item_number,
            action_type=action_type,
            payload=payload,
            mode="api",
        )
        return {
            "status": "applied",
            "repo": repo,
            "item_number": item_number,
            "action_type": action_type,
        }
    except Exception as exc:
        audit.record(
            "action_apply_failed",
            item=item_number,
            action_type=action_type,
            error=str(exc),
            mode="api",
        )
        raise HTTPException(status_code=502, detail=f"GitHub API error: {exc}")


# Serve the bundled dashboard at /static/, and index.html at /.


@app.post("/api/ask")
async def ask(request: Request) -> dict:
    """Interactive follow-up: ask the agent a question about a specific item.

    Accepts JSON: { repo, item_number, question }.
    Runs the pipeline (if not cached), then asks the LLM to answer based on
    the agent decisions and evidence.
    """
    body = await request.body()
    data = json.loads(body)
    repo = data.get("repo", "")
    item_number = data.get("item_number")
    question = data.get("question", "")

    if not repo or not item_number or not question:
        raise HTTPException(status_code=400, detail="repo, item_number, and question are required")

    items, cfg, offline = load_inputs(repo, False, 50)
    llm = get_llm()
    audit = AuditLog()
    results = run_pipeline(items, cfg, llm=llm, audit=audit)

    # Find the target item's result.
    result = None
    for r in results:
        if r.item.number == item_number:
            result = r
            break
    if not result:
        raise HTTPException(status_code=404, detail=f"Item #{item_number} not found in {repo}")

    # Build context summary from agent decisions.
    context_lines = [f"Item: #{result.item.number} - {result.item.title}"]
    for ar in result.results:
        d = ar.decision
        context_lines.append(f"\n{ar.agent} agent: verdict={d.verdict}, confidence={d.confidence:.2f}")
        context_lines.append(f"  Rationale: {d.rationale}")
        for ev in (d.evidence or [])[:3]:
            context_lines.append(f"  Evidence: {ev.kind} - {ev.detail} (weight={ev.weight})")
    context_summary = "\n".join(context_lines)

    # Ask the LLM.
    if llm and llm.available:
        answer = llm.complete(
            f"A maintainer asked the following question about this issue/PR:\n\n"
            f"Question: {question}\n\n"
            f"Agent analysis context:\n{context_summary}\n\n"
            f"Answer the maintainer's question clearly and concisely, "
            f"referencing the agent evidence where relevant.",
            system="You are a helpful engineering assistant for open-source maintainers. "
                   "Answer questions about issue/PR analysis based on the provided agent decisions.",
        )
    else:
        answer = "LLM not configured. Set MAINTAINER_AGENT_LLM_MODEL and an API key to enable interactive Q&A."

    return {
        "answer": answer.strip(),
        "item_number": item_number,
        "repo": repo,
    }


@app.post("/api/ci-analyze")
async def ci_analyze(request: Request) -> dict:
    """Analyze a CI failure log and return categorized diagnosis.

    Accepts JSON: { repo, log_text (or run_id for auto-fetch) }.
    """
    body = await request.body()
    data = json.loads(body)
    repo = data.get("repo", "")
    log_text = data.get("log_text", "")

    if not log_text:
        raise HTTPException(status_code=400, detail="log_text is required")

    from ..agents.ci_failure import analyze_log

    llm = get_llm()
    result = analyze_log(log_text, llm=llm)
    result["repo"] = repo
    return result
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return index_file.read_text(encoding="utf-8")
    return "<h1>maintainer-agent</h1><p>Dashboard assets not found.</p>"
