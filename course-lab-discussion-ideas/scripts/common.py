from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_text_if_exists(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def safe_label(text: str, *, default: str = "item") -> str:
    cleaned: list[str] = []
    for ch in text.strip():
        if ch.isspace():
            cleaned.append("-")
        elif ch.isalnum() or ch in "-_." or "\u4e00" <= ch <= "\u9fff":
            cleaned.append(ch)
        else:
            cleaned.append("-")
    name = "".join(cleaned)
    name = re.sub(r"-{2,}", "-", name).strip("-.")
    return name or default
