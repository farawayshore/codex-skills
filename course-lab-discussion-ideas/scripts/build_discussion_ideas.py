#!/usr/bin/env python3
"""Build artifact-only discussion ideas from stable interpretation inputs."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import read_json, read_text_if_exists, safe_label, write_json, write_text
from merge_idea_memory import merge_into_memory_dir
from render_discussion_ideas_markdown import (
    render_discussion_ideas_markdown,
    render_synthesis_markdown,
    render_unresolved_markdown,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-name", required=True)
    parser.add_argument("--experiment-safe-name", required=True)
    parser.add_argument("--results-interpretation-json", required=True)
    parser.add_argument("--results-interpretation-markdown")
    parser.add_argument("--processed-data-json")
    parser.add_argument("--uncertainty-markdown")
    parser.add_argument("--plots-manifest")
    parser.add_argument("--picture-evidence-plan")
    parser.add_argument("--modeling-result")
    parser.add_argument("--reference-report", action="append", required=True)
    parser.add_argument("--idea-gists", required=True)
    parser.add_argument("--memory-root", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-markdown", required=True)
    parser.add_argument("--output-unresolved", required=True)
    parser.add_argument("--output-synthesis-json", required=True)
    parser.add_argument("--output-synthesis-markdown", required=True)
    return parser


def load_reference_titles(reference_paths: list[str]) -> list[str]:
    titles: list[str] = []
    for raw_path in reference_paths:
        path = Path(raw_path)
        if not path.exists():
            raise SystemExit(f"reference-report input is required and must exist: {path}")
        payload = read_json(path)
        if isinstance(payload, dict) and payload.get("title"):
            titles.append(str(payload["title"]))
        else:
            titles.append(path.stem)
    return titles


def load_memory_ideas(memory_dir: Path) -> list[dict[str, object]]:
    memory_json = memory_dir / "idea_memory.json"
    if not memory_json.exists():
        return []
    payload = read_json(memory_json)
    if not isinstance(payload, dict):
        return []
    ideas = payload.get("discussion_ideas")
    if not isinstance(ideas, list):
        return []
    return [item for item in ideas if isinstance(item, dict)]


def confidence_and_posture(category: str, *, second_round: bool) -> tuple[str, str]:
    if category in {"comparison_to_reference", "interpretation_extension"}:
        return ("medium", "likely indicates")
    if category in {"anomaly_explanation", "memory_reuse"}:
        return ("medium", "likely indicates")
    if second_round:
        return ("low", "may indicate")
    if category in {"missing_result_family", "open_followup"}:
        return ("low", "may indicate")
    return ("medium", "likely indicates")


def should_run_broad_first_pass(memory_exists: bool) -> bool:
    return not memory_exists


def targeted_round_count(*, needs_second_pass: bool) -> int:
    return 2 if needs_second_pass else 1


def build_candidate(
    *,
    title: str,
    category: str,
    local_basis_summary: str,
    source_evidence: list[str],
    reference_titles: list[str],
    broad_first_pass_search_used: bool,
    reuse_status: str = "new",
    memory_analogy_notes: list[str] | None = None,
    needs_second_pass: bool = False,
) -> dict[str, object]:
    idea_id = safe_label(title, default="discussion-idea")
    round_count = targeted_round_count(needs_second_pass=needs_second_pass)
    confidence, posture = confidence_and_posture(category, second_round=needs_second_pass)
    lookup_summary = (
        "First targeted lookup stayed weak, so a second targeted lookup kept the idea tentative."
        if round_count == 2
        else "One targeted lookup round sharpened the idea against the current evidence and references."
    )
    if broad_first_pass_search_used:
        lookup_summary = "Broad first-pass search widened this direction. " + lookup_summary

    return {
        "idea_id": idea_id,
        "title": title,
        "category": category,
        "source_evidence": source_evidence,
        "reference_report_support": reference_titles,
        "memory_analogy_notes": memory_analogy_notes or [],
        "local_basis_summary": local_basis_summary,
        "beyond_handout": category in {"anomaly_explanation", "open_followup"},
        "suggests_modeling": category in {"missing_result_family", "open_followup"},
        "suggests_extraction_or_analysis_code": needs_second_pass,
        "confidence_level": confidence,
        "wording_posture": posture,
        "broad_web_seeded": broad_first_pass_search_used,
        "targeted_web_round_count": round_count,
        "outside_lookup_summary": lookup_summary,
        "reuse_status": reuse_status,
        "reusable_snippet": f"{title} {posture} and should remain tied to the current evidence.",
        "caution_notes": [local_basis_summary] if confidence == "low" else [],
        "suggested_synthesis_position": "further-discussion",
        "approval_status": "pending_synthesis_judgment",
        "approval_basis": "Generated by course-lab-discussion-ideas; course-lab-discussion-synthesis should judge whether to keep, compress, or discard this idea before staging.",
    }


def dedupe_candidates(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    seen: set[str] = set()
    retained: list[dict[str, object]] = []
    for item in candidates:
        key = str(item.get("idea_id") or "")
        if not key or key in seen:
            continue
        seen.add(key)
        retained.append(item)
    return retained


def build_candidates(
    interpretation_payload: dict[str, object],
    *,
    reference_titles: list[str],
    broad_first_pass_search_used: bool,
    memory_ideas: list[dict[str, object]],
) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []

    interpretation_items = interpretation_payload.get("interpretation_items")
    if isinstance(interpretation_items, list):
        for item in interpretation_items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "result")
            summary = str(item.get("summary") or "Interpret the current result carefully.")
            candidates.append(
                build_candidate(
                    title=f"{name.replace('_', ' ').title()} interpretation extension",
                    category="interpretation_extension",
                    local_basis_summary=summary,
                    source_evidence=[name, summary],
                    reference_titles=reference_titles,
                    broad_first_pass_search_used=broad_first_pass_search_used,
                )
            )

    comparison_records = interpretation_payload.get("comparison_records")
    if isinstance(comparison_records, list):
        for item in comparison_records:
            if not isinstance(item, dict):
                continue
            status = str(item.get("status") or "").lower()
            name = str(item.get("name") or "comparison")
            lane = str(item.get("lane") or "comparison")
            if status == "missing":
                candidates.append(
                    build_candidate(
                        title=f"{name.replace('_', ' ').title()} missing-result follow-up",
                        category="missing_result_family",
                        local_basis_summary=f"{lane} shows that {name} is still missing from the current evidence set.",
                        source_evidence=[lane, name, status],
                        reference_titles=reference_titles,
                        broad_first_pass_search_used=broad_first_pass_search_used,
                    )
                )
            elif status == "compared":
                candidates.append(
                    build_candidate(
                        title=f"{name.replace('_', ' ').title()} reference comparison",
                        category="comparison_to_reference",
                        local_basis_summary=f"{lane} already compares {name} and can be extended into a discussion direction.",
                        source_evidence=[lane, name, status],
                        reference_titles=reference_titles,
                        broad_first_pass_search_used=broad_first_pass_search_used,
                    )
                )

    anomalies = interpretation_payload.get("anomalies")
    if isinstance(anomalies, list):
        for raw in anomalies:
            text = str(raw).strip()
            if not text:
                continue
            candidates.append(
                build_candidate(
                    title=f"Anomaly follow-up: {text.split('.')[0]}",
                    category="anomaly_explanation",
                    local_basis_summary=text,
                    source_evidence=[text],
                    reference_titles=reference_titles,
                    broad_first_pass_search_used=broad_first_pass_search_used,
                )
            )

    completeness_checks = interpretation_payload.get("completeness_checks")
    if isinstance(completeness_checks, list):
        for raw in completeness_checks:
            text = str(raw).strip()
            if not text:
                continue
            candidates.append(
                build_candidate(
                    title=f"Completeness gap: {text.split('.')[0]}",
                    category="missing_result_family",
                    local_basis_summary=text,
                    source_evidence=[text],
                    reference_titles=reference_titles,
                    broad_first_pass_search_used=broad_first_pass_search_used,
                )
            )

    unresolved = interpretation_payload.get("unresolved")
    if isinstance(unresolved, list):
        for raw in unresolved:
            text = str(raw).strip()
            if not text:
                continue
            needs_second_pass = "second-pass" in text.lower() or "weak" in text.lower()
            candidates.append(
                build_candidate(
                    title=f"Open follow-up: {text.split('.')[0]}",
                    category="open_followup",
                    local_basis_summary=text,
                    source_evidence=[text],
                    reference_titles=reference_titles,
                    broad_first_pass_search_used=broad_first_pass_search_used,
                    needs_second_pass=needs_second_pass,
                )
            )

    for memory_item in memory_ideas:
        title = str(memory_item.get("title") or memory_item.get("idea_id") or "Prior idea")
        summary = str(memory_item.get("outside_lookup_summary") or "Prior experiment memory suggests a reusable analogy.")
        candidates.append(
            build_candidate(
                title=title,
                category="memory_reuse",
                local_basis_summary=summary,
                source_evidence=[title],
                reference_titles=reference_titles,
                broad_first_pass_search_used=False,
                reuse_status="reused",
                memory_analogy_notes=[summary],
            )
        )

    return dedupe_candidates(candidates)


def main() -> int:
    args = build_parser().parse_args()

    results_path = Path(args.results_interpretation_json)
    if not results_path.exists():
        raise SystemExit(f"results-interpretation-json is required and must exist: {results_path}")

    idea_gists_path = Path(args.idea_gists)
    if not idea_gists_path.exists():
        raise SystemExit(f"idea-gists is required and must exist: {idea_gists_path}")

    reference_titles = load_reference_titles(args.reference_report)
    memory_root = Path(args.memory_root)
    memory_dir = memory_root / args.experiment_safe_name
    permanent_memory_exists = memory_dir.exists() and any(memory_dir.iterdir())
    broad_first_pass_search_used = should_run_broad_first_pass(permanent_memory_exists)

    interpretation_payload = read_json(results_path)
    if not isinstance(interpretation_payload, dict):
        raise SystemExit(f"Expected JSON object at {results_path}")

    memory_ideas = load_memory_ideas(memory_dir)
    idea_gists_text = read_text_if_exists(idea_gists_path)
    if idea_gists_text and not memory_ideas:
        interpretation_payload.setdefault("unresolved", [])
        if isinstance(interpretation_payload["unresolved"], list):
            interpretation_payload["unresolved"].append(
                "Idea gists suggest analogical comparison directions for this experiment."
            )

    candidates = build_candidates(
        interpretation_payload,
        reference_titles=reference_titles,
        broad_first_pass_search_used=broad_first_pass_search_used,
        memory_ideas=memory_ideas,
    )

    unresolved_lines: list[str] = []
    raw_unresolved = interpretation_payload.get("unresolved")
    if isinstance(raw_unresolved, list):
        unresolved_lines.extend(str(item) for item in raw_unresolved if str(item).strip())
    if len(candidates) < 5:
        unresolved_lines.append("Fewer than 5 viable discussion ideas were available from the current evidence.")

    payload = {
        "experiment_name": args.experiment_name,
        "experiment_safe_name": args.experiment_safe_name,
        "candidate_count": len(candidates),
        "permanent_memory_exists": permanent_memory_exists,
        "broad_first_pass_search_used": broad_first_pass_search_used,
        "discussion_ideas": candidates,
        "unresolved": unresolved_lines,
    }

    write_json(Path(args.output_json), payload)
    write_text(Path(args.output_markdown), render_discussion_ideas_markdown(payload))

    synthesis_payload = {
        "candidate_count": len(candidates),
        "approval_mode": "synthesis_judgment",
        "discussion_ideas": candidates,
    }
    write_json(Path(args.output_synthesis_json), synthesis_payload)
    write_text(Path(args.output_synthesis_markdown), render_synthesis_markdown(synthesis_payload))
    merge_into_memory_dir(memory_dir, {"discussion_ideas": candidates})

    if unresolved_lines:
        write_text(Path(args.output_unresolved), render_unresolved_markdown(unresolved_lines))
    else:
        write_text(Path(args.output_unresolved), render_unresolved_markdown(["No unresolved discussion-idea gaps."]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
