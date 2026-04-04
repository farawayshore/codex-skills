#!/usr/bin/env python3
"""Prepare standalone review artifacts for course-lab raw-data transfer."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from common import (
    detect_source_type,
    read_delimited_preview,
    read_text_preview,
    read_workbook_preview,
    write_json,
    write_text,
)


PICTURE_RESULT_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare review artifacts for a raw-data source before course-lab transcription.",
    )
    parser.add_argument("--source", required=True, help="Path to the source file")
    parser.add_argument("--output-dir", required=True, help="Directory for the review bundle")
    parser.add_argument(
        "--mineru-markdown",
        help="Optional explicit path to the corresponding MinerU markdown file for a PDF source",
    )
    parser.add_argument(
        "--preview-rows",
        type=int,
        default=20,
        help="Maximum preview rows per direct-read source or worksheet (default: 20)",
    )
    parser.add_argument(
        "--discovery-json",
        help="Optional discovery manifest that may already point to matched picture-result files or directories",
    )
    parser.add_argument(
        "--picture-results-manifest",
        help="Optional staged picture-results manifest from course-lab-figure-evidence",
    )
    return parser.parse_args(argv)


def resolve_mineru_markdown(source: Path, explicit: str | None = None) -> Path | None:
    if explicit:
        candidate = Path(explicit).expanduser().resolve()
        return candidate if candidate.exists() else None

    stem = source.stem
    direct = source.parent / "pdf_markdown" / stem / f"{stem}.md"
    if direct.exists():
        return direct.resolve()

    root = source.parent / "pdf_markdown"
    if not root.exists():
        return None

    matches = sorted(
        path.resolve()
        for path in root.rglob(f"{stem}.md")
        if path.parent.name == stem
    )
    return matches[0] if matches else None


def run_command(command: list[str]) -> None:
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def render_pdf_pages(source: Path, pages_dir: Path) -> list[Path]:
    tool = shutil.which("pdftoppm")
    if not tool:
        raise RuntimeError("pdftoppm is required to render PDF pages for vision-first review.")

    pages_dir.mkdir(parents=True, exist_ok=True)
    prefix = pages_dir / "page"
    run_command([tool, "-png", str(source), str(prefix)])

    generated = sorted(pages_dir.glob("page-*.png"))
    renamed: list[Path] = []
    for index, path in enumerate(generated, start=1):
        target = pages_dir / f"page-{index:03d}.png"
        if path != target:
            path.rename(target)
        renamed.append(target.resolve())
    return renamed


def extract_pdf_text(source: Path, output_path: Path) -> tuple[Path, str]:
    tool = shutil.which("pdftotext")
    if tool:
        try:
            run_command([tool, "-layout", str(source), str(output_path)])
            if output_path.exists() and output_path.read_text(encoding="utf-8", errors="ignore").strip():
                return output_path.resolve(), "pdftotext"
        except (RuntimeError, subprocess.CalledProcessError):
            pass

    reader = PdfReader(str(source))
    text = "\n\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()
    write_text(output_path, text or "[No extractable text found with pypdf.]")
    return output_path.resolve(), "pypdf"


def build_direct_preview(source: Path, source_type: str, output_path: Path, preview_rows: int) -> tuple[Path | None, str | None]:
    if source_type == "csv":
        content = read_delimited_preview(source, delimiter=",", max_rows=preview_rows)
    elif source_type == "tsv":
        content = read_delimited_preview(source, delimiter="\t", max_rows=preview_rows)
    elif source_type in {"text", "markdown"}:
        content = read_text_preview(source)
    elif source_type == "spreadsheet":
        content, error = read_workbook_preview(source, max_rows=preview_rows)
        if error:
            return None, error
    else:
        return None, f"Unsupported direct preview source type: {source_type}"

    write_text(output_path, content)
    return output_path.resolve(), None


def read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def picture_paths_from_discovery(discovery_json: Path) -> list[Path]:
    payload = read_json_object(discovery_json)
    results: list[Path] = []

    for item in payload.get("picture_result_files") or []:
        if not isinstance(item, dict):
            continue
        raw_path = item.get("path")
        if not raw_path:
            continue
        path = Path(str(raw_path)).expanduser().resolve()
        if path.exists() and path.suffix.lower() in PICTURE_RESULT_SUFFIXES:
            results.append(path)

    if results:
        return dedupe_paths(results)

    for item in payload.get("picture_result_dirs") or []:
        if not isinstance(item, dict):
            continue
        raw_path = item.get("path")
        if not raw_path:
            continue
        path = Path(str(raw_path)).expanduser().resolve()
        if not path.is_dir():
            continue
        for child in sorted(path.rglob("*")):
            if child.is_file() and child.suffix.lower() in PICTURE_RESULT_SUFFIXES:
                results.append(child.resolve())
    return dedupe_paths(results)


def picture_paths_from_manifest(picture_results_manifest: Path) -> list[Path]:
    payload = read_json_object(picture_results_manifest)
    results: list[Path] = []
    for entry in payload.get("entries") or []:
        if not isinstance(entry, dict):
            continue
        raw_path = entry.get("copied_path") or entry.get("source_path")
        if not raw_path:
            continue
        path = Path(str(raw_path)).expanduser().resolve()
        if path.exists() and path.suffix.lower() in PICTURE_RESULT_SUFFIXES:
            results.append(path)
    return dedupe_paths(results)


def dedupe_paths(paths: list[Path]) -> list[Path]:
    ordered: dict[str, Path] = {}
    for path in paths:
        ordered.setdefault(str(path.resolve()), path.resolve())
    return list(ordered.values())


def build_picture_result_evidence(
    paths: list[Path],
    *,
    origin: str,
    output_dir: Path,
) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for index, path in enumerate(paths, start=1):
        entry: dict[str, Any] = {
            "source_path": str(path.resolve()),
            "origin": origin,
            "review_image_paths": [],
            "notes": [],
        }
        source_type = detect_source_type(path)
        if source_type == "pdf":
            review_dir = output_dir / "picture-result-review" / f"evidence-{index:03d}" / "pages"
            entry["review_image_paths"] = [str(item) for item in render_pdf_pages(path, review_dir)]
        elif source_type == "image":
            entry["review_image_paths"] = [str(path.resolve())]
        else:
            entry["notes"].append("Unsupported picture-result source type for vision review.")
        evidence.append(entry)
    return evidence


def prepare_bundle(
    *,
    source: Path,
    output_dir: Path,
    explicit_mineru_markdown: str | None = None,
    preview_rows: int = 20,
    discovery_json: Path | None = None,
    picture_results_manifest: Path | None = None,
) -> dict[str, Any]:
    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    output_dir.mkdir(parents=True, exist_ok=True)
    source_type = detect_source_type(source)
    manifest: dict[str, Any] = {
        "source_path": str(source.resolve()),
        "source_name": source.name,
        "source_type": source_type,
        "review_dir": str(output_dir.resolve()),
        "page_images": [],
        "pdf_text_path": None,
        "pdf_text_method": None,
        "mineru_markdown_path": None,
        "preview_markdown_path": None,
        "picture_result_evidence": [],
        "notes": [],
    }

    if source_type == "pdf":
        pages = render_pdf_pages(source, output_dir / "pages")
        pdf_text_path, pdf_text_method = extract_pdf_text(source, output_dir / f"{source.stem}.txt")
        mineru_markdown = resolve_mineru_markdown(source, explicit_mineru_markdown)
        manifest["page_images"] = [str(path) for path in pages]
        manifest["pdf_text_path"] = str(pdf_text_path)
        manifest["pdf_text_method"] = pdf_text_method
        manifest["mineru_markdown_path"] = str(mineru_markdown) if mineru_markdown else None
        if not mineru_markdown:
            manifest["notes"].append(
                "Corresponding MinerU markdown was not found. Invoke $mineru-pdf-markdown before the final comparison pass."
            )
    elif source_type == "image":
        manifest["page_images"] = [str(source.resolve())]
    elif source_type in {"csv", "tsv", "text", "markdown", "spreadsheet"}:
        preview_path, error = build_direct_preview(
            source,
            source_type,
            output_dir / f"{source.stem}_preview.md",
            preview_rows,
        )
        manifest["preview_markdown_path"] = str(preview_path) if preview_path else None
        if error:
            manifest["notes"].append(error)
    else:
        manifest["notes"].append("Unsupported source type. Inspect and transfer manually.")

    picture_paths: list[Path] = []
    if discovery_json is not None:
        picture_paths.extend(picture_paths_from_discovery(discovery_json))
    if picture_results_manifest is not None:
        picture_paths.extend(picture_paths_from_manifest(picture_results_manifest))
    picture_paths = dedupe_paths(picture_paths)
    if picture_paths:
        origin = "picture-results-manifest" if picture_results_manifest is not None else "discovery"
        manifest["picture_result_evidence"] = build_picture_result_evidence(
            picture_paths,
            origin=origin,
            output_dir=output_dir,
        )
        manifest["notes"].append(
            "Inspect the matched picture-result evidence with vision before treating a transferred phenomenon description as final."
        )

    write_json(output_dir / "transfer_bundle.json", manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source = Path(args.source).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    prepare_bundle(
        source=source,
        output_dir=output_dir,
        explicit_mineru_markdown=args.mineru_markdown,
        preview_rows=args.preview_rows,
        discovery_json=Path(args.discovery_json).expanduser().resolve() if args.discovery_json else None,
        picture_results_manifest=Path(args.picture_results_manifest).expanduser().resolve()
        if args.picture_results_manifest
        else None,
    )
    print(output_dir / "transfer_bundle.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
