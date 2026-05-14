<p align="center">
  <img src="assets/banner.png" alt="hyperresearch" width="700">
</p>

# hyperresearch

Codex-first deep research harness with a persistent vault, a 16-step research pipeline, and an automatic reasoning-effort router for direct Codex tasks.

This repository is an adaptation of the original hyperresearch project by Jordan Gibbs. The research workflow, vault structure, and multi-step pipeline were inspired by that work; this fork rewires the bundle for Codex CLI first while keeping Claude Code compatibility in the library.

<p align="center">
  <a href="https://pypi.org/project/hyperresearch/"><img src="https://img.shields.io/pypi/v/hyperresearch" alt="PyPI version"></a>
  <a href="https://pypi.org/project/hyperresearch/"><img src="https://img.shields.io/pypi/pyversions/hyperresearch" alt="Python 3.11+"></a>
  <a href="https://github.com/federicomeschini/hyperresearch/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT"></a>
  <a href="https://github.com/federicomeschini/hyperresearch"><img src="https://img.shields.io/badge/repo-hyperresearch-blue" alt="Repository"></a>
</p>

---

## Overview

hyperresearch turns Codex CLI or Claude Code into a deep research system that:

- keeps every fetched source in a persistent, searchable vault
- decomposes a query into a multi-step research plan
- spawns role-specific agents for fetching, analysis, drafting, critique, patching, and polish
- preserves provenance so sources can be traced through the workflow
- routes direct Codex tasks through a cheap preflight effort selector before launching the main run

The Codex branch defaults to the Codex path:

- `hyperresearch install --platform codex`
- `hyperresearch codex run "<task>"`

Claude Code remains supported as the legacy path:

- `hyperresearch install --platform claude`

---

## Install

```bash
pip install hyperresearch
hyperresearch install --platform codex
```

Then run research inside a vault:

```bash
hyperresearch research "your question"
```

For direct Codex tasks that should route reasoning effort automatically:

```bash
hyperresearch codex run "review this module for race conditions"
```

If you need the legacy Claude Code flow instead:

```bash
hyperresearch install --platform claude
```

Power users can make the bundle available globally:

```bash
hyperresearch install --global
```

---

## What Codex Installs

`hyperresearch install --platform codex` provisions the Codex-native bundle:

- `AGENTS.md` at the vault root
- `.agents/skills/<skill>/SKILL.md`
- `.codex/agents/*.toml`
- `.codex/config.toml`

It also installs a cheap read-only effort router agent. The router does not choose the model roster. It only recommends `reasoning.effort` for the task before the main Codex run starts.

The generated Codex launcher is:

```bash
hyperresearch codex run "<task>"
```

That wrapper:

1. runs the cheap effort router
2. reads `reasoning_effort`
3. launches `codex exec` with `-c reasoning.effort=<value>`

---

## Core Commands

| Command | Purpose |
|---|---|
| `hyperresearch install --platform codex` | Initialize a Codex vault and install the Codex bundle |
| `hyperresearch install --platform claude` | Install the legacy Claude Code hook flow |
| `hyperresearch setup` | Interactive first-time setup |
| `hyperresearch research "<topic>"` | Run the research pipeline inside the vault |
| `hyperresearch codex run "<task>"` | Run a direct Codex task with automatic effort routing |
| `hyperresearch fetch "<url>"` | Fetch and save a source |
| `hyperresearch search "<query>"` | Search the vault |
| `hyperresearch note show <id>` | Read a note |
| `hyperresearch lint` | Run structural health checks |
| `hyperresearch repair` | Repair the vault and refresh platform bundles |
| `hyperresearch sync` | Rescan markdown and rebuild the index |
| `hyperresearch mcp` | Start the read-only MCP server |

---

## The 16-Step Pipeline

The research workflow is still the same 16-step pipeline, but the README now describes it in platform-neutral terms instead of tying it to one creator's model table.

| # | Step | What it does | Tier |
|---|---|---|---|
| 1 | Decompose | Turn the query into atomic items and a coverage plan | both |
| 2 | Width sweep | Build a multi-perspective search plan and fetch seed sources | both |
| 3 | Contradiction graph | Cluster source conflicts and tensions | full |
| 4 | Loci analysis | Pick focused loci for deeper investigation | full |
| 5 | Depth investigation | Write interim notes with committed positions | full |
| 6 | Cross-locus reconcile | Reconcile the locus-level positions | full |
| 7 | Source tensions | Extract explicit disagreements between sources | full |
| 8 | Corpus critic | Ask what source would overturn the current direction | full |
| 9 | Evidence digest | Compile the strongest evidence and quotes | full |
| 10 | Triple draft | Produce draft material from curated angles | both |
| 11 | Synthesize | Build the final report | full |
| 12 | Critics | Run adversarial critique passes | full |
| 13 | Gap-fetch | Fetch sources identified by the critics | full |
| 14 | Patcher | Apply surgical edits, not rewrites | full |
| 15 | Polish | Clean up hygiene, filler, and drift | both |
| 16 | Readability audit | Suggest readability improvements | both |

The pipeline is tier-aware:

- `light` skips the deepest adversarial steps
- `full` runs the complete workflow

---

## Vault Model

The vault is the durable part of hyperresearch.

- Notes live in `research/notes/`
- Markdown is the source of truth
- SQLite is the rebuildable index
- Fetched sources can be searched, linked, and reused later
- `hyperresearch sync` rebuilds the index from markdown if needed

This makes the repository useful as both a research workflow and a long-lived knowledge base.

---

## How Codex Routing Works

The Codex path now has two layers:

1. fixed role mapping in `.codex/agents/*.toml`
2. automatic effort routing for direct tasks

The router is intentionally cheap:

- read-only
- low effort
- fast preflight classification
- output limited to `reasoning_effort` and a short explanation

That keeps the model roster stable while still avoiding unnecessary compute on trivial tasks.

---

## Setup and Crawling

`hyperresearch setup` provides interactive first-time configuration.

If you use browser-backed crawling, you can configure:

- web provider
- login profile
- stealth / browser behavior

`crawl4ai` is the preferred browser-backed provider when available. If it is not installed, the vault can still use the built-in web path.

---

## Attribution

Original inspiration:

- Jordan Gibbs' original hyperresearch repository: https://github.com/jordan-gibbs/hyperresearch

This repository keeps the core idea and adapts it for a Codex-first workflow with a Codex-native bundle, dynamic effort routing, and the same persistent vault model.

---

## Requirements

- Python 3.11 to 3.13
- Codex CLI for the Codex path
- Claude Code for the legacy Claude path

---

## License

[MIT](LICENSE)
