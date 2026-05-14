"""Install command - vault init + Codex bundle + docs injection."""

from __future__ import annotations

from pathlib import Path

import typer

from hyperresearch.cli._output import console, output
from hyperresearch.models.output import error, success


def install(
    path: str = typer.Argument(".", help="Path to install in"),
    name: str = typer.Option("Research Base", "--name", "-n", help="Vault name"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
    global_install: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Install the Codex bundle to your home directory so /hyperresearch works in every Codex session.",
    ),
    steps_only: bool = typer.Option(
        False,
        "--steps-only",
        help="Install only the 16 step skills to <PATH>/.agents/skills/.",
    ),
) -> None:
    """Install hyperresearch for Codex."""
    import sys

    from hyperresearch.core.vault import Vault, VaultError

    if steps_only:
        target = Path(path).resolve()
        from hyperresearch.core.codex_bundle import install_codex_step_skills

        result = install_codex_step_skills(target)
        if json_output:
            output(
                success({"steps_installed": result, "target": str(target)}, vault=None),
                json_mode=True,
            )
            return
        if result:
            console.print(f"[green]Step skills installed:[/] {target}/.agents/skills/")
            console.print(f"  {result}")
        else:
            console.print(f"[dim]Step skills already installed at {target}/.agents/skills/[/]")
        return

    if global_install:
        home = Path.home()
        from hyperresearch.core.agent_docs import _resolve_executable
        from hyperresearch.core.codex_bundle import install_codex_global_bundle

        hpr_path = _resolve_executable()
        bundle_actions = install_codex_global_bundle(home, hpr_path=hpr_path)

        if json_output:
            output(
                success(
                    {"global": True, "home": str(home), "codex_bundle": bundle_actions},
                    vault=None,
                ),
                json_mode=True,
            )
            return

        console.print(f"[green]Global install:[/] {home}/.agents/ and {home}/.codex/")
        if bundle_actions:
            for action in bundle_actions:
                console.print(f"  {action}")
        else:
            console.print("[dim]All skills and agents already installed.[/]")
        console.print("\n[bold]Ready.[/] /hyperresearch is now available in every Codex session.")
        console.print(
            "[dim]On first /hyperresearch run in a project, the vault, research/ folder, "
            "and the Codex bundle are created in that project's .agents/ and .codex/.[/]"
        )
        return

    root = Path(path).resolve()

    is_new = not (root / ".hyperresearch").exists()
    is_interactive = not json_output and sys.stdin.isatty()
    if is_new and is_interactive:
        from hyperresearch.cli.setup import setup

        setup(path=path, json_output=False)
        return

    try:
        vault = Vault.discover(root)
        vault_action = "existing"
    except VaultError:
        try:
            vault = Vault.init(root, name=name)
            vault_action = "created"
        except VaultError as e:
            if json_output:
                output(error(str(e), "INIT_ERROR"), json_mode=True)
            else:
                console.print(f"[red]Error:[/] {e}")
            raise typer.Exit(1)

    from hyperresearch.core.agent_docs import _resolve_executable, inject_agent_docs
    from hyperresearch.core.codex_bundle import install_codex_project_bundle

    hpr_path = _resolve_executable()
    doc_actions = inject_agent_docs(root)
    bundle_actions = install_codex_project_bundle(root, hpr_path=hpr_path)
    crawl4ai_status = _setup_crawl4ai(vault)

    data = {
        "agent_runtime": "codex",
        "vault_path": str(vault.root),
        "vault": vault_action,
        "agent_docs": doc_actions,
        "codex_bundle": bundle_actions,
        "crawl4ai": crawl4ai_status,
    }

    if json_output:
        output(success(data, vault=str(vault.root)), json_mode=True)
        return

    if vault_action == "created":
        console.print(f"[green]Vault created:[/] {vault.root}")
    else:
        console.print(f"[dim]Vault exists:[/] {vault.root}")

    if doc_actions:
        console.print("[green]Agent docs:[/]")
        for action in doc_actions:
            console.print(f"  {action}")

    if bundle_actions:
        console.print("[green]Codex bundle installed:[/]")
        for action in bundle_actions:
            console.print(f"  {action}")
    else:
        console.print("[dim]Codex bundle already up to date.[/]")

    if crawl4ai_status == "configured":
        console.print("[green]crawl4ai:[/] detected, set as default provider + browser ready")
    elif crawl4ai_status == "browser_installed":
        console.print("[green]crawl4ai:[/] browser installed + set as default provider")
    elif crawl4ai_status == "not_installed":
        console.print(
            "[dim]crawl4ai:[/] not installed. "
            "For local headless browsing: pip install hyperresearch[crawl4ai]"
        )

    console.print("\n[bold]Ready.[/] Codex will now check the research base before web searches.")
    console.print("[dim]Tip: Run 'hyperresearch setup' for interactive configuration (profile, stealth, etc.)[/]")


def _setup_crawl4ai(vault) -> str:
    """Detect crawl4ai, install browser if needed, set as default provider."""
    try:
        import crawl4ai  # noqa: F401
    except ImportError:
        return "not_installed"

    if vault.config.web_provider == "builtin":
        vault.config.web_provider = "crawl4ai"
        vault.config.save(vault.config_path)

    try:
        from playwright.sync_api import sync_playwright

        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True)
        browser.close()
        pw.stop()
        return "configured"
    except Exception:
        pass

    import subprocess
    import sys

    try:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            capture_output=True,
        )
        return "browser_installed"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "configured"
