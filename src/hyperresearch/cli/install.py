"""Install command — one-step setup: vault init + platform bundle + docs injection."""

from __future__ import annotations

from pathlib import Path

import typer

from hyperresearch.cli._output import console, output
from hyperresearch.models.output import error, success


def install(
    path: str = typer.Argument(".", help="Path to install in"),
    name: str = typer.Option("Research Base", "--name", "-n", help="Vault name"),
    platform: str = typer.Option(
        "codex",
        "--platform",
        help="Target agent platform: codex or claude",
    ),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
    global_install: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Install the platform bundle to your home directory so /hyperresearch works in every Codex or Claude Code session anywhere. Skips vault init and per-project step skills (those happen on first /hyperresearch run in a project).",
    ),
    steps_only: bool = typer.Option(
        False,
        "--steps-only",
        help="Install only the 16 step skills to <PATH>/.agents/skills/ for Codex or <PATH>/.claude/skills/ for Claude. Used internally by the entry skill bootstrap on first /hyperresearch invocation in a project. Not normally invoked by users.",
    ),
) -> None:
    """Install hyperresearch: init vault + inject agent docs + install the platform bundle."""
    import sys

    from hyperresearch.core.hooks import (
        _install_hyperresearch_step_skills,
        install_global_hooks,
        install_hooks,
    )
    from hyperresearch.core.vault import Vault, VaultError

    if platform not in {"claude", "codex"}:
        raise typer.BadParameter("platform must be 'claude' or 'codex'")

    # Steps-only path: lazy install of the 16 step skills to a project's
    # .claude/skills/ or .agents/skills/. Called by the entry skill's
    # bootstrap on first /hyperresearch in a project (after a global
    # install). Cheap no-op on subsequent invocations.
    if steps_only:
        target = Path(path).resolve()
        if platform == "claude":
            result = _install_hyperresearch_step_skills(target)
        else:
            from hyperresearch.core.codex_bundle import install_codex_step_skills

            result = install_codex_step_skills(target)
        if json_output:
            output(
                success({"steps_installed": result, "target": str(target)}, vault=None),
                json_mode=True,
            )
            return
        if result:
            skill_root = ".claude/skills" if platform == "claude" else ".agents/skills"
            console.print(f"[green]Step skills installed:[/] {target}/{skill_root}/")
            console.print(f"  {result}")
        else:
            skill_root = ".claude/skills" if platform == "claude" else ".agents/skills"
            console.print(f"[dim]Step skills already installed at {target}/{skill_root}/[/]")
        return

    # Global install path: only the user-level entry skill + agents.
    # No vault, no AGENTS.md/CLAUDE.md, no step skills — pure "make the
    # slash command available everywhere" mode. Step skills install
    # per-project, lazily, when the entry skill bootstrap calls
    # `hyperresearch install --steps-only .` on first invocation.
    if global_install:
        home = Path.home()
        from hyperresearch.core.agent_docs import _resolve_executable

        hpr_path = _resolve_executable()
        if platform == "claude":
            hook_actions = install_global_hooks(home, hpr_path=hpr_path)
        else:
            from hyperresearch.core.codex_bundle import install_codex_global_bundle

            hook_actions = install_codex_global_bundle(home, hpr_path=hpr_path)

        if json_output:
            output(
                success(
                    {"global": True, "home": str(home), "hooks_installed": hook_actions},
                    vault=None,
                ),
                json_mode=True,
            )
            return

        if platform == "claude":
            console.print(f"[green]Global install:[/] {home}/.claude/")
        else:
            console.print(f"[green]Global install:[/] {home}/.agents/ and {home}/.codex/")
        if hook_actions:
            for action in hook_actions:
                console.print(f"  {action}")
        else:
            console.print("[dim]All skills and agents already installed.[/]")
        console.print(
            "\n[bold]Ready.[/] /hyperresearch is now available in every Codex or Claude Code session."
        )
        if platform == "claude":
            console.print(
                "[dim]On first /hyperresearch run in a project, the vault, research/ folder, "
                "and the 16 step skills are created in that project's .claude/.[/]"
            )
        else:
            console.print(
                "[dim]On first /hyperresearch run in a project, the vault, research/ folder, "
                "and the Codex bundle are created in that project's .agents/ and .codex/.[/]"
            )
        return

    root = Path(path).resolve()

    # First-time install in an interactive terminal → run the setup TUI instead
    is_new = not (root / ".hyperresearch").exists()
    is_interactive = not json_output and sys.stdin.isatty()
    if is_new and is_interactive:
        from hyperresearch.cli.setup import setup

        setup(path=path, platform=platform, json_output=False)
        return

    # Step 1: Init vault (skip if already exists)
    try:
        vault = Vault.discover(root)
        vault_action = "existing"
    except VaultError:
        try:
            vault = Vault.init(root, name=name, agent_platform=platform)
            vault_action = "created"
        except VaultError as e:
            if json_output:
                output(error(str(e), "INIT_ERROR"), json_mode=True)
            else:
                console.print(f"[red]Error:[/] {e}")
            raise typer.Exit(1)

    if vault.config.agent_platform != platform:
        vault.config.agent_platform = platform
        vault.config.save(vault.config_path)

    # Step 2: Resolve the hyperresearch executable path
    from hyperresearch.core.agent_docs import _resolve_executable, inject_agent_docs

    hpr_path = _resolve_executable()

    # Step 3: Always re-inject the platform agent doc (updates blurb + path)
    doc_actions = inject_agent_docs(root, platform=platform)

    # Step 4: Install the platform-specific bundle.
    if platform == "claude":
        hook_actions = install_hooks(root, hpr_path=hpr_path)
    else:
        from hyperresearch.core.codex_bundle import install_codex_project_bundle

        hook_actions = install_codex_project_bundle(root, hpr_path=hpr_path)

    # Step 3: Auto-configure crawl4ai if installed
    crawl4ai_status = _setup_crawl4ai(vault)

    # Step 5: Report
    data = {
        "platform": platform,
        "vault_path": str(vault.root),
        "vault": vault_action,
        "agent_docs": doc_actions,
        "hooks_installed": hook_actions,
        "crawl4ai": crawl4ai_status,
    }

    if json_output:
        output(success(data, vault=str(vault.root)), json_mode=True)
    else:
        if vault_action == "created":
            console.print(f"[green]Vault created:[/] {vault.root}")
        else:
            console.print(f"[dim]Vault exists:[/] {vault.root}")

        if doc_actions:
            console.print("[green]Agent docs:[/]")
            for action in doc_actions:
                console.print(f"  {action}")

        if hook_actions:
            console.print("[green]Hooks installed:[/]" if platform == "claude" else "[green]Codex bundle installed:[/]")
            for action in hook_actions:
                console.print(f"  {action}")
        elif platform == "claude":
            console.print("[dim]All hooks already installed.[/]")
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

        ready_label = "Codex" if platform == "codex" else "Claude Code"
        console.print(f"\n[bold]Ready.[/] {ready_label} will now check the research base before web searches.")
        console.print("[dim]Tip: Run 'hyperresearch setup' for interactive configuration (profile, stealth, etc.)[/]")


def _setup_crawl4ai(vault) -> str:
    """Detect crawl4ai, install browser if needed, set as default provider.

    Returns: 'configured' (already ready), 'browser_installed' (just set up),
             'not_installed' (crawl4ai not available).
    """
    try:
        import crawl4ai  # noqa: F401
    except ImportError:
        return "not_installed"

    # Set crawl4ai as the default provider if still on builtin
    if vault.config.web_provider == "builtin":
        vault.config.web_provider = "crawl4ai"
        vault.config.save(vault.config_path)

    # Check if browser is already installed
    try:
        from playwright.sync_api import sync_playwright

        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True)
        browser.close()
        pw.stop()
        return "configured"
    except Exception:
        pass

    # Try to install the browser
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
        return "configured"  # best effort — user can install manually
