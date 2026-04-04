#!/usr/bin/env python3
"""Build artifact-only discussion synthesis outputs from approved idea handoffs."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import read_json, read_text_if_exists, safe_label, write_json, write_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-name", required=True)
    parser.add_argument("--experiment-safe-name", required=True)
    parser.add_argument("--synthesis-input-json", required=True)
    parser.add_argument("--synthesis-input-markdown")
    parser.add_argument("--reference-report", action="append", required=True)
    parser.add_argument("--results-interpretation-json")
    parser.add_argument("--results-interpretation-markdown")
    parser.add_argument("--prior-synthesis-json")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-markdown", required=True)
    parser.add_argument("--output-unresolved", required=True)
    parser.add_argument("--output-staging-json", required=True)
    parser.add_argument("--output-staging-markdown", required=True)
    return parser


def require_existing(path: Path, *, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"{label} input is required and must exist: {path}")


def load_approved_input(path: Path) -> dict[str, object]:
    require_existing(path, label="synthesis-input-json")
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise SystemExit("approval required: synthesis input must be approved before course-lab-discussion-synthesis runs")

    approval_status = str(payload.get("approval_status") or "").strip().lower()
    approved_ids = payload.get("approved_idea_ids")
    approved = approval_status == "approved" and isinstance(approved_ids, list) and bool(approved_ids)
    if not approved:
        raise SystemExit("approval required: synthesis input must be approved before course-lab-discussion-synthesis runs")
    return payload


def load_reference_reports(reference_paths: list[str]) -> list[dict[str, object]]:
    reports: list[dict[str, object]] = []
    for raw_path in reference_paths:
        path = Path(raw_path)
        require_existing(path, label="reference-report")
        payload = read_json(path)
        if isinstance(payload, dict):
            reports.append(payload)
        else:
            reports.append({"title": path.stem})
    return reports


def block_type_for(idea: dict[str, object]) -> str:
    position = str(idea.get("suggested_synthesis_position") or "").strip().lower()
    if position:
        return position

    category = str(idea.get("category") or "").strip().lower()
    if "error" in category or "anomaly" in category:
        return "error-analysis"
    if "improvement" in category:
        return "improvement-suggestions"
    if "question" in category:
        return "assigned-thinking-questions"
    return "physical-interpretation"


def support_strength_for(idea: dict[str, object]) -> str:
    confidence = str(idea.get("confidence_level") or "").strip().lower()
    if confidence in {"low", "medium", "high"}:
        return confidence
    return "medium"


def summary_for(idea: dict[str, object]) -> str:
    summary = str(idea.get("local_basis_summary") or "").strip()
    if summary:
        return summary
    return str(idea.get("reusable_snippet") or "Discussion support remains tied to the approved idea set.").strip()


def should_use_targeted_gap_fill(ideas: list[dict[str, object]], *, is_first_run: bool) -> bool:
    if is_first_run:
        return False
    for idea in ideas:
        if support_strength_for(idea) == "low":
            return True
        caution_notes = idea.get("caution_notes")
        if isinstance(caution_notes, list) and caution_notes:
            return True
        if "may indicate" in str(idea.get("wording_posture") or "").lower():
            return True
    return False


def build_support_records(
    ideas: list[dict[str, object]],
    reference_reports: list[dict[str, object]],
    *,
    is_first_run: bool,
    targeted_gap_fill_used: bool,
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    reference_titles = [str(item.get("title") or "Reference") for item in reference_reports]

    for idea in ideas:
        idea_id = str(idea.get("idea_id") or safe_label(str(idea.get("title") or "idea"), default="idea"))
        origin = "reference-report"
        if targeted_gap_fill_used and support_strength_for(idea) == "low":
            origin = "targeted-gap-fill"
        elif is_first_run:
            origin = "first-pass-web"

        refs = reference_titles or [str(value) for value in idea.get("reference_report_support", []) if value]
        records.append(
            {
                "record_id": safe_label(f"{idea_id}-{origin}", default="support-record"),
                "block_id": safe_label(idea_id, default="discussion-block"),
                "source_label": refs[0] if refs else "Approved idea support",
                "source_link": f"{origin}:{idea_id}",
                "support_note": summary_for(idea),
                "source_origin": origin,
            }
        )
    return records


def build_discussion_blocks(
    ideas: list[dict[str, object]],
    support_records: list[dict[str, object]],
    *,
    targeted_gap_fill_used: bool,
) -> tuple[list[dict[str, object]], list[str]]:
    blocks: list[dict[str, object]] = []
    unresolved: list[str] = []
    record_map: dict[str, list[str]] = {}

    for record in support_records:
        block_id = str(record.get("block_id") or "")
        if not block_id:
            continue
        record_map.setdefault(block_id, []).append(str(record.get("record_id") or "support-record"))

    for idea in ideas:
        idea_id = str(idea.get("idea_id") or safe_label(str(idea.get("title") or "idea"), default="idea"))
        block_id = safe_label(idea_id, default="discussion-block")
        block_type = block_type_for(idea)
        support_strength = support_strength_for(idea)
        summary = summary_for(idea)
        title = str(idea.get("title") or idea_id)
        polishing = str(idea.get("reusable_snippet") or "").strip() or f"{title} should stay tied to the approved evidence."

        block_unresolved: list[str] = []
        caution_notes = idea.get("caution_notes")
        if isinstance(caution_notes, list):
            block_unresolved.extend(str(item).strip() for item in caution_notes if str(item).strip())

        if support_strength == "low":
            weak_note = f"Weak support remains for {title}."
            block_unresolved.append(weak_note)
            unresolved.append(weak_note)
        elif targeted_gap_fill_used and block_type == "error-analysis":
            unresolved.append(f"Targeted gap fill was used to stabilize {title}.")

        blocks.append(
            {
                "block_id": block_id,
                "block_type": block_type,
                "title": title,
                "approved_idea_ids": [idea_id],
                "summary": summary,
                "polished_markdown": polishing,
                "support_strength": support_strength,
                "source_refs": record_map.get(block_id, []),
                "unresolved": block_unresolved,
            }
        )

    return blocks, unresolved


def overall_confidence_for(blocks: list[dict[str, object]]) -> str:
    strengths = [str(block.get("support_strength") or "").lower() for block in blocks]
    if any(item == "low" for item in strengths):
        return "low"
    if any(item == "medium" for item in strengths):
        return "medium"
    return "high"


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Discussion Synthesis",
        "",
        f"- Overall confidence: {payload.get('overall_confidence', 'medium')}",
        f"- Broad first-pass web research used: {str(bool(payload.get('broad_first_pass_web_research_used'))).lower()}",
        f"- Targeted gap fill research used: {str(bool(payload.get('targeted_gap_fill_research_used'))).lower()}",
        "",
    ]

    for block in payload.get("discussion_blocks", []):
        if not isinstance(block, dict):
            continue
        lines.append(f"## {block.get('title', 'Discussion Block')}")
        lines.append("")
        lines.append(f"- Block type: {block.get('block_type', '')}")
        lines.append(f"- Support strength: {block.get('support_strength', '')}")
        lines.append("")
        lines.append(str(block.get("polished_markdown", "")).strip())
        lines.append("")

    return "\n".join(lines) + "\n"


def render_unresolved_markdown(lines: list[str]) -> str:
    output = ["# Discussion Synthesis Unresolved", ""]
    for line in lines:
        output.append(f"- {line}")
    output.append("")
    return "\n".join(output) + "\n"


def render_staging_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Discussion Staging Input",
        "",
        f"- Overall confidence: {payload.get('overall_confidence', 'medium')}",
        "",
    ]
    for block in payload.get("discussion_blocks", []):
        if not isinstance(block, dict):
            continue
        lines.append(f"## {block.get('block_id', 'discussion-block')}")
        lines.append("")
        lines.append(f"- Title: {block.get('title', '')}")
        lines.append(f"- Block type: {block.get('block_type', '')}")
        lines.append(f"- Support strength: {block.get('support_strength', '')}")
        lines.append(f"- Text: {block.get('polished_markdown', '')}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    synthesis_input_path = Path(args.synthesis_input_json)
    synthesis_input = load_approved_input(synthesis_input_path)
    reference_reports = load_reference_reports(args.reference_report)

    prior_synthesis_path = Path(args.prior_synthesis_json) if args.prior_synthesis_json else None
    is_first_run = not (prior_synthesis_path and prior_synthesis_path.exists())

    ideas = synthesis_input.get("discussion_ideas")
    if not isinstance(ideas, list):
        ideas = []
    typed_ideas = [item for item in ideas if isinstance(item, dict)]

    targeted_gap_fill_used = should_use_targeted_gap_fill(typed_ideas, is_first_run=is_first_run)
    support_records = build_support_records(
        typed_ideas,
        reference_reports,
        is_first_run=is_first_run,
        targeted_gap_fill_used=targeted_gap_fill_used,
    )
    discussion_blocks, unresolved = build_discussion_blocks(
        typed_ideas,
        support_records,
        targeted_gap_fill_used=targeted_gap_fill_used,
    )

    if args.results_interpretation_json:
        interpretation_path = Path(args.results_interpretation_json)
        if interpretation_path.exists():
            interpretation_payload = read_json(interpretation_path)
            if isinstance(interpretation_payload, dict):
                for item in interpretation_payload.get("unresolved", []):
                    text = str(item).strip()
                    if text:
                        unresolved.append(text)

    overall_confidence = overall_confidence_for(discussion_blocks)
    payload = {
        "experiment_name": args.experiment_name,
        "experiment_safe_name": args.experiment_safe_name,
        "approved_idea_ids": synthesis_input.get("approved_idea_ids", []),
        "is_first_accepted_ideas_run": is_first_run,
        "broad_first_pass_web_research_used": is_first_run,
        "targeted_gap_fill_research_used": targeted_gap_fill_used,
        "discussion_blocks": discussion_blocks,
        "support_records": support_records,
        "unresolved": unresolved,
        "overall_confidence": overall_confidence,
        "synthesis_input_markdown_present": bool(read_text_if_exists(Path(args.synthesis_input_markdown)) if args.synthesis_input_markdown else ""),
        "results_interpretation_markdown_present": bool(
            read_text_if_exists(Path(args.results_interpretation_markdown)) if args.results_interpretation_markdown else ""
        ),
    }

    write_json(Path(args.output_json), payload)
    write_text(Path(args.output_markdown), render_markdown(payload))
    write_text(Path(args.output_unresolved), render_unresolved_markdown(unresolved))

    staging_payload = {
        "experiment_name": args.experiment_name,
        "experiment_safe_name": args.experiment_safe_name,
        "overall_confidence": overall_confidence,
        "discussion_blocks": discussion_blocks,
        "unresolved": unresolved,
    }
    write_json(Path(args.output_staging_json), staging_payload)
    write_text(Path(args.output_staging_markdown), render_staging_markdown(staging_payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
