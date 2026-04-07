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


NOVELTY_KEYWORDS = (
    "mathematica",
    "python",
    "code",
    "script",
    "extract",
    "extraction",
    "brightness",
    "intensity",
    "image",
    "images",
    "ccd",
    "digitize",
    "digitization",
    "digitisation",
    "fit",
    "fitting",
    "profile",
    "profiles",
    "grayscale",
    "grey scale",
    "quantify",
    "quantification",
    "radial",
)

SECOND_PASS_KEYWORDS = ("second-pass", "second pass", "weak", "tentative")


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


def confidence_and_posture(*, second_round: bool, reuse_status: str) -> tuple[str, str]:
    if reuse_status == "reused":
        return ("medium", "likely indicates")
    if second_round:
        return ("low", "may indicate")
    return ("medium", "likely indicates")


def targeted_round_count(*, needs_second_pass: bool) -> int:
    return 2 if needs_second_pass else 1


def contains_novelty_signal(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in NOVELTY_KEYWORDS)


def needs_second_pass(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in SECOND_PASS_KEYWORDS)


def infer_title(text: str, *, fallback: str) -> str:
    lowered = text.lower()
    if "digit" in lowered or "digitization" in lowered or ("fit" in lowered and "radial" in lowered):
        return "Interference image digitization and fitting follow-up"
    if "extract" in lowered or "brightness" in lowered or "quantify" in lowered or "profile" in lowered:
        return "Interference brightness extraction follow-up"
    if "mathematica" in lowered:
        return "Mathematica extra-analysis follow-up"
    if "python" in lowered:
        return "Python extra-analysis follow-up"
    if "image" in lowered or "ccd" in lowered:
        return "Image-derived evidence extraction follow-up"
    return fallback


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
    needs_second_pass_lookup: bool = False,
) -> dict[str, object]:
    idea_id = safe_label(title, default="discussion-idea")
    round_count = targeted_round_count(needs_second_pass=needs_second_pass_lookup)
    confidence, posture = confidence_and_posture(second_round=needs_second_pass_lookup, reuse_status=reuse_status)
    lookup_summary = (
        "First targeted lookup stayed weak, so a second targeted lookup kept the idea tentative."
        if round_count == 2
        else "One targeted lookup round sharpened the idea against the current evidence and references."
    )
    if broad_first_pass_search_used:
        lookup_summary = "Broad first-pass search widened this novelty-qualified direction. " + lookup_summary

    lowered = local_basis_summary.lower()
    suggests_modeling = "model" in lowered or "fit" in lowered

    return {
        "idea_id": idea_id,
        "title": title,
        "category": category,
        "source_evidence": source_evidence,
        "reference_report_support": reference_titles,
        "memory_analogy_notes": memory_analogy_notes or [],
        "local_basis_summary": local_basis_summary,
        "beyond_handout": True,
        "suggests_modeling": suggests_modeling,
        "suggests_extraction_or_analysis_code": True,
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


def novelty_seed_from_unresolved(text: str) -> dict[str, object] | None:
    if not contains_novelty_signal(text):
        return None
    return {
        "title": infer_title(text, fallback=f"Open follow-up: {text.split('.')[0]}"),
        "category": "extra_analysis_extension",
        "local_basis_summary": text,
        "source_evidence": [text],
        "reuse_status": "new",
        "needs_second_pass_lookup": needs_second_pass(text),
        "memory_analogy_notes": [],
    }


def novelty_seed_from_memory(memory_item: dict[str, object]) -> dict[str, object] | None:
    title = str(memory_item.get("title") or memory_item.get("idea_id") or "Prior idea").strip()
    summary = str(
        memory_item.get("outside_lookup_summary") or "Prior experiment memory suggests a reusable novelty direction."
    ).strip()
    combined = f"{title} {summary}".strip()
    if not contains_novelty_signal(combined):
        return None
    return {
        "title": title,
        "category": "memory_reuse",
        "local_basis_summary": summary,
        "source_evidence": [title, summary],
        "reuse_status": "reused",
        "needs_second_pass_lookup": needs_second_pass(combined),
        "memory_analogy_notes": [summary],
    }


def build_candidates(
    interpretation_payload: dict[str, object],
    *,
    reference_titles: list[str],
    permanent_memory_exists: bool,
    memory_ideas: list[dict[str, object]],
) -> tuple[list[dict[str, object]], bool]:
    seeds: list[dict[str, object]] = []

    unresolved = interpretation_payload.get("unresolved")
    if isinstance(unresolved, list):
        for raw in unresolved:
            text = str(raw).strip()
            if not text:
                continue
            seed = novelty_seed_from_unresolved(text)
            if seed:
                seeds.append(seed)

    for memory_item in memory_ideas:
        seed = novelty_seed_from_memory(memory_item)
        if seed:
            seeds.append(seed)

    has_new_novelty_seed = any(seed.get("reuse_status") != "reused" for seed in seeds)
    broad_first_pass_search_used = has_new_novelty_seed and not permanent_memory_exists

    candidates = [
        build_candidate(
            title=str(seed["title"]),
            category=str(seed["category"]),
            local_basis_summary=str(seed["local_basis_summary"]),
            source_evidence=[str(part) for part in seed["source_evidence"]],
            reference_titles=reference_titles,
            broad_first_pass_search_used=(
                broad_first_pass_search_used if str(seed.get("reuse_status")) != "reused" else False
            ),
            reuse_status=str(seed["reuse_status"]),
            memory_analogy_notes=[str(part) for part in seed.get("memory_analogy_notes", [])],
            needs_second_pass_lookup=bool(seed["needs_second_pass_lookup"]),
        )
        for seed in seeds
    ]

    return dedupe_candidates(candidates), broad_first_pass_search_used


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

    interpretation_payload = read_json(results_path)
    if not isinstance(interpretation_payload, dict):
        raise SystemExit(f"Expected JSON object at {results_path}")

    memory_ideas = load_memory_ideas(memory_dir)
    read_text_if_exists(idea_gists_path)

    candidates, broad_first_pass_search_used = build_candidates(
        interpretation_payload,
        reference_titles=reference_titles,
        permanent_memory_exists=permanent_memory_exists,
        memory_ideas=memory_ideas,
    )

    unresolved_lines: list[str] = []
    raw_unresolved = interpretation_payload.get("unresolved")
    if isinstance(raw_unresolved, list):
        unresolved_lines.extend(str(item) for item in raw_unresolved if str(item).strip())
    if not candidates:
        unresolved_lines.append("No non-routine discussion ideas were available from the current evidence.")

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
