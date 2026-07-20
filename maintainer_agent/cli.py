"""maintainer-agent command line interface.

Commands:
    run      Analyze issues/PRs and show explainable decisions (dry-run by default).
    digest   Print/save a maintainer digest for the tracker.
    serve    Start the API + dashboard.
    eval     Run the reliability evaluation and print metrics.
"""
import json
from pathlib import Path
from typing import Optional

import httpx
import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

from .agents.digest import DigestAgent
from .core.approval import ApprovalMode
from .core.audit import AuditLog
from .core.llm import get_llm
from .core.models import Action, ActionType, Item, PipelineResult
from .orchestrator.graph import describe_backend, run_pipeline
from .service import load_inputs

app = typer.Typer(add_completion=False, help="A multi-agent open-source maintainer assistant.")
console = Console()

_VERDICT_STYLE = {
    "likely-ai-slop": "bold red",
    "needs-work": "yellow",
    "looks-good": "green",
    "duplicate": "magenta",
    "security": "bold red",
    "bug": "red",
    "needs-more-info": "yellow",
    "reproduced": "bold red",
}


@app.callback()
def _init() -> None:
    load_dotenv()


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #
def _build_sandbox(reproduce: bool):
    if not reproduce:
        return None
    from .sandbox import Sandbox

    sb = Sandbox(enabled=True)
    if not sb.docker_available():
        console.print("[yellow]docker not found; reproduction will be skipped.[/]")
    return sb


def _make_approver():
    def approver(action: Action, item: Item) -> bool:
        preview = action.payload.get("body") or json.dumps(action.payload)
        console.print(
            Panel(
                escape(str(preview)[:800]),
                title=f"[bold]#{item.number}[/] proposes [cyan]{action.type.value}[/]",
                subtitle=action.reason,
                border_style="cyan",
            )
        )
        return typer.confirm("Approve this action?", default=False)

    return approver


def _color(verdict: str) -> str:
    return _VERDICT_STYLE.get(verdict, "white")


def _render_table(results: list[PipelineResult]) -> None:
    table = Table(title="maintainer-agent results", header_style="bold")
    for col in ("#", "Kind", "Triage", "Pri", "Quality (slop)", "Labels", "Actions"):
        table.add_column(col, overflow="fold")
    for r in results:
        tri = r.result_for("triage")
        qual = r.result_for("quality")
        tv = tri.decision.verdict if tri else "-"
        qv = qual.decision.verdict if qual else "-"
        slop = qual.decision.data.get("slop_score", 0.0) if qual else 0.0
        pri = tri.decision.data.get("priority", "-") if tri else "-"
        labels = next(
            (a.payload.get("labels", []) for a in r.actions if a.type == ActionType.ADD_LABELS),
            [],
        )
        acts = ", ".join(sorted({a.type.value for a in r.actions}))
        qcell = f"[{_color(qv)}]{qv}[/] ({slop})" if qv != "not-applicable" else "n/a"
        table.add_row(
            str(r.item.number),
            r.item.kind.value.replace("pull_request", "PR"),
            f"[{_color(tv)}]{tv}[/]",
            pri,
            qcell,
            escape(", ".join(labels)),
            acts,
        )
    console.print(table)


def _render_verbose(results: list[PipelineResult]) -> None:
    for r in results:
        console.rule(escape(f"#{r.item.number} {r.item.title}"))
        for res in r.results:
            d = res.decision
            console.print(
                f"[bold]{res.agent}[/] -> [{_color(d.verdict)}]{d.verdict}[/] "
                f"(conf {d.confidence:.2f}) {res.duration_ms}ms"
            )
            console.print("  " + escape(d.rationale))
            for ev in d.evidence:
                sign = "+" if ev.weight >= 0 else ""
                console.print("    - " + escape(f"[{ev.kind}] {ev.detail}") + f" ({sign}{ev.weight:.2f})")


def _dump_json(results: list[PipelineResult], path: Path) -> None:
    payload = [json.loads(r.model_dump_json()) for r in results]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    console.print(f"[green]Wrote {len(results)} results to {path}[/]")


def _safe_load(repo, fixtures, limit, config):
    try:
        return load_inputs(repo, fixtures, limit, config)
    except httpx.HTTPError as exc:
        console.print(f"[red]Failed to fetch from GitHub:[/] {exc}")
        console.print(
            "[dim]Check the owner/name and network, set GITHUB_TOKEN for higher "
            "rate limits, or use --fixtures for the offline demo.[/]"
        )
        raise typer.Exit(1)


# --------------------------------------------------------------------------- #
# Commands                                                                     #
# --------------------------------------------------------------------------- #
@app.command()
def run(
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="owner/name (live). Omit for offline demo."),
    fixtures: bool = typer.Option(False, "--fixtures", help="Force offline bundled fixtures."),
    limit: int = typer.Option(30, "--limit", "-n", help="Max items to analyze."),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Repo config name or path."),
    reproduce: bool = typer.Option(False, "--reproduce", help="Run bug snippets in the Docker sandbox."),
    apply: bool = typer.Option(False, "--apply", help="Enable APPLY mode with per-action approval prompts."),
    allow_write: bool = typer.Option(False, "--allow-write", help="With --apply, actually post to GitHub (needs token)."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show every decision's evidence."),
    json_out: Optional[Path] = typer.Option(None, "--json", help="Write full results as JSON."),
) -> None:
    """Analyze issues/PRs and show explainable decisions. Dry-run unless --apply."""
    items, cfg, offline = _safe_load(repo, fixtures, limit, config)
    if not items:
        console.print("[red]No items found.[/]")
        raise typer.Exit(1)

    mode = ApprovalMode.APPLY if apply else ApprovalMode.DRY_RUN
    approver = _make_approver() if apply else None
    writer = None
    if apply and allow_write:
        if offline or not repo:
            console.print("[red]--allow-write requires a live --repo.[/]")
            raise typer.Exit(1)
        from .github.writer import GitHubWriter

        writer = GitHubWriter(repo)
    elif apply:
        from .github.writer import SimulatedWriter

        writer = SimulatedWriter(printer=lambda m: console.print(f"[dim]{m}[/]"))

    llm = get_llm()
    audit = AuditLog()
    console.print(
        f"[dim]source={'fixtures' if offline else repo} | backend={describe_backend()} | "
        f"llm={llm.name} | mode={mode.value} | run={audit.run_id}[/]"
    )

    results = run_pipeline(
        items, cfg, mode=mode, approver=approver, writer=writer,
        sandbox=_build_sandbox(reproduce), llm=llm, audit=audit,
    )

    if verbose:
        _render_verbose(results)
    _render_table(results)
    if json_out:
        _dump_json(results, json_out)
    console.print(f"[dim]audit log: {audit.path}[/]")


@app.command()
def digest(
    repo: Optional[str] = typer.Option(None, "--repo", "-r"),
    fixtures: bool = typer.Option(False, "--fixtures"),
    limit: int = typer.Option(30, "--limit", "-n"),
    config: Optional[str] = typer.Option(None, "--config", "-c"),
    out: Optional[Path] = typer.Option(None, "--out", "-o", help="Write the digest markdown to a file."),
) -> None:
    """Produce a maintainer digest for the tracker."""
    items, cfg, offline = _safe_load(repo, fixtures, limit, config)
    llm = get_llm()
    results = run_pipeline(items, cfg, llm=llm)
    md = DigestAgent().build(results, repo=cfg.repo, llm=llm)
    if out:
        out.write_text(md, encoding="utf-8")
        console.print(f"[green]Wrote digest to {out}[/]")
    else:
        from rich.markdown import Markdown

        console.print(Markdown(md))


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port", "-p"),
) -> None:
    """Start the API + dashboard."""
    import uvicorn

    console.print(f"[green]Dashboard:[/] http://{host}:{port}/")
    uvicorn.run("maintainer_agent.api.server:app", host=host, port=port, reload=False)


@app.command("eval")
def evaluate(
    dataset: Optional[Path] = typer.Option(None, "--dataset", help="Path to a labeled JSONL dataset."),
) -> None:
    """Run the reliability evaluation and print precision/recall metrics."""
    from .eval.run_eval import run_evaluation

    report = run_evaluation(dataset)
    console.print_json(data=report)


@app.command()
def version() -> None:
    """Print the version and orchestration backend."""
    from . import __version__

    console.print(f"maintainer-agent {__version__} (backend: {describe_backend()})")


if __name__ == "__main__":
    app()
