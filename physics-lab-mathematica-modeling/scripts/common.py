from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any


def ensure_dir(path: str | Path) -> Path:
    resolved = Path(path)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: Any) -> Path:
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return resolved


def safe_case_stem(run_config: dict[str, Any]) -> str:
    raw = str(
        run_config.get("case_id")
        or run_config.get("run_id")
        or run_config.get("label")
        or "case"
    )
    lowered = raw.strip().lower()
    safe = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return safe or "case"


def write_run_result(path: str | Path, payload: dict[str, Any]) -> Path:
    return write_json(path, payload)


def case_identity_key(parameters: dict[str, Any]) -> tuple[Any, Any, Any]:
    frequency_hz = parameters.get("frequency_hz")
    if frequency_hz is None and "f_kHz" in parameters:
        frequency_hz = float(parameters["f_kHz"]) * 1000.0
    if frequency_hz is not None:
        frequency_hz = round(float(frequency_hz), 6)
    return (
        frequency_hz,
        parameters.get("m"),
        parameters.get("n"),
    )


def lookup_path(payload: dict[str, Any], dotted_path: str):
    current: Any = payload
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(dotted_path)
        current = current[part]
    return current
