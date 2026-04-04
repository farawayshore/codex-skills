#!/usr/bin/env python3
"""Shared helpers for the standalone course-lab-plotting skill."""

from __future__ import annotations

import csv
import json
import os
import re
import unicodedata
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent


def detect_repo_root() -> Path:
    override = os.environ.get("MODERN_PHYSICS_REPO_ROOT")
    if override:
        candidate = Path(override).expanduser().resolve()
        if (candidate / "AI_works" / "resources").is_dir():
            return candidate

    cwd = Path.cwd().resolve()
    candidates = [cwd, *cwd.parents, SKILL_DIR.parents[1], Path("/root/grassman_projects")]
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "AI_works" / "resources").is_dir():
            return candidate
    return cwd


ROOT = detect_repo_root()
PIC_RESULT_ROOT = ROOT / "AI_works" / "resources" / "experiment_pic_results"


def safe_label(text: str, *, default: str = "plot") -> str:
    normalized = unicodedata.normalize("NFKC", text or "").strip()
    cleaned: list[str] = []
    for ch in normalized:
        if ch.isspace():
            cleaned.append("-")
        elif ch.isalnum() or ch in "-_." or "\u4e00" <= ch <= "\u9fff":
            cleaned.append(ch)
        else:
            cleaned.append("-")
    label = "".join(cleaned)
    label = re.sub(r"-{2,}", "-", label).strip("-.")
    return label or default


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def build_plottings_root(matched_experiment_path: str) -> Path:
    normalized = matched_experiment_path.strip().strip("/")
    return PIC_RESULT_ROOT / normalized / "plottings"


def parameter_identity_stem(parameter_values: dict[str, object] | None) -> str:
    if not parameter_values:
        return "plot"
    parts: list[str] = []
    for key, value in parameter_values.items():
        key_text = safe_label(str(key), default="p")
        value_text = safe_label(str(value), default="value")
        parts.append(f"{key_text}{value_text}")
    return "-".join(parts) or "plot"


def parse_numeric_column(rows: list[dict[str, str]], field: str) -> list[float]:
    values: list[float] = []
    for index, row in enumerate(rows):
        if field not in row:
            raise KeyError(field)
        raw = (row.get(field) or "").strip()
        if not raw:
            raise ValueError(f"empty value for {field} at row {index + 1}")
        values.append(float(raw))
    return values
