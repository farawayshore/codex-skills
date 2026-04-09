#!/usr/bin/env python3
"""Discover likely course lab-report inputs for a given experiment query."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from common import (
    DATA_ROOT,
    EXPERIMENT_SIMULATION_ROOT,
    HANDOUT_LIBRARY_ROOT,
    PIC_RESULT_ROOT,
    REFERENCE_LIBRARY_ROOT,
    RESULTS_ROOT,
    SIGNATORY_ROOT,
    TEMPLATE_ROOT,
    ScoredPath,
    expand_query_variants,
    iter_files,
    match_tokens,
    normalize_for_match,
    path_match_texts,
    score_query_variants,
    summarize_result_dir,
    write_json,
)


PDF_SUFFIXES = {".pdf"}
DATA_SUFFIXES = {".csv", ".json", ".md", ".pdf", ".png", ".jpg", ".jpeg", ".txt", ".tsv", ".xls", ".xlsx"}
PIC_RESULT_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
TEMPLATE_SUFFIXES = {".tex"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}
DATA_TABLE_SUFFIXES = {".csv", ".tsv", ".xls", ".xlsx"}
DATA_SCAN_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
SIMULATION_FILE_SUFFIXES = {".py", ".wl", ".m", ".mlx", ".ipynb"}
SIMULATION_HINTS = ("simulation", "simulations", "simulator", "mathematica", "matlab", "simulink", "wolfram")
REFERENCE_PROCEDURE_SECTION_CANDIDATES = [
    "Experiment Steps",
    "Experimental Procedure",
    "Experiment Procedure",
    "Procedure",
    "Experiment Results",
    "实验步骤",
    "实验过程",
    "实验方法",
    "实验结果",
]


def parent_dirs_for_files(files: list[Path], root: Path) -> list[Path]:
    candidates: set[Path] = set()
    resolved_root = root.resolve()
    for file_path in files:
        current = file_path.parent.resolve()
        while current != resolved_root and resolved_root in current.parents:
            candidates.add(current)
            current = current.parent
    return sorted(candidates)


def score_paths(
    query: str,
    paths: list[Path],
    *,
    library_root: Path | None = None,
    extra_texts: dict[str, list[str]] | None = None,
) -> list[ScoredPath]:
    scored: list[ScoredPath] = []
    extra_texts = extra_texts or {}
    query_variants = expand_query_variants(query)
    for path in paths:
        primary_texts = [path.stem, path.name]
        primary_texts.extend(extra_texts.get(str(path), []))

        context_texts: list[str] = []
        if library_root is not None:
            try:
                relative = path.resolve().relative_to(library_root.resolve())
            except Exception:
                relative = None
            if relative is not None:
                context_texts.append(str(relative))
                if len(relative.parts) > 1:
                    trimmed_parent = Path(*relative.parts[1:]).parent
                    if str(trimmed_parent) != ".":
                        context_texts.append(str(trimmed_parent))
        else:
            context_texts.append(str(path.parent))

        primary_score, primary_details = score_query_variants(query_variants, primary_texts)
        context_score, _ = score_query_variants(query_variants, context_texts)
        score = primary_score + (context_score * 0.2)
        details = list(primary_details)
        if context_score > 0:
            details.append(f"context-boost:{round(context_score * 0.2, 3)}")
        scored.append(ScoredPath(path=str(path), score=score, label=path.name, details=details))
    return sorted(scored, key=lambda item: (-item.score, item.label.lower()))


def top_or_all(scored: list[ScoredPath], max_results: int) -> list[dict[str, object]]:
    if not scored:
        return []
    if scored[0].score <= 0:
        return [item.to_dict() for item in scored[:max_results]]
    filtered = [item for item in scored if item.score > 0]
    return [item.to_dict() for item in filtered[:max_results]]


def expected_reference_markdown_path(pdf_path: Path) -> Path:
    return pdf_path.parent / "pdf_markdown" / pdf_path.stem / f"{pdf_path.stem}.md"


def expected_reference_json_path(pdf_path: Path) -> Path:
    return pdf_path.parent / "pdf_decoded" / pdf_path.stem / f"{pdf_path.stem}.json"


def parse_detail_value(detail: str, prefix: str) -> str | None:
    if not detail.startswith(prefix):
        return None
    return detail.split(":", 1)[1]


def is_substantive_reference_match(item: ScoredPath) -> bool:
    detail_set = set(item.details)
    return (
        "exact-match" in detail_set
        or "contains-query" in detail_set
        or any(detail.startswith("token-overlap:") for detail in detail_set)
    )


def same_reference_cluster(scored: list[ScoredPath]) -> list[ScoredPath]:
    strong = [item for item in scored if is_substantive_reference_match(item)]
    if not strong:
        return []

    best = strong[0]
    best_label = normalize_for_match(best.label)
    best_tokens = set(match_tokens(best.label))
    clustered: list[ScoredPath] = []
    for item in strong:
        item_label = normalize_for_match(item.label)
        item_tokens = set(match_tokens(item.label))
        shared_tokens = best_tokens & item_tokens
        if shared_tokens or best_label in item_label or item_label in best_label:
            clustered.append(item)
    return clustered


def reference_selection_payload(query: str) -> dict[str, object]:
    references = list(iter_files(REFERENCE_LIBRARY_ROOT, suffixes=PDF_SUFFIXES, exclude_parts={"pdf_decoded", "pdf_markdown"}))
    scored = score_paths(query, references, library_root=REFERENCE_LIBRARY_ROOT)
    strong = same_reference_cluster(scored)
    if strong:
        selected = []
        for item in strong:
            pdf_path = Path(item.path)
            markdown_path = expected_reference_markdown_path(pdf_path)
            json_path = expected_reference_json_path(pdf_path)
            selected.append(
                {
                    "pdf_path": item.path,
                    "experiment_match_label": item.label,
                    "match_score": round(item.score, 3),
                    "selection_reason": item.details,
                    "expected_decoded_markdown_path": str(markdown_path),
                    "expected_decoded_json_path": str(json_path),
                    "current_decoded_markdown_exists": markdown_path.exists(),
                    "current_decoded_json_exists": json_path.exists(),
                    "procedure_section_candidates": REFERENCE_PROCEDURE_SECTION_CANDIDATES,
                }
            )
        return {
            "reference_selection_status": "selected",
            "selected_reference_reports": selected,
        }
    if any(item.score > 0 for item in scored):
        return {
            "reference_selection_status": "ambiguous",
            "selected_reference_reports": [],
        }
    return {
        "reference_selection_status": "none_found",
        "selected_reference_reports": [],
    }


def is_substantive_simulation_match(item: ScoredPath) -> bool:
    if item.score <= 0:
        return False

    ngram_overlap = 0
    context_boost = 0.0
    ratio = 0.0
    for detail in item.details:
        if detail in {"exact-match", "contains-query", "query-contains-candidate"}:
            return True
        if detail.startswith("token-overlap:"):
            return True

        ngram_value = parse_detail_value(detail, "ngram-overlap:")
        if ngram_value is not None:
            try:
                ngram_overlap = max(ngram_overlap, int(ngram_value))
            except ValueError:
                pass

        context_value = parse_detail_value(detail, "context-boost:")
        if context_value is not None:
            try:
                context_boost = max(context_boost, float(context_value))
            except ValueError:
                pass

        ratio_value = parse_detail_value(detail, "ratio:")
        if ratio_value is not None:
            try:
                ratio = max(ratio, float(ratio_value))
            except ValueError:
                pass

    if context_boost >= 18.0:
        return True
    if ngram_overlap >= 6:
        return True
    if ngram_overlap >= 3 and ratio >= 0.55:
        return True
    return False


def substantive_or_not_exist(scored: list[ScoredPath], max_results: int) -> list[dict[str, object]] | str:
    filtered = [item for item in scored if is_substantive_simulation_match(item)]
    if not filtered:
        return "not exist"
    return [item.to_dict() for item in filtered[:max_results]]


def sort_paths(paths: list[Path]) -> list[Path]:
    return sorted(paths, key=lambda path: str(path).lower())


def humanize_template_label(path: Path, template_kind: str) -> str:
    raw_name = path.stem if template_kind == "single_tex" else path.name
    label = raw_name.replace("_", " ").replace("-", " ")
    label = re.sub(r"\s+", " ", label).strip()
    label = re.sub(r"(?<!\s)\(", " (", label)
    return label or raw_name


def template_candidate(
    *,
    template_language: str,
    template_kind: str,
    template_root: Path,
    template_entry: Path,
) -> dict[str, object]:
    label_source = template_entry if template_kind == "single_tex" else template_root
    return {
        "path": str(template_entry),
        "score": 0.0,
        "label": humanize_template_label(label_source, template_kind),
        "details": [],
        "template_language": template_language,
        "template_kind": template_kind,
        "template_root": str(template_root),
        "template_entry": str(template_entry),
    }


def template_candidates_in_container(container_root: Path, template_language: str) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    if not container_root.exists():
        return candidates

    for path in sort_paths([item for item in container_root.iterdir()]):
        if path.is_file() and path.suffix.lower() in TEMPLATE_SUFFIXES:
            candidates.append(
                template_candidate(
                    template_language=template_language,
                    template_kind="single_tex",
                    template_root=path,
                    template_entry=path,
                )
            )
            continue

        if path.is_dir():
            entry = path / "main.tex"
            if entry.is_file():
                candidates.append(
                    template_candidate(
                        template_language=template_language,
                        template_kind="bundle",
                        template_root=path,
                        template_entry=entry,
                    )
                )
    return candidates


def template_languages() -> list[Path]:
    if not TEMPLATE_ROOT.exists():
        return []
    return sort_paths([path for path in TEMPLATE_ROOT.iterdir() if path.is_dir()])


def template_groups(template_language_requested: str | None = None) -> tuple[dict[str, list[dict[str, object]]], dict[str, list[dict[str, object]]]]:
    requested_language = normalize_for_match(template_language_requested) if template_language_requested else None
    grouped_templates: dict[str, list[dict[str, object]]] = {}
    grouped_excluded: dict[str, list[dict[str, object]]] = {}

    for language_root in template_languages():
        template_language = normalize_for_match(language_root.name)
        if requested_language and template_language != requested_language:
            continue

        grouped_templates[template_language] = template_candidates_in_container(language_root, template_language)

        excluded_candidates: list[dict[str, object]] = []
        for excluded_root in sort_paths([path for path in language_root.rglob("*") if path.is_dir() and path.name == "dont use"]):
            excluded_candidates.extend(template_candidates_in_container(excluded_root, template_language))
        grouped_excluded[template_language] = excluded_candidates

    if requested_language and requested_language not in grouped_templates:
        grouped_templates[requested_language] = []
        grouped_excluded[requested_language] = []

    return grouped_templates, grouped_excluded


def all_paths(paths: list[Path]) -> list[dict[str, object]]:
    return [ScoredPath(path=str(path), score=0.0, label=path.name, details=[]).to_dict() for path in sorted(paths)]


def ancestor_chain_within_root(path: Path, root: Path) -> list[Path]:
    resolved_root = root.resolve()
    ancestors: list[Path] = []
    current = path.parent.resolve()
    while current != resolved_root and resolved_root in current.parents:
        ancestors.append(current)
        current = current.parent
    return list(reversed(ancestors))


def best_data_group_root(path: Path, query: str) -> tuple[Path | None, float, list[str]]:
    best_root: Path | None = None
    best_score = 0.0
    best_details: list[str] = []
    strong_match_root: Path | None = None
    strong_match_score = 0.0
    strong_match_details: list[str] = []
    query_variants = expand_query_variants(query)

    for ancestor in ancestor_chain_within_root(path, DATA_ROOT):
        score, details = score_query_variants(query_variants, path_match_texts(ancestor, library_root=DATA_ROOT))
        if score > best_score:
            best_root = ancestor
            best_score = score
            best_details = details

        detail_set = set(details)
        has_strong_signal = any(
            detail == "exact-match"
            or detail == "contains-query"
            or detail.startswith("token-overlap:")
            for detail in detail_set
        )
        if has_strong_signal and (strong_match_root is None or score > strong_match_score):
            strong_match_root = ancestor
            strong_match_score = score
            strong_match_details = details

    if strong_match_root is not None:
        return strong_match_root, strong_match_score, strong_match_details
    return best_root, best_score, best_details


def classify_data_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in DATA_TABLE_SUFFIXES:
        return "table"
    if suffix in DATA_SCAN_SUFFIXES:
        return "scan"
    return "other"


def data_candidates(query: str, max_results: int) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    data_files = list(iter_files(DATA_ROOT, suffixes=DATA_SUFFIXES))
    scored_items = score_paths(query, data_files, library_root=DATA_ROOT)
    scored_by_path = {item.path: item for item in scored_items}

    grouped_paths: dict[Path, list[Path]] = {}
    group_scores: dict[Path, float] = {}
    group_details: dict[Path, list[str]] = {}
    for item in scored_items:
        if item.score <= 0:
            continue
        group_root, group_score, details = best_data_group_root(Path(item.path), query)
        if group_root is None or group_score <= 0:
            continue
        grouped_paths.setdefault(group_root, []).append(Path(item.path))
        if group_score > group_scores.get(group_root, 0.0):
            group_scores[group_root] = group_score
            group_details[group_root] = details

    data_groups: list[dict[str, object]] = []
    ranked_group_roots = sorted(grouped_paths, key=lambda path: (-group_scores[path], str(path).lower()))
    if ranked_group_roots:
        best_group_score = group_scores[ranked_group_roots[0]]
        if best_group_score >= 80:
            ranked_group_roots = [
                path for path in ranked_group_roots if group_scores[path] >= (best_group_score * 0.6)
            ]
    for group_root in ranked_group_roots:
        files = sorted(
            grouped_paths[group_root],
            key=lambda path: (
                {"table": 0, "scan": 1, "other": 2}[classify_data_file(path)],
                -scored_by_path[str(path)].score,
                path.name.lower(),
            ),
        )
        group_payload = {
            "path": str(group_root),
            "score": round(group_scores[group_root], 3),
            "label": group_root.name,
            "details": group_details[group_root],
            "csv_files": [],
            "scan_files": [],
            "other_files": [],
        }
        for file_path in files:
            item = scored_by_path[str(file_path)].to_dict()
            kind = classify_data_file(file_path)
            if kind == "table":
                group_payload["csv_files"].append(item)
            elif kind == "scan":
                group_payload["scan_files"].append(item)
            else:
                group_payload["other_files"].append(item)
        data_groups.append(group_payload)

    if not data_groups:
        return top_or_all(scored_items, max_results), []

    flattened: list[dict[str, object]] = []
    seen_paths: set[str] = set()
    for group in data_groups:
        for key in ("csv_files", "scan_files", "other_files"):
            for item in group[key]:
                item_path = str(item["path"])
                if item_path in seen_paths:
                    continue
                seen_paths.add(item_path)
                flattened.append(item)
    return flattened, data_groups


def discovery_query(course: str | None, experiment: str) -> str:
    if not course:
        return experiment
    return f"{course} {experiment}"


def result_candidates(query: str, max_results: int) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    query_variants = expand_query_variants(query)
    for path in sorted(item for item in RESULTS_ROOT.iterdir() if item.is_dir()):
        summary = summarize_result_dir(path)
        score, details = score_query_variants(query_variants, summary["match_texts"])
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
    json_paths = [
        path for path in iter_files(root, suffixes={".json"}) if "pdf_decoded" in {part.lower() for part in path.parts}
    ]
    return top_or_all(score_paths(query, json_paths, library_root=root), max_results)


def picture_result_dir_candidates(query: str, max_results: int) -> list[dict[str, object]]:
    if not PIC_RESULT_ROOT.exists():
        return []
    picture_result_files = list(iter_files(PIC_RESULT_ROOT, suffixes=PIC_RESULT_SUFFIXES))
    candidate_dirs = parent_dirs_for_files(picture_result_files, PIC_RESULT_ROOT)
    return top_or_all(score_paths(query, candidate_dirs, library_root=PIC_RESULT_ROOT), max_results)


def is_simulation_file(path: Path) -> bool:
    return (
        path.is_file()
        and path.suffix.lower() in SIMULATION_FILE_SUFFIXES
        and path_contains_simulation_hint(path)
    )


def path_contains_simulation_hint(path: Path) -> bool:
    normalized_text = normalize_for_match(str(path))
    return any(hint in normalized_text for hint in SIMULATION_HINTS)


def simulation_file_candidates(query: str, max_results: int) -> list[dict[str, object]] | str:
    roots = [RESULTS_ROOT, EXPERIMENT_SIMULATION_ROOT, DATA_ROOT]
    files: list[Path] = []
    for root in roots:
        files.extend(path for path in iter_files(root) if is_simulation_file(path))
    return substantive_or_not_exist(score_paths(query, sorted(files)), max_results)


def simulation_dir_candidates(query: str, max_results: int) -> list[dict[str, object]] | str:
    candidate_dirs: set[Path] = set()

    if RESULTS_ROOT.exists():
        for path in RESULTS_ROOT.iterdir():
            if not path.is_dir():
                continue
            if path_contains_simulation_hint(path):
                candidate_dirs.add(path)

    if EXPERIMENT_SIMULATION_ROOT.exists():
        for path in EXPERIMENT_SIMULATION_ROOT.rglob("*"):
            if not path.is_dir():
                continue
            if path == EXPERIMENT_SIMULATION_ROOT:
                continue
            if path_contains_simulation_hint(path) or any(is_simulation_file(child) for child in path.rglob("*")):
                candidate_dirs.add(path)

    return substantive_or_not_exist(score_paths(query, sorted(candidate_dirs)), max_results)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--course", help="Course name or course-family hint.")
    parser.add_argument("--experiment", required=True, help="Experiment name or query string.")
    parser.add_argument("--template-language", help="Optional template language filter such as english or chinese.")
    parser.add_argument("--max-results", type=int, default=8)
    parser.add_argument("--include-excluded-templates", action="store_true")
    parser.add_argument("--output-json", help="Optional manifest path.")
    args = parser.parse_args()

    query_text = discovery_query(args.course, args.experiment)

    handouts = list(iter_files(HANDOUT_LIBRARY_ROOT, suffixes=PDF_SUFFIXES, exclude_parts={"pdf_decoded"}))
    references = list(iter_files(REFERENCE_LIBRARY_ROOT, suffixes=PDF_SUFFIXES, exclude_parts={"pdf_decoded"}))
    data_files = list(iter_files(DATA_ROOT, suffixes=DATA_SUFFIXES))
    ranked_data_files, data_groups = data_candidates(args.experiment, args.max_results)
    picture_result_files = list(iter_files(PIC_RESULT_ROOT, suffixes=PIC_RESULT_SUFFIXES)) if PIC_RESULT_ROOT.exists() else []
    signatory_files = list(iter_files(SIGNATORY_ROOT, suffixes=PDF_SUFFIXES | IMAGE_SUFFIXES)) if SIGNATORY_ROOT.exists() else []
    templates, excluded_templates = template_groups(args.template_language)
    reference_selection = reference_selection_payload(query_text)

    warnings: list[str] = []
    if not SIGNATORY_ROOT.exists():
        warnings.append(f"Missing signatory root: {SIGNATORY_ROOT}")
    if not data_files:
        warnings.append(f"No data files found under {DATA_ROOT}")
    if not PIC_RESULT_ROOT.exists():
        warnings.append(f"Missing picture-result root: {PIC_RESULT_ROOT}")
    if any(excluded_templates.values()):
        warnings.append("Templates under directories named 'dont use' were excluded from default choices.")

    payload = {
        "course": args.course,
        "experiment_query": args.experiment,
        "normalized_query": normalize_for_match(args.experiment),
        "template_language_requested": normalize_for_match(args.template_language) if args.template_language else None,
        "roots": {
            "handout_root": str(HANDOUT_LIBRARY_ROOT),
            "reference_root": str(REFERENCE_LIBRARY_ROOT),
            "data_root": str(DATA_ROOT),
            "picture_result_root": str(PIC_RESULT_ROOT),
            "experiment_simulation_root": str(EXPERIMENT_SIMULATION_ROOT),
            "signatory_root": str(SIGNATORY_ROOT),
            "template_root": str(TEMPLATE_ROOT),
            "results_root": str(RESULTS_ROOT),
        },
        "handouts": top_or_all(score_paths(query_text, handouts, library_root=HANDOUT_LIBRARY_ROOT), args.max_results),
        "handout_decoded_json": decoded_candidates(HANDOUT_LIBRARY_ROOT, query_text, args.max_results),
        "reference_reports": top_or_all(
            score_paths(query_text, references, library_root=REFERENCE_LIBRARY_ROOT),
            args.max_results,
        ),
        **reference_selection,
        "reference_decoded_json": decoded_candidates(REFERENCE_LIBRARY_ROOT, query_text, args.max_results),
        "data_files": ranked_data_files,
        "data_groups": data_groups,
        "picture_result_dirs": picture_result_dir_candidates(args.experiment, args.max_results),
        "picture_result_files": top_or_all(score_paths(args.experiment, picture_result_files), args.max_results),
        "simulation_dirs": simulation_dir_candidates(args.experiment, args.max_results),
        "simulation_files": simulation_file_candidates(args.experiment, args.max_results),
        "signatory_files": top_or_all(score_paths(args.experiment, signatory_files), args.max_results),
        "templates": templates,
        "excluded_templates": excluded_templates,
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
