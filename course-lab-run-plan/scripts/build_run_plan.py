from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from common import (
    LEAF_SKILL_BUCKET_KEYS,
    append_unique_list,
    build_leaf_skill_handoffs,
    build_run_readiness,
    build_source_artifacts,
    append_unique,
    has_any_keyword,
    iter_normalized_sections,
    normalize_text,
    utc_now_iso,
)

PROCEDURE_KEYWORDS = (
    "procedure",
    "procedural",
    "step",
    "align",
    "place",
    "adjust",
    "turn on",
    "move",
    "capture",
)
THEORY_KEYWORDS = (
    "introduction",
    "principle",
    "theory",
    "background",
)
DATA_KEYWORDS = (
    "table",
    "data",
    "record",
    "measure",
    "transcription",
)
FIGURE_KEYWORDS = (
    "figure",
    "photo",
    "image",
    "caption",
)
PLOT_KEYWORDS = (
    "plot",
    "graph",
    "chart",
)
DISCUSSION_KEYWORDS = (
    "thinking question",
    "question",
    "discuss",
    "compare",
    "explain",
    "why",
    "what would change",
    "discrepanc",
)
PROCESSING_KEYWORDS = (
    "calculate",
    "calculation",
    "compute",
    "derived",
    "derive",
    "estimate",
    "density",
    "young's modulus",
    "youngs modulus",
    "modulus",
    "wave speed",
    "c_bar",
    "ratio",
    "error",
    "evaluate",
    "求出",
    "算出",
    "计算",
    "密度",
    "杨氏模量",
    "波速",
    "频率",
    "半径",
    "误差",
)
SIMULATION_KEYWORDS = (
    "simulation",
    "simulate",
    "model",
    "mode shape",
    "mode-pattern",
    "mode pattern",
    "mathematica",
    "matlab",
    "仿真",
    "模拟",
    "数值",
)
REFERENCE_KEYWORDS = (
    "reference",
    "references",
    "reference value",
    "literature",
    "现已有值",
    "参考文献",
    "文献",
)
OBSERVATION_KEYWORDS = (
    "observation",
    "observe",
    "record",
    "note",
    "pattern",
    "photo",
    "image",
    "figure",
    "测出",
    "记录",
    "观察",
    "拍下",
)
UNRESOLVED_KEYWORDS = (
    "missing",
    "tbd",
    "to be confirmed",
    "unclear",
    "specify which",
)
BUCKET_SYNTHESIS_DEFAULTS: dict[str, dict[str, tuple[str, ...]]] = {
    "course-lab-body-scaffold": {
        "required_outputs_or_deliverables": (
            "Handout-aligned body scaffold with section skeletons, procedure anchors, and source-traceable placeholders.",
        ),
        "suggested_focus": (
            "Preserve the experiment flow and branch structure before later data, theory, and discussion content is inserted.",
        ),
        "enrichment_opportunities": (
            "Reserve insertion points for later plots, interpretation blocks, and figure evidence instead of flattening branches too early.",
        ),
    },
    "course-lab-experiment-principle": {
        "required_outputs_or_deliverables": (
            "Theory-facing principle package with report sections, equation hooks, and source-backed theory references.",
        ),
        "suggested_focus": (
            "Emphasize the principle, background, and modeling ideas that justify later experiment-versus-theory comparisons.",
        ),
        "enrichment_opportunities": (
            "Connect theory text to reference figures, modeled patterns, or cited sources when the handout exposes them.",
        ),
    },
    "course-lab-data-transfer": {
        "required_outputs_or_deliverables": (
            "Validated transfer artifact for raw measurements, observation notes, table records, and caption-linked evidence labels.",
        ),
        "suggested_focus": (
            "Keep every measured value and observation traceable to its original handout table or required-observation cue.",
        ),
        "enrichment_opportunities": (
            "Preserve case labels so later processing, plotting, and figure placement can reuse the same names without re-mapping.",
        ),
    },
    "course-lab-data-processing": {
        "required_outputs_or_deliverables": (
            "Derived-quantity processing artifact covering handout-named calculations, theory-side quantities, and comparison-ready summaries.",
        ),
        "suggested_focus": (
            "Process only quantities the handout makes explicit and keep formula-to-data traceability visible.",
        ),
        "enrichment_opportunities": (
            "Organize processed outputs so later interpretation can compare experiment, theory, and reference values branch by branch.",
        ),
    },
    "course-lab-plotting": {
        "required_outputs_or_deliverables": (
            "Plotting or comparison-visual package for any handout-required curves, graphs, mode-shape visuals, or radius comparisons.",
        ),
        "suggested_focus": (
            "Use the same case naming and measured quantities that appear in the transferred tables and observation records.",
        ),
        "enrichment_opportunities": (
            "Prefer visuals that can later sit beside photo evidence or theory-model comparisons without rework.",
        ),
    },
    "course-lab-results-interpretation": {
        "required_outputs_or_deliverables": (
            "Results-interpretation handoff comparing processed measurements with theory, references, or modeled expectations.",
        ),
        "suggested_focus": (
            "Compare processed measurements with theory, reference values, or modeled expectations at the case level.",
        ),
        "enrichment_opportunities": (
            "Promote the strongest evidence-backed comparison threads into discussion and final staging.",
        ),
    },
    "course-lab-discussion-ideas": {
        "required_outputs_or_deliverables": (
            "Discussion-idea bank keyed to handout thinking questions, improvement prompts, and anomaly explanations.",
        ),
        "suggested_focus": (
            "Turn open questions into concrete answer threads that depend on actual processed results and observed phenomena.",
        ),
        "enrichment_opportunities": (
            "Capture optional extensions, limitations, and method-improvement threads without forcing them into final prose yet.",
        ),
    },
    "course-lab-discussion-synthesis": {
        "required_outputs_or_deliverables": (
            "Discussion-synthesis handoff that merges approved idea threads into a concise, evidence-ordered storyline.",
        ),
        "suggested_focus": (
            "Group later discussion around the most defensible themes: comparison, discrepancy, limitations, and improvements.",
        ),
        "enrichment_opportunities": (
            "Keep lower-priority but interesting explanation threads parked for optional inclusion if space allows.",
        ),
    },
    "course-lab-final-staging": {
        "required_outputs_or_deliverables": (
            "Final-staging assembly plan mapping upstream artifacts into report order, appendix hooks, and cross-skill checkpoints.",
        ),
        "suggested_focus": (
            "Keep section order, case naming, and evidence dependencies aligned so late assembly does not relabel results.",
        ),
        "enrichment_opportunities": (
            "Use the run plan to reserve space for comparison tables, modeled figures, and appendix material before QC.",
        ),
    },
    "course-lab-figure-evidence": {
        "required_outputs_or_deliverables": (
            "Figure-evidence plan covering required photos, figures, captions, and evidence groupings.",
        ),
        "suggested_focus": (
            "Prioritize images or figure groups that the handout expects the report to compare against data or theory.",
        ),
        "enrichment_opportunities": (
            "Pair each photo-ready case with matching case labels, processed values, and theory-model references when available.",
        ),
    },
}
ALLOWED_COMPARISON_LANES = (
    "theory_vs_data",
    "simulation_vs_data",
    "literature_report_vs_data",
)
ALLOWED_SUPPORTING_BASES = (
    "handout_standard",
    "internet_reference",
)
HELPER_RESULT_TOKENS = (
    "helper",
    "tmp",
    "temp",
    "placeholder",
    "intermediate",
    "aux",
)
RESULT_SIGNAL_SPECS: tuple[dict[str, Any], ...] = (
    {"name": "wavelength", "label": "Wavelength", "result_kind": "quantitative", "keywords": ("wavelength", "lambda")},
    {
        "name": "fringe_spacing",
        "label": "Fringe spacing",
        "result_kind": "quantitative",
        "keywords": ("fringe spacing", "spacing of the fringes"),
    },
    {
        "name": "wave_speed",
        "label": "Wave speed",
        "result_kind": "quantitative",
        "keywords": ("wave speed", "c_bar", "c bar", "波速"),
    },
    {
        "name": "youngs_modulus",
        "label": "Young's modulus",
        "result_kind": "quantitative",
        "keywords": ("young's modulus", "youngs modulus", "杨氏模量"),
    },
    {"name": "density", "label": "Density", "result_kind": "quantitative", "keywords": ("density", "密度")},
    {"name": "frequency", "label": "Frequency", "result_kind": "quantitative", "keywords": ("frequency", "频率")},
    {"name": "radius", "label": "Radius", "result_kind": "quantitative", "keywords": ("radius", "半径")},
    {
        "name": "mode_shape",
        "label": "Mode shape",
        "result_kind": "qualitative",
        "keywords": ("mode shape", "mode pattern", "pattern shape", "振型"),
    },
    {
        "name": "central_maximum",
        "label": "Central maximum profile",
        "result_kind": "qualitative",
        "keywords": ("central maximum", "sharp or broadened", "broadened"),
    },
    {
        "name": "alignment_condition",
        "label": "Alignment condition",
        "result_kind": "qualitative",
        "keywords": ("misalignment", "stray-light", "stray light", "alignment"),
    },
)


def _clip_text(value: str, limit: int = 96) -> str:
    text = normalize_text(value).strip(" \t-:;,.")
    if not text:
        return ""
    if len(text) <= limit:
        return text
    clipped = text[: limit - 3].rstrip()
    if " " in clipped:
        clipped = clipped.rsplit(" ", 1)[0].rstrip(" ,;:.")
    return clipped + "..."


def _preview(values: list[str], limit: int = 3) -> str:
    previews: list[str] = []
    for value in values:
        clipped = _clip_text(value)
        if clipped and clipped not in previews:
            previews.append(clipped)
        if len(previews) >= limit:
            break
    return ", ".join(previews)


def _extract_labeled_items(text: str, label: str, stop_markers: tuple[str, ...]) -> list[str]:
    stop_pattern = "|".join(re.escape(marker) for marker in stop_markers)
    pattern = re.compile(
        rf"{re.escape(label)}\s*(.+?)(?:(?:{stop_pattern})|$)",
        flags=re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return []
    captured = normalize_text(match.group(1))
    values: list[str] = []
    for piece in re.split(r"\s*,\s*", captured):
        cleaned = _clip_text(piece, limit=120)
        if cleaned:
            append_unique_list(values, cleaned)
    return values


def _append_bucket_values(
    leaf_skill_handoffs: dict[str, dict[str, Any]],
    bucket_key: str,
    field_name: str,
    values: tuple[str, ...] | list[str],
) -> None:
    for value in values:
        append_unique(leaf_skill_handoffs[bucket_key], field_name, value)


def _slugify_result_name(value: str) -> str:
    lowered = normalize_text(value).lower().replace("'", "")
    slug = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    if not slug:
        return "comparison_result"
    if slug[0].isdigit():
        slug = f"result_{slug}"
    return slug


def _normalize_lane_values(values: list[str] | tuple[str, ...] | None) -> list[str]:
    normalized: list[str] = []
    for value in values or []:
        cleaned = normalize_text(value).lower()
        if cleaned in ALLOWED_COMPARISON_LANES and cleaned not in normalized:
            normalized.append(cleaned)
    return normalized


def _normalize_supporting_bases(values: list[str] | tuple[str, ...] | None) -> list[str]:
    normalized: list[str] = []
    for value in values or []:
        cleaned = normalize_text(value).lower()
        if cleaned in ALLOWED_SUPPORTING_BASES and cleaned not in normalized:
            normalized.append(cleaned)
    return normalized


def _is_helper_result_name(name: str) -> bool:
    normalized = normalize_text(name).lower()
    return any(token in normalized for token in HELPER_RESULT_TOKENS)


def _find_result_signal_spec(text: str) -> dict[str, Any] | None:
    lowered = normalize_text(text).lower()
    for spec in RESULT_SIGNAL_SPECS:
        if any(keyword in lowered for keyword in spec["keywords"]):
            return spec
    return None


def _infer_result_kind(text: str, fallback: str | None = None) -> str:
    if fallback in {"quantitative", "qualitative"}:
        return fallback
    lowered = normalize_text(text).lower()
    qualitative_tokens = (
        "mode",
        "pattern",
        "shape",
        "photo",
        "observation",
        "sharp",
        "broad",
        "alignment",
        "stray",
    )
    if any(token in lowered for token in qualitative_tokens):
        return "qualitative"
    return "quantitative"


def _infer_lane_sets(
    signal_text: str,
    *,
    result_kind: str,
    has_references: bool,
    has_simulation_context: bool,
) -> tuple[list[str], list[str], list[str]]:
    lowered = normalize_text(signal_text).lower()
    required_lanes: list[str] = []
    optional_lanes: list[str] = []
    supporting_bases = ["handout_standard"]

    if has_any_keyword(lowered, SIMULATION_KEYWORDS):
        append_unique_list(required_lanes, "simulation_vs_data")
    if has_any_keyword(lowered, REFERENCE_KEYWORDS):
        append_unique_list(required_lanes, "literature_report_vs_data")
    if (
        has_any_keyword(
            lowered,
            (
                "compare",
                "theory",
                "theoretical",
                "prediction",
                "equation",
                "estimate",
                "calculate",
                "derived",
            ),
        )
        or has_any_keyword(lowered, PROCESSING_KEYWORDS)
        or not required_lanes
    ):
        append_unique_list(required_lanes, "theory_vs_data")

    if has_simulation_context and result_kind == "qualitative" and "simulation_vs_data" not in required_lanes:
        append_unique_list(optional_lanes, "simulation_vs_data")
    if has_references and "literature_report_vs_data" not in required_lanes:
        append_unique_list(optional_lanes, "literature_report_vs_data")
        append_unique_list(supporting_bases, "internet_reference")
    if "literature_report_vs_data" in required_lanes:
        append_unique_list(supporting_bases, "internet_reference")

    return required_lanes, optional_lanes, supporting_bases


def _make_comparison_obligation(
    *,
    name: str,
    label: str,
    result_kind: str,
    importance_origin: str,
    importance_reason: str,
    required_lanes: list[str],
    optional_lanes: list[str],
    supporting_bases: list[str],
    source_signals: list[str],
    confirmation_state: str = "confirmed",
) -> dict[str, Any]:
    return {
        "name": name,
        "label": label,
        "result_kind": result_kind,
        "importance_origin": importance_origin,
        "importance_reason": importance_reason,
        "confirmation_state": confirmation_state,
        "required_lanes": _normalize_lane_values(required_lanes),
        "optional_lanes": _normalize_lane_values(optional_lanes),
        "supporting_bases": _normalize_supporting_bases(supporting_bases),
        "source_signals": [value for value in source_signals if value],
    }


def _record_comparison_obligation(
    obligations_by_name: dict[str, dict[str, Any]],
    obligation: dict[str, Any] | None,
) -> None:
    if not obligation:
        return
    existing = obligations_by_name.get(obligation["name"])
    if not existing:
        obligations_by_name[obligation["name"]] = obligation
        return
    for field_name in ("required_lanes", "optional_lanes", "supporting_bases", "source_signals"):
        for value in obligation[field_name]:
            if value not in existing[field_name]:
                existing[field_name].append(value)
    if not existing["importance_reason"] and obligation["importance_reason"]:
        existing["importance_reason"] = obligation["importance_reason"]


def _build_handout_comparison_obligation(
    signal_text: str,
    *,
    origin_reason: str,
    facts: dict[str, Any],
    allow_generic_label: bool = False,
) -> dict[str, Any] | None:
    spec = _find_result_signal_spec(signal_text)
    if spec is None and not allow_generic_label:
        return None

    if spec is None:
        label = _clip_text(signal_text, limit=80)
        name = _slugify_result_name(label)
        result_kind = _infer_result_kind(signal_text)
    else:
        label = spec["label"]
        name = spec["name"]
        result_kind = spec["result_kind"]

    if _is_helper_result_name(name):
        return None

    required_lanes, optional_lanes, supporting_bases = _infer_lane_sets(
        signal_text,
        result_kind=result_kind,
        has_references=facts["has_references"],
        has_simulation_context=bool(facts["simulation_cues"]),
    )
    return _make_comparison_obligation(
        name=name,
        label=label,
        result_kind=result_kind,
        importance_origin="handout_required",
        importance_reason=origin_reason,
        required_lanes=required_lanes,
        optional_lanes=optional_lanes,
        supporting_bases=supporting_bases,
        source_signals=[signal_text],
    )


def _build_agent_confirmed_obligation(
    item: dict[str, Any],
    *,
    facts: dict[str, Any],
) -> dict[str, Any] | None:
    confirmation_state = normalize_text(item.get("confirmation_state") or item.get("status") or "confirmed").lower()
    if confirmation_state and confirmation_state not in {"confirmed", "approved"}:
        return None

    label = normalize_text(item.get("label", ""))
    importance_reason = normalize_text(item.get("importance_reason", ""))
    raw_name = normalize_text(item.get("name", "")) or _slugify_result_name(label or importance_reason)
    name = _slugify_result_name(raw_name)
    if _is_helper_result_name(name):
        return None

    combined_text = " ".join(part for part in (name, label, importance_reason) if part)
    spec = _find_result_signal_spec(combined_text)
    label = label or (spec["label"] if spec else raw_name.replace("_", " ").strip().title())
    result_kind = _infer_result_kind(combined_text, fallback=normalize_text(item.get("result_kind", "")).lower())

    required_lanes = _normalize_lane_values(item.get("required_lanes"))
    optional_lanes = _normalize_lane_values(item.get("optional_lanes"))
    supporting_bases = _normalize_supporting_bases(item.get("supporting_bases"))
    if not required_lanes and not optional_lanes:
        required_lanes, optional_lanes, inferred_supporting_bases = _infer_lane_sets(
            combined_text,
            result_kind=result_kind,
            has_references=facts["has_references"],
            has_simulation_context=bool(facts["simulation_cues"]),
        )
        if not supporting_bases:
            supporting_bases = inferred_supporting_bases
    elif not supporting_bases:
        supporting_bases = ["internet_reference"] if "literature_report_vs_data" in required_lanes else ["handout_standard"]

    return _make_comparison_obligation(
        name=name,
        label=label,
        result_kind=result_kind,
        importance_origin="agent_confirmed",
        importance_reason=importance_reason or "User-approved agent-confirmed comparison result.",
        required_lanes=required_lanes,
        optional_lanes=optional_lanes,
        supporting_bases=supporting_bases,
        source_signals=[combined_text],
    )


def _collect_handout_facts(sections: dict[str, Any]) -> dict[str, Any]:
    facts: dict[str, Any] = {
        "result_families": [],
        "required_observations": [],
        "thinking_questions": [],
        "table_cues": [],
        "image_cues": [],
        "comparison_cues": [],
        "simulation_cues": [],
        "processing_cues": [],
        "has_references": False,
        "has_multi_branch_context": False,
    }
    all_text_chunks: list[str] = []
    section_prefixes: set[str] = set()
    for section_key, section, normalized in iter_normalized_sections(sections):
        if "::" in section_key:
            prefix = section_key.split("::", 1)[0]
            if prefix:
                section_prefixes.add(prefix)
        heading = normalized["heading"][0] if normalized["heading"] else ""
        text = normalize_text(section.get("text", ""))
        list_items = normalized["list_items"]
        table_cues = normalized["tables"]
        image_cues = normalized["images"]
        subheadings = normalized["subheadings"]
        all_text_chunks.extend([heading, text, *list_items, *table_cues, *image_cues, *subheadings])
        searchable = normalize_text(" ".join([heading, text, *list_items, *table_cues, *image_cues, *subheadings]))

        if has_any_keyword(f"{heading} {searchable}", ("thinking question", "thinking questions", "思考题")):
            for item in list_items:
                append_unique_list(facts["thinking_questions"], item)
        if table_cues:
            for item in table_cues:
                append_unique_list(facts["table_cues"], item)
        if image_cues:
            for item in image_cues:
                append_unique_list(facts["image_cues"], item)
        if has_any_keyword(searchable, DISCUSSION_KEYWORDS):
            for item in list_items:
                if has_any_keyword(item, DISCUSSION_KEYWORDS):
                    append_unique_list(facts["comparison_cues"], item)
            if heading:
                append_unique_list(facts["comparison_cues"], heading)
        if has_any_keyword(searchable, SIMULATION_KEYWORDS):
            if heading:
                append_unique_list(facts["simulation_cues"], heading)
            for item in list_items:
                if has_any_keyword(item, SIMULATION_KEYWORDS):
                    append_unique_list(facts["simulation_cues"], item)
            if text and has_any_keyword(text, SIMULATION_KEYWORDS):
                append_unique_list(facts["simulation_cues"], text)
        if has_any_keyword(searchable, PROCESSING_KEYWORDS):
            if heading:
                append_unique_list(facts["processing_cues"], heading)
            for item in list_items:
                if has_any_keyword(item, PROCESSING_KEYWORDS):
                    append_unique_list(facts["processing_cues"], item)
            if text and has_any_keyword(text, PROCESSING_KEYWORDS):
                append_unique_list(facts["processing_cues"], text)
        if has_any_keyword(searchable, REFERENCE_KEYWORDS):
            facts["has_references"] = True
    combined_text = "\n".join(chunk for chunk in all_text_chunks if chunk)
    facts["result_families"] = _extract_labeled_items(
        combined_text,
        "Required result families:",
        ("Required observations:", "Compare data with theory", "LX1 expects:", "Both handouts describe"),
    )
    facts["required_observations"] = _extract_labeled_items(
        combined_text,
        "Required observations:",
        ("Compare data with theory", "LX1 expects:", "Both handouts describe"),
    )
    facts["has_multi_branch_context"] = len({prefix for prefix in section_prefixes if prefix not in {"combined"}}) > 1
    return facts


def _synthesize_bucket_content(
    leaf_skill_handoffs: dict[str, dict[str, Any]],
    sections: dict[str, Any],
) -> list[str]:
    facts = _collect_handout_facts(sections)
    for bucket_key, defaults in BUCKET_SYNTHESIS_DEFAULTS.items():
        for field_name, values in defaults.items():
            _append_bucket_values(leaf_skill_handoffs, bucket_key, field_name, values)

    if facts["has_multi_branch_context"]:
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-body-scaffold",
            "suggested_focus",
            "Keep separate scaffold lanes for each experiment branch or case family before any combined writeup merges them.",
        )
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-final-staging",
            "enrichment_opportunities",
            "Keep branch-level artifacts separate until final staging so shared comparisons do not blur source traceability.",
        )

    if facts["result_families"]:
        preview = _preview(facts["result_families"])
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-data-processing",
            "required_outputs_or_deliverables",
            f"Named result-family coverage should stay visible for {preview}.",
        )
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-results-interpretation",
            "suggested_focus",
            f"Prioritize interpretation for named result families such as {preview}.",
        )
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-final-staging",
            "required_outputs_or_deliverables",
            f"Final assembly checkpoints should preserve the named result families, including {preview}.",
        )

    if facts["required_observations"]:
        preview = _preview(facts["required_observations"])
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-body-scaffold",
            "enrichment_opportunities",
            f"Reserve explicit subsection slots for required observations such as {preview}.",
        )
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-data-transfer",
            "suggested_focus",
            f"Capture required observations such as {preview} alongside the raw numeric records.",
        )
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-figure-evidence",
            "suggested_focus",
            f"Prefer figure groups that make required observations visible, including {preview}.",
        )

    if facts["table_cues"]:
        preview = _preview(facts["table_cues"])
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-data-transfer",
            "required_outputs_or_deliverables",
            f"Transfer coverage should include the handout-named tables or records such as {preview}.",
        )
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-plotting",
            "suggested_focus",
            f"Use table-backed case naming from cues such as {preview} so later plots stay traceable.",
        )

    if facts["image_cues"]:
        preview = _preview(facts["image_cues"])
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-figure-evidence",
            "required_outputs_or_deliverables",
            f"Figure evidence should cover handout-named image cues such as {preview}.",
        )
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-data-transfer",
            "enrichment_opportunities",
            f"Keep caption-compatible labels for image cues such as {preview}.",
        )

    if facts["simulation_cues"]:
        preview = _preview(facts["simulation_cues"])
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-experiment-principle",
            "suggested_focus",
            f"Carry forward the handout's modeling or simulation cues, including {preview}.",
        )
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-plotting",
            "enrichment_opportunities",
            f"Prepare visuals that can sit beside modeled or simulated references such as {preview}.",
        )
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-final-staging",
            "required_outputs_or_deliverables",
            "Late-stage assembly should preserve appendix code hooks for major modeling or simulation artifacts when the handout asks for report-side comparison.",
        )
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-final-staging",
            "suggested_focus",
            f"Keep modeled comparisons such as {preview} traceable to any later appendix code attachment instead of flattening them into prose-only references.",
        )
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-figure-evidence",
            "enrichment_opportunities",
            "Pair observed photos or figures with modeled mode shapes or simulation references when the handout explicitly asks for comparison.",
        )

    if facts["comparison_cues"]:
        preview = _preview(facts["comparison_cues"])
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-results-interpretation",
            "enrichment_opportunities",
            f"Use comparison prompts such as {preview} to anchor discrepancy analysis and later discussion handoff.",
        )
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-discussion-ideas",
            "enrichment_opportunities",
            f"Promote comparison prompts such as {preview} into candidate discussion angles after the evidence is stable.",
        )

    if facts["processing_cues"]:
        preview = _preview(facts["processing_cues"])
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-data-processing",
            "suggested_focus",
            f"Prioritize explicitly named calculations or derived quantities such as {preview}.",
        )
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-results-interpretation",
            "required_outputs_or_deliverables",
            f"Interpretation should stay tied to processed quantities or calculations such as {preview}.",
        )

    if facts["thinking_questions"]:
        preview = _preview(facts["thinking_questions"])
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-discussion-ideas",
            "suggested_focus",
            f"Answer the strongest thinking-question prompts directly, including {preview}.",
        )
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-discussion-synthesis",
            "enrichment_opportunities",
            f"Keep the most evidence-backed answer threads from prompts such as {preview} available for later compression.",
        )

    if facts["has_references"]:
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-experiment-principle",
            "enrichment_opportunities",
            "Reuse cited literature or reference values where the handout already names them instead of paraphrasing theory in isolation.",
        )
        _route_section_text(
            leaf_skill_handoffs,
            "course-lab-results-interpretation",
            "suggested_focus",
            "Keep experimental-versus-reference comparisons explicit when the handout already provides literature or reference values.",
        )

    global_enrichment_opportunities = [
        "Keep downstream skills synchronized on shared case labels, branch names, and source traceability.",
    ]
    if facts["has_multi_branch_context"]:
        append_unique_list(
            global_enrichment_opportunities,
            "Keep multi-branch experiment families separated in intermediate artifacts, then merge only at final staging.",
        )
    if facts["table_cues"] and facts["image_cues"]:
        append_unique_list(
            global_enrichment_opportunities,
            "Cross-link table-backed cases, plots, and photo or figure evidence under the same case labels.",
        )
    if facts["comparison_cues"] and (facts["simulation_cues"] or facts["has_references"]):
        append_unique_list(
            global_enrichment_opportunities,
            "Use theory, reference, or modeled comparisons as explicit cross-skill anchors instead of leaving them implicit.",
        )
    if facts["thinking_questions"]:
        append_unique_list(
            global_enrichment_opportunities,
            "Promote the strongest discrepancy or improvement questions only after the supporting calculations and evidence are stable.",
        )
    return global_enrichment_opportunities


def _route_section_text(
    leaf_skill_handoffs: dict[str, dict[str, Any]], bucket_key: str, field_name: str, value: str
) -> None:
    append_unique(leaf_skill_handoffs[bucket_key], field_name, value)


def _matching_bucket_keys(text: str) -> tuple[str, ...]:
    bucket_keys: list[str] = []
    if has_any_keyword(text, PROCEDURE_KEYWORDS):
        append_unique_list(bucket_keys, "course-lab-body-scaffold")
    if has_any_keyword(text, THEORY_KEYWORDS):
        append_unique_list(bucket_keys, "course-lab-experiment-principle")
    if has_any_keyword(text, DATA_KEYWORDS):
        append_unique_list(bucket_keys, "course-lab-data-transfer")
    if has_any_keyword(text, PROCESSING_KEYWORDS):
        append_unique_list(bucket_keys, "course-lab-data-processing")
    if has_any_keyword(text, PLOT_KEYWORDS):
        append_unique_list(bucket_keys, "course-lab-plotting")
    if has_any_keyword(text, FIGURE_KEYWORDS):
        append_unique_list(bucket_keys, "course-lab-figure-evidence")
    if has_any_keyword(text, DISCUSSION_KEYWORDS):
        append_unique_list(bucket_keys, "course-lab-discussion-ideas")
    if has_any_keyword(text, ("analysis", "compare", "explain", "discrepanc")):
        append_unique_list(bucket_keys, "course-lab-results-interpretation")
    return tuple(bucket_keys)


def _route_unresolved_item(
    leaf_skill_handoffs: dict[str, dict[str, Any]],
    global_unresolved_gaps: list[str],
    value: str,
) -> None:
    if not has_any_keyword(value, UNRESOLVED_KEYWORDS):
        return
    matched_buckets = _matching_bucket_keys(value) or ("course-lab-final-staging",)
    for bucket_key in matched_buckets:
        _route_section_text(leaf_skill_handoffs, bucket_key, "unresolved_gaps", value)
    append_unique_list(global_unresolved_gaps, value)


def _route_section(
    leaf_skill_handoffs: dict[str, dict[str, Any]],
    global_unresolved_gaps: list[str],
    section_key: str,
    section: dict[str, Any],
    normalized: dict[str, list[str]],
) -> None:
    heading = normalized["heading"][0] if normalized["heading"] else ""
    section_text = " ".join(normalized["text"] + normalized["list_items"] + normalized["tables"] + normalized["images"])
    searchable = normalize_text(" ".join([heading, section_text, " ".join(normalized["subheadings"])]))

    if has_any_keyword(searchable, PROCEDURE_KEYWORDS):
        if heading:
            _route_section_text(leaf_skill_handoffs, "course-lab-body-scaffold", "required_inputs_from_handout", heading)
        for item in normalized["list_items"]:
            if has_any_keyword(item, PROCEDURE_KEYWORDS):
                _route_section_text(
                    leaf_skill_handoffs,
                    "course-lab-body-scaffold",
                    "required_inputs_from_handout",
                    item,
                )
                _route_section_text(
                    leaf_skill_handoffs,
                    "course-lab-body-scaffold",
                    "candidate_sections",
                    item,
                )
        for subheading in normalized["subheadings"]:
            if has_any_keyword(subheading, PROCEDURE_KEYWORDS):
                _route_section_text(
                    leaf_skill_handoffs,
                    "course-lab-body-scaffold",
                    "candidate_sections",
                    subheading,
                )

    if has_any_keyword(searchable, THEORY_KEYWORDS):
        if heading:
            _route_section_text(
                leaf_skill_handoffs,
                "course-lab-experiment-principle",
                "candidate_sections",
                heading,
            )
        for subheading in normalized["subheadings"]:
            if has_any_keyword(subheading, THEORY_KEYWORDS):
                _route_section_text(
                    leaf_skill_handoffs,
                    "course-lab-experiment-principle",
                    "candidate_sections",
                    subheading,
                )

    if has_any_keyword(searchable, DATA_KEYWORDS) or normalized["tables"]:
        if heading:
            _route_section_text(
                leaf_skill_handoffs,
                "course-lab-data-transfer",
                "required_inputs_from_handout",
                heading,
            )
        for table in normalized["tables"]:
            _route_section_text(
                leaf_skill_handoffs,
                "course-lab-data-transfer",
                "required_inputs_from_handout",
                f"Table: {table}",
            )

    if has_any_keyword(searchable, PROCESSING_KEYWORDS):
        if heading:
            _route_section_text(
                leaf_skill_handoffs,
                "course-lab-data-processing",
                "required_inputs_from_handout",
                heading,
            )
        for item in normalized["list_items"]:
            if has_any_keyword(item, PROCESSING_KEYWORDS):
                _route_section_text(
                    leaf_skill_handoffs,
                    "course-lab-data-processing",
                    "required_inputs_from_handout",
                    item,
                )
                _route_section_text(
                    leaf_skill_handoffs,
                    "course-lab-data-processing",
                    "candidate_sections",
                    item,
                )

    if has_any_keyword(searchable, PLOT_KEYWORDS):
        if heading:
            _route_section_text(
                leaf_skill_handoffs,
                "course-lab-plotting",
                "required_inputs_from_handout",
                heading,
            )
        for item in normalized["list_items"]:
            if has_any_keyword(item, PLOT_KEYWORDS):
                _route_section_text(
                    leaf_skill_handoffs,
                    "course-lab-plotting",
                    "required_inputs_from_handout",
                    item,
                )

    if has_any_keyword(searchable, FIGURE_KEYWORDS) or normalized["images"]:
        if heading:
            _route_section_text(
                leaf_skill_handoffs,
                "course-lab-figure-evidence",
                "required_inputs_from_handout",
                heading,
            )
        for image in normalized["images"]:
            _route_section_text(
                leaf_skill_handoffs,
                "course-lab-figure-evidence",
                "required_inputs_from_handout",
                image,
            )
        for item in normalized["list_items"]:
            if has_any_keyword(item, FIGURE_KEYWORDS):
                _route_section_text(
                    leaf_skill_handoffs,
                    "course-lab-figure-evidence",
                    "required_inputs_from_handout",
                    item,
                )

    if has_any_keyword(searchable, DISCUSSION_KEYWORDS):
        if heading:
            _route_section_text(
                leaf_skill_handoffs,
                "course-lab-discussion-ideas",
                "candidate_sections",
                heading,
            )
        for item in normalized["list_items"]:
            if has_any_keyword(item, DISCUSSION_KEYWORDS):
                _route_section_text(
                    leaf_skill_handoffs,
                    "course-lab-discussion-ideas",
                    "required_inputs_from_handout",
                    item,
                )
                _route_section_text(
                    leaf_skill_handoffs,
                    "course-lab-discussion-ideas",
                    "candidate_sections",
                    item,
                )

    if has_any_keyword(searchable, ("analysis", "compare", "explain", "discrepanc")):
        if heading:
            _route_section_text(
                leaf_skill_handoffs,
                "course-lab-results-interpretation",
                "candidate_sections",
                heading,
            )
        for item in normalized["list_items"]:
            if has_any_keyword(item, ("compare", "explain", "discrepanc")):
                _route_section_text(
                    leaf_skill_handoffs,
                    "course-lab-results-interpretation",
                    "required_inputs_from_handout",
                    item,
                )

    for item in normalized["list_items"]:
        _route_unresolved_item(leaf_skill_handoffs, global_unresolved_gaps, item)


def _route_handout_cues(sections: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    leaf_skill_handoffs = build_leaf_skill_handoffs()
    global_unresolved_gaps: list[str] = []
    for section_key, section, normalized in iter_normalized_sections(sections):
        _route_section(leaf_skill_handoffs, global_unresolved_gaps, section_key, section, normalized)
    return leaf_skill_handoffs, global_unresolved_gaps


def build_comparison_obligations(
    *,
    sections: dict[str, Any],
    sections_markdown: str,
    confirmed_agent_key_results: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    del sections_markdown  # Reserved for future rule expansion; structured sections drive current extraction.

    facts = _collect_handout_facts(sections)
    obligations_by_name: dict[str, dict[str, Any]] = {}

    for signal_text in facts["result_families"]:
        _record_comparison_obligation(
            obligations_by_name,
            _build_handout_comparison_obligation(
                signal_text,
                origin_reason="Handout explicitly names this required result family for later comparison.",
                facts=facts,
                allow_generic_label=True,
            ),
        )

    for signal_text in facts["comparison_cues"]:
        _record_comparison_obligation(
            obligations_by_name,
            _build_handout_comparison_obligation(
                signal_text,
                origin_reason="Handout comparison cue requires this result to stay in the official comparison contract.",
                facts=facts,
            ),
        )

    for signal_text in facts["processing_cues"]:
        _record_comparison_obligation(
            obligations_by_name,
            _build_handout_comparison_obligation(
                signal_text,
                origin_reason="Handout processing cue names a comparison-ready quantity that later skills must preserve.",
                facts=facts,
            ),
        )

    for signal_text in facts["required_observations"]:
        _record_comparison_obligation(
            obligations_by_name,
            _build_handout_comparison_obligation(
                signal_text,
                origin_reason="Required observation should stay visible for later comparison and discrepancy analysis.",
                facts=facts,
            ),
        )

    for item in confirmed_agent_key_results or []:
        if isinstance(item, dict):
            _record_comparison_obligation(
                obligations_by_name,
                _build_agent_confirmed_obligation(item, facts=facts),
            )

    return sorted(obligations_by_name.values(), key=lambda item: item["name"])


def build_run_plan(
    *,
    sections: dict[str, Any],
    sections_markdown: str,
    workspace: Path,
    experiment_name: str,
    experiment_safe_name: str,
    report_language: str | None = None,
    confirmed_agent_key_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    leaf_skill_handoffs, global_unresolved_gaps = _route_handout_cues(sections)
    global_enrichment_opportunities = _synthesize_bucket_content(leaf_skill_handoffs, sections)
    return {
        "plan_metadata": {
            "experiment_name": experiment_name,
            "experiment_safe_name": experiment_safe_name,
            "workspace": str(workspace),
            "report_language": report_language,
            "generator_name": "course-lab-run-plan",
            "generator_version": "0.1.0",
            "generated_at": utc_now_iso(),
        },
        "source_artifacts": build_source_artifacts(
            sections=sections,
            sections_markdown=sections_markdown,
            workspace=str(workspace),
        ),
        "run_readiness": build_run_readiness(sections, sections_markdown),
        "leaf_skill_handoffs": leaf_skill_handoffs,
        "comparison_obligations": build_comparison_obligations(
            sections=sections,
            sections_markdown=sections_markdown,
            confirmed_agent_key_results=confirmed_agent_key_results,
        ),
        "global_enrichment_opportunities": global_enrichment_opportunities,
        "global_unresolved_gaps": global_unresolved_gaps,
    }


def _format_field_title(field_name: str) -> str:
    return field_name.replace("_", " ").title()


def render_run_plan_markdown(plan: dict[str, Any]) -> str:
    metadata = plan["plan_metadata"]
    source_artifacts = plan["source_artifacts"]
    run_readiness = plan["run_readiness"]
    lines = [
        f"# Run Plan: {metadata['experiment_name']}",
        "",
        "## Run Summary",
        f"- Experiment: {metadata['experiment_name']}",
        f"- Experiment Safe Name: {metadata['experiment_safe_name']}",
        f"- Workspace: {metadata['workspace']}",
        f"- Report Language: {metadata['report_language'] or 'Unspecified'}",
        "",
        "## Source Artifacts",
        f"- Workspace: {source_artifacts['workspace']}",
        f"- Sections JSON Title: {source_artifacts['sections'].get('title', '')}",
        "",
        "## Run Readiness",
    ]
    for key, value in run_readiness.items():
        lines.append(f"- {_format_field_title(key)}: {'yes' if value else 'no'}")

    for bucket_key, bucket in plan["leaf_skill_handoffs"].items():
        lines.extend(
            [
                "",
                f"## {bucket_key}",
                f"- Status: {bucket['status']}",
            ]
        )
        for field_name in (
            "required_inputs_from_handout",
            "candidate_sections",
            "required_outputs_or_deliverables",
            "suggested_focus",
            "enrichment_opportunities",
            "unresolved_gaps",
        ):
            values = bucket[field_name]
            lines.append(f"### {_format_field_title(field_name)}")
            if values:
                lines.extend(f"- {value}" for value in values)
            else:
                lines.append("- None")

    lines.extend(["", "## Comparison Obligations"])
    if plan["comparison_obligations"]:
        for obligation in plan["comparison_obligations"]:
            lines.extend(
                [
                    f"### {obligation['label']} (`{obligation['name']}`)",
                    f"- Importance Origin: {obligation['importance_origin']}",
                    f"- Confirmation State: {obligation['confirmation_state']}",
                    f"- Result Kind: {obligation['result_kind']}",
                    f"- Required Lanes: {', '.join(obligation['required_lanes']) or 'None'}",
                    f"- Optional Lanes: {', '.join(obligation['optional_lanes']) or 'None'}",
                    f"- Supporting Bases: {', '.join(obligation['supporting_bases']) or 'None'}",
                    f"- Importance Reason: {obligation['importance_reason']}",
                ]
            )
            if obligation["source_signals"]:
                lines.append("- Source Signals:")
                lines.extend(f"  - {value}" for value in obligation["source_signals"])
    else:
        lines.append("- None")

    lines.extend(["", "## Global Enrichment Opportunities"])
    if plan["global_enrichment_opportunities"]:
        lines.extend(f"- {value}" for value in plan["global_enrichment_opportunities"])
    else:
        lines.append("- None")

    lines.extend(["", "## Global Unresolved Gaps"])
    if plan["global_unresolved_gaps"]:
        lines.extend(f"- {value}" for value in plan["global_unresolved_gaps"])
    else:
        lines.append("- None")

    lines.append("")
    return "\n".join(lines)


def _read_sections_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Expected JSON object in {path}")
    return payload


def _read_confirmed_agent_key_results(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("confirmed_agent_key_results", "agent_key_results", "key_results"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    raise SystemExit(f"Expected a list of confirmed agent key results in {path}")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a course-lab run-plan contract.")
    parser.add_argument("--sections-json", required=True)
    parser.add_argument("--sections-markdown", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--experiment-name", required=True)
    parser.add_argument("--experiment-safe-name", required=True)
    parser.add_argument("--report-language")
    parser.add_argument("--confirmed-agent-key-results-json")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-markdown", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sections_json_path = Path(args.sections_json)
    sections_markdown_path = Path(args.sections_markdown)
    plan = build_run_plan(
        sections=_read_sections_json(sections_json_path),
        sections_markdown=sections_markdown_path.read_text(encoding="utf-8"),
        workspace=Path(args.workspace),
        experiment_name=args.experiment_name,
        experiment_safe_name=args.experiment_safe_name,
        report_language=args.report_language,
        confirmed_agent_key_results=_read_confirmed_agent_key_results(
            Path(args.confirmed_agent_key_results_json) if args.confirmed_agent_key_results_json else None
        ),
    )
    _write_json(Path(args.output_json), plan)
    _write_text(Path(args.output_markdown), render_run_plan_markdown(plan))
    return 0


__all__ = ["build_run_plan", "LEAF_SKILL_BUCKET_KEYS"]


if __name__ == "__main__":
    raise SystemExit(main())
