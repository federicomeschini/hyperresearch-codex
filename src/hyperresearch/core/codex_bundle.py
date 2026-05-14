"""Codex bundle installer for hyperresearch skills, agent roles, and config.

This module mirrors the Claude installer's roster, but writes the Codex-native
layout:

- `AGENTS.md` at the vault root
- project/home skills under `.agents/skills/<skill>/SKILL.md`
- project/home agent roles under `.codex/agents/*.toml`
- Codex config defaults under `.codex/config.toml`

The implementation is intentionally conservative: it preserves user-owned
content in existing config files and only updates the Codex-specific sections
hyperresearch needs.

Role selection is tiered: `gpt-5.4-mini` handles high-throughput extraction
and formatting, `gpt-5.4` handles mid-depth analysis and editing, and
`gpt-5.5` handles the hardest adversarial and final-arbitration roles.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

from hyperresearch.core.agent_docs import transform_claude_markdown_for_codex
from hyperresearch.core.hooks import (
    CORPUS_CRITIC_AGENT,
    DEPTH_CRITIC_AGENT,
    DEPTH_INVESTIGATOR_AGENT,
    DIALECTIC_CRITIC_AGENT,
    DRAFT_ORCHESTRATOR_AGENT,
    INSTRUCTION_CRITIC_AGENT,
    LOCI_ANALYST_AGENT,
    PATCHER_AGENT,
    POLISH_AUDITOR_AGENT,
    READABILITY_REFORMATTER_AGENT,
    RESEARCHER_AGENT,
    SOURCE_ANALYST_AGENT,
    SYNTHESIZER_AGENT,
    WIDTH_CRITIC_AGENT,
    _HYPERRESEARCH_STEP_SKILLS,
    _RETIRED_AGENT_FILES,
    _RETIRED_SKILL_DIRS,
    _read_skill_source,
    _render_scaffold_only_bullets,
)

@dataclass(frozen=True)
class _CodexModelPolicy:
    model: str
    reasoning_effort: str
    rationale: str


_CODEx_LIGHT_POLICY = _CodexModelPolicy(
    model="gpt-5.4-mini",
    reasoning_effort="low",
    rationale="high-throughput extraction and formatting",
)
_CODEx_STANDARD_POLICY = _CodexModelPolicy(
    model="gpt-5.4",
    reasoning_effort="medium",
    rationale="mid-depth reasoning and surgical editing",
)
_CODEx_FRONTIER_POLICY = _CodexModelPolicy(
    model="gpt-5.5",
    reasoning_effort="high",
    rationale="frontier adversarial reasoning and final arbitration",
)

_CODEx_LIGHT_AGENT_NAMES = {
    "hyperresearch-fetcher",
    "hyperresearch-readability-recommender",
}
_CODEx_STANDARD_AGENT_NAMES = {
    "hyperresearch-loci-analyst",
    "hyperresearch-depth-investigator",
    "hyperresearch-source-analyst",
    "hyperresearch-patcher",
    "hyperresearch-polish-auditor",
    "hyperresearch-draft-orchestrator",
}
_CODEx_FRONTIER_AGENT_NAMES = {
    "hyperresearch-corpus-critic",
    "hyperresearch-dialectic-critic",
    "hyperresearch-depth-critic",
    "hyperresearch-width-critic",
    "hyperresearch-instruction-critic",
    "hyperresearch-synthesizer",
}

_CODEx_AGENT_SPECS: tuple[tuple[str, str], ...] = (
    ("hyperresearch-fetcher", RESEARCHER_AGENT),
    ("hyperresearch-loci-analyst", LOCI_ANALYST_AGENT),
    ("hyperresearch-depth-investigator", DEPTH_INVESTIGATOR_AGENT),
    ("hyperresearch-source-analyst", SOURCE_ANALYST_AGENT),
    ("hyperresearch-corpus-critic", CORPUS_CRITIC_AGENT),
    ("hyperresearch-dialectic-critic", DIALECTIC_CRITIC_AGENT),
    ("hyperresearch-depth-critic", DEPTH_CRITIC_AGENT),
    ("hyperresearch-width-critic", WIDTH_CRITIC_AGENT),
    ("hyperresearch-instruction-critic", INSTRUCTION_CRITIC_AGENT),
    ("hyperresearch-patcher", PATCHER_AGENT),
    ("hyperresearch-polish-auditor", POLISH_AUDITOR_AGENT),
    ("hyperresearch-readability-recommender", READABILITY_REFORMATTER_AGENT),
    ("hyperresearch-draft-orchestrator", DRAFT_ORCHESTRATOR_AGENT),
    ("hyperresearch-synthesizer", SYNTHESIZER_AGENT),
)


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _toml_array(values: Iterable[str]) -> str:
    return json.dumps(list(values), ensure_ascii=False)


def _toml_multiline_string(value: str) -> str:
    escaped = json.dumps(value, ensure_ascii=False)[1:-1]
    return f'"""{escaped}"""'


def _write_text_if_changed(path: Path, content: str) -> bool:
    """Write text only when it changed. Returns True when a write happened."""
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing == content:
            return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _codex_model_policy(agent_name: str) -> _CodexModelPolicy:
    if agent_name in _CODEx_FRONTIER_AGENT_NAMES:
        return _CODEx_FRONTIER_POLICY
    if agent_name in _CODEx_LIGHT_AGENT_NAMES:
        return _CODEx_LIGHT_POLICY
    return _CODEx_STANDARD_POLICY


def _render_prompt(prompt: str, hpr_path: str, *, model_label: str) -> str:
    """Format the Claude prompt and translate it into Codex-oriented text."""
    rendered = prompt.replace("{hpr_path}", hpr_path.replace("\\", "/"))
    rendered = rendered.replace(
        "{scaffold_only_sections}",
        _render_scaffold_only_bullets(indent="- "),
    )
    return transform_claude_markdown_for_codex(rendered, model_label=model_label)


def _split_prompt(prompt: str) -> tuple[dict[str, object], str]:
    """Split a skill/agent prompt into YAML frontmatter and body."""
    if not prompt.startswith("---\n"):
        raise ValueError("prompt is missing YAML frontmatter")

    end = prompt.find("\n---\n", 4)
    if end == -1:
        raise ValueError("prompt frontmatter is not terminated")

    frontmatter = prompt[4:end]
    body = prompt[end + 5 :].lstrip("\n")
    meta = yaml.safe_load(frontmatter) or {}
    if not isinstance(meta, dict):
        raise ValueError("prompt frontmatter is not a mapping")
    return meta, body


def _nickname_candidates(name: str) -> list[str]:
    """Derive a few human-friendly nicknames for a Codex agent role."""
    if name.startswith("hyperresearch-"):
        slug = name.removeprefix("hyperresearch-")
    else:
        slug = name

    candidates: list[str] = []
    spaced = slug.replace("-", " ").strip()
    if spaced:
        candidates.append(spaced)

    tail = slug.split("-")[-1].strip()
    if tail and tail not in candidates:
        candidates.append(tail)

    return candidates


def _render_agent_toml(
    *,
    name: str,
    description: str,
    developer_instructions: str,
    model: str,
    model_policy: _CodexModelPolicy,
    sandbox_mode: str = "workspace-write",
    nickname_candidates: Iterable[str] = (),
) -> str:
    """Render a Codex agent role TOML file."""
    lines = [
        f"name = {_toml_string(name)}",
        f"description = {_toml_string(description)}",
        f"# Model tier: {model_policy.rationale}",
        f"developer_instructions = {_toml_multiline_string(developer_instructions)}",
        f"model = {_toml_string(model)}",
        f"model_reasoning_effort = {_toml_string(model_policy.reasoning_effort)}",
        f"sandbox_mode = {_toml_string(sandbox_mode)}",
    ]

    nicknames = [candidate for candidate in nickname_candidates if candidate]
    if nicknames:
        lines.append(f"nickname_candidates = {_toml_array(nicknames)}")

    return "\n".join(lines) + "\n"


def _render_agent_content(
    prompt: str,
    hpr_path: str,
    target_model: str,
) -> tuple[dict[str, object], str]:
    """Format and transform an agent prompt into Codex-ready content."""
    rendered = _render_prompt(prompt, hpr_path, model_label=target_model)
    return _split_prompt(rendered)


def _prune_codex_skill_dirs(skill_root: Path) -> str | None:
    """Remove stale step skill directories from a Codex skills root."""
    if not skill_root.is_dir():
        return None

    pruned: list[str] = []
    expected = set(_HYPERRESEARCH_STEP_SKILLS) | {"hyperresearch"}
    for child in skill_root.iterdir():
        if not child.is_dir():
            continue
        is_stale_hpr = child.name.startswith("hyperresearch-") and child.name not in expected
        is_legacy_layercake = child.name.startswith("layercake-")
        is_retired = child.name in _RETIRED_SKILL_DIRS
        if not (is_stale_hpr or is_legacy_layercake or is_retired):
            continue
        for f in child.iterdir():
            if f.is_file():
                f.unlink()
            elif f.is_dir():
                import shutil

                shutil.rmtree(f)
        child.rmdir()
        pruned.append(child.name)

    if not pruned:
        return None
    return f"Pruned stale Codex skills: {', '.join(sorted(pruned))}"


def _prune_codex_agent_files(agents_dir: Path) -> str | None:
    """Remove retired agent role files from a Codex agents root."""
    if not agents_dir.is_dir():
        return None

    retired_stems = set(_RETIRED_AGENT_FILES) | {"hyperresearch-readability-reformatter"}
    removed: list[str] = []

    for stem in retired_stems:
        for suffix in (".toml", ".md"):
            path = agents_dir / f"{stem}{suffix}"
            if path.exists():
                path.unlink()
                removed.append(path.name)

    if not removed:
        return None
    return f"Pruned retired Codex agents: {', '.join(sorted(removed))}"


def _install_codex_entry_skill(root: Path, hpr_path: str) -> str | None:
    content = _read_skill_source("hyperresearch.md")
    if content is None:
        return None

    content = transform_claude_markdown_for_codex(content, model_label="gpt-5.5")
    skill_root = root / ".agents" / "skills"
    skill_root.mkdir(parents=True, exist_ok=True)
    dest_path = skill_root / "hyperresearch" / "SKILL.md"
    if not _write_text_if_changed(dest_path, content):
        return None
    return f"Codex: {dest_path.as_posix()}"


def _install_codex_step_skills(root: Path, hpr_path: str) -> str | None:
    skill_root = root / ".agents" / "skills"
    skill_root.mkdir(parents=True, exist_ok=True)

    installed: list[str] = []
    for skill_name in _HYPERRESEARCH_STEP_SKILLS:
        source_name = f"{skill_name}.md"
        content = _read_skill_source(source_name)
        if content is None:
            continue
        content = transform_claude_markdown_for_codex(content)
        dest_path = skill_root / skill_name / "SKILL.md"
        if _write_text_if_changed(dest_path, content):
            installed.append(skill_name)

    pruned = _prune_codex_skill_dirs(skill_root)
    if not installed and pruned is None:
        return None

    parts: list[str] = []
    if installed:
        parts.append(f"{len(installed)} step skills")
    if pruned:
        parts.append(pruned)
    return f"Codex: {skill_root.as_posix()} ({'; '.join(parts)})"


def _install_codex_agents(root: Path, hpr_path: str) -> list[str]:
    agents_dir = root / ".codex" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    actions: list[str] = []
    for name, prompt in _CODEx_AGENT_SPECS:
        policy = _codex_model_policy(name)
        meta, body = _render_agent_content(prompt, hpr_path, policy.model)
        rendered_name = str(meta.get("name", name))
        description = str(meta.get("description", "")).strip()
        model_value = policy.model
        nickname_candidates = _nickname_candidates(rendered_name)
        toml = _render_agent_toml(
            name=rendered_name,
            description=description,
            developer_instructions=body,
            model=model_value,
            model_policy=policy,
            nickname_candidates=nickname_candidates,
        )
        dest_path = agents_dir / f"{name}.toml"
        if _write_text_if_changed(dest_path, toml):
            actions.append(f"Codex: {dest_path.as_posix()}")

    pruned = _prune_codex_agent_files(agents_dir)
    if pruned is not None:
        actions.append(pruned)

    return actions


def _update_toml_section(
    text: str,
    section_name: str,
    updates: dict[str, object],
) -> tuple[str, bool]:
    """Update or append a TOML section with the supplied keys."""
    header = f"[{section_name}]"
    section_re = re.compile(
        rf"(?ms)^(\[{re.escape(section_name)}\])\s*(.*?)(?=^\[|\Z)"
    )
    match = section_re.search(text)

    if match is None:
        section_lines = [header]
        for key, value in updates.items():
            section_lines.append(f"{key} = {_render_toml_value(value)}")
        section_lines.append("")
        if text and not text.endswith("\n"):
            text += "\n"
        return text + ("\n".join(section_lines) + "\n"), True

    body = match.group(2)
    original_lines = body.splitlines()
    remaining = dict(updates)
    new_lines: list[str] = []

    for line in original_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue

        key_match = re.match(r"^([A-Za-z0-9_-]+)\s*=\s*.*$", line)
        if key_match is None:
            new_lines.append(line)
            continue

        key = key_match.group(1)
        if key in remaining:
            new_lines.append(f"{key} = {_render_toml_value(remaining.pop(key))}")
        else:
            new_lines.append(line)

    for key, value in remaining.items():
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        new_lines.append(f"{key} = {_render_toml_value(value)}")

    new_body = "\n".join(new_lines).rstrip() + "\n"
    new_text = text[: match.start(2)] + new_body + text[match.end(2) :]
    return new_text, new_text != text


def _render_toml_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, str):
        return _toml_string(value)
    if isinstance(value, (list, tuple)):
        return _toml_array(str(item) for item in value)
    raise TypeError(f"Unsupported TOML value type: {type(value)!r}")


def _update_codex_config(root: Path) -> str | None:
    """Update `.codex/config.toml` with the hyperresearch defaults."""
    config_path = root / ".codex" / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if config_path.exists():
        text = config_path.read_text(encoding="utf-8")
    else:
        text = ""

    changed = False

    text, section_changed = _update_toml_section(
        text,
        "features",
        {"multi_agent": True},
    )
    changed = changed or section_changed

    text, section_changed = _update_toml_section(
        text,
        "agents",
        {
            "max_threads": 16,
            "max_depth": 4,
            "job_max_runtime_seconds": 10800,
            "interrupt_message": True,
        },
    )
    changed = changed or section_changed

    if changed:
        config_path.write_text(text.rstrip() + "\n", encoding="utf-8")
        return f"Codex: {config_path.as_posix()}"
    return None


def install_codex_project_bundle(vault_root: Path, hpr_path: str = "hyperresearch") -> list[str]:
    """Install the full Codex bundle inside a project vault."""
    actions: list[str] = []

    entry = _install_codex_entry_skill(vault_root, hpr_path)
    if entry:
        actions.append(entry)

    steps = _install_codex_step_skills(vault_root, hpr_path)
    if steps:
        actions.append(steps)

    actions.extend(_install_codex_agents(vault_root, hpr_path))

    config = _update_codex_config(vault_root)
    if config:
        actions.append(config)

    return actions


def install_codex_global_bundle(home: Path | None = None, hpr_path: str = "hyperresearch") -> list[str]:
    """Install the user-level Codex bundle under the home directory."""
    if home is None:
        home = Path.home()

    actions: list[str] = []

    entry = _install_codex_entry_skill(home, hpr_path)
    if entry:
        actions.append(entry)

    # Global installs keep the shared entry skill and agent roles, but skip
    # the per-project step skills. Those are installed lazily on first use.
    actions.extend(_install_codex_agents(home, hpr_path))

    config = _update_codex_config(home)
    if config:
        actions.append(config)

    # Clean up stale per-project step skills left in the home scope by older
    # versions that installed them globally.
    pruned = _prune_codex_skill_dirs(home / ".agents" / "skills")
    if pruned:
        actions.append(pruned)

    return actions


def install_codex_step_skills(root: Path, hpr_path: str = "hyperresearch") -> str | None:
    """Install only the 16 Codex step skills inside the target project."""
    return _install_codex_step_skills(root, hpr_path)


def refresh_codex_project_bundle(vault_root: Path, hpr_path: str = "hyperresearch") -> list[str]:
    """Refresh the project Codex bundle."""
    return install_codex_project_bundle(vault_root, hpr_path=hpr_path)
