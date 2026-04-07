from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from common import maybe_read_json, read_json, read_text, read_text_if_exists, safe_label
from normalize_comparison_cases import (
    infer_case_id,
    infer_case_title,
    normalize_comparison_case_record,
    normalize_comparison_cases,
)


def require_existing(path: Path, *, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"{label} input is required and must exist: {path}")


def infer_code_role(path: Path) -> str:
    name = path.name.lower()
    parent = str(path.parent).lower()
    if "model" in name or "model" in parent or path.suffix.lower() == ".wl":
        return "modeling"
    if "process" in name or "analysis" in parent:
        return "data-processing"
    return "helper"


def infer_case_key(result_name: str) -> str:
    tokens = [token for token in result_name.strip().split("_") if token]
    if not tokens:
        return "case-1"

    if re.fullmatch(r"lx\d+", tokens[0]):
        if len(tokens) >= 2 and tokens[1] in {"string", "strip", "ring", "plate"}:
            return f"{tokens[0]}_{tokens[1]}"
        return tokens[0]

    return safe_label(tokens[0], default="case-1")


def infer_case_title(case_key: str) -> str:
    parts = [part for part in case_key.split("_") if part]
    if not parts:
        return "Case 1"

    rendered: list[str] = []
    for part in parts:
        if re.fullmatch(r"lx\d+", part):
            rendered.append(part.upper())
        else:
            rendered.append(part.replace("-", " ").title())
    return " ".join(rendered)


def normalize_flat_results(results: list[object]) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, object]] = {}
    order: list[str] = []

    for raw_item in results:
        if not isinstance(raw_item, dict):
            continue

        name = str(raw_item.get("name") or "").strip()
        case_key = infer_case_key(name or "case-1")
        case = grouped.get(case_key)
        if case is None:
            case = {
                "case_id": case_key,
                "title": infer_case_title(case_key),
                "direct_results": [],
                "indirect_results": [],
            }
            grouped[case_key] = case
            order.append(case_key)

        kind = str(raw_item.get("kind") or "").strip().lower()
        if kind in {"derived", "comparison"}:
            case["indirect_results"].append(raw_item)
        else:
            case["direct_results"].append(raw_item)

    normalized = [grouped[key] for key in order if grouped[key]["direct_results"] or grouped[key]["indirect_results"]]
    if normalized:
        return normalized

    raise SystemExit("processed-data input is required and must contain usable result records")


def normalize_cases(processed_payload: dict[str, object]) -> list[dict[str, object]]:
    cases = processed_payload.get("cases")
    if isinstance(cases, list) and cases:
        normalized: list[dict[str, object]] = []
        for index, item in enumerate(cases, start=1):
            if not isinstance(item, dict):
                continue
            case_id = str(item.get("case_id") or f"case-{index}")
            title = str(item.get("title") or item.get("label") or case_id)
            normalized.append(
                {
                    "case_id": case_id,
                    "title": title,
                    "direct_results": list(item.get("direct_results") or []),
                    "indirect_results": list(item.get("indirect_results") or []),
                }
            )
        if normalized:
            return normalized

    results = processed_payload.get("results")
    if isinstance(results, list) and results:
        return normalize_flat_results(results)

    raise SystemExit("processed-data input is required and must contain case or result records")


def normalize_appendix_entries(raw_paths: list[str] | None) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for raw_path in raw_paths or []:
        path = Path(raw_path)
        entries.append(
            {
                "source_path": str(path),
                "label": path.name,
                "role": infer_code_role(path),
                "exists": path.exists(),
                "slug": safe_label(path.stem, default="code"),
            }
        )
    return entries


def normalize_appendix_data_entries(raw_paths: list[str] | None) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for raw_path in raw_paths or []:
        path = Path(raw_path)
        display_label = path.stem.replace("_", " ").replace("-", " ").strip() or path.stem
        entries.append(
            {
                "source_path": str(path),
                "label": display_label,
                "role": "data-file",
                "exists": path.exists(),
                "slug": safe_label(path.stem, default="data-file"),
            }
        )
    return entries


def normalize_calculation_detail_entries(manifest_path: Path | None) -> list[dict[str, object]]:
    if manifest_path is None:
        return []

    payload = read_json(manifest_path)
    if not isinstance(payload, dict):
        raise SystemExit(f"Expected JSON object at {manifest_path}")

    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, list):
        raise SystemExit(f"Calculation-details manifest must contain a list-valued 'entries': {manifest_path}")

    entries: list[dict[str, object]] = []
    for index, raw_entry in enumerate(raw_entries, start=1):
        if not isinstance(raw_entry, dict):
            continue
        raw_path = str(raw_entry.get("path") or "").strip()
        path = Path(raw_path) if raw_path else manifest_path.parent / f"missing-{index}.tex"
        title = str(raw_entry.get("title") or f"Calculation Details {index}")
        entries.append(
            {
                "source_path": str(path),
                "title": title,
                "label": title,
                "order": int(raw_entry.get("order") or index * 10),
                "kind": "calculation_details",
                "exists": bool(raw_entry.get("exists")) if "exists" in raw_entry else path.exists(),
                "slug": str(raw_entry.get("slug") or safe_label(path.stem, default=f"calculation-details-{index}")),
            }
        )
    entries.sort(key=lambda item: (int(item.get("order") or 0), str(item.get("title") or "")))
    return entries


def _optional_cli_paths(values: list[str] | None) -> list[Path]:
    return [Path(str(value).strip()) for value in values or [] if str(value).strip()]


def normalize_symbolic_handoff(args: Any) -> dict[str, object]:
    handout_raw = str(getattr(args, "symbolic_handout", None) or "").strip()
    handout_path = Path(handout_raw) if handout_raw else None
    calculation_code_paths = _optional_cli_paths(getattr(args, "symbolic_calculation_code", None))
    processed_result_paths = _optional_cli_paths(getattr(args, "symbolic_processed_result", None))
    result_keys = [
        str(value).strip()
        for value in getattr(args, "symbolic_result_key", None) or []
        if str(value).strip()
    ]
    output_dir_raw = str(getattr(args, "symbolic_output_dir", None) or "").strip()
    output_dir = Path(output_dir_raw) if output_dir_raw else None

    desired = bool(handout_path or calculation_code_paths or processed_result_paths or result_keys or output_dir)
    unresolved: list[str] = []
    if desired:
        if handout_path is None:
            unresolved.append("Symbolic handoff requested but symbolic handout path is missing; pass --symbolic-handout.")
        elif not handout_path.exists():
            unresolved.append(f"Symbolic handoff requested but symbolic handout path does not exist: {handout_path}")

        if not calculation_code_paths:
            unresolved.append(
                "Symbolic handoff requested but symbolic calculation code path is missing; pass --symbolic-calculation-code."
            )
        else:
            for path in calculation_code_paths:
                if not path.exists():
                    unresolved.append(f"Symbolic handoff requested but symbolic calculation code path does not exist: {path}")

        if not processed_result_paths:
            unresolved.append(
                "Symbolic handoff requested but symbolic processed result path is missing; pass --symbolic-processed-result."
            )
        else:
            for path in processed_result_paths:
                if not path.exists():
                    unresolved.append(f"Symbolic handoff requested but symbolic processed result path does not exist: {path}")

        if not result_keys:
            unresolved.append("Symbolic handoff requested but symbolic result key is missing; pass --symbolic-result-key.")

        if output_dir is None:
            unresolved.append("Symbolic handoff requested but symbolic output dir is missing; pass --symbolic-output-dir.")

        if len(processed_result_paths) > 1 and len(processed_result_paths) != len(result_keys):
            unresolved.append(
                "Symbolic processed result paths are ambiguous; pass one --symbolic-processed-result for all selected keys "
                "or the same count as --symbolic-result-key."
            )

    processed_result_by_key: dict[str, str] = {}
    if len(processed_result_paths) == len(result_keys):
        processed_result_by_key = {
            result_key: str(path)
            for result_key, path in zip(result_keys, processed_result_paths)
        }
    elif len(processed_result_paths) == 1:
        processed_result_by_key = {result_key: str(processed_result_paths[0]) for result_key in result_keys}

    return {
        "desired": desired,
        "enabled": desired and not unresolved,
        "handout_path": str(handout_path) if handout_path is not None else "",
        "calculation_code_paths": [str(path) for path in calculation_code_paths],
        "processed_result_paths": [str(path) for path in processed_result_paths],
        "processed_result_by_key": processed_result_by_key,
        "result_keys": result_keys,
        "output_dir": str(output_dir) if output_dir is not None else "",
        "unresolved": unresolved,
    }


def first_present_comparison_cases(
    interpretation_payload: dict[str, object],
    processed_payload: dict[str, object],
    discussion_payload: dict[str, object],
) -> list[dict[str, object]] | None:
    for payload in (interpretation_payload, processed_payload, discussion_payload):
        if "comparison_cases" in payload:
            normalized = normalize_comparison_cases(payload.get("comparison_cases"))
            if normalized:
                return normalized
    return None


def parse_key_value_summary(path: Path) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw_line in read_text(path).splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        cleaned_key = key.strip()
        cleaned_value = value.strip()
        if cleaned_key and cleaned_value and cleaned_key not in parsed:
            parsed[cleaned_key] = cleaned_value
    return parsed


def case_sort_key(case_id: str) -> tuple[int, str]:
    match = re.fullmatch(r"case-(\d+)", case_id)
    if match:
        return (int(match.group(1)), case_id)
    return (10**9, case_id)


def candidate_search_roots(workspace_root: Path) -> list[Path]:
    roots = [workspace_root]
    parent = workspace_root.parent
    if parent.exists():
        def looks_like_comparison_dir(path: Path) -> bool:
            normalized = path.name.casefold()
            return any(token in normalized for token in ("simulation", "model", "comparison"))

        sibling_dirs = sorted(
            child
            for child in parent.iterdir()
            if child.is_dir() and child != workspace_root and looks_like_comparison_dir(child)
        )
        roots.extend(sibling_dirs)
    return roots


def comparison_summary_files(workspace_root: Path) -> list[Path]:
    results: list[Path] = []
    seen: set[str] = set()
    for root in candidate_search_roots(workspace_root):
        for path in sorted(root.rglob("case-*-summary.txt")):
            rendered = str(path.resolve())
            if rendered in seen:
                continue
            seen.add(rendered)
            results.append(path)
    return results


def find_unique_comparison_asset(summary_path: Path, case_id: str) -> Path | None:
    pattern = f"{case_id}-*.png"
    matches = sorted(summary_path.parent.glob(pattern))
    if not matches:
        return None

    primary_matches = [path for path in matches if not path.stem.lower().endswith("-radial")]
    if len(primary_matches) == 1:
        return primary_matches[0]
    if not primary_matches and len(matches) == 1:
        return matches[0]
    return None


def extract_case_ids_from_text(value: object) -> set[str]:
    text = str(value or "")
    matches = {f"case-{match.lower()}" for match in re.findall(r"case[-_]?([a-z0-9]+)", text, flags=re.IGNORECASE)}
    basename = Path(text).name
    prefix = re.match(r"(\d+)(?:\D|$)", basename)
    if prefix:
        matches.add(f"case-{prefix.group(1)}")
    return matches


def picture_manifest_candidates(workspace_root: Path) -> list[Path]:
    manifest_paths = [workspace_root / "picture_results_manifest.json"]
    return [path for path in manifest_paths if path.exists()]


def observed_asset_candidates_from_manifest(workspace_root: Path) -> dict[str, list[Path]]:
    mapping: dict[str, list[Path]] = {}
    for manifest_path in picture_manifest_candidates(workspace_root):
        manifest_payload = maybe_read_json(manifest_path)
        if not isinstance(manifest_payload, dict):
            continue
        for entry in manifest_payload.get("entries", []):
            if not isinstance(entry, dict):
                continue
            evidence_role = str(entry.get("evidence_role") or "").strip().lower()
            if evidence_role and evidence_role != "observed":
                continue
            candidate_values = [
                entry.get("copied_path"),
                entry.get("relative_output_path"),
                entry.get("source_path"),
                entry.get("stem"),
                entry.get("group"),
            ]
            if not evidence_role and any("measurement_procedure" in str(value or "").casefold() or "measuring" in str(value or "").casefold() for value in candidate_values):
                continue
            case_ids: set[str] = set()
            for value in candidate_values:
                case_ids.update(extract_case_ids_from_text(value))
            if not case_ids:
                continue
            raw_path = str(entry.get("copied_path") or entry.get("source_path") or "").strip()
            if not raw_path:
                continue
            candidate_path = Path(raw_path).expanduser()
            for case_id in sorted(case_ids):
                mapping.setdefault(case_id, []).append(candidate_path)
    return mapping


def is_measurement_proof_path(path: Path) -> bool:
    normalized = str(path).casefold()
    name = path.name.casefold()
    return (
        "measurement_procedure" in normalized
        or "measuring" in normalized
        or "comparison-cases" in normalized
        or name.endswith("-radial.png")
    )


def prefer_primary_observed_candidates(paths: list[Path]) -> list[Path]:
    preferred = [path for path in paths if not is_measurement_proof_path(path)]
    return preferred if preferred else paths


def observed_candidate_priority(workspace_root: Path, path: Path) -> tuple[int, int, str]:
    picture_root = workspace_root / "picture-results"
    try:
        relative = path.relative_to(picture_root)
        top_level_penalty = 1 if len(relative.parts) <= 1 else 0
        depth_bonus = -len(relative.parts)
        return (top_level_penalty, depth_bonus, str(relative))
    except ValueError:
        return (0, -len(path.parts), str(path))


def observed_asset_candidates_from_filenames(workspace_root: Path) -> dict[str, list[Path]]:
    mapping: dict[str, list[Path]] = {}
    picture_dir = workspace_root / "picture-results"
    if not picture_dir.exists():
        return mapping

    for path in sorted(picture_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
            continue
        case_ids = extract_case_ids_from_text(path.name)
        if not case_ids:
            continue
        for case_id in sorted(case_ids):
            mapping.setdefault(case_id, []).append(path)
    return mapping


def find_unique_observed_asset(workspace_root: Path, case_id: str) -> Path | None:
    manifest_candidates = observed_asset_candidates_from_manifest(workspace_root)
    filename_candidates = observed_asset_candidates_from_filenames(workspace_root)

    combined = list(manifest_candidates.get(case_id, [])) + list(filename_candidates.get(case_id, []))
    unique_candidates: list[Path] = []
    seen: set[str] = set()
    for path in combined:
        rendered = str(path)
        if rendered in seen:
            continue
        seen.add(rendered)
        unique_candidates.append(path)

    unique_candidates = prefer_primary_observed_candidates(unique_candidates)
    if not unique_candidates:
        return None

    best_priority = min(observed_candidate_priority(workspace_root, path) for path in unique_candidates)
    prioritized = [path for path in unique_candidates if observed_candidate_priority(workspace_root, path) == best_priority]
    return prioritized[0] if len(prioritized) == 1 else None


def build_fallback_comparison_case(
    *,
    summary_path: Path,
    workspace_root: Path,
) -> tuple[dict[str, object] | None, list[str]]:
    unresolved: list[str] = []
    parsed = parse_key_value_summary(summary_path)
    raw_case_id = parsed.get("caseId") or parsed.get("case_id") or summary_path.stem
    case_id = infer_case_id(raw_case_id, default="case-unknown")
    if case_id == "case-unknown":
        unresolved.append(f"Could not parse a deterministic case id from {summary_path}.")
        return None, unresolved

    comparison_asset = find_unique_comparison_asset(summary_path, case_id)
    if comparison_asset is None:
        unresolved.append(
            f"Could not uniquely map comparison asset for {case_id} from {summary_path.parent}."
        )
        return None, unresolved

    observed_asset = find_unique_observed_asset(workspace_root, case_id)
    if observed_asset is None:
        unresolved.append(
            f"Could not uniquely map observed asset for {case_id} from staged picture evidence."
        )
        return None, unresolved

    summary_fields: list[str] = []
    for key in ("frequencyHz", "f_kHz", "m", "n"):
        value = parsed.get(key)
        if value:
            summary_fields.append(f"{key}={value}")

    observed_reference = parsed.get("imageFile") or observed_asset.name
    observed_summary = f"Observed source image: {observed_reference}." if observed_reference else ""
    comparison_summary = (
        f"Parsed summary fields: {', '.join(summary_fields)}."
        if summary_fields
        else f"Parsed comparison summary file: {summary_path.name}."
    )

    record = normalize_comparison_case_record(
        {
            "case_id": case_id,
            "title": infer_case_title(case_id),
            "observed_label": observed_asset.name,
            "observed_summary": observed_summary,
            "comparison_label": comparison_asset.name,
            "comparison_summary": comparison_summary,
            "agreement_summary": "",
            "caveats": [],
            "confidence": "low",
            "observed_asset_path": str(observed_asset),
            "comparison_asset_path": str(comparison_asset),
        },
        default_case_id=case_id,
    )
    return record, unresolved


def collect_fallback_comparison_cases(workspace_root: Path) -> tuple[list[dict[str, object]], list[str]]:
    grouped_cases: dict[str, list[dict[str, object]]] = {}
    unresolved: list[str] = []

    for summary_path in comparison_summary_files(workspace_root):
        case_record, case_unresolved = build_fallback_comparison_case(
            summary_path=summary_path,
            workspace_root=workspace_root,
        )
        unresolved.extend(case_unresolved)
        if case_record is not None:
            case_id = str(case_record.get("case_id") or "").strip()
            if case_id:
                grouped_cases.setdefault(case_id, []).append(case_record)

    cases: list[dict[str, object]] = []
    for case_id in sorted(grouped_cases, key=case_sort_key):
        records = grouped_cases[case_id]
        if len(records) > 1:
            unresolved.append(
                f"Ambiguous fallback comparison bundles for {case_id}; skipped all local-normalized records for this case."
            )
            continue
        cases.append(records[0])

    cases.sort(key=lambda item: case_sort_key(str(item.get("case_id") or "")))
    return cases, unresolved


def collect_staging_inputs(args: Any) -> dict[str, object]:
    main_tex_path = Path(args.main_tex)
    body_scaffold_path = Path(args.body_scaffold_json)
    procedures_path = Path(args.procedures_markdown)
    processed_data_path = Path(args.processed_data_json)
    results_interpretation_path = Path(args.results_interpretation_json)
    discussion_synthesis_path = Path(args.discussion_synthesis_json)
    references_json_path = Path(args.references_json) if getattr(args, "references_json", None) else None

    require_existing(main_tex_path, label="main-tex")
    require_existing(body_scaffold_path, label="body-scaffold")
    require_existing(procedures_path, label="procedures-markdown")
    require_existing(processed_data_path, label="processed-data")
    require_existing(results_interpretation_path, label="results-interpretation")
    require_existing(discussion_synthesis_path, label="discussion-synthesis")

    plots_manifest_path = Path(args.plots_manifest) if args.plots_manifest else None
    modeling_result_path = Path(args.modeling_result) if args.modeling_result else None
    calculation_details_manifest_path = (
        Path(args.calculation_details_manifest) if getattr(args, "calculation_details_manifest", None) else None
    )
    if plots_manifest_path is not None and not plots_manifest_path.exists():
        raise SystemExit(f"plots-manifest input must exist when provided: {plots_manifest_path}")
    if modeling_result_path is not None and not modeling_result_path.exists():
        raise SystemExit(f"modeling-result input must exist when provided: {modeling_result_path}")
    if references_json_path is not None and not references_json_path.exists():
        raise SystemExit(f"references-json input must exist when provided: {references_json_path}")
    if calculation_details_manifest_path is not None and not calculation_details_manifest_path.exists():
        raise SystemExit(
            "calculation-details-manifest input must exist when provided: "
            f"{calculation_details_manifest_path}"
        )

    processed_payload = read_json(processed_data_path)
    if not isinstance(processed_payload, dict):
        raise SystemExit(f"Expected JSON object at {processed_data_path}")

    interpretation_payload = read_json(results_interpretation_path)
    if not isinstance(interpretation_payload, dict):
        raise SystemExit(f"Expected JSON object at {results_interpretation_path}")

    discussion_payload = read_json(discussion_synthesis_path)
    if not isinstance(discussion_payload, dict):
        raise SystemExit(f"Expected JSON object at {discussion_synthesis_path}")

    references_payload = maybe_read_json(references_json_path)
    if references_json_path is not None and references_payload is not None and not isinstance(references_payload, dict):
        raise SystemExit(f"Expected JSON object at {references_json_path}")

    appendix_entries = normalize_appendix_entries(list(args.appendix_code or []))
    appendix_data_entries = normalize_appendix_data_entries(list(getattr(args, "appendix_data", []) or []))
    calculation_detail_entries = normalize_calculation_detail_entries(calculation_details_manifest_path)
    symbolic_handoff = normalize_symbolic_handoff(args)
    workspace_root = main_tex_path.parent

    explicit_comparison_cases = first_present_comparison_cases(
        interpretation_payload,
        processed_payload,
        discussion_payload,
    )
    if explicit_comparison_cases is not None:
        normalized_comparison_cases = explicit_comparison_cases
        comparison_case_unresolved: list[str] = []
    else:
        normalized_comparison_cases, comparison_case_unresolved = collect_fallback_comparison_cases(workspace_root)

    raw_references = []
    if isinstance(references_payload, dict):
        raw_references = list(references_payload.get("references") or [])
    literature_references = [
        dict(entry)
        for entry in raw_references
        if isinstance(entry, dict) and str(entry.get("comparison_basis") or "").strip() == "literature_report"
    ]

    return {
        "main_tex_path": main_tex_path,
        "main_tex_text": read_text(main_tex_path),
        "body_scaffold": read_json(body_scaffold_path),
        "procedures_markdown_text": read_text(procedures_path),
        "processed_payload": processed_payload,
        "cases": normalize_cases(processed_payload),
        "results_interpretation": interpretation_payload,
        "discussion_synthesis": discussion_payload,
        "plots_manifest": maybe_read_json(plots_manifest_path),
        "modeling_payload": maybe_read_json(modeling_result_path),
        "references_payload": references_payload if isinstance(references_payload, dict) else {},
        "literature_references": literature_references,
        "processed_data_markdown": read_text_if_exists(Path(args.processed_data_markdown)) if getattr(args, "processed_data_markdown", None) else "",
        "results_interpretation_markdown": read_text_if_exists(Path(args.results_interpretation_markdown)) if getattr(args, "results_interpretation_markdown", None) else "",
        "discussion_synthesis_markdown": read_text_if_exists(Path(args.discussion_synthesis_markdown)) if getattr(args, "discussion_synthesis_markdown", None) else "",
        "appendix_entries": appendix_entries,
        "appendix_data_entries": appendix_data_entries,
        "calculation_detail_entries": calculation_detail_entries,
        "symbolic_handoff": symbolic_handoff,
        "comparison_cases": normalized_comparison_cases,
        "comparison_case_unresolved": comparison_case_unresolved,
    }
