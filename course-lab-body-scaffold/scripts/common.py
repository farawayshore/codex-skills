#!/usr/bin/env python3
"""Shared helpers for the course-lab-body-scaffold skill."""

from __future__ import annotations

import json
import re
from pathlib import Path


SECTION_RE = re.compile(r"\\(?:section|chapter)\*?\{([^}]*)\}")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_heading(text: str) -> str:
    value = text.casefold().replace("&", " and ")
    value = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^]]*\])?\{([^}]*)\}", r"\1", value)
    value = re.sub(r"[^\w\u4e00-\u9fff]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    escaped = []
    for char in text:
        escaped.append(replacements.get(char, char))
    return "".join(escaped)


def extract_template_sections(tex_text: str) -> list[str]:
    return [match.strip() for match in SECTION_RE.findall(tex_text) if match.strip()]


def dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(key)
    return result
