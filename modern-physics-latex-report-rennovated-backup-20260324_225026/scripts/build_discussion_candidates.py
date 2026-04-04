#!/usr/bin/env python3
"""Build structured further-discussion candidates from an evidence plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import safe_label, write_json


def read_plan(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def confidence_rank(level: str) -> int:
    return {"high": 3, "medium": 2, "low": 1}.get(level, 1)


def lower_confidence(level: str) -> str:
    if level == "high":
        return "medium"
    return "low"


def build_anomaly_candidate(unit: dict[str, object]) -> dict[str, object]:
    anomaly_signals = [str(item) for item in unit.get("anomaly_signals") or []]
    confidence = "medium" if unit.get("mapping_confidence") == "high" else "low"
    return {
        "candidate_id": safe_label(f"{unit['group_id']}-anomaly", default="discussion-candidate"),
        "candidate_type": "anomaly_explanation",
        "source_group_ids": [unit["group_id"]],
        "trigger_reason": "Observed result deviates from expected or cleaner comparison behavior.",
        "observed_facts": anomaly_signals,
        "proposed_interpretation": (
            f"The conflicting {unit['sample_label']} observation likely reflects weak contrast, orientation sensitivity, "
            "or incomplete method-specific evidence rather than a clean reversal of the main result."
        ),
        "confidence_level": confidence,
        "wording_posture": "likely indicates" if confidence == "medium" else "may indicate",
        "outside_lookup_needed": True,
        "source_notes": [],
        "open_conflicts": anomaly_signals,
    }


def build_vague_image_candidate(unit: dict[str, object]) -> dict[str, object]:
    warnings = [str(item) for item in unit.get("warnings") or []]
    return {
        "candidate_id": safe_label(f"{unit['group_id']}-vague-image", default="discussion-candidate"),
        "candidate_type": "vague_image_interpretation",
        "source_group_ids": [unit["group_id"]],
        "trigger_reason": "Low-confidence image mapping or visibly ambiguous observation.",
        "observed_facts": warnings or [f"{unit['sample_label']} remains hard to classify confidently from the current image group."],
        "proposed_interpretation": (
            f"The {unit['sample_label']} image set may indicate a real but low-contrast interference feature, "
            "though the current visual evidence is not strong enough for a sharper claim."
        ),
        "confidence_level": "low",
        "wording_posture": "may indicate",
        "outside_lookup_needed": True,
        "source_notes": [],
        "open_conflicts": warnings,
    }


def build_material_candidate(unit: dict[str, object], candidate_type: str, confidence: str, outside_lookup_needed: bool) -> dict[str, object]:
    method_label = str(unit.get("method_label") or "")
    wording = "is consistent with" if confidence == "high" else ("likely indicates" if confidence == "medium" else "may indicate")
    return {
        "candidate_id": safe_label(f"{unit['group_id']}-{candidate_type}", default="discussion-candidate"),
        "candidate_type": candidate_type,
        "source_group_ids": [unit["group_id"]],
        "trigger_reason": f"{unit['sample_label']} has method-specific behavior worth interpreting beyond the handout summary.",
        "observed_facts": [str(unit.get("analysis_focus") or "").strip() or f"{unit['sample_label']} has report-specific method evidence."],
        "proposed_interpretation": (
            f"The {unit['sample_label']} behavior {wording} material-dependent optical response seen under {method_label}, "
            "so the report should compare the local pattern with common experiment outcomes instead of stopping at description."
        ),
        "confidence_level": confidence,
        "wording_posture": wording,
        "outside_lookup_needed": outside_lookup_needed,
        "source_notes": [],
        "open_conflicts": [str(item) for item in unit.get("warnings") or []],
    }


def candidates_for_unit(unit: dict[str, object]) -> list[dict[str, object]]:
    method_label = str(unit.get("method_label") or "")
    mapping_confidence = str(unit.get("mapping_confidence") or "low")
    warnings = [str(item) for item in unit.get("warnings") or []]
    anomaly_signals = [str(item) for item in unit.get("anomaly_signals") or []]

    if anomaly_signals:
        return [build_anomaly_candidate(unit)]

    if mapping_confidence == "low" or method_label == "unmapped observation":
        return [build_vague_image_candidate(unit)]

    if method_label == "extended sample comparison":
        confidence = "medium" if not warnings else "low"
        return [build_material_candidate(unit, "material_specific_explanation", confidence, True)]

    if method_label in {"z-cut conoscopic observation", "oblique-cut sequence", "x-cut observation"}:
        confidence = "medium" if confidence_rank(mapping_confidence) >= 2 else "low"
        if warnings:
            confidence = lower_confidence(confidence)
        return [build_material_candidate(unit, "material_specific_explanation", confidence, True)]

    if method_label == "Airy spiral":
        confidence = "medium" if not warnings else "low"
        return [build_material_candidate(unit, "comparison_to_common_outcomes", confidence, False)]

    return []


def build_candidates(plan: dict[str, object]) -> dict[str, object]:
    units = [item for item in plan.get("evidence_units") or [] if isinstance(item, dict)]
    discussion_candidates: list[dict[str, object]] = []
    for unit in units:
        discussion_candidates.extend(candidates_for_unit(unit))

    return {
        "candidate_count": len(discussion_candidates),
        "discussion_candidates": discussion_candidates,
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Discussion Candidates",
        "",
        f"- Candidates: {payload['candidate_count']}",
        "",
    ]
    for candidate in payload["discussion_candidates"]:
        lines.append(f"## {candidate['candidate_id']}")
        lines.append("")
        lines.append(f"- Type: {candidate['candidate_type']}")
        lines.append(f"- Confidence: {candidate['confidence_level']}")
        lines.append(f"- Wording posture: {candidate['wording_posture']}")
        lines.append(f"- Outside lookup needed: {candidate['outside_lookup_needed']}")
        lines.append(f"- Source groups: {', '.join(candidate['source_group_ids'])}")
        lines.append(f"- Observed facts: {' | '.join(candidate['observed_facts'])}")
        lines.append(f"- Interpretation: {candidate['proposed_interpretation']}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-plan", required=True, help="Path to picture_evidence_plan.json.")
    parser.add_argument("--output-json", required=True, help="Path to write discussion_candidates.json.")
    parser.add_argument("--output-markdown", required=True, help="Path to write discussion_candidates.md.")
    args = parser.parse_args()

    evidence_plan = read_plan(Path(args.evidence_plan))
    payload = build_candidates(evidence_plan)
    write_json(Path(args.output_json), payload)
    Path(args.output_markdown).write_text(render_markdown(payload) + "\n", encoding="utf-8")
    print(json.dumps({"output_json": args.output_json, "candidate_count": payload["candidate_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
