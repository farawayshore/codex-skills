#!/usr/bin/env python3
"""Standalone final compile/QC orchestrator for course lab reports."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from common import copy_if_needed, read_json, run_command, write_json, write_text
from reference_procedure_compare import compare_reference_procedure_coverage


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_BUILD_ASSET = SKILL_DIR / "assets" / "build.sh"
DEFAULT_REPORT_QC = SCRIPT_DIR / "report_qc.py"
MAX_PDF_BYTES = 20 * 1024 * 1024
PAGE_WARN_MIN = 20
PAGE_WARN_MAX = 30
BUILD_LAYOUT_PATTERNS = [
    re.compile(r"Overfull \\\\+hbox .*", re.IGNORECASE),
    re.compile(r"Overfull \\\\+vbox .*", re.IGNORECASE),
    re.compile(r"Float too large for page .*", re.IGNORECASE),
]


def count_pdf_pages(pdf_path: Path) -> int | None:
    try:
        from pypdf import PdfReader  # type: ignore

        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        pass

    try:
        from PyPDF2 import PdfReader  # type: ignore

        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        pass

    try:
        data = pdf_path.read_bytes()
    except Exception:
        return None

    matches = re.findall(rb"/Type\s*/Page(?!s)\b", data)
    return len(matches) or None


def extract_build_layout_issues(*, build_stdout: str, build_stderr: str) -> list[str]:
    issues: list[str] = []
    seen: set[str] = set()
    for raw_line in (build_stdout + "\n" + build_stderr).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        for pattern in BUILD_LAYOUT_PATTERNS:
            if not pattern.search(line):
                continue
            if line not in seen:
                seen.add(line)
                issues.append(line)
            break
    return issues


def build_summary_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Final QC Summary",
        "",
        f"- Overall pass: `{summary['overall_pass']}`",
        f"- Build pass: `{summary['build_pass']}`",
        f"- QC pass: `{summary['qc_pass']}`",
        f"- Build script status: `{summary['build_script_status']}`",
        f"- PDF path: `{summary['pdf_path']}`",
        f"- PDF exists: `{summary['pdf_exists']}`",
        f"- PDF size bytes: `{summary['pdf_size_bytes']}`",
        f"- PDF size ok: `{summary['pdf_size_ok']}`",
        f"- PDF page count: `{summary['pdf_page_count']}`",
        f"- Page count warning: `{summary['page_count_warning']}`",
        f"- Preferred page band: `{PAGE_WARN_MIN}-{PAGE_WARN_MAX}`",
        "",
    ]

    qc_summary = summary.get("qc_summary")
    if isinstance(qc_summary, dict):
        lines.extend(
            [
                "## QC Snapshot",
                "",
                f"- Covered steps: {qc_summary.get('covered_steps')} / {qc_summary.get('total_steps')}",
                f"- Forbidden hits: {len(qc_summary.get('forbidden_hits', []))}",
                f"- Irrelevant hits: {len(qc_summary.get('irrelevant_hits', []))}",
                f"- Discussion issues: {len(qc_summary.get('discussion_issues', []))}",
                f"- Table layout issues: {len(qc_summary.get('table_layout_issues', []))}",
                f"- Build layout issues: {len(summary.get('build_layout_issues', []))}",
                "",
            ]
        )

    comparison_summary = summary.get("reference_procedure_comparison")
    if isinstance(comparison_summary, dict) and comparison_summary.get("enabled"):
        lines.extend(
            [
                "## Reference Procedure Comparison",
                "",
                f"- Selection status: `{comparison_summary.get('selection_status')}`",
                f"- Pass: `{summary.get('reference_procedure_comparison_pass')}`",
                f"- Blocked: `{summary.get('reference_procedure_comparison_blocked')}`",
                f"- Missing structure items: {len(comparison_summary.get('missing_structure_items', []))}",
                f"- Missing content items: {len(comparison_summary.get('missing_content_items', []))}",
                f"- Declared unresolved items: {len(comparison_summary.get('declared_unresolved_items', []))}",
                f"- Suspected data-lack items: {len(comparison_summary.get('data_lack_suspected_items', []))}",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def build_unresolved_markdown(summary: dict[str, object]) -> str:
    unresolved: list[str] = list(summary.get("unresolved_items", []))
    lines = ["# Final QC Unresolved", ""]
    if unresolved:
        for item in unresolved:
            lines.append(f"- {item}")
    else:
        lines.append("- No unresolved hard failures or warnings remain.")
    lines.append("")
    return "\n".join(lines)


def run_local_report_qc(
    *,
    main_tex: Path,
    procedures: Path,
    evidence_plan: Path | None,
    discussion_candidates: Path | None,
    body_scaffold: Path | None,
    workspace: Path,
) -> tuple[bool, dict[str, object], str, str]:
    temp_markdown = workspace / ".finalize_qc_report_qc.md"
    temp_json = workspace / ".finalize_qc_report_qc.json"
    args = [
        sys.executable,
        str(DEFAULT_REPORT_QC),
        "--tex",
        str(main_tex),
        "--procedures",
        str(procedures),
        "--output-markdown",
        str(temp_markdown),
        "--output-json",
        str(temp_json),
    ]
    if evidence_plan:
        args.extend(["--evidence-plan", str(evidence_plan)])
    if discussion_candidates:
        args.extend(["--discussion-candidates", str(discussion_candidates)])
    if body_scaffold:
        args.extend(["--body-scaffold", str(body_scaffold)])

    result = run_command(args, workspace)
    summary = read_json(temp_json)
    if not isinstance(summary, dict):
        summary = {}

    try:
        temp_markdown.unlink(missing_ok=True)
    except TypeError:
        if temp_markdown.exists():
            temp_markdown.unlink()
    try:
        temp_json.unlink(missing_ok=True)
    except TypeError:
        if temp_json.exists():
            temp_json.unlink()

    return result.returncode == 0, summary, result.stdout, result.stderr


def run_finalize_qc(
    *,
    main_tex: Path,
    procedures: Path,
    output_summary_json: Path,
    output_summary_markdown: Path,
    output_unresolved: Path,
    evidence_plan: Path | None = None,
    discussion_candidates: Path | None = None,
    discovery_json: Path | None = None,
    build_asset: Path = DEFAULT_BUILD_ASSET,
) -> dict[str, object]:
    workspace = main_tex.resolve().parent
    build_path = workspace / "build.sh"
    body_scaffold = workspace / "body_scaffold.json"
    build_script_status = "unchanged"
    if not build_path.exists():
        copy_if_needed(build_asset, build_path)
        build_script_status = "installed"
    elif copy_if_needed(build_asset, build_path):
        build_script_status = "refreshed"

    build_result = run_command(["bash", str(build_path)], workspace)
    pdf_path = workspace / f"{main_tex.stem}.pdf"
    pdf_exists = pdf_path.exists()
    pdf_size_bytes = pdf_path.stat().st_size if pdf_exists else 0
    pdf_size_ok = pdf_exists and pdf_size_bytes <= MAX_PDF_BYTES

    qc_pass = False
    qc_summary: dict[str, object] = {}
    qc_stdout = ""
    qc_stderr = ""
    build_layout_issues = extract_build_layout_issues(build_stdout=build_result.stdout, build_stderr=build_result.stderr)
    if build_result.returncode == 0 and pdf_exists:
        qc_pass, qc_summary, qc_stdout, qc_stderr = run_local_report_qc(
            main_tex=main_tex,
            procedures=procedures,
            evidence_plan=evidence_plan,
            discussion_candidates=discussion_candidates,
            body_scaffold=body_scaffold if body_scaffold.exists() else None,
            workspace=workspace,
        )
        if build_layout_issues:
            qc_pass = False

    pdf_page_count = count_pdf_pages(pdf_path) if pdf_exists else None
    page_count_warning = (
        pdf_page_count is not None and (pdf_page_count < PAGE_WARN_MIN or pdf_page_count > PAGE_WARN_MAX)
    )

    comparison_summary: dict[str, object] = {
        "enabled": False,
        "selection_status": "not_requested",
        "pass": False,
        "blocked": False,
        "blocked_reference_decode_items": [],
        "missing_structure_items": [],
        "missing_content_items": [],
        "declared_unresolved_items": [],
        "data_lack_suspected_items": [],
        "recommended_reroutes": [],
    }

    required_paths = [
        workspace / "principle_ownership.json",
        workspace / "final_staging_summary.json",
        workspace / "appendix_code_manifest.json",
        workspace / "picture_evidence_plan.json",
    ]
    missing_required = [path.name for path in required_paths if not path.exists()]

    principle_has_figures = (workspace / "principle_figures.json").exists() and (workspace / "principle_figures.tex").exists()
    principle_is_unresolved = (workspace / "principle_unresolved.md").exists()
    if not principle_has_figures and not principle_is_unresolved:
        missing_required.extend(["principle_figures.json", "principle_figures.tex or principle_unresolved.md"])

    unresolved_items: list[str] = []
    for item in missing_required:
        unresolved_items.append(f"Required workflow artifact is missing: {item}")
    if build_result.returncode != 0:
        unresolved_items.append("Compile failed. Inspect the captured build stdout and stderr before rerunning final QC.")
    if build_result.returncode == 0 and not pdf_exists:
        unresolved_items.append("Compile completed without producing the expected PDF output.")
    if build_result.returncode == 0 and pdf_exists and not qc_pass:
        unresolved_items.append("QC failed. Review the QC summary and fix the report before handoff.")
    if build_layout_issues:
        unresolved_items.append(
            "Build output reported layout diagnostics that indicate the compiled PDF is not visually safe: "
            + "; ".join(build_layout_issues[:3])
        )
    if build_result.returncode == 0 and pdf_exists and not qc_pass and qc_stderr.strip():
        stderr_lines = [line.strip() for line in qc_stderr.splitlines() if line.strip()]
        if stderr_lines:
            condensed_stderr = " | ".join(stderr_lines[-3:])
        else:
            condensed_stderr = qc_stderr.strip()
        unresolved_items.append("Inner QC stderr: " + condensed_stderr[:1000])
    if pdf_exists and not pdf_size_ok:
        unresolved_items.append(
            f"PDF size exceeds 20 MB ({pdf_size_bytes} bytes). Hand the image-compression follow-up to `$compress-png` before the next rerun."
        )
    if page_count_warning:
        unresolved_items.append(
            f"Compiled PDF page count is {pdf_page_count}, outside the preferred {PAGE_WARN_MIN}-{PAGE_WARN_MAX} page band. This is a warning, not a hard failure."
        )

    overall_pass = build_result.returncode == 0 and pdf_exists and qc_pass and pdf_size_ok and not missing_required
    if discovery_json and build_result.returncode == 0 and pdf_exists and qc_pass and pdf_size_ok and not build_layout_issues:
        comparison_summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery_json)
        if (
            comparison_summary["blocked"]
            or comparison_summary["missing_structure_items"]
            or comparison_summary["missing_content_items"]
            or comparison_summary["data_lack_suspected_items"]
        ):
            overall_pass = False
        if comparison_summary["blocked"]:
            unresolved_items.append("Reference procedure comparison blocked. Review the reroute targets before rerunning final QC.")
        if comparison_summary["missing_structure_items"] or comparison_summary["missing_content_items"]:
            unresolved_items.append("Reference procedure comparison found missing structure or content relative to same-experiment references.")
        if comparison_summary["data_lack_suspected_items"]:
            unresolved_items.append("Reference procedure comparison warning: unresolved data-lack lanes still need an explicit visible TBD or NeedsInput marker.")
        if comparison_summary["declared_unresolved_items"]:
            unresolved_items.append("Reference procedure comparison warning: declared unresolved lanes remain visible in the report and should stay visible in the final handoff.")
        if comparison_summary["enabled"] and not comparison_summary["pass"]:
            unresolved_items.append("Reference procedure comparison produced parent-facing reroutes that must be handled before completion.")

    summary: dict[str, object] = {
        "main_tex": str(main_tex),
        "procedures": str(procedures),
        "build_script_status": build_script_status,
        "build_pass": build_result.returncode == 0 and pdf_exists,
        "build_returncode": build_result.returncode,
        "build_stdout": build_result.stdout,
        "build_stderr": build_result.stderr,
        "qc_pass": qc_pass,
        "qc_summary": qc_summary,
        "qc_stdout": qc_stdout,
        "qc_stderr": qc_stderr,
        "build_layout_issues": build_layout_issues,
        "pdf_path": str(pdf_path),
        "pdf_exists": pdf_exists,
        "pdf_size_bytes": pdf_size_bytes,
        "pdf_size_ok": pdf_size_ok,
        "pdf_page_count": pdf_page_count,
        "page_count_warning": page_count_warning,
        "preferred_page_band": [PAGE_WARN_MIN, PAGE_WARN_MAX],
        "reference_procedure_comparison_pass": comparison_summary["pass"],
        "reference_procedure_comparison_blocked": comparison_summary["blocked"],
        "reference_procedure_comparison": comparison_summary,
        "recommended_reroutes": comparison_summary["recommended_reroutes"],
        "missing_required_artifacts": missing_required,
        "overall_pass": overall_pass,
        "unresolved_items": unresolved_items,
    }

    write_json(output_summary_json, summary)
    write_text(output_summary_markdown, build_summary_markdown(summary))
    write_text(output_unresolved, build_unresolved_markdown(summary))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main-tex", required=True)
    parser.add_argument("--procedures", required=True)
    parser.add_argument("--evidence-plan")
    parser.add_argument("--discussion-candidates")
    parser.add_argument("--discovery-json")
    parser.add_argument("--output-summary-json", required=True)
    parser.add_argument("--output-summary-markdown", required=True)
    parser.add_argument("--output-unresolved", required=True)
    parser.add_argument("--build-asset")
    args = parser.parse_args()

    summary = run_finalize_qc(
        main_tex=Path(args.main_tex),
        procedures=Path(args.procedures),
        evidence_plan=Path(args.evidence_plan) if args.evidence_plan else None,
        discussion_candidates=Path(args.discussion_candidates) if args.discussion_candidates else None,
        discovery_json=Path(args.discovery_json) if args.discovery_json else None,
        output_summary_json=Path(args.output_summary_json),
        output_summary_markdown=Path(args.output_summary_markdown),
        output_unresolved=Path(args.output_unresolved),
        build_asset=Path(args.build_asset) if args.build_asset else DEFAULT_BUILD_ASSET,
    )

    print(json.dumps({"overall_pass": summary["overall_pass"], "summary_json": args.output_summary_json}, ensure_ascii=False))
    return 0 if summary["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
