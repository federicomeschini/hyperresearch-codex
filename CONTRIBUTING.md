# Contributing to hyperresearch-codex

hyperresearch-codex is a Codex-first repository. Keep user-facing commands, generated docs, tests, and examples aligned with the Codex installer path.

## Development Setup

```bash
git clone https://github.com/federicomeschini/hyperresearch-codex.git
cd hyperresearch-codex
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

If you are running tests without an editable install, set `PYTHONPATH=src`.

## Smoke Tests

```bash
hyperresearch install --json
hyperresearch repair --json
```

The install should create `AGENTS.md`, `.agents/skills/`, `.codex/agents/`, and `.codex/config.toml`.

## Running Tests

```bash
python -m pytest tests/ -q
```

Focused checks for the Codex bundle:

```bash
python -m pytest tests/test_core/test_codex_bundle.py tests/test_cli/test_codex_cmd.py tests/test_core/test_vault.py -q
```

The Codex bundle tests verify generated agent TOML, installed skill files, and idempotent `AGENTS.md` injection.

## Code Style

```bash
ruff check src tests
ruff format src tests
mypy src/hyperresearch
```

Configuration lives in `pyproject.toml`. Keep code changes narrow and prefer existing installer patterns over new abstractions.

## Documentation

Update `README.md` when user-facing commands, install outputs, agent rosters, or workflow defaults change. Update `CHANGELOG.md` when behavior changes. Do not document generated install outputs as source files; the source of truth is:

- skills: `src/hyperresearch/skills/*.md`
- Codex bundle rendering: `src/hyperresearch/core/codex_bundle.py`
- Codex docs injection: `src/hyperresearch/core/agent_docs.py`
- vault/install/config behavior: `src/hyperresearch/core/` and `src/hyperresearch/cli/`

The light/full mode is always selected by the user. Do not add classifier logic that silently chooses or upgrades the pipeline tier.

## Project Structure

- `src/hyperresearch/cli/` - Typer commands and Codex entry points
- `src/hyperresearch/core/` - vault management, bundle installers, sync, config, and agent docs
- `src/hyperresearch/skills/` - the 16-step hyperresearch skill chain
- `src/hyperresearch/mcp/` - read-only MCP server entry point
- `src/hyperresearch/search/` - FTS5 search and filters
- `src/hyperresearch/models/` - Pydantic/domain models
- `tests/` - pytest suite

Markdown notes remain the source of truth. SQLite and generated Codex bundles are derived state that can be rebuilt with `hyperresearch sync`, `hyperresearch repair`, or `hyperresearch install`.
