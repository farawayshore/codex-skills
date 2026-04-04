#!/usr/bin/env python3
"""Discover the required modeling cases for a batch run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from common import case_identity_key, load_json, safe_case_stem
from validate_modeling_config import validate_modeling_config


LX2_PATTERN = re.compile(
    r"^(?P<case_id>\d+)\.f=(?P<frequency>[0-9]+(?:\.[0-9]+)?)kHz,m=(?P<m>\d+),n=(?P<n>\d+)"
)


def parse_lx2_picture_result_filename(filename: str) -> dict | None:
    match = LX2_PATTERN.match(filename)
    if match is None:
        return None
    frequency_hz = float(match.group("frequency")) * 1000.0
    m_value = int(match.group("m"))
    n_value = int(match.group("n"))
    case_id = safe_case_stem(
        {
            "case_id": (
                f"case-{match.group('case_id')}-"
                f"f{match.group('frequency')}khz-m{m_value}-n{n_value}"
            )
        }
    )
    return {
        "case_id": case_id,
        "parameters": {
            "frequency_hz": frequency_hz,
            "m": m_value,
            "n": n_value,
        },
        "sources": ["picture_results"],
        "picture_result_file": filename,
        "handout_expectations": {"required": False, "checks": []},
    }


def _merge_case(existing: dict, incoming: dict) -> dict:
    merged = dict(existing)
    merged_sources = list(dict.fromkeys(existing.get("sources", []) + incoming.get("sources", [])))
    merged["sources"] = merged_sources
    if not merged.get("case_id") and incoming.get("case_id"):
        merged["case_id"] = incoming["case_id"]
    if "picture_result_file" not in merged and "picture_result_file" in incoming:
        merged["picture_result_file"] = incoming["picture_result_file"]
    if incoming.get("handout_expectations"):
        merged["handout_expectations"] = incoming["handout_expectations"]
    return merged


def discover_required_cases(config: dict) -> dict:
    required_by_key: dict[tuple, dict] = {}
    discovered_cases: list[dict] = []
    handout_only_cases: list[dict] = []

    batch_policy = config.get("batch_policy", {})
    discovery = config.get("discovery", {})

    if batch_policy.get("include_picture_result_cases", True) and discovery.get("enabled"):
        picture_dir = Path(discovery["picture_results_dir"])
        if picture_dir.exists():
            for path in sorted(picture_dir.iterdir()):
                if not path.is_file():
                    continue
                if discovery.get("parser") == "lx2_filename":
                    parsed = parse_lx2_picture_result_filename(path.name)
                else:
                    parsed = None
                if parsed is None:
                    continue
                key = case_identity_key(parsed["parameters"])
                required_by_key[key] = _merge_case(required_by_key.get(key, parsed), parsed)
                discovered_cases.append(parsed)

    if batch_policy.get("include_handout_only_cases", True):
        for case in config.get("handout_cases", []):
            case_copy = {
                "case_id": case.get("case_id") or safe_case_stem(case),
                "parameters": dict(case["parameters"]),
                "sources": ["handout"],
                "handout_expectations": case.get(
                    "handout_expectations",
                    {"required": False, "checks": []},
                ),
            }
            key = case_identity_key(case_copy["parameters"])
            existing = required_by_key.get(key)
            if existing is None:
                required_by_key[key] = case_copy
                handout_only_cases.append(case_copy)
            else:
                required_by_key[key] = _merge_case(existing, case_copy)

    required_cases = sorted(
        required_by_key.values(),
        key=lambda case: (
            case["parameters"].get("frequency_hz", 0.0),
            case["parameters"].get("m", 0),
            case["parameters"].get("n", 0),
        ),
    )
    return {
        "required_cases": required_cases,
        "discovered_cases": discovered_cases,
        "handout_only_cases": handout_only_cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover required modeling cases for a batch run.")
    parser.add_argument("--config", required=True, help="Path to run_config.json")
    args = parser.parse_args()
    config = validate_modeling_config(load_json(args.config))
    result = discover_required_cases(config)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
