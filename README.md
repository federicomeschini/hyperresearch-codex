# hyperresearch-codex

Codex-first research harness with a persistent vault, a 16-step research workflow, Codex-native skills/subagents, and an automatic reasoning-effort preflight for direct Codex tasks.

This repository is the independent Codex transposition of hyperresearch. The user-facing installer writes Codex assets only: `AGENTS.md`, `.agents/skills/`, `.codex/agents/`, and `.codex/config.toml`.

## What This Repo Does

- Creates a local vault for research notes, fetched sources, indexes, and final reports.
- Installs the complete hyperresearch workflow as Codex-native skills and subagents.
- Runs the research workflow as small step skills loaded fresh by Codex.
- Keeps the vault rebuildable from markdown through `sync`, `repair`, and `lint`.
- Provides a read-only MCP server for vault search and note access.
- Routes direct Codex tasks through a cheap preflight agent before the main run.

## Research Workflow

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

Tier is always a user choice:

- `light` runs the bounded path: 1 -> 2 -> 10 -> 15 -> 16.
- `full` runs all 16 steps with adversarial review and patching.

The pipeline should not infer the tier from the query. Pass it explicitly in the prompt, for example `--tier light` or `tier: full`, or choose when Codex asks.

## Install

```bash
pip install hyperresearch
hyperresearch install
```

Global install is available when you want `/hyperresearch` available in every Codex session:

```bash
hyperresearch install --global
```

Install only the per-project step skills:

```bash
hyperresearch install --steps-only .
```

`hyperresearch install` creates or refreshes:

- `AGENTS.md`
- `.agents/skills/<skill>/SKILL.md`
- `.codex/agents/*.toml`
- `.codex/config.toml`

## Typical Workflow

1. Run `hyperresearch install` in the project or vault root.
2. Start a Codex session in that directory.
3. Run `/hyperresearch <query> --tier light` for a faster bounded report, or `/hyperresearch <query> --tier full` for the complete pipeline.
4. Let Codex fetch, store, search, and synthesize sources through the vault.
5. Read the final report at `research/notes/final_report_<vault_tag>.md`.
6. Run `hyperresearch lint` and `hyperresearch repair` when you want to check or refresh vault state.

## Vault Access

The vault is a local markdown-first research store.

- Notes live in `research/notes/`.
- Temporary pipeline artifacts live in `research/temp/`.
- The SQLite index lives under `.hyperresearch/`.
- Fetched PDFs and assets are stored under `research/raw/` or asset paths linked from notes.
- `hyperresearch sync` rebuilds the index from markdown.
- `hyperresearch repair` refreshes docs, Codex bundle files, indexes, links, and metadata.

The vault is accessible in three ways:

- Codex skills and subagents during `/hyperresearch`.
- The CLI: `fetch`, `search`, `note show`, `note list`, `tags`, `lint`, `repair`, and `sync`.
- The read-only MCP server: `hyperresearch mcp`.

There is no separate GUI in this repo. The CLI and MCP server are the supported vault interfaces.

## Practical Commands

- `hyperresearch setup` starts interactive setup.
- `hyperresearch fetch "<url>"` fetches a source into the vault.
- `hyperresearch search "<query>"` searches the vault.
- `hyperresearch note show <id>` reads a note.
- `hyperresearch note list` lists notes.
- `hyperresearch tags` lists the tag vocabulary.
- `hyperresearch lint` checks vault structure and links.
- `hyperresearch repair` repairs vault state and Codex bundle files.
- `hyperresearch sync` rescans markdown and rebuilds the index.
- `hyperresearch mcp` starts the read-only MCP server.
- `hyperresearch codex run "<task>"` runs the direct-task effort router before invoking Codex.

## Codex Agent Policy

The installed Codex bundle uses static role definitions in `.codex/agents/*.toml` plus dynamic effort routing for direct tasks.

| Agent | Role | Model | Default effort |
|---|---|---|---|
| `hyperresearch-effort-router` | Direct-task effort classifier | `gpt-5.4-mini` | `low` |
| `hyperresearch-fetcher` | URL fetching | `gpt-5.4-mini` | `medium` |
| `hyperresearch-readability-recommender` | Readability suggestions | `gpt-5.4-mini` | `medium` |
| `hyperresearch-loci-analyst` | Loci selection | `gpt-5.4` | `medium` |
| `hyperresearch-depth-investigator` | Locus investigation | `gpt-5.4` | `medium` |
| `hyperresearch-source-analyst` | Long-source digest | `gpt-5.4` | `medium` |
| `hyperresearch-draft-orchestrator` | Draft orchestration | `gpt-5.4` | `medium` |
| `hyperresearch-patcher` | Surgical editing | `gpt-5.4` | `medium` |
| `hyperresearch-polish-auditor` | Hygiene pass | `gpt-5.4` | `medium` |
| `hyperresearch-corpus-critic` | Corpus pressure test | `gpt-5.5` | `high` |
| `hyperresearch-dialectic-critic` | Counter-evidence | `gpt-5.5` | `high` |
| `hyperresearch-depth-critic` | Depth coverage | `gpt-5.5` | `high` |
| `hyperresearch-width-critic` | Breadth coverage | `gpt-5.5` | `high` |
| `hyperresearch-instruction-critic` | Prompt fidelity | `gpt-5.5` | `high` |
| `hyperresearch-synthesizer` | Final synthesis | `gpt-5.5` | `high` |

## Requirements

- Python 3.11 to 3.13
- Codex CLI for `hyperresearch codex run`

## Attribution

This repository is based on the original hyperresearch project by Jordan Gibbs:

https://github.com/jordan-gibbs/hyperresearch

The original workflow and vault idea were the starting point. This repo reworks the runtime and documentation for Codex-first usage.

## License

[MIT](LICENSE)
