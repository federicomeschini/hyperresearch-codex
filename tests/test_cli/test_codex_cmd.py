from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from hyperresearch.core import codex_runner
from hyperresearch.core.codex_bundle import build_codex_effort_router_prompt


def test_build_codex_effort_router_prompt_includes_task():
    prompt = build_codex_effort_router_prompt("analyze this task")

    assert "reasoning budget" in prompt
    assert "Task brief:" in prompt
    assert "analyze this task" in prompt
    assert "`model`" not in prompt


def test_route_effort_parses_router_json(monkeypatch):
    def fake_run(cmd, check=False, capture_output=False, text=False):
        output_path = Path(cmd[cmd.index("-o") + 1])
        output_path.write_text(
            '{"reasoning_effort": "high", "why": "adversarial and final"}',
            encoding="utf-8",
        )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(codex_runner, "resolve_codex_cli", lambda: "codex")
    monkeypatch.setattr(codex_runner.subprocess, "run", fake_run)

    effort, why = codex_runner.route_effort("analyze this task", Path("C:/workspace"))

    assert effort == "high"
    assert why == "adversarial and final"


def test_route_effort_falls_back_to_medium(monkeypatch):
    def fake_run(cmd, check=False, capture_output=False, text=False):
        return SimpleNamespace(returncode=1, stdout="", stderr="router failed")

    monkeypatch.setattr(codex_runner, "resolve_codex_cli", lambda: "codex")
    monkeypatch.setattr(codex_runner.subprocess, "run", fake_run)

    effort, why = codex_runner.route_effort("analyze this task", Path("C:/workspace"))

    assert effort == "medium"
    assert why is None


def test_run_codex_builds_reasoning_override(monkeypatch):
    recorded = {}

    def fake_run(cmd, check=False):
        recorded["cmd"] = cmd
        return SimpleNamespace(returncode=7)

    monkeypatch.setattr(codex_runner, "resolve_codex_cli", lambda: "codex")
    monkeypatch.setattr(codex_runner.subprocess, "run", fake_run)

    rc = codex_runner.run_codex("analyze this task", Path("C:/workspace"), "medium")

    assert rc == 7
    assert recorded["cmd"][:2] == ["codex", "exec"]
    assert "-c" in recorded["cmd"]
    assert "reasoning.effort=medium" in recorded["cmd"]
    assert recorded["cmd"][-1] == "analyze this task"
