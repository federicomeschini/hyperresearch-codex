# Changelog

## [Unreleased] - Codex-only adaptation

### Changed

- Removed the user-facing platform switch from install/setup/repair/config flows. `hyperresearch install` now targets Codex assets directly.
- Updated vault initialization and docs injection to create `AGENTS.md` only.
- Updated the Codex bundle and generated docs to treat `light` vs `full` as a required user choice, not an inferred classifier result.
- Updated README, CONTRIBUTING, and AGENTS.md for the independent Codex repository at `federicomeschini/hyperresearch-codex`.

### Removed

- Removed legacy hook tests and documentation for non-Codex install paths.
- Removed generated legacy agent output paths from `.gitignore`.
