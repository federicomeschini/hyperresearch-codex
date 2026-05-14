# hyperresearch

Codex-first research harness with a persistent vault, a 16-step research workflow, and an automatic reasoning-effort preflight for direct Codex tasks.

This fork adapts the original hyperresearch idea to Codex CLI first, while keeping Claude Code compatibility in the library for the legacy hook flow.

## What this repo does

- Creates a vault for research notes, sources, and indexes.
- Runs the research workflow as a sequence of small agent steps.
- Installs Codex-native agent bundles under `.codex/` and `.agents/`.
- Routes direct Codex tasks through a cheap preflight agent before the main run.
- Keeps the vault rebuildable from markdown.

## Research workflow

| Step | Name | Output | Tier |
|---|---|---|---|
| 1 | Decompose | Atomic asks + coverage plan | both |
| 2 | Width sweep | Search plan + seed sources | both |
| 3 | Contradiction graph | Clustered tensions | full |
| 4 | Loci analysis | Focused loci + budgets | full |
| 5 | Depth investigation | Interim notes with committed positions | full |
| 6 | Cross-locus reconcile | Merged locus positions | full |
| 7 | Source tensions | Explicit source disagreements | full |
| 8 | Corpus critic | Overturning-source check | full |
| 9 | Evidence digest | Quotes + strongest claims | full |
| 10 | Triple draft | Draft material from curated angles | both |
| 11 | Synthesize | Final report | full |
| 12 | Critics | Adversarial critique passes | full |
| 13 | Gap-fetch | Fetch critic-identified gaps | full |
| 14 | Patcher | Surgical edits only | full |
| 15 | Polish | Clean-up and consistency pass | both |
| 16 | Readability audit | Readability recommendations | both |

The workflow stays tier-aware:

- `light` trims the deepest review steps
- `full` runs the complete pipeline

## Install

```bash
pip install hyperresearch
hyperresearch install --platform codex
```

Use the Codex path for normal work:

```bash
hyperresearch research "your question"
```

Use the Codex task wrapper when you want automatic reasoning-effort routing:

```bash
hyperresearch codex run "review this module for race conditions"
```

Use the legacy Claude Code path only if you need the old hook flow:

```bash
hyperresearch install --platform claude
```

Global install is available too:

```bash
hyperresearch install --global
```

## Codex path

`hyperresearch install --platform codex` installs:

- `AGENTS.md` at the vault root
- `.agents/skills/<skill>/SKILL.md`
- `.codex/agents/*.toml`
- `.codex/config.toml`

The Codex install also adds a tiny router agent. It does not change the model roster. It only recommends `reasoning.effort` for the task so the main Codex run does not spend more compute than needed.

The launcher command is:

```bash
hyperresearch codex run "<task>"
```

That wrapper:

1. runs the router agent
2. reads `reasoning_effort`
3. starts `codex exec` with `-c reasoning.effort=<value>`

## Codex agent budget map

| Agent group | Model | Reasoning effort | Notes |
|---|---|---|---|
| Effort router | `gpt-5.4-mini` | `low` | Read-only preflight that picks the cheapest safe effort |
| Fetcher / readability | `gpt-5.4-mini` | `medium` | High-throughput extraction and formatting work |
| Loci / depth / source / patch / polish / draft orchestration | `gpt-5.4` | `medium` | Operational analysis and editing roles |
| Critics / synthesizer | `gpt-5.5` | `high` | Adversarial review and final arbitration |

The model roster is fixed by role. The router only changes the effort budget, not the model choice.

## Vault layout

The vault is the persistent part of the system.

- Markdown notes live in `research/notes/`
- The SQLite index lives under `.hyperresearch/`
- Fetched sources can be searched later
- `hyperresearch sync` rebuilds the index from markdown
- `hyperresearch repair` refreshes the vault and platform bundle

The goal is that the repository stays useful even if the index is deleted or the session changes.

## Practical commands

- `hyperresearch setup` starts interactive setup.
- `hyperresearch fetch "<url>"` fetches a source into the vault.
- `hyperresearch search "<query>"` searches the vault.
- `hyperresearch note show <id>` reads a note.
- `hyperresearch lint` checks vault structure and links.
- `hyperresearch repair` repairs vault state and bundle files.
- `hyperresearch sync` rescans markdown and rebuilds the index.
- `hyperresearch mcp` starts the read-only MCP server.

## How to think about the Codex bundle

There are two layers in the Codex setup:

1. static role definitions in `.codex/agents/*.toml`
2. dynamic effort routing for direct tasks

That keeps the system predictable while still letting cheap tasks stay cheap.

## Requirements

- Python 3.11 to 3.13
- Codex CLI for the Codex path
- Claude Code for the legacy path

## Attribution

This repository is an adaptation of the original hyperresearch project by Jordan Gibbs:

https://github.com/jordan-gibbs/hyperresearch

The original workflow and vault idea were the starting point. This fork reworked the runtime for Codex-first usage and added the Codex-native bundle plus effort routing.

## License

[MIT](LICENSE)
