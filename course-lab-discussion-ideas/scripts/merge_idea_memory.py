#!/usr/bin/env python3
"""Merge retained discussion ideas into experiment-local permanent memory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import read_json, safe_label, write_json, write_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--memory-dir", required=True)
    parser.add_argument("--new-ideas-json", required=True)
    return parser


def stable_key(item: dict[str, object]) -> str:
    raw = str(item.get("idea_id") or "").strip()
    if raw:
        return raw
    return safe_label(str(item.get("title") or "idea"), default="idea")


def merge_string_lists(left: list[object], right: list[object]) -> list[str]:
    merged: list[str] = []
    for raw in [*left, *right]:
        text = str(raw).strip()
        if text and text not in merged:
            merged.append(text)
    return merged


def merge_item(existing: dict[str, object], new_item: dict[str, object]) -> dict[str, object]:
    merged = dict(existing)
    merged.update(new_item)
    merged["idea_id"] = stable_key(new_item if new_item.get("idea_id") else existing)
    merged["title"] = str(new_item.get("title") or existing.get("title") or merged["idea_id"])
    merged["reference_report_support"] = merge_string_lists(
        list(existing.get("reference_report_support") or []),
        list(new_item.get("reference_report_support") or []),
    )
    merged["memory_analogy_notes"] = merge_string_lists(
        list(existing.get("memory_analogy_notes") or []),
        list(new_item.get("memory_analogy_notes") or []),
    )

    old_summary = str(existing.get("outside_lookup_summary") or "").strip()
    new_summary = str(new_item.get("outside_lookup_summary") or "").strip()
    if old_summary and new_summary and old_summary != new_summary:
        merged["outside_lookup_summary"] = f"{old_summary} {new_summary}".strip()
    else:
        merged["outside_lookup_summary"] = new_summary or old_summary
    return merged


def merge_memory(existing: list[dict[str, object]], new_items: list[dict[str, object]]) -> list[dict[str, object]]:
    merged_by_key: dict[str, dict[str, object]] = {}
    ordered_keys: list[str] = []

    for item in existing:
        key = stable_key(item)
        if key not in merged_by_key:
            ordered_keys.append(key)
            merged_by_key[key] = dict(item)

    for item in new_items:
        key = stable_key(item)
        if key in merged_by_key:
            merged_by_key[key] = merge_item(merged_by_key[key], item)
        else:
            ordered_keys.append(key)
            merged_by_key[key] = dict(item)

    return [merged_by_key[key] for key in ordered_keys]


def render_idea_notes(ideas: list[dict[str, object]]) -> str:
    lines = ["# Idea Notes", ""]
    for item in ideas:
        lines.append(f"## {item.get('idea_id', 'idea')}")
        lines.append("")
        lines.append(f"- Title: {item.get('title', '')}")
        lines.append(f"- Reuse status: {item.get('reuse_status', '')}")
        support = ", ".join(str(part) for part in item.get("reference_report_support", []))
        lines.append(f"- Reference support: {support}")
        lines.append(f"- Outside lookup summary: {item.get('outside_lookup_summary', '')}")
        lines.append("")
    return "\n".join(lines) + "\n"


def merge_into_memory_dir(memory_dir: Path, new_payload: dict[str, object]) -> dict[str, object]:
    memory_dir.mkdir(parents=True, exist_ok=True)
    existing_path = memory_dir / "idea_memory.json"
    existing_payload = read_json(existing_path) if existing_path.exists() else {}
    existing_items = []
    if isinstance(existing_payload, dict) and isinstance(existing_payload.get("discussion_ideas"), list):
        existing_items = [item for item in existing_payload["discussion_ideas"] if isinstance(item, dict)]

    new_items = []
    if isinstance(new_payload.get("discussion_ideas"), list):
        new_items = [item for item in new_payload["discussion_ideas"] if isinstance(item, dict)]

    merged_items = merge_memory(existing_items, new_items)
    merged_payload = {"discussion_ideas": merged_items}
    write_json(existing_path, merged_payload)
    write_text(memory_dir / "idea_notes.md", render_idea_notes(merged_items))
    return merged_payload


def main() -> int:
    args = build_parser().parse_args()
    memory_dir = Path(args.memory_dir)
    new_ideas_path = Path(args.new_ideas_json)
    if not new_ideas_path.exists():
        raise SystemExit(f"new-ideas-json must exist: {new_ideas_path}")
    new_payload = read_json(new_ideas_path)
    if not isinstance(new_payload, dict):
        raise SystemExit(f"Expected JSON object at {new_ideas_path}")

    merged_payload = merge_into_memory_dir(memory_dir, new_payload)
    print(
        json.dumps(
            {"memory_dir": str(memory_dir), "idea_count": len(merged_payload["discussion_ideas"])},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
