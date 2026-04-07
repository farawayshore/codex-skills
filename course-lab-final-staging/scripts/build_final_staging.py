#!/usr/bin/env python3
"""Build the late-stage non-figure report draft from staged lab artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from collect_staging_inputs import collect_staging_inputs
from common import replace_owned_heading, resolve_heading_target, scaffold_block_order, write_json, write_text
from render_appendix_materials import render_appendix_materials
from render_catalog_and_timing import render_catalog_and_timing
from render_results_sections import render_results_sections


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main-tex", required=True)
    parser.add_argument("--body-scaffold-json", required=True)
    parser.add_argument("--procedures-markdown", required=True)
    parser.add_argument("--processed-data-json", required=True)
    parser.add_argument("--results-interpretation-json", required=True)
    parser.add_argument("--discussion-synthesis-json", required=True)
    parser.add_argument("--output-summary-json", required=True)
    parser.add_argument("--output-summary-markdown", required=True)
    parser.add_argument("--output-unresolved", required=True)
    parser.add_argument("--output-appendix-manifest", required=True)
    parser.add_argument("--processed-data-markdown")
    parser.add_argument("--results-interpretation-markdown")
    parser.add_argument("--discussion-synthesis-markdown")
    parser.add_argument("--plots-manifest")
    parser.add_argument("--modeling-result")
    parser.add_argument("--references-json")
    parser.add_argument("--appendix-code", action="append")
    parser.add_argument("--appendix-data", action="append")
    parser.add_argument("--calculation-details-manifest")
    parser.add_argument("--skip-main-tex-mutation", action="store_true")
    return parser


def summary_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Final Staging Summary",
        "",
        f"- Length goal: {payload.get('length_goal', '')}",
        "",
        "## Written Sections",
        "",
    ]

    written_sections = list(payload.get("written_sections", []))
    if written_sections:
        for section in written_sections:
            lines.append(f"- {section}")
    else:
        lines.append("- None")

    lines.extend(["", "## Case Records", ""])
    for case in payload.get("case_records", []):
        if not isinstance(case, dict):
            continue
        lines.append(
            f"- {case.get('title') or case.get('case_id')}: "
            f"{case.get('direct_result_count', 0)} direct, {case.get('indirect_result_count', 0)} indirect"
        )

    lines.extend(["", "## Appendix Entries", ""])
    appendix_entries = list(payload.get("appendix_entries", []))
    if appendix_entries:
        for entry in appendix_entries:
            if not isinstance(entry, dict):
                continue
            lines.append(f"- {entry.get('label')}: {entry.get('role')}")
    else:
        lines.append("- None")

    lines.extend(["", "## Comparison Cases", ""])
    comparison_cases = list(payload.get("comparison_cases", []))
    if comparison_cases:
        for case in comparison_cases:
            if not isinstance(case, dict):
                continue
            case_label = str(case.get("title") or case.get("case_id") or "Case").strip()
            observed_path = str(case.get("observed_asset_path") or "").strip()
            comparison_path = str(case.get("comparison_asset_path") or "").strip()
            lines.append(f"- {case_label}: observed={observed_path or 'None'}, comparison={comparison_path or 'None'}")
    else:
        lines.append("- None")

    lines.extend(["", "## Literature References", ""])
    literature_references = list(payload.get("literature_references", []))
    if literature_references:
        for entry in literature_references:
            if not isinstance(entry, dict):
                continue
            label = str(entry.get("label") or entry.get("name") or "Reference").strip()
            source = str(entry.get("source_title") or entry.get("source") or "").strip()
            lane = str(entry.get("lane") or "").strip()
            rendered = f"- {label}"
            if lane:
                rendered += f" [{lane}]"
            if source:
                rendered += f": {source}"
            lines.append(rendered)
    else:
        lines.append("- None")

    lines.extend(["", "## Unresolved", ""])
    unresolved = list(payload.get("unresolved") or [])
    if unresolved:
        for item in unresolved:
            lines.append(f"- {item}")
    else:
        lines.append("- None")

    return "\n".join(lines).rstrip() + "\n"


def dedupe_preserving_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        cleaned = item.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        deduped.append(cleaned)
    return deduped


def unresolved_markdown(items: list[str]) -> str:
    lines = ["# Final Staging Unresolved", ""]
    if items:
        for item in items:
            lines.append(f"- {item}")
    else:
        lines.append("- None")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    payload = collect_staging_inputs(args)
    rendered_sections = render_results_sections(payload)
    catalog_and_timing = render_catalog_and_timing(payload)
    block_order = scaffold_block_order(payload.get("body_scaffold"))
    staging_mode = ""
    if isinstance(payload.get("body_scaffold"), dict):
        staging_mode = str(payload["body_scaffold"].get("staging_mode") or "").strip()
    preserve_existing_draft = staging_mode == "summary_only_existing_draft"

    tex = str(payload["main_tex_text"])
    written_section_names: list[str] = []
    appendix = {"appendix_tex": "", "appendix_entries": [], "unresolved": []}
    unresolved = list(rendered_sections["unresolved"])
    preferred_block: str | None = None

    if not args.skip_main_tex_mutation:
        experimental_process_body = rendered_sections["written_sections"]["experimental_process"] + "\n" + catalog_and_timing
        tex, written_heading, preferred_block, was_written = replace_owned_heading(
            tex,
            bucket_name="process",
            exact_headings=("Experimental Process", "Experimental Phenomenon"),
            slug="experimental-process",
            new_body=experimental_process_body,
            block_order=block_order,
            preserve_if_unsafe=preserve_existing_draft,
        )
        if was_written:
            written_section_names.append(written_heading)
        elif preserve_existing_draft:
            unresolved.append(
                f"Preserved existing substantive {written_heading} section in summary_only_existing_draft mode."
            )

        tex, written_heading, preferred_block, was_written = replace_owned_heading(
            tex,
            bucket_name="results",
            exact_headings=("Results",),
            slug="results",
            new_body=str(rendered_sections["written_sections"]["results"]),
            preferred_block=preferred_block,
            block_order=block_order,
            preserve_if_unsafe=preserve_existing_draft,
        )
        if was_written:
            written_section_names.append(written_heading)
        elif preserve_existing_draft:
            unresolved.append(
                f"Preserved existing substantive {written_heading} section in summary_only_existing_draft mode."
            )

        tex, written_heading, preferred_block, was_written = replace_owned_heading(
            tex,
            bucket_name="discussion",
            exact_headings=("Experiment Discussion", "Experimental Discussion", "Discussion"),
            slug="discussion",
            new_body=str(rendered_sections["written_sections"]["discussion"]),
            preferred_block=preferred_block,
            block_order=block_order,
            preserve_if_unsafe=preserve_existing_draft,
        )
        if was_written:
            written_section_names.append(written_heading)
        elif preserve_existing_draft:
            unresolved.append(
                f"Preserved existing substantive {written_heading} section in summary_only_existing_draft mode."
            )

        appendix_target = resolve_heading_target(
            tex,
            bucket_name="appendix",
            exact_headings=("Appendix",),
            block_order=block_order,
        )
        appendix = render_appendix_materials(payload, top_level_heading=str(appendix_target["heading"]))
        unresolved.extend(list(appendix["unresolved"]))

        tex, written_heading, _, was_written = replace_owned_heading(
            tex,
            bucket_name="appendix",
            exact_headings=("Appendix",),
            slug="appendix",
            new_body=str(appendix["appendix_tex"]),
            block_order=block_order,
            preserve_if_unsafe=preserve_existing_draft,
        )
        if was_written:
            written_section_names.append(written_heading)
        elif preserve_existing_draft:
            unresolved.append(
                f"Preserved existing substantive {written_heading} section in summary_only_existing_draft mode."
            )

        main_tex_path = Path(args.main_tex)
        write_text(main_tex_path, tex)
    else:
        unresolved.append("main.tex mutation was skipped by CLI flag; existing draft preserved.")

    unresolved = dedupe_preserving_order(unresolved + list(payload["results_interpretation"].get("unresolved", [])) + list(payload["discussion_synthesis"].get("unresolved", [])))
    summary_payload = {
        "written_sections": written_section_names,
        "case_records": rendered_sections["case_records"],
        "comparison_cases": list(payload.get("comparison_cases") or []),
        "literature_references": list(payload.get("literature_references") or []),
        "appendix_entries": appendix["appendix_entries"],
        "unresolved": unresolved,
        "length_goal": "Favor substantive completeness toward a two-column 20-30 page final PDF after figure placement and QC compilation.",
    }

    write_json(Path(args.output_summary_json), summary_payload)
    write_text(Path(args.output_summary_markdown), summary_markdown(summary_payload))
    write_text(Path(args.output_unresolved), unresolved_markdown(unresolved))
    write_json(Path(args.output_appendix_manifest), {"appendix_entries": appendix["appendix_entries"]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
