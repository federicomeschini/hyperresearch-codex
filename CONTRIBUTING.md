# Contributing to hyperresearch

hyperresearch is a Codex-first adaptation of the original Claude Code research workflow. Keep the Codex path complete, but do not remove Claude Code compatibility unless the change is explicitly about retiring it.

## Development setup

```bash
git clone https://github.com/federicomeschini/hyperresearch.git
cd hyperresearch
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

If you are running tests without an editable install, set `PYTHONPATH=src`.

## Platform smoke tests

Codex is the primary install path:

```bash
hyperresearch install --platform codex --json
hyperresearch repair --json
```

Use the Claude Code path only to verify legacy hook compatibility:

```bash
hyperresearch install --platform claude --json
```

The Codex install should create `AGENTS.md`, `.agents/skills/`, `.codex/agents/`, and `.codex/config.toml`. The Claude install should continue to create `CLAUDE.md`, `.claude/skills/`, `.claude/agents/`, and the PreToolUse hook.

## Running tests

```bash
python -m pytest tests/ -q
```

Focused checks for the Codex adaptation:

```bash
python -m pytest tests/test_core/test_codex_bundle.py tests/test_cli/test_codex_cmd.py tests/test_core/test_vault.py -q
```

All tests should pass before submitting a PR. The Codex bundle tests verify that the generated agent TOML parses, the Claude step roster is fully transposed, and repeated doc injection is idempotent.

## Code style

```bash
ruff check src tests
ruff format src tests
mypy src/hyperresearch
```

Configuration lives in `pyproject.toml`. Keep code changes narrow and prefer existing installer patterns over new abstractions.

## Documentation

Update `README.md` when user-facing commands, install outputs, agent rosters, or platform defaults change. Update `CHANGELOG.md` when behavior changes. Do not document generated install outputs as source files; the source of truth is:

- skills: `src/hyperresearch/skills/*.md`
- Claude agent templates: `src/hyperresearch/core/hooks.py`
- Codex transposition: `src/hyperresearch/core/codex_bundle.py`
- platform docs injection: `src/hyperresearch/core/agent_docs.py`

## Project structure

- `src/hyperresearch/cli/` - Typer commands and platform entry points
- `src/hyperresearch/core/` - vault management, bundle installers, sync, config, and agent docs
- `src/hyperresearch/skills/` - the 16-step hyperresearch skill chain
- `src/hyperresearch/mcp/` - read-only MCP server entry point
- `src/hyperresearch/search/` - FTS5 search and filters
- `src/hyperresearch/models/` - Pydantic/domain models
- `tests/` - pytest suite

Markdown notes remain the source of truth. SQLite and generated agent bundles are derived state that can be rebuilt with `hyperresearch sync`, `hyperresearch repair`, or `hyperresearch install`.
