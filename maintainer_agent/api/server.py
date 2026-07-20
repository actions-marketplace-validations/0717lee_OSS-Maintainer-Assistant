"""HTTP API + bundled dashboard.

Endpoints:
    GET /api/health          -> backend / llm / version info
    GET /api/run             -> run the pipeline and return results + digest
    GET /api/audit           -> recent audit-log events
    GET /                    -> the bundled single-page dashboard

The React/Vite app in ``web/`` consumes the same JSON API; CORS is open so it can
run from the Vite dev server during development.
"""
from __future__ import annotations

import json
import os
import time
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .. import __version__
from ..agents.digest import DigestAgent
from ..core.audit import AuditLog
from ..core.llm import get_llm
from ..core.models import PipelineResult
from ..core.paths import STATIC_DIR
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
    items, cfg, offline = load_inputs(repo, fixtures, limit)
    llm = get_llm()
    audit = AuditLog()
    results = run_pipeline(items, cfg, llm=llm, audit=audit)
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


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return index_file.read_text(encoding="utf-8")
    return "<h1>maintainer-agent</h1><p>Dashboard assets not found.</p>"
