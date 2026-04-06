#!/usr/bin/env python3
"""Shared helpers for the standalone finalize-qc skill."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


def read_json(path: Path) -> dict[str, object] | list[object] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def copy_if_needed(src: Path, dst: Path) -> bool:
    src_text = src.read_text(encoding="utf-8")
    if dst.exists() and dst.read_text(encoding="utf-8") == src_text:
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def run_command(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="backslashreplace",
        capture_output=True,
        check=False,
    )
