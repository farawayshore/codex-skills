#!/usr/bin/env python3
"""Write plot manifests and unresolved notes for course-lab-plotting."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import ensure_directory, read_json, write_json


def write_plot_manifest(
    *,
    job: dict[str, object],
    status: str,
    annotations: list[dict[str, object]] | None = None,
    unresolved_reasons: list[str] | None = None,
    renderer: str | None = None,
) -> dict[str, object]:
    output_root = ensure_directory(Path(str(job["output_root"])).expanduser().resolve())
    manifest_path = Path(str(job.get("manifest_json") or output_root / "plot_manifest.json"))
    unresolved_path = Path(str(job.get("unresolved_markdown") or output_root / "plot_unresolved.md"))

    payload = {
        "status": status,
        "output_stem": job.get("output_stem"),
        "output_png": job.get("output_png"),
        "source_path": job.get("source_path"),
        "x_field": job.get("x_field"),
        "y_field": job.get("y_field"),
        "plot_type": job.get("plot_type"),
        "style_profile": job.get("style_profile"),
        "renderer": renderer,
        "annotations": annotations or [],
        "unresolved_reasons": unresolved_reasons or [],
    }
    write_json(manifest_path, payload)

    if status != "ok":
        lines = ["# Plot Unresolved", ""]
        for reason in unresolved_reasons or ["plot request could not be satisfied honestly"]:
            lines.append(f"- {reason}")
        unresolved_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write plot_manifest.json and optional unresolved notes.")
    parser.add_argument("--job-json", required=True, help="Path to plot_job.json.")
    parser.add_argument("--status", required=True, choices=["ok", "unresolved"], help="Final plot status.")
    parser.add_argument("--annotations-json", help="Path to a JSON array of annotation entries.")
    parser.add_argument("--reason", action="append", default=[], help="Unresolved reason. May be repeated.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    job = read_json(Path(args.job_json))
    if not isinstance(job, dict):
        raise ValueError("job JSON must contain one object")

    annotations: list[dict[str, object]] | None = None
    if args.annotations_json:
        loaded = read_json(Path(args.annotations_json))
        if isinstance(loaded, list):
            annotations = [item for item in loaded if isinstance(item, dict)]

    payload = write_plot_manifest(job=job, status=args.status, annotations=annotations, unresolved_reasons=args.reason)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
