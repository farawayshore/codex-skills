#!/usr/bin/env python3
"""Plan report-facing picture evidence units from a staged manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import safe_label, write_json


def read_manifest(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_group_id(group: str, entries: list[dict[str, object]]) -> str:
    if group:
        return safe_label(group, default="evidence-unit")
    if entries:
        return safe_label(str(entries[0].get("relative_output_path") or "evidence-unit"), default="evidence-unit")
    return "evidence-unit"


def classify_group(group: str) -> dict[str, str]:
    normalized = group.casefold()
    if "airy-spiral" in normalized:
        return {
            "target_subsection": "Airy spiral observations",
            "method_label": "Airy spiral",
            "analysis_focus": "Compare mirrored stack orders to infer opposite rotation behavior.",
            "mapping_confidence": "high",
        }
    if "z-cut material" in normalized:
        return {
            "target_subsection": "z-cut sample analysis",
            "method_label": "z-cut conoscopic observation",
            "analysis_focus": "Relate conoscopic, accessory-plate, and wedge evidence for optic-sign judgment.",
            "mapping_confidence": "high",
        }
    if "oblique-cut material" in normalized:
        return {
            "target_subsection": "oblique and x-cut sample analysis",
            "method_label": "oblique-cut sequence",
            "analysis_focus": "Track how oblique-cut interference features evolve through the observed sequence.",
            "mapping_confidence": "high",
        }
    if "x-cut material" in normalized:
        return {
            "target_subsection": "oblique and x-cut sample analysis",
            "method_label": "x-cut observation",
            "analysis_focus": "Interpret the weaker or transient conoscopic features of x-cut samples.",
            "mapping_confidence": "high",
        }
    if "extended samples" in normalized:
        return {
            "target_subsection": "extended sample comparison",
            "method_label": "extended sample comparison",
            "analysis_focus": "Compare how extended samples respond across polarization and conoscopic modes.",
            "mapping_confidence": "high",
        }
    if "schematic diagram of fast axis for plates" in normalized:
        return {
            "target_subsection": "A/B/I-series fast-axis analysis",
            "method_label": "fast-axis schematic",
            "analysis_focus": "Support the plate-by-plate fast-axis and retardation interpretation.",
            "mapping_confidence": "high",
        }
    return {
        "target_subsection": "unmapped evidence review",
        "method_label": "unmapped observation",
        "analysis_focus": "Inspect this evidence manually before drafting a local interpretation.",
        "mapping_confidence": "low",
    }


def choose_selected_entries(
    group: str,
    entries: list[dict[str, object]],
    sequence_lookup: dict[str, list[dict[str, object]]],
) -> tuple[str, list[str], list[str]]:
    normalized = group.casefold()
    if "airy-spiral" in normalized:
        selected = [str(entry.get("relative_output_path")) for entry in entries]
        return "paired_comparison", selected, []

    sequence_entries = sequence_lookup.get(group, [])
    if len(sequence_entries) >= 4:
        ordered = sorted(
            sequence_entries,
            key=lambda item: (
                int(item.get("sequence_serial") or 0),
                str(item.get("relative_output_path") or ""),
            ),
        )
        keep_indexes = {0, len(ordered) // 2, len(ordered) - 1}
        selected = [str(entry.get("relative_output_path")) for idx, entry in enumerate(ordered) if idx in keep_indexes]
        omitted = [str(entry.get("relative_output_path")) for idx, entry in enumerate(ordered) if idx not in keep_indexes]
        return "representative_subset", selected, omitted

    selected = [str(entry.get("relative_output_path")) for entry in entries]
    return "all", selected, []


def sample_label_from_group(group: str, entries: list[dict[str, object]]) -> str:
    if group:
        parts = [part for part in group.split("/") if part]
        return parts[-1]
    if entries:
        return Path(str(entries[0].get("relative_output_path") or "")).stem
    return "Unknown sample"


def entry_case_ids(entry: dict[str, object]) -> list[str]:
    raw = entry.get("case_ids")
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    return []


def entry_role(entry: dict[str, object]) -> str:
    return str(entry.get("evidence_role") or "observed").strip() or "observed"


def paired_comparison_units(entries: list[dict[str, object]]) -> tuple[list[dict[str, object]], set[str], list[str]]:
    by_case: dict[str, dict[str, list[dict[str, object]]]] = {}
    for item in entries:
        if not isinstance(item, dict):
            continue
        case_ids = entry_case_ids(item)
        if len(case_ids) != 1:
            continue
        role = entry_role(item)
        if role not in {"observed", "comparison"}:
            continue
        by_case.setdefault(case_ids[0], {}).setdefault(role, []).append(item)

    evidence_units: list[dict[str, object]] = []
    consumed_paths: set[str] = set()
    warnings: list[str] = []
    for case_id in sorted(by_case):
        observed_entries = by_case[case_id].get("observed", [])
        comparison_entries = by_case[case_id].get("comparison", [])
        if not observed_entries or not comparison_entries:
            continue
        if len(observed_entries) != 1 or len(comparison_entries) != 1:
            warnings.append(
                f"Could not confidently pair observed and comparison evidence for {case_id}; expected exactly one of each."
            )
            continue

        observed_entry = observed_entries[0]
        comparison_entry = comparison_entries[0]
        observed_rel = str(observed_entry.get("relative_output_path") or "")
        comparison_rel = str(comparison_entry.get("relative_output_path") or "")
        if not observed_rel or not comparison_rel:
            warnings.append(f"Skipped paired comparison for {case_id} because a staged relative path was missing.")
            continue

        consumed_paths.add(observed_rel)
        consumed_paths.add(comparison_rel)
        evidence_units.append(
            {
                "group_id": safe_label(f"comparison-{case_id}", default="comparison-case"),
                "case_id": case_id,
                "sample_label": case_id.replace("case-", "Case "),
                "method_label": "experiment vs simulation",
                "source_group_paths": list(
                    dict.fromkeys(
                        [
                            str(observed_entry.get("group") or ""),
                            str(comparison_entry.get("group") or ""),
                        ]
                    )
                ),
                "target_subsection": "Comparison",
                "analysis_focus": "Place the same-case experimental pattern next to the corresponding non-radial simulation output.",
                "selection_policy": "paired_comparison",
                "selected_entries": [observed_rel, comparison_rel],
                "omitted_entries": [],
                "placement_mode": "same_subsection_local_float",
                "caption_metadata": {
                    "sample_label": case_id.replace("case-", "Case "),
                    "method_label": "experiment vs simulation",
                },
                "mapping_confidence": "high",
                "warnings": [],
            }
        )

    return evidence_units, consumed_paths, warnings


def build_evidence_plan(manifest: dict[str, object]) -> dict[str, object]:
    entries = manifest.get("entries") or []
    if not isinstance(entries, list):
        entries = []

    paired_units, consumed_paths, warnings = paired_comparison_units(entries)

    grouped_entries: dict[str, list[dict[str, object]]] = {}
    for item in entries:
        if not isinstance(item, dict):
            continue
        relative_output_path = str(item.get("relative_output_path") or "")
        if relative_output_path and relative_output_path in consumed_paths:
            continue
        group = str(item.get("group") or "")
        grouped_entries.setdefault(group, []).append(item)

    sequence_lookup: dict[str, list[dict[str, object]]] = {}
    for item in manifest.get("sequence_groups") or []:
        if not isinstance(item, dict):
            continue
        group = str(item.get("group") or "")
        item_entries = item.get("entries") or []
        if isinstance(item_entries, list):
            sequence_lookup[group] = [entry for entry in item_entries if isinstance(entry, dict)]

    evidence_units: list[dict[str, object]] = list(paired_units)

    for group in sorted(grouped_entries):
        items = sorted(grouped_entries[group], key=lambda entry: str(entry.get("relative_output_path") or ""))
        classification = classify_group(group)
        selection_policy, selected_entries, omitted_entries = choose_selected_entries(group, items, sequence_lookup)
        group_id = normalize_group_id(group, items)
        sample_label = sample_label_from_group(group, items)

        unit_warnings: list[str] = []
        if classification["mapping_confidence"] == "low":
            unit_warnings.append(f"Could not confidently map group '{group}' to a standard report subsection.")
        if selection_policy == "representative_subset" and omitted_entries:
            unit_warnings.append(
                f"Selected a representative subset for group '{group}' and omitted {len(omitted_entries)} repetitive entries."
            )

        warnings.extend(unit_warnings)
        evidence_units.append(
            {
                "group_id": group_id,
                "sample_label": sample_label,
                "method_label": classification["method_label"],
                "source_group_paths": [group] if group else [],
                "target_subsection": classification["target_subsection"],
                "analysis_focus": classification["analysis_focus"],
                "selection_policy": selection_policy,
                "selected_entries": selected_entries,
                "omitted_entries": omitted_entries,
                "placement_mode": "same_subsection_local_float",
                "caption_metadata": {
                    "sample_label": sample_label,
                    "method_label": classification["method_label"],
                },
                "mapping_confidence": classification["mapping_confidence"],
                "warnings": unit_warnings,
            }
        )

    return {
        "file_count": int(manifest.get("file_count") or len(entries)),
        "unit_count": len(evidence_units),
        "warning_count": len(warnings),
        "warnings": warnings,
        "evidence_units": evidence_units,
    }


def render_markdown(plan: dict[str, object]) -> str:
    lines = [
        "# Picture Evidence Plan",
        "",
        f"- Evidence units: {plan['unit_count']}",
        f"- Warnings: {plan['warning_count']}",
        "",
    ]
    for unit in plan["evidence_units"]:
        lines.append(f"## {unit['group_id']}")
        lines.append("")
        lines.append(f"- Subsection: {unit['target_subsection']}")
        lines.append(f"- Sample: {unit['sample_label']}")
        lines.append(f"- Method: {unit['method_label']}")
        lines.append(f"- Selection policy: {unit['selection_policy']}")
        lines.append(f"- Selected entries: {len(unit['selected_entries'])}")
        lines.append(f"- Omitted entries: {len(unit['omitted_entries'])}")
        if unit["warnings"]:
            lines.append(f"- Warnings: {' | '.join(unit['warnings'])}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest-json", required=True, help="Path to picture_results_manifest.json.")
    parser.add_argument("--output-json", required=True, help="Path to write the evidence plan JSON.")
    parser.add_argument("--output-markdown", required=True, help="Path to write the evidence plan Markdown summary.")
    args = parser.parse_args()

    manifest = read_manifest(Path(args.manifest_json))
    plan = build_evidence_plan(manifest)
    write_json(Path(args.output_json), plan)
    Path(args.output_markdown).write_text(render_markdown(plan) + "\n", encoding="utf-8")
    print(json.dumps({"output_json": args.output_json, "unit_count": plan["unit_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
