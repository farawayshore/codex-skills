#!/usr/bin/env python3
"""Discover likely Modern Physics report inputs for a given experiment query."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import (
    DATA_ROOT,
    HANDOUT_ROOT,
    PIC_RESULT_ROOT,
    REFERENCE_ROOT,
    RESULTS_ROOT,
    SIGNATORY_ROOT,
    TEMPLATE_ROOT,
    ScoredPath,
    iter_files,
    normalize_for_match,
    score_text,
    summarize_result_dir,
    write_json,
)


PDF_SUFFIXES = {".pdf"}
DATA_SUFFIXES = {".csv", ".json", ".md", ".pdf", ".png", ".jpg", ".jpeg", ".txt", ".tsv", ".xls", ".xlsx"}
PIC_RESULT_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
TEMPLATE_SUFFIXES = {".tex"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}


def score_paths(query: str, paths: list[Path], *, extra_texts: dict[str, list[str]] | None = None) -> list[ScoredPath]:
    scored: list[ScoredPath] = []
    extra_texts = extra_texts or {}
    for path in paths:
        match_texts = [path.stem, path.name, str(path.parent)]
        match_texts.extend(extra_texts.get(str(path), []))
        score, details = score_text(query, match_texts)
        scored.append(ScoredPath(path=str(path), score=score, label=path.name, details=details))
    return sorted(scored, key=lambda item: (-item.score, item.label.lower()))


def top_or_all(scored: list[ScoredPath], max_results: int) -> list[dict[str, object]]:
    if not scored:
        return []
    if scored[0].score <= 0:
        return [item.to_dict() for item in scored[:max_results]]
    filtered = [item for item in scored if item.score > 0]
    return [item.to_dict() for item in filtered[:max_results]]


def template_paths(include_excluded: bool) -> tuple[list[Path], list[Path]]:
    allowed: list[Path] = []
    excluded: list[Path] = []
    for path in iter_files(TEMPLATE_ROOT, suffixes=TEMPLATE_SUFFIXES):
        lowered = {part.lower() for part in path.parts}
        if not include_excluded and "dont use" in lowered:
            excluded.append(path)
        else:
            allowed.append(path)
    return sorted(allowed), sorted(excluded)


def result_candidates(query: str, max_results: int) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for path in sorted(item for item in RESULTS_ROOT.iterdir() if item.is_dir()):
        summary = summarize_result_dir(path)
        score, details = score_text(query, summary["match_texts"])
        candidates.append(
            {
                "path": summary["path"],
                "label": summary["label"],
                "score": round(score, 3),
                "details": details,
                "tex_files": summary["tex_files"],
                "manifest_topic": summary["manifest_topic"],
                "manifest_path": summary["manifest_path"],
            }
        )
    candidates.sort(key=lambda item: (-float(item["score"]), item["label"].lower()))
    if not candidates:
        return []
    if candidates[0]["score"] <= 0:
        return candidates[:max_results]
    return [item for item in candidates if item["score"] > 0][:max_results]


def decoded_candidates(root: Path, query: str, max_results: int) -> list[dict[str, object]]:
    pdf_decoded_root = root / "pdf_decoded"
    json_paths = list(iter_files(pdf_decoded_root, suffixes={".json"}))
    return top_or_all(score_paths(query, json_paths), max_results)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", required=True, help="Experiment name or query string.")
    parser.add_argument("--max-results", type=int, default=8)
    parser.add_argument("--include-excluded-templates", action="store_true")
    parser.add_argument("--output-json", help="Optional manifest path.")
    args = parser.parse_args()

    handouts = list(iter_files(HANDOUT_ROOT, suffixes=PDF_SUFFIXES, exclude_parts={"pdf_decoded"}))
    references = list(iter_files(REFERENCE_ROOT, suffixes=PDF_SUFFIXES, exclude_parts={"pdf_decoded"}))
    data_files = list(iter_files(DATA_ROOT, suffixes=DATA_SUFFIXES))
    picture_result_files = list(iter_files(PIC_RESULT_ROOT, suffixes=PIC_RESULT_SUFFIXES)) if PIC_RESULT_ROOT.exists() else []
    signatory_files = list(iter_files(SIGNATORY_ROOT, suffixes=PDF_SUFFIXES | IMAGE_SUFFIXES)) if SIGNATORY_ROOT.exists() else []
    templates, excluded_templates = template_paths(args.include_excluded_templates)

    warnings: list[str] = []
    if not SIGNATORY_ROOT.exists():
        warnings.append(f"Missing signatory root: {SIGNATORY_ROOT}")
    if not data_files:
        warnings.append(f"No data files found under {DATA_ROOT}")
    if not PIC_RESULT_ROOT.exists():
        warnings.append(f"Missing picture-result root: {PIC_RESULT_ROOT}")
    if excluded_templates and not args.include_excluded_templates:
        warnings.append("Templates under directories named 'dont use' were excluded from default choices.")

    payload = {
        "experiment_query": args.experiment,
        "normalized_query": normalize_for_match(args.experiment),
        "roots": {
            "handout_root": str(HANDOUT_ROOT),
            "reference_root": str(REFERENCE_ROOT),
            "data_root": str(DATA_ROOT),
            "picture_result_root": str(PIC_RESULT_ROOT),
            "signatory_root": str(SIGNATORY_ROOT),
            "template_root": str(TEMPLATE_ROOT),
            "results_root": str(RESULTS_ROOT),
        },
        "handouts": top_or_all(score_paths(args.experiment, handouts), args.max_results),
        "handout_decoded_json": decoded_candidates(HANDOUT_ROOT, args.experiment, args.max_results),
        "reference_reports": top_or_all(score_paths(args.experiment, references), args.max_results),
        "reference_decoded_json": decoded_candidates(REFERENCE_ROOT, args.experiment, args.max_results),
        "data_files": top_or_all(score_paths(args.experiment, data_files), args.max_results),
        "picture_result_files": top_or_all(score_paths(args.experiment, picture_result_files), args.max_results),
        "signatory_files": top_or_all(score_paths(args.experiment, signatory_files), args.max_results),
        "templates": top_or_all(score_paths(args.experiment, templates), args.max_results),
        "excluded_templates": top_or_all(score_paths(args.experiment, excluded_templates), args.max_results),
        "result_dirs": result_candidates(args.experiment, args.max_results),
        "warnings": warnings,
    }

    output_text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output_json:
        write_json(Path(args.output_json), payload)
    print(output_text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
