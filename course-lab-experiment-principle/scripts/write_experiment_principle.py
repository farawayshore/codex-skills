#!/usr/bin/env python3
"""Write theory-facing lab-report sections directly into the canonical report."""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path

from common import write_json
from stage_principle_images import write_tex as write_figure_tex


SECTION_RE = re.compile(r"(?m)^\\section\{([^}]+)\}[ \t]*\n?")
SUBSECTION_RE = re.compile(r"(?m)^\\subsection\{([^}]+)\}[ \t]*\n?")
NORMALIZED_KEY_RE = re.compile(r"(?m)^- Normalized key: `([^`]+)`\s*$")
OWNED_SECTIONS = ("Introduction", "Background", "Experiment Principle")
PLACEHOLDER_TOKENS = ("\\NeedsInput{", "PLACEHOLDER", "TBD", "TODO")


def read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Expected JSON object at {path}")
    return payload


def read_sections_markdown(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"(?m)^##\s+", text)
    sections: dict[str, dict[str, str]] = {}
    section_order: list[str] = []

    for block in blocks[1:]:
        block = block.strip()
        if not block:
            continue
        lines = block.splitlines()
        heading = lines[0].strip()
        body = "\n".join(lines[1:])
        match = NORMALIZED_KEY_RE.search(body)
        if not match:
            raise SystemExit(f"Malformed normalized sections markdown: missing Normalized key for section {heading!r}")
        key = match.group(1).strip()

        trailing = body[match.end() :].splitlines()
        index = 0
        while index < len(trailing):
            stripped = trailing[index].strip()
            if not stripped:
                index += 1
                continue
            if stripped.startswith("- ") or stripped.startswith("|"):
                index += 1
                continue
            if trailing[index].startswith("  - "):
                index += 1
                continue
            break
        section_text = "\n".join(trailing[index:]).strip()
        sections[key] = {"heading": heading, "text": section_text}
        section_order.append(key)

    if not sections:
        raise SystemExit(f"Malformed normalized sections markdown: no normalized sections found in {path}")

    return {
        "title": "",
        "section_order": section_order,
        "sections": sections,
    }


def normalize_heading(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).casefold()


def first_other_section_text(summary: dict[str, object]) -> str:
    sections = summary.get("sections", {})
    if not isinstance(sections, dict):
        return ""

    section_order = summary.get("section_order", [])
    if isinstance(section_order, list):
        for key in section_order:
            if not isinstance(key, str) or not key.startswith("other::"):
                continue
            payload = sections.get(key)
            if not isinstance(payload, dict):
                continue
            text = str(payload.get("text") or "").strip()
            if text:
                return text

    for key, payload in sections.items():
        if not isinstance(key, str) or not key.startswith("other::"):
            continue
        if not isinstance(payload, dict):
            continue
        text = str(payload.get("text") or "").strip()
        if text:
            return text
    return ""


def preferred_section_text(summary: dict[str, object], key: str, fallback_keys: tuple[str, ...] = ()) -> str:
    sections = summary.get("sections", {})
    if not isinstance(sections, dict):
        return ""

    for name in (key,) + fallback_keys:
        payload = sections.get(name)
        if not isinstance(payload, dict):
            continue
        text = str(payload.get("text") or "").strip()
        if text:
            return text
    if key == "introduction":
        return first_other_section_text(summary)
    return ""


def safe_to_overwrite(body: str) -> bool:
    stripped = body.strip()
    if not stripped:
        return True
    return any(token in stripped for token in PLACEHOLDER_TOKENS)


def section_ranges(tex: str) -> list[dict[str, object]]:
    matches = list(SECTION_RE.finditer(tex))
    results: list[dict[str, object]] = []
    for index, match in enumerate(matches):
        start = match.start()
        heading = match.group(1).strip()
        body_start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(tex)
        results.append(
            {
                "heading": heading,
                "normalized_heading": normalize_heading(heading),
                "start": start,
                "body_start": body_start,
                "end": end,
            }
        )
    return results


def subsection_ranges(tex: str) -> list[dict[str, object]]:
    matches = list(SUBSECTION_RE.finditer(tex))
    results: list[dict[str, object]] = []
    for index, match in enumerate(matches):
        start = match.start()
        heading = match.group(1).strip()
        body_start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(tex)
        results.append(
            {
                "heading": heading,
                "normalized_heading": normalize_heading(heading),
                "start": start,
                "body_start": body_start,
                "end": end,
            }
        )
    return results


def render_figure_block(block: dict[str, object]) -> str:
    with tempfile.TemporaryDirectory() as temp_name:
        out_path = Path(temp_name) / "block.tex"
        write_figure_tex({"figure_blocks": [block]}, out_path)
        return out_path.read_text(encoding="utf-8").strip()


def unresolved_markdown(items: list[dict[str, object]]) -> str:
    if not items:
        return ""
    lines = ["# Experiment Principle Unresolved Items", ""]
    for item in items:
        section = str(item.get("section") or "Unknown Section")
        reason = str(item.get("reason") or "unspecified")
        detail = str(item.get("detail") or "").strip()
        lines.append(f"- {section}: {reason}")
        if detail:
            lines.append(f"  - {detail}")
    return "\n".join(lines).rstrip() + "\n"


def resolve_latex_image_path(entry: dict[str, object]) -> str:
    latex_path = str(entry.get("latex_image_path") or "").strip()
    if latex_path:
        return latex_path
    relative = str(entry.get("relative_output_path") or "").strip()
    if not relative:
        return ""
    return f"principle-images/{relative}"


def build_section_payloads(summary: dict[str, object], figures: dict[str, object]) -> tuple[dict[str, str], list[str], list[dict[str, object]]]:
    unresolved_items: list[dict[str, object]] = []
    inserted_figures: list[str] = []
    payloads = {
        "Introduction": preferred_section_text(summary, "introduction"),
        "Background": preferred_section_text(summary, "background", ("introduction",)),
        "Experiment Principle": preferred_section_text(summary, "principle"),
    }

    for heading, body in list(payloads.items()):
        if body:
            continue
        payloads[heading] = rf"\NeedsInput{{Missing handout support for {heading}.}}"
        unresolved_items.append(
            {
                "section": heading,
                "reason": "missing_handout_support",
                "detail": f"No normalized handout text was available for {heading}.",
            }
        )

    figure_sections: dict[str, list[str]] = {heading: [] for heading in OWNED_SECTIONS}
    for block in figures.get("figure_blocks", []):
        if not isinstance(block, dict):
            continue
        target_section = str(block.get("target_section") or "Experiment Principle").strip() or "Experiment Principle"
        if target_section not in figure_sections:
            target_section = "Experiment Principle"

        figure_sections[target_section].append(render_figure_block(block))
        for entry in block.get("entries", []):
            if not isinstance(entry, dict):
                continue
            relative = str(entry.get("relative_output_path") or "").strip()
            latex_path = resolve_latex_image_path(entry)
            if relative and not entry.get("missing_source"):
                inserted_figures.append(latex_path if latex_path.count("/") > 1 else relative)
            if entry.get("missing_source"):
                unresolved_items.append(
                    {
                        "section": target_section,
                        "reason": "missing_figure_source",
                        "detail": str(entry.get("caption_text") or entry.get("latex_caption") or "Missing principle image"),
                    }
                )
        if str(block.get("type") or "") == "needs_user_grouping":
            unresolved_items.append(
                {
                    "section": target_section,
                    "reason": "grouping_decision_required",
                    "detail": str(block.get("question") or "Picture grouping requires user confirmation."),
                }
            )

    for heading, snippets in figure_sections.items():
        if not snippets:
            continue
        payloads[heading] = payloads[heading].rstrip() + "\n\n" + "\n\n".join(snippets)

    return payloads, sorted(set(inserted_figures)), unresolved_items


def rewrite_ranges(tex: str, ranges: list[dict[str, object]], payloads: dict[str, str], *, scope_label: str) -> tuple[str, list[dict[str, object]]]:
    unresolved_items: list[dict[str, object]] = []
    pieces: list[str] = []
    cursor = 0
    seen_headings: set[str] = set()
    for info in ranges:
        start = int(info["start"])
        body_start = int(info["body_start"])
        end = int(info["end"])
        heading = str(info["heading"])
        seen_headings.add(heading)
        pieces.append(tex[cursor:start])
        heading_text = tex[start:body_start]
        pieces.append(heading_text)
        replacement = payloads.get(heading)
        body = tex[body_start:end]
        if replacement is None:
            pieces.append(body)
        elif safe_to_overwrite(body):
            pieces.append(replacement.strip() + "\n\n")
        else:
            pieces.append(body)
            unresolved_items.append(
                {
                    "section": f"{scope_label} / {heading}" if scope_label else heading,
                    "reason": "existing_user_text_conflict",
                    "detail": f"{heading} already contains non-placeholder text and was left unchanged.",
                }
            )
        cursor = end
    pieces.append(tex[cursor:])
    for heading in payloads:
        if heading in seen_headings:
            continue
        unresolved_items.append(
            {
                "section": f"{scope_label} / {heading}" if scope_label else heading,
                "reason": "missing_target_subsection",
                "detail": f"{heading} was not found in the targeted report scope.",
            }
        )
    return "".join(pieces).rstrip() + "\n", unresolved_items


def rewrite_report(tex: str, payloads: dict[str, str], parent_section: str | None = None) -> tuple[str, list[dict[str, object]], str]:
    if not parent_section:
        rewritten, unresolved = rewrite_ranges(tex, section_ranges(tex), payloads, scope_label="")
        return rewritten, unresolved, "top-level"

    parent_ranges = section_ranges(tex)
    normalized_parent = normalize_heading(parent_section)
    parent_info = next((item for item in parent_ranges if item["normalized_heading"] == normalized_parent), None)
    if parent_info is None:
        unresolved = [
            {
                "section": parent_section,
                "reason": "missing_target_parent_section",
                "detail": f'Target parent section "{parent_section}" was not found in the report.',
            }
        ]
        return tex if tex.endswith("\n") else tex + "\n", unresolved, "part-scoped"

    parent_body = tex[int(parent_info["body_start"]) : int(parent_info["end"])]
    rewritten_body, unresolved = rewrite_ranges(parent_body, subsection_ranges(parent_body), payloads, scope_label=parent_section)
    rewritten = (
        tex[: int(parent_info["body_start"])]
        + rewritten_body
        + tex[int(parent_info["end"]) :]
    )
    return rewritten.rstrip() + "\n", unresolved, "part-scoped"


def resolve_sections_source(sections_markdown: Path | None, sections_json: Path | None) -> dict[str, object]:
    if sections_markdown and sections_markdown.exists():
        return read_sections_markdown(sections_markdown)
    if sections_markdown and not sections_markdown.exists() and sections_json and sections_json.exists():
        return read_json(sections_json)
    if sections_json and sections_json.exists() and not sections_markdown:
        return read_json(sections_json)
    raise SystemExit("No normalized sections source found")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sections-json")
    parser.add_argument("--sections-markdown")
    parser.add_argument("--report-tex", required=True)
    parser.add_argument("--figures-json", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-unresolved")
    parser.add_argument("--parent-section")
    args = parser.parse_args()

    sections_markdown = Path(args.sections_markdown).resolve() if args.sections_markdown else None
    sections_json = Path(args.sections_json).resolve() if args.sections_json else None
    if not sections_markdown and not sections_json:
        parser.error("one of --sections-markdown or --sections-json is required")

    sections = resolve_sections_source(sections_markdown, sections_json)
    figures = read_json(Path(args.figures_json))
    report_path = Path(args.report_tex)
    tex = report_path.read_text(encoding="utf-8")

    payloads, inserted_figures, unresolved_items = build_section_payloads(sections, figures)
    rewritten_tex, rewrite_unresolved, mode = rewrite_report(tex, payloads, args.parent_section)
    unresolved_items.extend(rewrite_unresolved)
    report_path.write_text(rewritten_tex, encoding="utf-8")

    if args.output_unresolved:
        Path(args.output_unresolved).write_text(unresolved_markdown(unresolved_items), encoding="utf-8")

    manifest = {
        "report_path": str(report_path),
        "owned_sections": list(OWNED_SECTIONS),
        "inserted_figures": inserted_figures,
        "mode": mode,
        "target_parent_section": args.parent_section,
        "unresolved_items": unresolved_items,
    }
    write_json(Path(args.output_json), manifest)
    print(json.dumps({"output_json": args.output_json, "report_tex": args.report_tex}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
