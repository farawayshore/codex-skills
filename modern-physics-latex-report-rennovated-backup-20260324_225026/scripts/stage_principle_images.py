#!/usr/bin/env python3
"""Copy decoded principle-section images into a report workspace and emit LaTeX snippets."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

from common import safe_label, score_text, write_json
from extract_decoded_sections import build_summary, load_blocks


CAPTION_PREFIX_RE = re.compile(
    r"^\s*(?:图|Fig(?:ure)?\.?)\s*[-\s0-9A-Za-z一二三四五六七八九十()（）.:：、]*"
)
SUBFIG_MARKER_RE = re.compile(r"^\s*[（(]([a-zA-Z])[\)）]\s*")
INLINE_GROUP_CAPTION_RE = re.compile(
    r"\s((?:图|Fig(?:ure)?\.?)\s*[-\s0-9A-Za-z一二三四五六七八九十()（）.:：、].*)$",
    re.IGNORECASE,
)


def latex_escape(text: str) -> str:
    repl = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(repl.get(ch, ch) for ch in text)


def strip_figure_prefix(text: str) -> str:
    return CAPTION_PREFIX_RE.sub("", text).strip(" .:：-")


def clean_caption(caption_items: list[str], fallback_name: str) -> str:
    joined = " ".join(item.strip() for item in caption_items if item.strip())
    joined = re.sub(r"\s+", " ", joined).strip()
    if joined:
        cleaned = strip_figure_prefix(joined)
        if cleaned:
            return cleaned
    fallback = Path(fallback_name).stem
    return fallback.replace("-", " ").replace("_", " ").strip() or "Principle figure"


def load_sections(decoded_json: Path, sections_json: Path | None) -> dict[str, object]:
    if sections_json and sections_json.exists():
        return json.loads(sections_json.read_text(encoding="utf-8"))
    return build_summary(load_blocks(decoded_json))


def resolve_source_path(decoded_json: Path, raw_img_path: str, caption_items: list[str]) -> Path:
    direct_path = (decoded_json.parent / raw_img_path).resolve()
    if direct_path.is_file():
        return direct_path

    images_dir = decoded_json.parent / "images"
    if not images_dir.is_dir():
        return direct_path

    query = " ".join(caption_items).strip() or Path(raw_img_path).stem
    best_path = direct_path
    best_score = 0.0
    for candidate in sorted(images_dir.iterdir()):
        if not candidate.is_file():
            continue
        score, _ = score_text(query, [candidate.stem, candidate.name])
        if score > best_score:
            best_score = score
            best_path = candidate
    return best_path if best_score > 0 else direct_path


def parse_caption_metadata(caption_items: list[str], cleaned_caption: str) -> tuple[str | None, str, str | None]:
    subfigure_marker: str | None = None
    subfigure_caption = cleaned_caption
    group_caption: str | None = None

    for item in caption_items:
        normalized = re.sub(r"\s+", " ", str(item).strip())
        if not normalized:
            continue

        marker_match = SUBFIG_MARKER_RE.match(normalized)
        if marker_match and subfigure_marker is None:
            subfigure_marker = marker_match.group(1).lower()
            remainder = normalized[marker_match.end() :].strip(" .:：-")
            inline_group = INLINE_GROUP_CAPTION_RE.search(remainder)
            if inline_group:
                maybe_group = strip_figure_prefix(inline_group.group(1))
                if maybe_group:
                    group_caption = maybe_group
                remainder = remainder[: inline_group.start()].strip(" .:：-")
            if remainder:
                subfigure_caption = remainder
            continue

        stripped = strip_figure_prefix(normalized)
        if stripped and stripped != normalized:
            group_caption = stripped

    return subfigure_marker, subfigure_caption, group_caption


def markers_are_consecutive(markers: list[str]) -> bool:
    if not markers:
        return False
    values = [ord(marker.lower()) for marker in markers]
    return all(values[idx] == values[0] + idx for idx in range(len(values)))


def build_group_caption(entries: list[dict[str, object]]) -> str:
    for entry in reversed(entries):
        caption = str(entry.get("group_caption") or "").strip()
        if caption:
            return caption
    for key in ("context_subheading", "section_heading"):
        candidate = str(entries[0].get(key) or "").strip()
        if candidate:
            return candidate
    return "Principle schematic diagrams"


def build_group_question(entries: list[dict[str, object]]) -> str:
    labels = [str(entry.get("caption_text") or entry.get("relative_output_path") or entry.get("label")) for entry in entries]
    joined = ", ".join(labels)
    return f'Pictures {joined}, do they belong to the same group?'


def standalone_block(entry: dict[str, object]) -> dict[str, object]:
    return {
        "type": "standalone",
        "label": entry["label"],
        "context_subheading": entry.get("context_subheading"),
        "section_heading": entry.get("section_heading"),
        "caption_text": entry["latex_caption"],
        "placement_hint": entry.get("placement_hint"),
        "entries": [entry],
    }


def build_figure_blocks(entries: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    blocks: list[dict[str, object]] = []
    grouping_questions: list[dict[str, object]] = []
    idx = 0

    while idx < len(entries):
        entry = entries[idx]
        marker = str(entry.get("subfigure_marker") or "").lower()
        if not marker:
            blocks.append(standalone_block(entry))
            idx += 1
            continue

        run = [entry]
        lookahead = idx + 1
        while lookahead < len(entries):
            candidate = entries[lookahead]
            candidate_marker = str(candidate.get("subfigure_marker") or "").lower()
            if not candidate_marker:
                break
            if str(candidate.get("context_subheading") or "") != str(entry.get("context_subheading") or ""):
                break
            run.append(candidate)
            lookahead += 1

        markers = [str(item.get("subfigure_marker") or "").lower() for item in run]
        if len(run) >= 2 and len(set(markers)) == len(markers) and markers_are_consecutive(markers) and markers[0] == "a":
            blocks.append(
                {
                    "type": "subfigure_group",
                    "label": entry["label"],
                    "context_subheading": entry.get("context_subheading"),
                    "section_heading": entry.get("section_heading"),
                    "caption_text": build_group_caption(run),
                    "placement_hint": (
                        f'Place this grouped figure in subsection "{entry.get("context_subheading")}" and mention it in nearby prose before or after the figure.'
                        if entry.get("context_subheading")
                        else "Mention this grouped figure in nearby principle prose before or after the figure."
                    ),
                    "entries": run,
                }
            )
        else:
            question = build_group_question(run)
            grouping_questions.append(
                {
                    "context_subheading": entry.get("context_subheading"),
                    "entries": [item["caption_text"] for item in run],
                    "question": question,
                }
            )
            blocks.append(
                {
                    "type": "needs_user_grouping",
                    "label": entry["label"],
                    "context_subheading": entry.get("context_subheading"),
                    "section_heading": entry.get("section_heading"),
                    "question": question,
                    "entries": run,
                }
            )

        idx = lookahead

    return blocks, grouping_questions


def subfigure_width(entry_count: int) -> str:
    if entry_count <= 2:
        return r"0.48\columnwidth"
    if entry_count == 3:
        return r"0.31\columnwidth"
    return r"0.23\columnwidth"


def build_manifest(decoded_json: Path, sections: dict[str, object], output_dir: Path) -> dict[str, object]:
    principle = sections.get("sections", {}).get("principle", {})
    images = principle.get("images", []) if isinstance(principle, dict) else []
    entries: list[dict[str, object]] = []
    output_dir.mkdir(parents=True, exist_ok=True)

    for idx, image in enumerate(images, start=1):
        if not isinstance(image, dict):
            continue
        raw_img_path = str(image.get("img_path", "")).strip()
        if not raw_img_path:
            continue
        caption_items = [str(item).strip() for item in image.get("caption", []) if str(item).strip()]
        source_path = resolve_source_path(decoded_json, raw_img_path, caption_items)
        caption_text = clean_caption(caption_items, source_path.name)
        subfigure_marker, subfigure_caption, group_caption = parse_caption_metadata(caption_items, caption_text)
        context_subheading = str(image.get("context_subheading", "")).strip() or None
        destination_name = f"fig-{idx:02d}-{safe_label(caption_text, default='principle-figure')}{source_path.suffix.lower()}"
        destination_path = output_dir / destination_name
        exists = source_path.is_file()
        if exists:
            shutil.copy2(source_path, destination_path)

        entries.append(
            {
                "index": idx,
                "page": image.get("page"),
                "source_path": str(source_path),
                "copied_path": str(destination_path) if exists else None,
                "relative_output_path": destination_name if exists else None,
                "caption_source": caption_items,
                "caption_text": caption_text,
                "latex_caption": caption_text,
                "label": f"fig:principle-{idx:02d}",
                "subfigure_marker": subfigure_marker,
                "subfigure_caption": subfigure_caption,
                "group_caption": group_caption,
                "context_subheading": context_subheading,
                "section_heading": image.get("section_heading"),
                "placement_hint": (
                    f'Place in subsection "{context_subheading}" and mention it in the nearby text as a schematic diagram when that matches the handout.'
                    if context_subheading
                    else "Mention this figure in the nearby principle discussion and describe it as a schematic diagram when that matches the handout."
                ),
                "missing_source": not exists,
            }
        )

    figure_blocks, grouping_questions = build_figure_blocks(entries)
    return {
        "decoded_json": str(decoded_json),
        "output_dir": str(output_dir),
        "principle_image_count": len(entries),
        "figure_block_count": len(figure_blocks),
        "figure_blocks": figure_blocks,
        "grouping_questions": grouping_questions,
        "entries": entries,
    }


def write_tex(manifest: dict[str, object], tex_path: Path) -> None:
    blocks = manifest.get("figure_blocks", [])
    lines: list[str] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type") or "")
        entries = [entry for entry in block.get("entries", []) if isinstance(entry, dict)]
        if block_type == "needs_user_grouping":
            lines.extend(
                [
                    rf"\NeedsInput{{Pending picture grouping decision: {latex_escape(str(block.get('question') or 'Do these pictures belong to the same group?'))}}}",
                ]
            )
            continue
        context_subheading = str(block.get("context_subheading") or "").strip()
        label = latex_escape(str(block["label"]))

        if block_type == "subfigure_group":
            caption = latex_escape(str(block.get("caption_text") or "Principle schematic diagrams"))
            width = subfigure_width(len(entries))
            lines.extend([r"\begin{figure}[H]", r"    \centering"])
            for position, entry in enumerate(entries):
                subcaption = latex_escape(str(entry.get("subfigure_caption") or entry.get("caption_text") or "Subfigure"))
                lines.extend(
                    [
                        rf"    \begin{{subfigure}}[t]{{{width}}}",
                        r"        \centering",
                    ]
                )
                if entry.get("missing_source"):
                    lines.append(
                        rf"        \NeedsInput{{Missing principle image: {latex_escape(str(entry.get('caption_text') or 'Principle figure'))}}}"
                    )
                else:
                    rel_path = latex_escape(str(entry["relative_output_path"]))
                    lines.append(rf"        \includegraphics[width=\linewidth]{{principle-images/{rel_path}}}")
                lines.extend(
                    [
                        rf"        \caption{{{subcaption}}}",
                        r"    \end{subfigure}",
                    ]
                )
                if position != len(entries) - 1:
                    lines.append(r"    \hfill")
            lines.extend(
                [
                    rf"    \caption{{{caption}}}",
                    rf"    \label{{{label}}}",
                    r"\end{figure}",
                ]
            )
            continue

        entry = entries[0]
        if entry.get("missing_source"):
            lines.extend(
                [
                    rf"\NeedsInput{{Missing principle image: {latex_escape(str(entry.get('caption_text') or 'Principle figure'))}}}",
                ]
            )
            continue
        rel_path = latex_escape(str(entry["relative_output_path"]))
        caption = latex_escape(str(entry["latex_caption"]))
        lines.extend(
            [
                r"\begin{figure}[H]",
                r"    \centering",
                rf"    \includegraphics[width=0.92\columnwidth]{{principle-images/{rel_path}}}",
                rf"    \caption{{{caption}}}",
                rf"    \label{{{label}}}",
                r"\end{figure}",
            ]
        )
    tex_path.parent.mkdir(parents=True, exist_ok=True)
    tex_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decoded-json", required=True)
    parser.add_argument("--output-dir", required=True, help="Directory to receive copied principle images.")
    parser.add_argument("--output-tex", required=True, help="LaTeX snippet output path.")
    parser.add_argument("--output-json", required=True, help="Manifest output path.")
    parser.add_argument("--sections-json", help="Optional normalized sections JSON.")
    args = parser.parse_args()

    decoded_json = Path(args.decoded_json).resolve()
    sections_json = Path(args.sections_json).resolve() if args.sections_json else None
    sections = load_sections(decoded_json, sections_json)
    manifest = build_manifest(decoded_json, sections, Path(args.output_dir))
    write_json(Path(args.output_json), manifest)
    write_tex(manifest, Path(args.output_tex))
    print(
        json.dumps(
            {
                "output_json": args.output_json,
                "output_tex": args.output_tex,
                "grouping_questions": len(manifest.get("grouping_questions", [])),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
