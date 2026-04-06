#!/usr/bin/env python3
"""Copy signatory-page files into a report workspace and emit a grouped LaTeX snippet."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

from common import safe_label, write_json


SIGNATORY_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".pdf"}
SIGNATORY_PAGES_PER_ROW = 2
MAX_SIGNATORY_PAGES_PER_BLOCK = 4
SIGNATORY_SUBFIGURE_WIDTH = r"0.42\textwidth"
SIGNATORY_IMAGE_MAX_HEIGHT = r"0.33\textheight"


def subfigure_width() -> str:
    return SIGNATORY_SUBFIGURE_WIDTH


def subfigure_image_options() -> str:
    return rf"width=\linewidth,height={SIGNATORY_IMAGE_MAX_HEIGHT},keepaspectratio"


def build_subfigure_caption(path: Path) -> str:
    match = re.search(r"(\d+)$", path.stem)
    if not match:
        return ""
    return rf"Serial No.~{match.group(1)}"


def chunk_entries(entries: list[dict[str, object]], chunk_size: int = MAX_SIGNATORY_PAGES_PER_BLOCK) -> list[list[dict[str, object]]]:
    return [entries[index : index + chunk_size] for index in range(0, len(entries), chunk_size)]


def build_manifest(source_root: Path, output_dir: Path) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    output_dir.mkdir(parents=True, exist_ok=True)

    index = 0
    for path in sorted(source_root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SIGNATORY_SUFFIXES:
            continue
        index += 1
        target_name = f"signatory-page-{index:02d}-{safe_label(path.stem, default='page')}{path.suffix.lower()}"
        target_path = output_dir / target_name
        shutil.copy2(path, target_path)
        entries.append(
            {
                "index": index,
                "source_path": str(path),
                "copied_path": str(target_path),
                "relative_output_path": target_name,
                "subfigure_caption": build_subfigure_caption(path),
            }
        )

    return {
        "source_root": str(source_root),
        "output_dir": str(output_dir),
        "file_count": len(entries),
        "entries": entries,
        "group_caption": "Signatory pages",
        "label": "fig:signatory-pages",
        "pages_per_row": SIGNATORY_PAGES_PER_ROW,
        "max_pages_per_block": MAX_SIGNATORY_PAGES_PER_BLOCK,
    }


def write_tex(manifest: dict[str, object], tex_path: Path) -> None:
    entries = [entry for entry in manifest.get("entries", []) if isinstance(entry, dict)]
    lines: list[str] = []
    if not entries:
        lines.extend(
            [
                r"\NeedsInput{Missing signatory pages: add the signed record sheets when they are available.}",
            ]
        )
    else:
        groups = chunk_entries(entries)
        width = subfigure_width()
        for group_index, group_entries in enumerate(groups, start=1):
            lines.extend([r"\begin{figure*}[p]", r"    \centering"])
            if group_index > 1:
                lines.append(r"    \ContinuedFloat")
            for position, entry in enumerate(group_entries):
                rel_path = str(entry["relative_output_path"]).replace("\\", "/")
                lines.extend(
                    [
                        rf"    \begin{{subfigure}}[t]{{{width}}}",
                        r"        \centering",
                        rf"        \includegraphics[{subfigure_image_options()}]{{signatory-pages/{rel_path}}}",
                    ]
                )
                caption_text = str(entry.get("subfigure_caption", "")).strip()
                if caption_text:
                    lines.append(rf"        \caption{{{caption_text}}}")
                lines.append(r"    \end{subfigure}")
                is_last = position == len(group_entries) - 1
                if position % SIGNATORY_PAGES_PER_ROW == 0:
                    if not is_last:
                        lines.append(r"    \hfill")
                elif not is_last:
                    lines.append(r"    \par\medskip")
            lines.extend(
                [
                    rf"    \caption{{{manifest.get('group_caption', 'Signatory pages')}{' (continued)' if group_index > 1 else ''}}}",
                ]
            )
            if group_index == 1:
                lines.append(rf"    \label{{{manifest.get('label', 'fig:signatory-pages')}}}")
            lines.append(r"\end{figure*}")

    tex_path.parent.mkdir(parents=True, exist_ok=True)
    tex_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, help="Signatory-page source directory.")
    parser.add_argument("--output-dir", required=True, help="Directory to receive copied signatory pages.")
    parser.add_argument("--output-json", required=True, help="Manifest output path.")
    parser.add_argument("--output-tex", required=True, help="LaTeX snippet output path.")
    args = parser.parse_args()

    manifest = build_manifest(Path(args.source_root).resolve(), Path(args.output_dir).resolve())
    write_json(Path(args.output_json), manifest)
    write_tex(manifest, Path(args.output_tex))
    print(
        json.dumps(
            {
                "output_json": args.output_json,
                "output_tex": args.output_tex,
                "file_count": manifest["file_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
