from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

NORMALIZED_KEY_RE = re.compile(r"(?m)^- Normalized key: `([^`]+)`\s*$")
PRIMARY_COMPARISON_LANES = {
    "theory_vs_data",
    "simulation_vs_data",
    "literature_report_vs_data",
}
SUPPORTING_BASES = {
    "handout_standard",
    "internet_reference",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def maybe_read_json(path: Path | None) -> Any:
    if path is None or not path.exists():
        return None
    return read_json(path)


def read_sections_json(path: Path) -> dict[str, object]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise SystemExit(f"Expected JSON object at {path}")
    return payload


def read_sections_markdown(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"(?m)^##\s+", text)
    sections: dict[str, dict[str, str]] = {}
    section_order: list[str] = []

    for block in blocks[1:]:
        block = block.strip()
        if not block:
            continue
        lines = block.splitlines()
        heading = lines[0].strip()
        body = "\n".join(lines[1:])
        match = NORMALIZED_KEY_RE.search(body)
        if not match:
            raise SystemExit(
                f"Malformed normalized sections markdown: missing Normalized key for section {heading!r}"
            )
        key = match.group(1).strip()
        trailing = body[match.end() :].splitlines()
        while trailing and not trailing[0].strip():
            trailing.pop(0)
        section_text = "\n".join(trailing).strip()
        sections[key] = {"heading": heading, "text": section_text}
        section_order.append(key)

    if not sections:
        raise SystemExit(f"Malformed normalized sections markdown: no normalized sections found in {path}")

    return {
        "section_order": section_order,
        "sections": sections,
    }


def resolve_handout_sections(
    handout_sections_markdown: str | None,
    handout_sections_json: str | None,
) -> dict[str, object]:
    markdown_path = Path(handout_sections_markdown) if handout_sections_markdown else None
    json_path = Path(handout_sections_json) if handout_sections_json else None

    if markdown_path and markdown_path.exists():
        return read_sections_markdown(markdown_path)
    if markdown_path and not markdown_path.exists() and json_path and json_path.exists():
        return read_sections_json(json_path)
    if json_path and json_path.exists() and not markdown_path:
        return read_sections_json(json_path)

    raise SystemExit("Handout sections input is required. No normalized handout sections source found.")


def extract_handout_expectations(summary: dict[str, object]) -> dict[str, object]:
    sections = summary.get("sections", {})
    texts: list[str] = []
    if isinstance(sections, dict):
        for payload in sections.values():
            if not isinstance(payload, dict):
                continue
            text = str(payload.get("text") or "").strip()
            if text:
                texts.append(text)

    combined = "\n".join(texts)
    required_result_families: list[str] = []
    required_observations: list[str] = []

    result_match = re.search(r"required result families:\s*(.+)", combined, re.IGNORECASE)
    if result_match:
        required_result_families = [
            item.strip()
            for item in result_match.group(1).split(",")
            if item.strip()
        ]

    observation_match = re.search(r"required observations:\s*(.+)", combined, re.IGNORECASE)
    if observation_match:
        required_observations = [
            item.strip()
            for item in observation_match.group(1).split(",")
            if item.strip()
        ]

    simulation_required = bool(
        re.search(r"simulation comparison is required", combined, re.IGNORECASE)
    )
    compare_simulation_to_theory = bool(
        re.search(r"compare simulation with theory", combined, re.IGNORECASE)
    )

    return {
        "required_result_families": required_result_families,
        "required_observations": required_observations,
        "simulation_required": simulation_required,
        "compare_simulation_to_theory": compare_simulation_to_theory,
    }


def load_confirmed_comparison_obligations(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []

    payload = read_json(path)
    if not isinstance(payload, dict):
        raise SystemExit(f"Expected JSON object at {path}")

    obligations = payload.get("comparison_obligations", [])
    if not isinstance(obligations, list):
        return []

    sanitized: list[dict[str, Any]] = []
    for entry in obligations:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "").strip()
        if not name:
            continue
        if str(entry.get("confirmation_state") or "").strip() != "confirmed":
            continue

        required_lanes = [
            value
            for value in entry.get("required_lanes", [])
            if isinstance(value, str) and value in PRIMARY_COMPARISON_LANES
        ]
        optional_lanes = [
            value
            for value in entry.get("optional_lanes", [])
            if isinstance(value, str) and value in PRIMARY_COMPARISON_LANES and value not in required_lanes
        ]
        supporting_bases = [
            value
            for value in entry.get("supporting_bases", [])
            if isinstance(value, str) and value in SUPPORTING_BASES
        ]

        sanitized.append(
            {
                "name": name,
                "label": str(entry.get("label") or name),
                "result_kind": str(entry.get("result_kind") or "reported"),
                "importance_origin": str(entry.get("importance_origin") or "handout_required"),
                "confirmation_state": "confirmed",
                "required_lanes": required_lanes,
                "optional_lanes": optional_lanes,
                "supporting_bases": supporting_bases,
            }
        )

    return sanitized
