# AGENTS.md

This repository is being adapted for Codex CLI first, while keeping Claude Code compatibility in the library.

Use these defaults when working here:

- Prefer `hyperresearch install --platform codex` when testing the Codex path.
- Use `hyperresearch install --platform claude` only when you need the legacy Claude Code hook flow.
- `hyperresearch mcp` is the read-only MCP server entry point.
- Keep changes narrow and avoid rewriting unrelated Claude-specific code unless the task requires it.
- Preserve existing vault behavior unless the requested change is explicitly about platform adaptation.
