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


def build_manifest(source_root: Path, output_dir: Path) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    output_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted(source_root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in PICTURE_SUFFIXES:
            continue

        relative_parent = path.parent.relative_to(source_root)
        safe_parts = [safe_label(part, default="group") for part in relative_parent.parts]
        target_parent = output_dir.joinpath(*safe_parts)
        target_parent.mkdir(parents=True, exist_ok=True)
        target_name = f"{safe_label(path.stem, default='picture')}{path.suffix.lower()}"
        target_path = target_parent / target_name
        shutil.copy2(path, target_path)
        sequence_base, sequence_serial, normalized_sequence_base = parse_serial_stem(path.stem)

        entries.append(
            {
                "source_path": str(path),
                "copied_path": str(target_path),
                "relative_output_path": str(target_path.relative_to(output_dir)),
                "group": "/".join(relative_parent.parts) if relative_parent.parts else "",
                "stem": path.stem,
                "suffix": path.suffix.lower(),
                "sequence_base": sequence_base,
                "sequence_serial": sequence_serial,
                "sequence_base_normalized": normalized_sequence_base,
            }
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
    parser.add_argument("--output-dir", required=True, help="Directory to receive copied picture results.")
    parser.add_argument("--output-json", required=True, help="Manifest output path.")
    args = parser.parse_args()

    manifest = build_manifest(Path(args.source_root).resolve(), Path(args.output_dir).resolve())
    write_json(Path(args.output_json), manifest)
    print(json.dumps({"output_json": args.output_json, "file_count": manifest["file_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
