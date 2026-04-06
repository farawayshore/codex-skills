from __future__ import annotations

import re
from pathlib import Path
from typing import Any


DEFAULT_OBSERVED_LABEL = "Observed evidence"
DEFAULT_COMPARISON_LABEL = "Comparison evidence"
CONFIDENCE_LEVELS = {"low", "medium", "high"}
CASE_ID_RE = re.compile(r"case[-_]?([a-z0-9]+)", re.IGNORECASE)


def infer_case_id(value: object, *, default: str) -> str:
    text = str(value or "").strip()
    if not text:
        return default

    match = CASE_ID_RE.search(text)
    if match:
        return f"case-{match.group(1).lower()}"

    basename = Path(text).name
    prefix = re.match(r"(\d+)(?:\D|$)", basename)
    if prefix:
        return f"case-{prefix.group(1)}"

    return default


def infer_case_title(case_id: str) -> str:
    suffix = case_id.removeprefix("case-").strip()
    if not suffix:
        return "Case"
    if suffix.isdigit():
        return f"Case {suffix}"
    return f"Case {suffix.replace('-', ' ').title()}"


def normalize_confidence(value: object) -> str:
    text = str(value or "").strip().lower()
    return text if text in CONFIDENCE_LEVELS else "low"


def normalize_caveats(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def has_explicit_case_identity(raw_case: dict[str, object]) -> bool:
    return any(
        str(raw_case.get(field) or "").strip()
        for field in ("case_id", "title", "label")
    )


def has_substantive_case_content(normalized_case: dict[str, object]) -> bool:
    if str(normalized_case.get("observed_summary") or "").strip():
        return True
    if str(normalized_case.get("comparison_summary") or "").strip():
        return True
    if str(normalized_case.get("agreement_summary") or "").strip():
        return True
    if list(normalized_case.get("caveats") or []):
        return True
    return False


def normalize_comparison_case_record(
    raw_case: dict[str, object],
    *,
    default_case_id: str,
) -> dict[str, object] | None:
    case_id = infer_case_id(
        raw_case.get("case_id")
        or raw_case.get("title")
        or raw_case.get("observed_asset_path")
        or raw_case.get("comparison_asset_path"),
        default=default_case_id,
    )

    observed_asset_path = str(
        raw_case.get("observed_asset_path")
        or raw_case.get("observed_path")
        or raw_case.get("observed_asset")
        or ""
    ).strip()
    comparison_asset_path = str(
        raw_case.get("comparison_asset_path")
        or raw_case.get("comparison_path")
        or raw_case.get("comparison_asset")
        or raw_case.get("reference_asset_path")
        or ""
    ).strip()

    normalized_case = {
        "case_id": case_id,
        "title": str(raw_case.get("title") or raw_case.get("label") or infer_case_title(case_id)).strip() or infer_case_title(case_id),
        "observed_label": str(raw_case.get("observed_label") or raw_case.get("observed_name") or DEFAULT_OBSERVED_LABEL).strip() or DEFAULT_OBSERVED_LABEL,
        "observed_summary": str(raw_case.get("observed_summary") or raw_case.get("observed_text") or "").strip(),
        "comparison_label": str(
            raw_case.get("comparison_label")
            or raw_case.get("reference_label")
            or raw_case.get("modeled_label")
            or DEFAULT_COMPARISON_LABEL
        ).strip()
        or DEFAULT_COMPARISON_LABEL,
        "comparison_summary": str(
            raw_case.get("comparison_summary")
            or raw_case.get("comparison_text")
            or raw_case.get("reference_summary")
            or raw_case.get("modeled_summary")
            or ""
        ).strip(),
        "agreement_summary": str(raw_case.get("agreement_summary") or raw_case.get("agreement") or "").strip(),
        "caveats": normalize_caveats(raw_case.get("caveats")),
        "confidence": normalize_confidence(raw_case.get("confidence")),
        "observed_asset_path": observed_asset_path,
        "comparison_asset_path": comparison_asset_path,
    }
    if not has_explicit_case_identity(raw_case):
        return None
    if not has_substantive_case_content(normalized_case):
        return None
    return normalized_case


def normalize_comparison_cases(raw_cases: object) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []

    if isinstance(raw_cases, dict):
        items = list(raw_cases.items())
        iterable = []
        for key, value in items:
            if isinstance(value, dict):
                enriched = dict(value)
                enriched.setdefault("case_id", str(key))
                iterable.append(enriched)
        raw_iterable = iterable
    elif isinstance(raw_cases, list):
        raw_iterable = raw_cases
    else:
        return normalized

    for index, item in enumerate(raw_iterable, start=1):
        if not isinstance(item, dict):
            continue
        normalized_case = normalize_comparison_case_record(
            item,
            default_case_id=f"case-{index}",
        )
        if normalized_case is not None:
            normalized.append(normalized_case)

    return normalized
