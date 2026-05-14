"""Tests for the Codex bundle installer."""

from __future__ import annotations

from pathlib import Path

from hyperresearch.core.codex_bundle import (
    install_codex_global_bundle,
    install_codex_project_bundle,
    install_codex_step_skills,
)
from hyperresearch.core.vault import Vault


def test_install_codex_project_bundle_creates_codex_layout(tmp_path: Path):
    root = tmp_path / "kb"
    Vault.init(root, agent_platform="codex")

    codex_dir = root / ".codex"
    codex_dir.mkdir(exist_ok=True)
    (codex_dir / "config.toml").write_text(
        'model = "gpt-5.4-mini"\npersonality = "pragmatic"\n',
        encoding="utf-8",
    )

    actions = install_codex_project_bundle(root, hpr_path=r"C:\Tools\hyperresearch.exe")
    assert actions

    entry_skill = root / ".agents" / "skills" / "hyperresearch" / "SKILL.md"
    step_skill = root / ".agents" / "skills" / "hyperresearch-1-decompose" / "SKILL.md"
    fetcher = root / ".codex" / "agents" / "hyperresearch-fetcher.toml"
    router = root / ".codex" / "agents" / "hyperresearch-effort-router.toml"
    config = root / ".codex" / "config.toml"

    assert entry_skill.exists()
    assert step_skill.exists()
    assert fetcher.exists()
    assert router.exists()
    assert config.exists()

    entry_text = entry_skill.read_text(encoding="utf-8")
    assert ".agents/skills" in entry_text
    assert "gpt-5.5" in entry_text

    fetcher_text = fetcher.read_text(encoding="utf-8")
    assert 'model = "gpt-5.4-mini"' in fetcher_text
    assert 'model_reasoning_effort = "medium"' in fetcher_text
    assert 'developer_instructions = """' in fetcher_text
    assert "C:/Tools/hyperresearch.exe" in fetcher_text

    router_text = router.read_text(encoding="utf-8")
    assert 'model = "gpt-5.4-mini"' in router_text
    assert 'model_reasoning_effort = "low"' in router_text
    assert 'sandbox_mode = "read-only"' in router_text
    assert "reasoning-effort selection" in router_text
    assert "- `reasoning_effort`" in router_text
    assert "- `tier`" not in router_text
    assert "- `model`" not in router_text

    corpus_critic = root / ".codex" / "agents" / "hyperresearch-corpus-critic.toml"
    patcher = root / ".codex" / "agents" / "hyperresearch-patcher.toml"
    synthesizer = root / ".codex" / "agents" / "hyperresearch-synthesizer.toml"

    assert corpus_critic.exists()
    assert patcher.exists()
    assert synthesizer.exists()
    assert 'model = "gpt-5.5"' in corpus_critic.read_text(encoding="utf-8")
    assert 'model_reasoning_effort = "high"' in corpus_critic.read_text(encoding="utf-8")
    assert 'model = "gpt-5.4"' in patcher.read_text(encoding="utf-8")
    assert 'model_reasoning_effort = "medium"' in patcher.read_text(encoding="utf-8")
    assert 'model = "gpt-5.5"' in synthesizer.read_text(encoding="utf-8")
    assert 'model_reasoning_effort = "high"' in synthesizer.read_text(encoding="utf-8")

    config_text = config.read_text(encoding="utf-8")
    assert 'model = "gpt-5.4-mini"' in config_text
    assert 'personality = "pragmatic"' in config_text
    assert "[features]" in config_text
    assert "multi_agent = true" in config_text
    assert "[agents]" in config_text
    assert "max_threads = 16" in config_text
    assert "max_depth = 4" in config_text


def test_install_codex_global_bundle_skips_step_skills(tmp_path: Path):
    home = tmp_path / "home"
    actions = install_codex_global_bundle(home, hpr_path="hyperresearch")
    assert actions

    assert (home / ".agents" / "skills" / "hyperresearch" / "SKILL.md").exists()
    assert not (home / ".agents" / "skills" / "hyperresearch-1-decompose" / "SKILL.md").exists()
    assert (home / ".codex" / "agents" / "hyperresearch-effort-router.toml").exists()
    assert (home / ".codex" / "agents" / "hyperresearch-synthesizer.toml").exists()
    assert (home / ".codex" / "config.toml").exists()


def test_install_codex_step_skills_is_idempotent(tmp_path: Path):
    root = tmp_path / "project"
    first = install_codex_step_skills(root)
    second = install_codex_step_skills(root)

    assert first is not None
    assert second is None
    assert (root / ".agents" / "skills" / "hyperresearch-16-readability-audit" / "SKILL.md").exists()
