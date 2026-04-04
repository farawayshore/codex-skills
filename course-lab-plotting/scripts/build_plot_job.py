#!/usr/bin/env python3
"""Build one standalone plot-job contract for course lab plotting."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import build_plottings_root, ensure_directory, parameter_identity_stem, safe_label, write_json


def build_plot_job(
    *,
    source_path: str | Path,
    x_field: str,
    y_field: str,
    output_root: str | Path | None = None,
    matched_experiment_path: str | None = None,
    plot_id: str | None = None,
    parameter_values: dict[str, object] | None = None,
    plot_type: str = "scatter-plus-line",
    annotations: list[str] | None = None,
    style_profile: str = "scientific-default",
    x_unit: str | None = None,
    y_unit: str | None = None,
    title: str | None = None,
) -> dict[str, object]:
    if output_root is None:
        if not matched_experiment_path:
            raise ValueError("output_root or matched_experiment_path is required")
        output_root_path = build_plottings_root(matched_experiment_path)
    else:
        output_root_path = Path(output_root).expanduser().resolve()

    ensure_directory(output_root_path)

    stem = safe_label(plot_id, default="plot") if plot_id else parameter_identity_stem(parameter_values)
    requested_annotations = list(annotations or ["max", "min", "zero"])

    return {
        "source_path": str(Path(source_path).expanduser().resolve()),
        "x_field": x_field,
        "y_field": y_field,
        "x_unit": x_unit,
        "y_unit": y_unit,
        "plot_type": plot_type,
        "plot_id": plot_id,
        "parameter_values": parameter_values or {},
        "style_profile": style_profile,
        "requested_annotations": requested_annotations,
        "title": title,
        "output_root": str(output_root_path),
        "output_stem": stem,
        "output_png": str(output_root_path / f"{stem}.png"),
        "job_json": str(output_root_path / "plot_job.json"),
        "manifest_json": str(output_root_path / "plot_manifest.json"),
        "unresolved_markdown": str(output_root_path / "plot_unresolved.md"),
    }


def parse_param_assignments(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in values:
        if "=" not in item:
            raise ValueError(f"parameter assignment must look like key=value: {item}")
        key, raw_value = item.split("=", 1)
        result[key.strip()] = raw_value.strip()
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a standalone plot_job.json for course-lab-plotting.")
    parser.add_argument("--source", required=True, help="Path to the validated numeric source CSV.")
    parser.add_argument("--x-field", required=True, help="Column name for the x axis.")
    parser.add_argument("--y-field", required=True, help="Column name for the y axis.")
    parser.add_argument("--output-root", help="Output directory, usually .../experiment_pic_results/<matched>/plottings.")
    parser.add_argument("--matched-experiment-path", help="Matched experiment path used to derive the permanent plottings folder.")
    parser.add_argument("--plot-id", help="Stable serial identity such as plot-01.")
    parser.add_argument("--param", action="append", default=[], help="Fallback parameter identity in key=value form. May be repeated.")
    parser.add_argument("--plot-type", default="scatter-plus-line", help="Plot type such as line, scatter, or scatter-plus-line.")
    parser.add_argument("--annotation", action="append", default=[], help="Requested annotation kind such as max, min, or zero.")
    parser.add_argument("--style-profile", default="scientific-default", help="Local style profile name.")
    parser.add_argument("--x-unit", help="Unit label for the x axis.")
    parser.add_argument("--y-unit", help="Unit label for the y axis.")
    parser.add_argument("--title", help="Optional plot title.")
    parser.add_argument("--output-json", help="Path for the saved plot job JSON. Defaults to <output-root>/plot_job.json.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    parameter_values = parse_param_assignments(args.param)
    output_root = args.output_root
    job = build_plot_job(
        source_path=args.source,
        x_field=args.x_field,
        y_field=args.y_field,
        output_root=output_root,
        matched_experiment_path=args.matched_experiment_path,
        plot_id=args.plot_id,
        parameter_values=parameter_values,
        plot_type=args.plot_type,
        annotations=args.annotation or None,
        style_profile=args.style_profile,
        x_unit=args.x_unit,
        y_unit=args.y_unit,
        title=args.title,
    )
    output_json = Path(args.output_json).expanduser().resolve() if args.output_json else Path(str(job["job_json"]))
    write_json(output_json, job)
    print(output_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
