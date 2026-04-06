from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any


LEAF_SKILL_BUCKET_KEYS = (
    "course-lab-body-scaffold",
    "course-lab-experiment-principle",
    "course-lab-data-transfer",
    "course-lab-data-processing",
    "course-lab-plotting",
    "course-lab-results-interpretation",
    "course-lab-discussion-ideas",
    "course-lab-discussion-synthesis",
    "course-lab-final-staging",
    "course-lab-figure-evidence",
)

BUCKET_SHAPE_KEYS = (
    "status",
    "required_inputs_from_handout",
    "candidate_sections",
    "required_outputs_or_deliverables",
    "suggested_focus",
    "enrichment_opportunities",
    "unresolved_gaps",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_heading(value: Any) -> str:
    return normalize_text(value).strip(" \t-:;")


def normalize_list_item(value: Any) -> str:
    text = normalize_text(value)
    text = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", text)
    return text


def append_unique(bucket: dict[str, Any], field_name: str, value: str) -> None:
    if not value:
        return
    field = bucket[field_name]
    if value not in field:
        field.append(value)


def append_unique_list(values: list[str], value: str) -> None:
    if value and value not in values:
        values.append(value)


def has_any_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def section_strings(section: dict[str, Any]) -> dict[str, list[str]]:
    heading = normalize_heading(section.get("heading", ""))
    text = normalize_text(section.get("text", ""))
    list_items = [
        normalize_list_item(item)
        for item in section.get("list_items", [])
        if normalize_list_item(item)
    ]
    table_strings = []
    for table in section.get("tables", []):
        if not isinstance(table, dict):
            continue
        caption = normalize_text(" ".join(table.get("caption", [])))
        body = normalize_text(table.get("body", ""))
        if caption:
            table_strings.append(caption)
        if body:
            table_strings.append(body)
    image_strings = []
    for image in section.get("images", []):
        if not isinstance(image, dict):
            continue
        caption = normalize_text(" ".join(image.get("caption", [])))
        if caption:
            image_strings.append(caption)
    subheading_strings = [
        normalize_heading(subheading.get("heading", ""))
        for subheading in section.get("subheadings", [])
        if isinstance(subheading, dict) and normalize_heading(subheading.get("heading", ""))
    ]
    return {
        "heading": [heading] if heading else [],
        "text": [text] if text else [],
        "list_items": list_items,
        "tables": table_strings,
        "images": image_strings,
        "subheadings": subheading_strings,
    }


def iter_normalized_sections(sections: dict[str, Any]):
    section_map = sections.get("sections", {})
    section_order = sections.get("section_order") or list(section_map.keys())
    for section_key in section_order:
        section = section_map.get(section_key)
        if isinstance(section, dict):
            yield section_key, section, section_strings(section)


def build_empty_bucket(status: str = "pending") -> dict[str, Any]:
    bucket = {key: [] for key in BUCKET_SHAPE_KEYS}
    bucket["status"] = status
    return bucket


def build_leaf_skill_handoffs() -> dict[str, dict[str, Any]]:
    return {bucket_key: build_empty_bucket() for bucket_key in LEAF_SKILL_BUCKET_KEYS}


def build_run_readiness(sections: dict[str, Any], sections_markdown: str) -> dict[str, bool]:
    section_values = sections.get("sections", {})
    section_text = "\n".join(
        " ".join(
            [
                str(section.get("heading", "")),
                str(section.get("text", "")),
                " ".join(section.get("list_items", [])),
                " ".join(
                    table.get("body", "") for table in section.get("tables", []) if isinstance(table, dict)
                ),
                " ".join(
                    " ".join(image.get("caption", []))
                    for image in section.get("images", [])
                    if isinstance(image, dict)
                ),
            ]
        )
        for section in section_values.values()
        if isinstance(section, dict)
    )
    combined_text = f"{section_text}\n{sections_markdown}".lower()
    return {
        "has_procedure_content": "procedure" in combined_text or "step" in combined_text,
        "has_required_observations": "observation" in combined_text,
        "has_explicit_deliverables": (
            "deliverable" in combined_text
            or "must include" in combined_text
            or "submit" in combined_text
            or "hand in" in combined_text
            or "turn in" in combined_text
        ),
        "has_data_tables": "table" in combined_text or "|" in sections_markdown,
        "has_plotting_requirements": "plot" in combined_text or "graph" in combined_text,
        "has_thinking_questions": "thinking question" in combined_text or "question" in combined_text,
        "has_figure_or_photo_requirements": "figure" in combined_text or "photo" in combined_text,
    }


def build_source_artifacts(sections: dict[str, Any], sections_markdown: str, workspace: str) -> dict[str, Any]:
    return {
        "sections": sections,
        "sections_markdown": sections_markdown,
        "workspace": workspace,
    }
