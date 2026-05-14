"""Codex launcher helpers for automatic effort routing and execution."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from hyperresearch.core.codex_bundle import build_codex_effort_router_prompt

_EFFORT_VALUES = {"low", "medium", "high"}


def resolve_codex_cli() -> str:
    for candidate in ("codex.cmd", "codex.exe", "codex"):
        path = shutil.which(candidate)
        if path:
            return path
    raise FileNotFoundError("Codex CLI is not on PATH. Install Codex first.")


def extract_json_object(text: str) -> dict[str, object]:
    stripped = text.strip()
    if not stripped:
        raise ValueError("empty router output")

    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        data = json.loads(stripped[start : end + 1])

    if not isinstance(data, dict):
        raise ValueError("router output was not a JSON object")
    return data


def normalize_effort(value: object) -> str:
    effort = str(value or "").strip().lower()
    if effort not in _EFFORT_VALUES:
        return "medium"
    return effort


def route_effort(task: str, cwd: Path) -> tuple[str, str | None]:
    """Run the cheap Codex router and return `(effort, why)`."""
    codex = resolve_codex_cli()
    router_prompt = build_codex_effort_router_prompt(task)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
        output_path = Path(tmp.name)

    try:
        result = subprocess.run(
            [
                codex,
                "exec",
                "--cd",
                str(cwd),
                "--skip-git-repo-check",
                "--ephemeral",
                "--ignore-user-config",
                "-m",
                "gpt-5.4-mini",
                "-s",
                "read-only",
                "-a",
                "never",
                "-o",
                str(output_path),
                router_prompt,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        router_text = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "router failed").strip())
        data = extract_json_object(router_text)
        effort = normalize_effort(data.get("reasoning_effort"))
        why = str(data.get("why") or "").strip() or None
        return effort, why
    except Exception:
        return "medium", None
    finally:
        try:
            output_path.unlink(missing_ok=True)
        except Exception:
            pass


def run_codex(task: str, cwd: Path, effort: str) -> int:
    codex = resolve_codex_cli()
    cmd = [
        codex,
        "exec",
        "--cd",
        str(cwd),
        "-c",
        f"reasoning.effort={effort}",
        task,
    ]
    return subprocess.run(cmd, check=False).returncode
