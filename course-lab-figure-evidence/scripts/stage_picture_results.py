#!/usr/bin/env python3
"""Copy experiment picture-result files into a report workspace and emit a manifest."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

from common import safe_label, write_json


PICTURE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".pdf"}
SERIAL_SUFFIX_RE = re.compile(r"^(?P<base>.*?)(?:[\s_-]*|[\s_-]*[（(])(?P<serial>\d+)(?:[）)])?$")
CASE_ID_RE = re.compile(
    r"(?<![a-z0-9])case(?:[\s_-]+(?P<sep_id>[a-z0-9]+)|(?P<plain_digits>[0-9]+))(?=[^a-z0-9]|$)",
    re.IGNORECASE,
)
PREFIX_CASE_RE = re.compile(r"^\s*(\d+)(?:\D|$)")


def parse_serial_stem(stem: str) -> tuple[str | None, int | None, str | None]:
    match = SERIAL_SUFFIX_RE.match(stem.strip())
    if not match:
        return None, None, None
    base = (match.group("base") or "").strip(" _-()（）")
    serial_raw = match.group("serial")
    if not base or not serial_raw:
        return None, None, None
    normalized_base = re.sub(r"[\s_-]+", "", base).casefold()
    return base, int(serial_raw), normalized_base


def extract_case_ids_from_text(value: object) -> set[str]:
    text = str(value or "").strip()
    if not text:
        return set()

    matches: set[str] = set()
    for match in CASE_ID_RE.finditer(text):
        case_suffix = match.group("sep_id") or match.group("plain_digits") or ""
        if case_suffix:
            matches.add(f"case-{case_suffix.lower()}")
    basename = Path(text).name
    prefix = PREFIX_CASE_RE.match(basename)
    if prefix:
        matches.add(f"case-{prefix.group(1)}")
    return matches


def infer_evidence_role(*, group: str, stem: str) -> str:
    normalized_group = group.casefold()
    normalized_stem = stem.casefold()
    if "measurement_procedure" in normalized_group or "measuring" in normalized_stem:
        return "measurement_proof"
    return "observed"


def copy_entry(
    *,
    source_path: Path,
    output_dir: Path,
    group: str,
    target_parent_parts: list[str],
    evidence_role: str,
    case_ids: set[str] | None = None,
) -> dict[str, object]:
    safe_parts = [safe_label(part, default="group") for part in target_parent_parts]
    target_parent = output_dir.joinpath(*safe_parts)
    target_parent.mkdir(parents=True, exist_ok=True)
    target_name = f"{safe_label(source_path.stem, default='picture')}{source_path.suffix.lower()}"
    target_path = target_parent / target_name
    shutil.copy2(source_path, target_path)
    sequence_base, sequence_serial, normalized_sequence_base = parse_serial_stem(source_path.stem)
    inferred_case_ids = set(case_ids or set())
    inferred_case_ids.update(extract_case_ids_from_text(source_path.name))
    inferred_case_ids.update(extract_case_ids_from_text(group))

    return {
        "source_path": str(source_path),
        "copied_path": str(target_path),
        "relative_output_path": str(target_path.relative_to(output_dir)),
        "group": group,
        "stem": source_path.stem,
        "suffix": source_path.suffix.lower(),
        "sequence_base": sequence_base,
        "sequence_serial": sequence_serial,
        "sequence_base_normalized": normalized_sequence_base,
        "case_ids": sorted(inferred_case_ids),
        "evidence_role": evidence_role,
    }


def comparison_case_records(payload: object) -> list[dict[str, object]]:
    if isinstance(payload, dict):
        raw_cases = payload.get("comparison_cases")
        if isinstance(raw_cases, list):
            return [item for item in raw_cases if isinstance(item, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def build_sequence_groups(entries: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
    for entry in entries:
        serial = entry.get("sequence_serial")
        normalized_base = entry.get("sequence_base_normalized")
        if serial is None or not normalized_base:
            continue
        key = (str(entry.get("group") or ""), str(normalized_base))
        grouped.setdefault(key, []).append(entry)

    payload: list[dict[str, object]] = []
    for (group_name, normalized_base), group_entries in sorted(grouped.items()):
        serials = [int(entry["sequence_serial"]) for entry in group_entries if entry.get("sequence_serial") is not None]
        if len(group_entries) < 2 or len(set(serials)) != len(serials):
            continue
        sorted_entries = sorted(group_entries, key=lambda item: (int(item["sequence_serial"]), str(item["relative_output_path"])))
        payload.append(
            {
                "group": group_name,
                "sequence_base": sorted_entries[0]["sequence_base"],
                "sequence_base_normalized": normalized_base,
                "entries": [
                    {
                        "source_path": entry["source_path"],
                        "copied_path": entry["copied_path"],
                        "relative_output_path": entry["relative_output_path"],
                        "sequence_serial": entry["sequence_serial"],
                        "stem": entry["stem"],
                    }
                    for entry in sorted_entries
                ],
            }
        )
    return payload


def build_manifest(
    source_root: Path,
    output_dir: Path,
    *,
    comparison_cases_payload: object | None = None,
) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    output_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted(source_root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in PICTURE_SUFFIXES:
            continue

        relative_parent = path.parent.relative_to(source_root)
        group = "/".join(relative_parent.parts) if relative_parent.parts else ""

        entries.append(
            copy_entry(
                source_path=path,
                output_dir=output_dir,
                group=group,
                target_parent_parts=list(relative_parent.parts),
                evidence_role=infer_evidence_role(group=group, stem=path.stem),
            )
        )

    for raw_case in comparison_case_records(comparison_cases_payload):
        comparison_asset_text = str(raw_case.get("comparison_asset_path") or "").strip()
        if not comparison_asset_text:
            continue
        comparison_asset_path = Path(comparison_asset_text).expanduser()
        if not comparison_asset_path.is_file():
            continue

        case_ids = extract_case_ids_from_text(raw_case.get("case_id") or raw_case.get("title") or "")
        if not case_ids:
            case_ids = extract_case_ids_from_text(comparison_asset_text)
        if not case_ids:
            continue

        case_id = sorted(case_ids)[0]
        entries.append(
            copy_entry(
                source_path=comparison_asset_path,
                output_dir=output_dir,
                group=f"comparison-cases/{case_id}",
                target_parent_parts=["comparison-cases", case_id],
                evidence_role="comparison",
                case_ids={case_id},
            )
        )

    sequence_groups = build_sequence_groups(entries)
    return {
        "source_root": str(source_root),
        "output_dir": str(output_dir),
        "file_count": len(entries),
        "entries": entries,
        "sequence_group_count": len(sequence_groups),
        "sequence_groups": sequence_groups,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, help="Picture-result source directory.")
    parser.add_argument("--comparison-cases-json", help="Optional JSON file containing comparison_cases with comparison_asset_path values.")
    parser.add_argument("--output-dir", required=True, help="Directory to receive copied picture results.")
    parser.add_argument("--output-json", required=True, help="Manifest output path.")
    args = parser.parse_args()

    comparison_cases_payload: object | None = None
    if args.comparison_cases_json:
        comparison_cases_payload = json.loads(Path(args.comparison_cases_json).read_text(encoding="utf-8"))

    manifest = build_manifest(
        Path(args.source_root).resolve(),
        Path(args.output_dir).resolve(),
        comparison_cases_payload=comparison_cases_payload,
    )
    write_json(Path(args.output_json), manifest)
    print(json.dumps({"output_json": args.output_json, "file_count": manifest["file_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
