#!/usr/bin/env python3
"""Normalize a MinerU-decoded JSON file into named report-ready sections."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from common import write_json


HEADING_PATTERNS = {
    "introduction": re.compile(r"(引言|简介|绪论|introduction|background)", re.IGNORECASE),
    "objectives": re.compile(r"(实验目的|实验目标|研究目的|objective|aim)", re.IGNORECASE),
    "equipment": re.compile(r"(实验仪器|实验设备|仪器设备|equipment|apparatus|materials)", re.IGNORECASE),
    "principle": re.compile(r"(实验原理|实验理论|原理|principle|theory)", re.IGNORECASE),
    "steps": re.compile(r"(实验步骤|实验方法|实验内容|操作步骤|procedure|steps?|method)", re.IGNORECASE),
    "thinking_questions": re.compile(r"(思考题|讨论题|thinking questions?)", re.IGNORECASE),
    "appendix": re.compile(r"(附录|appendix)", re.IGNORECASE),
    "references": re.compile(r"(参考文献|references?)", re.IGNORECASE),
}
IGNORE_TYPES = {"header", "footer", "page_number", "aside_text"}
SUBSECTION_RE = re.compile(
    r"^\s*(?:"
    r"\d+(?:\.\d+)+|"
    r"[（(]?[a-zA-Z][)）]?|"
    r"[一二三四五六七八九十]+[、.]|"
    r"[0-9]+[、.]"
    r")"
)


def heading_key(text: str) -> str | None:
    for key, pattern in HEADING_PATTERNS.items():
        if pattern.search(text):
            return key
    return None


def is_heading(block: dict[str, object]) -> bool:
    if block.get("type") != "text":
        return False
    text = str(block.get("text", "")).strip()
    if not text:
        return False
    level = block.get("text_level")
    if isinstance(level, int) and level >= 1:
        return True
    return bool(heading_key(text) and len(text) <= 60)


def empty_section(heading: str = "") -> dict[str, object]:
    return {
        "heading": heading,
        "pages": [],
        "text_parts": [],
        "list_items": [],
        "equations": [],
        "tables": [],
        "images": [],
        "subheadings": [],
    }


def finalize_section(section: dict[str, object]) -> dict[str, object]:
    section["pages"] = sorted(set(int(page) for page in section["pages"]))
    text_parts = [part.strip() for part in section["text_parts"] if str(part).strip()]
    section["text"] = "\n\n".join(text_parts).strip()
    del section["text_parts"]
    return section


def add_page(section: dict[str, object], page_idx: object) -> None:
    if isinstance(page_idx, int):
        section["pages"].append(page_idx + 1)


def load_blocks(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise SystemExit(f"Decoded JSON must be a list of MinerU blocks: {path}")
    return [item for item in payload if isinstance(item, dict)]


def build_summary(blocks: list[dict[str, object]]) -> dict[str, object]:
    title = ""
    front_matter = empty_section("Front Matter")
    sections: dict[str, dict[str, object]] = {}
    section_order: list[str] = []
    current_key = "front_matter"
    current_major_key = "front_matter"
    current = front_matter
    current_subheading: str | None = None
    appendix_candidates = {"appendix_sections": [], "image_captions": [], "table_captions": []}

    for block in blocks:
        block_type = str(block.get("type", "")).strip()
        if block_type in IGNORE_TYPES:
            continue

        page_idx = block.get("page_idx")
        if is_heading(block):
            raw_heading = str(block.get("text", "")).strip()
            mapped = heading_key(raw_heading)
            if mapped is None and current_major_key != "front_matter" and SUBSECTION_RE.match(raw_heading):
                current = sections[current_major_key]
                current["subheadings"].append(
                    {
                        "heading": raw_heading,
                        "page": int(page_idx) + 1 if isinstance(page_idx, int) else None,
                    }
                )
                current["text_parts"].append(f"[Subheading] {raw_heading}")
                add_page(current, page_idx)
                current_subheading = raw_heading
                continue

            mapped = mapped or f"other::{raw_heading}"
            if mapped not in sections:
                sections[mapped] = empty_section(raw_heading)
                section_order.append(mapped)
            current_key = mapped
            current_major_key = mapped if not mapped.startswith("other::") else current_major_key
            current = sections[mapped]
            current_subheading = None
            if not title and mapped not in {"references", "appendix"} and not raw_heading.startswith(("一", "二", "三", "四", "五")):
                title = raw_heading
            add_page(current, page_idx)
            continue

        add_page(current, page_idx)
        if block_type == "text":
            text = str(block.get("text", "")).strip()
            if text:
                current["text_parts"].append(text)
                if not title and not heading_key(text) and len(text) <= 120:
                    title = text
        elif block_type == "list":
            for item in block.get("list_items", []):
                value = str(item).strip()
                if value:
                    current["list_items"].append(value)
        elif block_type == "equation":
            equation = str(block.get("text", "")).strip()
            if equation:
                current["equations"].append(equation)
        elif block_type == "table":
            entry = {
                "caption": [str(item).strip() for item in block.get("table_caption", []) if str(item).strip()],
                "footnote": [str(item).strip() for item in block.get("table_footnote", []) if str(item).strip()],
                "body": str(block.get("table_body", "")).strip(),
                "img_path": str(block.get("img_path", "")).strip(),
                "page": int(page_idx) + 1 if isinstance(page_idx, int) else None,
                "context_subheading": current_subheading,
                "section_heading": str(current.get("heading") or "").strip() or None,
            }
            current["tables"].append(entry)
            appendix_candidates["table_captions"].extend(entry["caption"])
        elif block_type == "image":
            entry = {
                "caption": [str(item).strip() for item in block.get("image_caption", []) if str(item).strip()],
                "footnote": [str(item).strip() for item in block.get("image_footnote", []) if str(item).strip()],
                "img_path": str(block.get("img_path", "")).strip(),
                "page": int(page_idx) + 1 if isinstance(page_idx, int) else None,
                "context_subheading": current_subheading,
                "section_heading": str(current.get("heading") or "").strip() or None,
            }
            current["images"].append(entry)
            appendix_candidates["image_captions"].extend(entry["caption"])

    finalized_sections = {key: finalize_section(value) for key, value in sections.items()}
    if "appendix" in finalized_sections:
        appendix_candidates["appendix_sections"].append(finalized_sections["appendix"])

    return {
        "title": title,
        "section_order": section_order,
        "front_matter": finalize_section(front_matter),
        "sections": finalized_sections,
        "appendix_candidates": appendix_candidates,
    }


def markdown_summary(summary: dict[str, object]) -> str:
    lines = [
        "# Decoded Section Summary",
        "",
        f"- Title: {summary.get('title') or 'TBD'}",
        "",
    ]
    front_matter = summary["front_matter"]
    if front_matter.get("text"):
        lines.extend(["## Front Matter", "", str(front_matter["text"]), ""])

    sections = summary["sections"]
    for key in summary["section_order"]:
        section = sections[key]
        heading = str(section.get("heading") or key)
        lines.extend([f"## {heading}", "", f"- Normalized key: `{key}`"])
        pages = section.get("pages") or []
        if pages:
            lines.append(f"- Pages: {', '.join(str(page) for page in pages)}")
        if section.get("list_items"):
            lines.append("- List items:")
            lines.extend([f"  - {item}" for item in section["list_items"]])
        if section.get("subheadings"):
            lines.append("- Subheadings:")
            lines.extend([f"  - {item['heading']}" for item in section["subheadings"]])
        if section.get("equations"):
            lines.append(f"- Equations: {len(section['equations'])}")
        if section.get("tables"):
            lines.append(f"- Tables: {len(section['tables'])}")
        if section.get("images"):
            lines.append(f"- Images: {len(section['images'])}")
        if section.get("text"):
            lines.extend(["", str(section["text"]), ""])
        else:
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decoded-json", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-markdown", required=True)
    args = parser.parse_args()

    blocks = load_blocks(Path(args.decoded_json))
    summary = build_summary(blocks)
    write_json(Path(args.output_json), summary)
    Path(args.output_markdown).write_text(markdown_summary(summary), encoding="utf-8")
    print(json.dumps({"output_json": args.output_json, "output_markdown": args.output_markdown}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
