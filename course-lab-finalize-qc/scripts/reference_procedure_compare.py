#!/usr/bin/env python3
"""Compare final-report TeX against discovery-selected reference procedures."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path


PROCEDURE_HEADING_ALIASES = (
    "experiment steps",
    "experimental procedure",
    "experiment procedure",
    "procedure",
    "experiment results",
    "实验步骤",
    "实验过程",
    "实验方法",
    "实验结果",
)
THEORY_KEYWORDS = (
    "理论",
    "文献",
    "compare",
    "comparison",
    "理论值",
    "一致",
    "误差",
)
DATA_LACK_KEYWORDS = (
    "缺少数据",
    "没有保存",
    "未测得",
    "data missing",
    "insufficient data",
    "无法测量",
)


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text or "").lower()
    normalized = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\{([^{}]*)\}", r" \1 ", normalized)
    normalized = re.sub(r"[^\w\u4e00-\u9fff]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def strip_leading_numbering(text: str) -> str:
    return re.sub(r"^\s*(?:\d+(?:\.\d+)*\.?\s*)+", "", text).strip()


def is_procedure_heading(title: str) -> bool:
    normalized = normalize_text(strip_leading_numbering(title))
    return any(normalized == normalize_text(alias) for alias in PROCEDURE_HEADING_ALIASES)


def make_reroute(*, target_skill: str, reason_code: str, reason_summary: str, source_reference: str | None = None, missing_items: list[str] | None = None) -> dict[str, object]:
    return {
        "target_skill": target_skill,
        "reason_code": reason_code,
        "reason_summary": reason_summary,
        "source_reference": source_reference,
        "missing_items": missing_items or [],
    }


def build_blocked_summary(*, selection_status: str, reason_code: str, reason_summary: str, reroute: dict[str, object], blocked_reference_decode_items: list[dict[str, object]] | None = None) -> dict[str, object]:
    return {
        "enabled": True,
        "selection_status": selection_status,
        "pass": False,
        "blocked": True,
        "blocked_reference_decode_items": blocked_reference_decode_items or [],
        "missing_structure_items": [],
        "missing_content_items": [],
        "declared_unresolved_items": [],
        "data_lack_suspected_items": [],
        "recommended_reroutes": [reroute],
        "reason_code": reason_code,
        "reason_summary": reason_summary,
    }


def expand_tex_tree(main_tex: Path) -> str:
    include_re = re.compile(r"\\(?:input|include)\{([^}]+)\}")
    seen: set[Path] = set()

    def read_with_includes(path: Path) -> str:
        resolved = path.resolve()
        if resolved in seen:
            return ""
        seen.add(resolved)
        text = path.read_text(encoding="utf-8", errors="replace")

        def replace(match: re.Match[str]) -> str:
            rel = match.group(1).strip()
            candidate = path.parent / rel
            if candidate.suffix != ".tex":
                candidate = candidate.with_suffix(".tex")
            if not candidate.exists():
                raise FileNotFoundError(f"Missing included TeX file: {candidate}")
            return read_with_includes(candidate)

        return include_re.sub(replace, text)

    return read_with_includes(main_tex)


def extract_reference_items(markdown_text: str, *, source_reference: str) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    in_section = False
    section_level = 0
    current_item: dict[str, object] | None = None
    for raw_line in markdown_text.splitlines():
        heading_match = re.match(r"^(#{1,6})\s+(.*)$", raw_line)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            if not in_section:
                if is_procedure_heading(title):
                    in_section = True
                    section_level = level
                    current_item = None
                continue

            if level <= section_level and not is_procedure_heading(title):
                in_section = False
                section_level = 0
                current_item = None
                continue

            if level <= section_level and is_procedure_heading(title):
                section_level = level
                current_item = None
                continue

            current_item = {
                "source_reference": source_reference,
                "heading": strip_leading_numbering(title),
                "anchor_text": "",
            }
            items.append(current_item)
            continue

        if not in_section:
            continue

        stripped = raw_line.strip()
        if not stripped:
            continue
        bullet_match = re.match(r"^\s*(?:[-*]|\d+[.)])\s*(.+)$", raw_line)
        text = strip_leading_numbering((bullet_match.group(1) if bullet_match else stripped).strip())
        if not text:
            continue

        if bullet_match:
            items.append(
                {
                    "source_reference": source_reference,
                    "heading": "",
                    "anchor_text": text,
                }
            )
            current_item = None
            continue

        if current_item is not None and not current_item["anchor_text"]:
            current_item["anchor_text"] = text
            continue

        items.append(
            {
                "source_reference": source_reference,
                "heading": "",
                "anchor_text": text,
            }
        )
        current_item = None

    return [item for item in items if item["heading"] or item["anchor_text"]]


def extract_section_body(tex_text: str, heading: str) -> str:
    if not heading:
        return ""
    pattern = re.compile(
        rf"\\(?:sub)*section\{{[^}}]*{re.escape(heading)}[^}}]*\}}(?P<body>.*?)(?=\\(?:sub)*section\{{|\\end\{{document\}}|\Z)",
        re.DOTALL,
    )
    match = pattern.search(tex_text)
    return match.group("body") if match else ""


def contains_any(normalized_text: str, keywords: tuple[str, ...]) -> bool:
    return any(normalize_text(keyword) in normalized_text for keyword in keywords)


def char_ngrams(text: str, size: int = 2) -> set[str]:
    compact = normalize_text(text).replace(" ", "")
    if len(compact) < size:
        return {compact} if compact else set()
    return {compact[index : index + size] for index in range(0, len(compact) - size + 1)}


def text_matches(expected: str, actual: str) -> bool:
    expected_norm = normalize_text(expected)
    actual_norm = normalize_text(actual)
    if not expected_norm:
        return False
    if expected_norm in actual_norm:
        return True
    expected_ngrams = char_ngrams(expected_norm)
    if not expected_ngrams:
        return False
    overlap_ratio = len(expected_ngrams & char_ngrams(actual_norm)) / len(expected_ngrams)
    return overlap_ratio >= 0.6


def compare_reference_procedure_coverage(*, main_tex: Path, discovery_json: Path) -> dict[str, object]:
    discovery = json.loads(discovery_json.read_text(encoding="utf-8"))
    if not isinstance(discovery, dict) or "reference_selection_status" not in discovery or "selected_reference_reports" not in discovery:
        reroute = make_reroute(
            target_skill="course-lab-discovery",
            reason_code="malformed-discovery-contract",
            reason_summary="The discovery JSON is missing required reference-selection fields.",
        )
        return build_blocked_summary(
            selection_status="malformed",
            reason_code="malformed-discovery-contract",
            reason_summary="The discovery JSON is missing required reference-selection fields.",
            reroute=reroute,
        )

    selection_status = discovery["reference_selection_status"]
    if selection_status == "ambiguous":
        reroute = make_reroute(
            target_skill="course-lab-discovery",
            reason_code="ambiguous-reference-selection",
            reason_summary="Discovery found plausible same-experiment references but could not confirm the bundle.",
        )
        return build_blocked_summary(
            selection_status="ambiguous",
            reason_code="ambiguous-reference-selection",
            reason_summary="Discovery found plausible same-experiment references but could not confirm the bundle.",
            reroute=reroute,
        )

    if selection_status == "none_found":
        return {
            "enabled": True,
            "selection_status": "none_found",
            "pass": False,
            "blocked": False,
            "blocked_reference_decode_items": [],
            "missing_structure_items": [],
            "missing_content_items": [],
            "declared_unresolved_items": [],
            "data_lack_suspected_items": [],
            "recommended_reroutes": [],
        }

    selected = discovery["selected_reference_reports"]
    if not isinstance(selected, list):
        reroute = make_reroute(
            target_skill="course-lab-discovery",
            reason_code="malformed-discovery-contract",
            reason_summary="The discovery JSON does not contain a usable selected_reference_reports list.",
        )
        return build_blocked_summary(
            selection_status="malformed",
            reason_code="malformed-discovery-contract",
            reason_summary="The discovery JSON does not contain a usable selected_reference_reports list.",
            reroute=reroute,
        )

    try:
        tex_text = expand_tex_tree(main_tex)
    except FileNotFoundError as exc:
        reroute = make_reroute(
            target_skill="course-lab-final-staging",
            reason_code="tex-include-missing",
            reason_summary=str(exc),
        )
        return build_blocked_summary(
            selection_status="selected",
            reason_code="tex-include-missing",
            reason_summary=str(exc),
            reroute=reroute,
        )

    blocked_reference_decode_items: list[dict[str, object]] = []
    reference_items: list[dict[str, object]] = []
    for entry in selected:
        if not isinstance(entry, dict):
            continue
        source_reference = str(entry.get("pdf_path") or "")
        markdown_path = entry.get("expected_decoded_markdown_path")
        if not isinstance(markdown_path, str) or not markdown_path:
            blocked_reference_decode_items.append(
                {
                    "target_skill": "course-lab-discovery",
                    "reason_code": "malformed-discovery-contract",
                    "reason_summary": "A selected reference is missing the expected_decoded_markdown_path field.",
                    "source_reference": source_reference,
                }
            )
            continue
        markdown_file = Path(markdown_path)
        if not markdown_file.exists():
            blocked_reference_decode_items.append(
                {
                    "target_skill": "course-lab-handout-normalization",
                    "reason_code": "reference-markdown-missing",
                    "reason_summary": "The selected reference still lacks decoded Markdown for late comparison.",
                    "source_reference": source_reference,
                }
            )
            continue
        markdown_text = markdown_file.read_text(encoding="utf-8", errors="replace")
        reference_items.extend(extract_reference_items(markdown_text, source_reference=source_reference or markdown_path))

    if blocked_reference_decode_items:
        reroute = blocked_reference_decode_items[0]
        return {
            "enabled": True,
            "selection_status": "selected",
            "pass": False,
            "blocked": True,
            "blocked_reference_decode_items": blocked_reference_decode_items,
            "missing_structure_items": [],
            "missing_content_items": [],
            "declared_unresolved_items": [],
            "data_lack_suspected_items": [],
            "recommended_reroutes": [reroute],
        }

    normalized_tex = normalize_text(tex_text)
    missing_structure_items: list[dict[str, object]] = []
    missing_content_items: list[dict[str, object]] = []
    declared_unresolved_items: list[dict[str, object]] = []
    data_lack_suspected_items: list[dict[str, object]] = []

    for item in reference_items:
        heading = str(item.get("heading") or "")
        anchor_text = str(item.get("anchor_text") or "")
        source_reference = str(item.get("source_reference") or "")
        heading_norm = normalize_text(heading)
        anchor_norm = normalize_text(anchor_text)

        heading_present = bool(heading_norm and heading_norm in normalized_tex)
        anchor_present = bool(anchor_norm and text_matches(anchor_norm, normalized_tex))

        if heading_norm and not heading_present:
            missing_structure_items.append(
                {
                    "target_skill": "course-lab-body-scaffold",
                    "reason_code": "reference-procedure-structure-missing",
                    "reason_summary": "A selected same-experiment reference contains a heading lane that is missing from main.tex.",
                    "source_reference": source_reference,
                    "heading": heading,
                    "anchor_text": anchor_text,
                }
            )
            continue

        if not heading_norm and anchor_norm and anchor_present:
            continue

        local_body = extract_section_body(tex_text, heading) if heading_present else tex_text
        normalized_body = normalize_text(local_body)

        if heading_present and ("\\NeedsInput{" in local_body or "TBD" in local_body):
            declared_unresolved_items.append(
                {
                    "target_skill": "course-lab-final-staging",
                    "reason_code": "reference-procedure-declared-unresolved",
                    "reason_summary": "The matching report lane is present but explicitly left unresolved with a visible placeholder.",
                    "source_reference": source_reference,
                    "heading": heading,
                    "anchor_text": anchor_text,
                }
            )
            continue

        if heading_present and contains_any(normalized_body, DATA_LACK_KEYWORDS):
            data_lack_suspected_items.append(
                {
                    "target_skill": "course-lab-final-staging",
                    "reason_code": "reference-procedure-data-lack-suspected",
                    "reason_summary": "The matching report lane admits missing data but has not yet been converted into an explicit TBD or NeedsInput marker.",
                    "source_reference": source_reference,
                    "heading": heading,
                    "anchor_text": anchor_text,
                }
            )
            continue

        reference_expectation_text = normalize_text(" ".join(part for part in (heading, anchor_text) if part))
        if heading_present and contains_any(reference_expectation_text, THEORY_KEYWORDS) and not contains_any(normalized_body, THEORY_KEYWORDS):
            missing_content_items.append(
                {
                    "target_skill": "course-lab-results-interpretation",
                    "reason_code": "reference-procedure-interpretation-gap",
                    "reason_summary": "The report has the heading lane, but it does not yet include the comparison or evidence support visible in the reference lane.",
                    "source_reference": source_reference,
                    "heading": heading,
                    "anchor_text": anchor_text,
                }
            )
            continue

        if heading_present:
            thin_body = len(normalized_body) < 20
            if anchor_norm and not text_matches(anchor_norm, normalized_body) and thin_body:
                missing_content_items.append(
                    {
                        "target_skill": "course-lab-final-staging",
                        "reason_code": "reference-procedure-content-missing",
                        "reason_summary": "The report has the lane heading but still lacks substantive content from the reference lane.",
                        "source_reference": source_reference,
                        "heading": heading,
                        "anchor_text": anchor_text,
                    }
                )
                continue
            if not anchor_norm and normalized_body:
                continue
            if anchor_norm and text_matches(anchor_norm, normalized_body):
                continue

        if not anchor_present:
            missing_content_items.append(
                {
                    "target_skill": "course-lab-final-staging",
                    "reason_code": "reference-procedure-content-missing",
                    "reason_summary": "The report does not yet present a body-anchor-only operation block found in the reference lane.",
                    "source_reference": source_reference,
                    "heading": heading,
                    "anchor_text": anchor_text,
                }
            )

    recommended_reroutes: list[dict[str, object]] = []
    for group in (missing_structure_items, missing_content_items, declared_unresolved_items, data_lack_suspected_items):
        for item in group:
            reroute = make_reroute(
                target_skill=str(item["target_skill"]),
                reason_code=str(item["reason_code"]),
                reason_summary=str(item["reason_summary"]),
                source_reference=str(item.get("source_reference") or ""),
                missing_items=[part for part in (str(item.get("heading") or ""), str(item.get("anchor_text") or "")) if part],
            )
            if reroute not in recommended_reroutes:
                recommended_reroutes.append(reroute)

    return {
        "enabled": True,
        "selection_status": "selected",
        "pass": not missing_structure_items and not missing_content_items and not blocked_reference_decode_items and not declared_unresolved_items and not data_lack_suspected_items,
        "blocked": False,
        "blocked_reference_decode_items": blocked_reference_decode_items,
        "missing_structure_items": missing_structure_items,
        "missing_content_items": missing_content_items,
        "declared_unresolved_items": declared_unresolved_items,
        "data_lack_suspected_items": data_lack_suspected_items,
        "recommended_reroutes": recommended_reroutes,
    }
