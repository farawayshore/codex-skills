#!/usr/bin/env python3
"""Build a first-pass Markdown draft for course-lab data transfer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import pretty_experiment_name, write_text


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a Markdown transfer draft from a prepared review bundle.",
    )
    parser.add_argument("--bundle-json", required=True, help="Path to transfer_bundle.json")
    parser.add_argument("--experiment-safe-name", required=True, help="Experiment-safe name for the title")
    parser.add_argument("--output-markdown", required=True, help="Output Markdown file")
    return parser.parse_args(argv)


def read_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Expected bundle JSON object: {path}")
    return payload


def render_pdf_sections(manifest: dict[str, Any]) -> list[str]:
    lines = ["## Method Order", ""]
    lines.append("1. Read the rendered page images first. Do not start from MinerU Markdown or OCR.")
    mineru_path = manifest.get("mineru_markdown_path")
    if mineru_path:
        lines.append(f"2. Compare the vision-first reading against `{mineru_path}`.")
    else:
        lines.append("2. Corresponding MinerU Markdown is still missing. Run `$mineru-pdf-markdown` before finalizing the transfer.")
    pdf_text_path = manifest.get("pdf_text_path")
    if pdf_text_path:
        lines.append(f"3. If the first two readings disagree or confidence stays low, compare them against `{pdf_text_path}`.")
    lines.extend(["", "## Source Summary", ""])
    lines.append(f"- Original PDF: `{manifest['source_path']}`")
    if mineru_path:
        lines.append(f"- MinerU Markdown: `{mineru_path}`")
    if pdf_text_path:
        lines.append(f"- Local PDF-to-text artifact: `{pdf_text_path}`")
    lines.append("")

    page_images = manifest.get("page_images") or []
    for index, image_path in enumerate(page_images, start=1):
        lines.extend(
            [
                f"## Page {index}",
                "",
                f"- Review image: `{image_path}`",
                "- Vision-first transcription:",
                "- MinerU comparison:",
                "- PDF-to-text comparison:",
                "- Final transferred content:",
                "- Confidence / ambiguity:",
                "",
            ]
        )
    return lines


def render_image_sections(manifest: dict[str, Any]) -> list[str]:
    image_paths = manifest.get("page_images") or []
    lines = [
        "## Method Order",
        "",
        "1. Read the source image first.",
        "2. Transcribe from the image before adding any interpretation.",
        "3. Keep visible uncertainty notes where handwriting or numbers remain weak.",
        "",
        "## Source Summary",
        "",
        f"- Source image: `{manifest['source_path']}`",
        "",
    ]
    for index, image_path in enumerate(image_paths, start=1):
        label = f"Image {index}" if len(image_paths) > 1 else "Image"
        lines.extend(
            [
                f"## {label}",
                "",
                f"- Review image: `{image_path}`",
                "- Vision-first transcription:",
                "- Final transferred content:",
                "- Confidence / ambiguity:",
                "",
            ]
        )
    return lines


def render_direct_sections(manifest: dict[str, Any]) -> list[str]:
    lines = [
        "## Method Order",
        "",
        "1. Read the direct source artifact first.",
        "2. Transfer the values or notes without adding calculations or interpretation.",
        "3. Keep visible uncertainty notes for missing cells, weak labels, or unclear units.",
        "",
        "## Source Summary",
        "",
        f"- Source file: `{manifest['source_path']}`",
    ]
    preview_path = manifest.get("preview_markdown_path")
    if preview_path:
        lines.append(f"- Preview artifact: `{preview_path}`")
    lines.extend(
        [
            "",
            "## Direct Transfer",
            "",
            "- Final transferred content:",
            "- Confidence / ambiguity:",
            "",
        ]
    )
    return lines


def render_picture_cross_check_sections(manifest: dict[str, Any]) -> list[str]:
    evidence = manifest.get("picture_result_evidence") or []
    if not evidence:
        return []

    lines = [
        "## Picture-Result Cross-Check",
        "",
        "Use vision on the matched picture-result evidence before final judgment.",
        "If a transferred phenomenon description is not visibly supported by the relevant picture, downgrade it to an uncertainty note or ask the user instead of keeping it as final wording.",
        "",
    ]

    for index, entry in enumerate(evidence, start=1):
        lines.append(f"### Picture Result {index}")
        lines.append("")
        lines.append(f"- Evidence source: `{entry['source_path']}`")
        for image_path in entry.get("review_image_paths") or []:
            lines.append(f"- Review image: `{image_path}`")
        lines.extend(
            [
                "- Which transferred phenomenon is being checked?",
                "- Does the transferred phenomenon really appear in this picture?",
                "- Keep / revise / question:",
                "- Confidence / mismatch note:",
                "",
            ]
        )
    return lines


def build_transfer_draft(manifest: dict[str, Any], experiment_safe_name: str) -> str:
    title = pretty_experiment_name(experiment_safe_name)
    lines = [f"# {title} Raw-Data Transfer", ""]

    source_type = str(manifest.get("source_type") or "unknown")
    if source_type == "pdf":
        lines.extend(render_pdf_sections(manifest))
    elif source_type == "image":
        lines.extend(render_image_sections(manifest))
    else:
        lines.extend(render_direct_sections(manifest))
    lines.extend(render_picture_cross_check_sections(manifest))

    notes = manifest.get("notes") or []
    if notes:
        lines.extend(["## Bundle Notes", ""])
        for note in notes:
            lines.append(f"- {note}")
        lines.append("")

    lines.extend(
        [
            "## Bilingual Observation Notes",
            "",
            "- Keep the original Chinese note first.",
            "- Add the English translation immediately after the original note.",
            "- If part of the note is uncertain, preserve the visible text and mark the uncertainty locally.",
            "",
            "## Proofread Checkpoint",
            "",
            "Please proofread this transferred Markdown before uncertainty analysis, anomaly judgments, or report drafting continue.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = read_manifest(Path(args.bundle_json).expanduser().resolve())
    output_path = Path(args.output_markdown).expanduser().resolve()
    write_text(output_path, build_transfer_draft(manifest, args.experiment_safe_name))
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
