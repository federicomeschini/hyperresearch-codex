"""Codex task runner - route task effort automatically, then execute Codex."""

from __future__ import annotations

from pathlib import Path

import typer

from hyperresearch.cli._output import console
from hyperresearch.core.codex_runner import route_effort, run_codex

app = typer.Typer()

def _route_effort(task: str, cwd: Path) -> tuple[str, str | None]:
    """Run the cheap Codex router and return `(effort, why)`."""
    return route_effort(task, cwd)


def _run_codex(task: str, cwd: Path, effort: str) -> int:
    return run_codex(task, cwd, effort)


@app.command("run")
def run(
    task: str = typer.Argument(..., help="Task prompt to execute in Codex"),
    path: str = typer.Option(".", "--cd", help="Workspace / vault root"),
) -> None:
    """Route the task effort automatically, then run Codex."""
    from hyperresearch.core.vault import Vault, VaultError

    try:
        vault = Vault.discover(Path(path).resolve())
    except VaultError as exc:
        console.print(f"[red]Error:[/] {exc}")
        raise typer.Exit(1)

    effort, why = _route_effort(task, vault.root)

    if why:
        console.print(f"[green]Router:[/] {effort} [dim]({why})[/]")
    else:
        console.print(f"[green]Router:[/] {effort}")
    console.print("[dim]Launching Codex...[/]")

    raise typer.Exit(_run_codex(task, vault.root, effort))
