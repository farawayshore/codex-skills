#!/usr/bin/env python3
"""Shared helpers for the course-lab-metadata-frontmatter skill."""

from __future__ import annotations

import json
import os
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent


def detect_repo_root() -> Path:
    override = os.environ.get("MODERN_PHYSICS_REPO_ROOT")
    if override:
        candidate = Path(override).expanduser().resolve()
        if (candidate / "AI_works" / "resources").is_dir():
            return candidate

    candidates: list[Path] = []
    cwd = Path.cwd().resolve()
    candidates.append(cwd)
    candidates.extend(cwd.parents)
    candidates.append(SKILL_DIR.parents[1])
    candidates.append(Path("/root/grassman_projects"))

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "AI_works" / "resources").is_dir():
            return candidate
    return cwd


ROOT = detect_repo_root()
AI_WORKS_ROOT = ROOT / "AI_works"
RESOURCES_ROOT = AI_WORKS_ROOT / "resources"
AUTHOR_PROFILE_PATH = RESOURCES_ROOT / "report_author_profile.json"


def read_json(path: Path) -> dict[str, object] | list[object] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
