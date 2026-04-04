#!/usr/bin/env python3
"""Render standalone lab plots with honest annotations."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
VENDOR_DIR = SCRIPT_DIR.parent / "vendor"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

import matplotlib

matplotlib.use("Agg")

from matplotlib import pyplot as plt

from common import ensure_directory, parse_numeric_column, read_csv_rows, read_json
from detect_special_points import detect_special_points
from write_plot_manifest import write_plot_manifest


RENDERER_NAME = "matplotlib"

STYLE_PROFILES = {
    "scientific-default": {
        "background": "#f8fbff",
        "grid": "#d9e4f2",
        "axes": "#1f2937",
        "series": "#2563eb",
        "series_fill": "#bfdbfe",
        "text": "#111827",
        "max": "#dc2626",
        "min": "#7c3aed",
        "zero": "#059669",
    }
}


def _padded_bounds(values: list[float]) -> tuple[float, float]:
    minimum = min(values)
    maximum = max(values)
    if minimum == maximum:
        padding = 1.0 if minimum == 0 else abs(minimum) * 0.1
        return minimum - padding, maximum + padding
    padding = (maximum - minimum) * 0.08
    return minimum - padding, maximum + padding


def _label_with_unit(name: str, unit: object | None) -> str:
    if unit:
        return f"{name} ({unit})"
    return name


def render_plot_job(job: dict[str, object]) -> dict[str, object]:
    output_root = ensure_directory(Path(str(job["output_root"])).expanduser().resolve())
    source_path = Path(str(job["source_path"])).expanduser().resolve()
    x_field = str(job["x_field"])
    y_field = str(job["y_field"])
    style_name = str(job.get("style_profile") or "scientific-default")
    style = STYLE_PROFILES.get(style_name, STYLE_PROFILES["scientific-default"])

    try:
        rows = read_csv_rows(source_path)
    except FileNotFoundError:
        return write_plot_manifest(
            job=job,
            status="unresolved",
            unresolved_reasons=[f"missing source file: {source_path}"],
            renderer=RENDERER_NAME,
        )

    if not rows:
        return write_plot_manifest(
            job=job,
            status="unresolved",
            unresolved_reasons=["numeric source contains no data rows"],
            renderer=RENDERER_NAME,
        )

    available_fields = set(rows[0].keys())
    missing_fields = [field for field in (x_field, y_field) if field not in available_fields]
    if missing_fields:
        reason = f"missing required column(s): {', '.join(missing_fields)}"
        return write_plot_manifest(job=job, status="unresolved", unresolved_reasons=[reason], renderer=RENDERER_NAME)

    try:
        x_values = parse_numeric_column(rows, x_field)
        y_values = parse_numeric_column(rows, y_field)
    except (KeyError, ValueError) as exc:
        return write_plot_manifest(job=job, status="unresolved", unresolved_reasons=[str(exc)], renderer=RENDERER_NAME)

    annotations = detect_special_points(
        x_values=x_values,
        y_values=y_values,
        requested_kinds=list(job.get("requested_annotations") or ["max", "min", "zero"]),
    )

    plot_type = str(job.get("plot_type") or "scatter-plus-line")
    title = str(job.get("title") or f"{y_field} vs {x_field}")
    x_label = _label_with_unit(x_field, job.get("x_unit"))
    y_label = _label_with_unit(y_field, job.get("y_unit"))

    output_png = Path(str(job["output_png"])).expanduser().resolve()
    output_png.parent.mkdir(parents=True, exist_ok=True)
    x_bounds = _padded_bounds(x_values)
    y_bounds = _padded_bounds(y_values)

    plt.style.use("default")
    figure, axis = plt.subplots(figsize=(12, 8), dpi=120)
    figure.patch.set_facecolor(style["background"])
    axis.set_facecolor(style["background"])
    axis.grid(True, color=style["grid"], linewidth=1.0)
    axis.set_axisbelow(True)
    for spine in axis.spines.values():
        spine.set_color(style["axes"])
        spine.set_linewidth(1.2)
    axis.tick_params(colors=style["text"], labelsize=11)
    axis.set_xlim(*x_bounds)
    axis.set_ylim(*y_bounds)
    axis.set_title(title, color=style["text"], fontsize=16, pad=14)
    axis.set_xlabel(x_label, color=style["text"], fontsize=12)
    axis.set_ylabel(y_label, color=style["text"], fontsize=12)

    line_label = job.get("plot_id") or job.get("output_stem") or "series"
    if plot_type in {"line", "scatter-plus-line", "comparison"} and len(x_values) > 1:
        axis.plot(x_values, y_values, color=style["series"], linewidth=2.6, label=str(line_label))

    if plot_type in {"scatter", "scatter-plus-line", "line", "comparison"}:
        axis.scatter(
            x_values,
            y_values,
            s=52,
            color=style["series_fill"],
            edgecolors=style["series"],
            linewidths=1.1,
            zorder=3,
        )

    for annotation in annotations:
        color = style.get(str(annotation["kind"]), style["axes"])
        axis.scatter(
            [float(annotation["x"])],
            [float(annotation["y"])],
            s=95,
            color=color,
            edgecolors="white",
            linewidths=0.9,
            zorder=4,
        )
        axis.annotate(
            str(annotation["label"]),
            (float(annotation["x"]), float(annotation["y"])),
            xytext=(8, 8),
            textcoords="offset points",
            color=color,
            fontsize=10,
            weight="bold",
        )

    if plot_type in {"line", "scatter-plus-line", "comparison"}:
        axis.legend(frameon=False, fontsize=10, loc="best")

    figure.tight_layout()
    figure.savefig(output_png, format="png", facecolor=figure.get_facecolor())
    plt.close(figure)

    return write_plot_manifest(job=job, status="ok", annotations=annotations, renderer=RENDERER_NAME)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render a standalone scientific plot from plot_job.json.")
    parser.add_argument("--job-json", required=True, help="Path to plot_job.json.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    loaded = read_json(Path(args.job_json))
    if not isinstance(loaded, dict):
        raise ValueError("plot job JSON must contain one object")
    result = render_plot_job(loaded)
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
