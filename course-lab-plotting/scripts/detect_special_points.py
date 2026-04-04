#!/usr/bin/env python3
"""Detect honest special points for lab plots."""

from __future__ import annotations

import argparse
import json
from typing import Iterable


ORDER = {"max": 0, "min": 1, "zero": 2}


def _first_index_of(values: list[float], target: float) -> int:
    for index, value in enumerate(values):
        if value == target:
            return index
    return 0


def _detect_zero_point(x_values: list[float], y_values: list[float]) -> dict[str, object] | None:
    for index, value in enumerate(y_values):
        if value == 0:
            return {
                "kind": "zero",
                "label": "zero",
                "x": float(x_values[index]),
                "y": 0.0,
                "index": index,
            }

    for index in range(len(y_values) - 1):
        left = y_values[index]
        right = y_values[index + 1]
        if left == right:
            continue
        if left * right < 0:
            x_left = x_values[index]
            x_right = x_values[index + 1]
            x_zero = x_left + (0.0 - left) * (x_right - x_left) / (right - left)
            return {
                "kind": "zero",
                "label": "zero",
                "x": float(x_zero),
                "y": 0.0,
                "index": index,
            }
    return None


def detect_special_points(
    *,
    x_values: Iterable[float],
    y_values: Iterable[float],
    requested_kinds: list[str] | None = None,
) -> list[dict[str, object]]:
    x_list = [float(value) for value in x_values]
    y_list = [float(value) for value in y_values]
    if len(x_list) != len(y_list):
        raise ValueError("x_values and y_values must have the same length")
    if not x_list:
        return []

    requested = set(requested_kinds or ["max", "min", "zero"])
    points: list[dict[str, object]] = []

    if "max" in requested:
        maximum = max(y_list)
        index = _first_index_of(y_list, maximum)
        points.append(
            {
                "kind": "max",
                "label": "max",
                "x": float(x_list[index]),
                "y": float(y_list[index]),
                "index": index,
            }
        )

    if "min" in requested:
        minimum = min(y_list)
        index = _first_index_of(y_list, minimum)
        points.append(
            {
                "kind": "min",
                "label": "min",
                "x": float(x_list[index]),
                "y": float(y_list[index]),
                "index": index,
            }
        )

    if "zero" in requested:
        zero_point = _detect_zero_point(x_list, y_list)
        if zero_point is not None:
            points.append(zero_point)

    return sorted(points, key=lambda item: ORDER.get(str(item.get("kind")), 99))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Detect max, min, and zero points for a numeric series.")
    parser.add_argument("--x", action="append", type=float, default=[], help="One x value. May be repeated.")
    parser.add_argument("--y", action="append", type=float, default=[], help="One y value. May be repeated.")
    parser.add_argument("--kind", action="append", default=[], help="Requested kind such as max, min, or zero.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    points = detect_special_points(x_values=args.x, y_values=args.y, requested_kinds=args.kind or None)
    print(json.dumps(points, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
