#!/usr/bin/env python3
"""Build a handout-driven report body scaffold from normalized section artifacts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from common import dedupe_keep_order, extract_template_sections, latex_escape, normalize_heading, write_json


CANONICAL_SECTIONS = [
    ("introduction", "Introduction"),
    ("objectives", "Objectives"),
    ("equipment", "Experiment Equipment"),
    ("principle", "Experiment Principle"),
    ("process", "Experimental Process / Experimental Phenomenon"),
    ("discussion", "Experiment Discussion"),
    ("appendix", "Appendix"),
    ("references", "References"),
]

HEADING_ALIASES = {
    "Introduction": {"introduction", "background", "overview", "引言", "简介", "绪论"},
    "Objectives": {"objectives", "objective", "aim", "aims", "purpose", "experiment purpose", "实验目的", "实验目标"},
    "Experiment Equipment": {
        "experiment equipment",
        "equipment",
        "apparatus",
        "materials",
        "实验仪器",
        "实验设备",
        "仪器设备",
    },
    "Experiment Principle": {"experiment principle", "principle", "theory", "实验原理", "实验理论", "原理"},
    "Experimental Process / Experimental Phenomenon": {
        "experimental process",
        "experimental phenomenon",
        "experimental process experimental phenomenon",
        "experimental procedure",
        "experiment steps",
        "experiment content",
        "experimental procedure and observations",
        "experimental process data and analysis results",
        "results and analysis",
        "实验步骤",
        "实验方法",
        "实验内容",
        "操作步骤",
    },
    "Experiment Discussion": {
        "experiment discussion",
        "discussion",
        "further discussion",
        "thinking questions",
        "assigned thinking questions",
        "思考题",
        "讨论",
        "讨论题",
    },
    "Appendix": {"appendix", "signature pages", "code", "附录"},
    "References": {"references", "reference", "bibliography", "参考文献"},
}

REFERENCE_ENTRY_PATTERN = re.compile(r"^\[\d+\]\s*")


def read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Expected section summary JSON object: {path}")
    return payload


def normalize_for_match(text: str) -> str:
    return normalize_heading(text)


def heading_is_present(canonical_heading: str, template_sections: list[str]) -> bool:
    aliases = {normalize_for_match(alias) for alias in HEADING_ALIASES[canonical_heading]}
    for heading in template_sections:
        normalized = normalize_for_match(heading)
        if normalized in aliases:
            return True
    return False


def clip_text(text: str, *, limit: int = 180) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def nonempty_lines(text: str) -> list[str]:
    lines = [line.strip(" -\t") for line in text.replace("\r", "\n").split("\n")]
    return [line for line in lines if line]


def extract_list_items(section: dict[str, object] | None) -> list[str]:
    if not isinstance(section, dict):
        return []
    values = section.get("list_items")
    if not isinstance(values, list):
        return []
    return dedupe_keep_order([str(item).strip() for item in values if str(item).strip()])


def is_reference_entry(text: str) -> bool:
    return bool(REFERENCE_ENTRY_PATTERN.match(text.strip()))


def split_thinking_questions_and_references(summary: dict[str, object]) -> tuple[list[str], list[str]]:
    section = section_seed(summary, "thinking_questions")
    items = extract_list_items(section)
    if items:
        questions = [item for item in items if not is_reference_entry(item)]
        references = [item for item in items if is_reference_entry(item)]
        return questions, references

    text = str(section.get("text") or "") if isinstance(section, dict) else ""
    questions = []
    references = []
    for line in nonempty_lines(text):
        if is_reference_entry(line):
            references.append(line)
        else:
            questions.append(line)
    return dedupe_keep_order(questions), dedupe_keep_order(references)


def extract_procedures(summary: dict[str, object]) -> list[dict[str, str]]:
    sections = summary.get("sections")
    steps_section = sections.get("steps", {}) if isinstance(sections, dict) else {}
    step_items = extract_list_items(steps_section)
    if not step_items and isinstance(steps_section, dict):
        text = str(steps_section.get("text") or "")
        candidates = []
        for line in nonempty_lines(text):
            candidates.extend(
                segment.strip()
                for segment in re.split(r"(?:^|\s)(?:\d+[.)]|[一二三四五六七八九十]+[、.])\s*", line)
                if segment.strip()
            )
        step_items = dedupe_keep_order(candidates)
    procedures = []
    for index, text in enumerate(step_items, start=1):
        procedures.append({"id": f"P{index:02d}", "text": text})
    return procedures


def thinking_questions(summary: dict[str, object]) -> list[str]:
    questions, _ = split_thinking_questions_and_references(summary)
    return questions


def reference_entries(summary: dict[str, object]) -> list[str]:
    references = extract_list_items(section_seed(summary, "references"))
    if not references:
        references_text = str(section_seed(summary, "references").get("text") or "")
        references = nonempty_lines(references_text)
    _, references_from_questions = split_thinking_questions_and_references(summary)
    return dedupe_keep_order(references + references_from_questions)


def section_seed(summary: dict[str, object], key: str) -> dict[str, object]:
    sections = summary.get("sections")
    if not isinstance(sections, dict):
        return {}
    payload = sections.get(key)
    return payload if isinstance(payload, dict) else {}


def scaffold_sections(summary: dict[str, object], template_sections: list[str], procedures: list[dict[str, str]]) -> list[dict[str, object]]:
    intro = section_seed(summary, "introduction")
    objectives = section_seed(summary, "objectives")
    equipment = section_seed(summary, "equipment")
    principle = section_seed(summary, "principle")
    appendix = section_seed(summary, "appendix")

    questions = thinking_questions(summary)
    references = reference_entries(summary)
    result = []
    for key, heading in CANONICAL_SECTIONS:
        source_key = {
            "introduction": "introduction",
            "objectives": "objectives",
            "equipment": "equipment",
            "principle": "principle",
            "process": "steps",
            "discussion": "thinking_questions",
            "appendix": "appendix",
            "references": "references",
        }[key]
        seed = section_seed(summary, source_key)
        entry: dict[str, object] = {
            "key": key,
            "heading": heading,
            "source_key": source_key,
            "present_in_template": heading_is_present(heading, template_sections),
            "seed_heading": seed.get("heading") if isinstance(seed, dict) else None,
        }
        if key == "introduction":
            entry["seed_text"] = clip_text(str(intro.get("text") or ""))
        elif key == "objectives":
            entry["seed_list_items"] = extract_list_items(objectives)
        elif key == "equipment":
            entry["seed_text"] = clip_text(str(equipment.get("text") or ""))
            entry["table_count"] = len(equipment.get("tables") or []) if isinstance(equipment.get("tables"), list) else 0
        elif key == "principle":
            entry["seed_text"] = clip_text(str(principle.get("text") or ""))
            entry["subheadings"] = [item.get("heading") for item in principle.get("subheadings", []) if isinstance(item, dict)]
            entry["image_count"] = len(principle.get("images") or []) if isinstance(principle.get("images"), list) else 0
        elif key == "process":
            entry["procedure_ids"] = [item["id"] for item in procedures]
        elif key == "discussion":
            entry["thinking_questions"] = questions
        elif key == "appendix":
            entry["appendix_seed_heading"] = appendix.get("heading") if isinstance(appendix, dict) else None
            entry["default_subsections"] = ["Code", "Signature Pages"]
        elif key == "references":
            entry["seed_list_items"] = references
        result.append(entry)
    return result


def render_introduction(summary: dict[str, object]) -> list[str]:
    intro = section_seed(summary, "introduction")
    text = clip_text(str(intro.get("text") or ""))
    lines = [r"\section{Introduction}"]
    if text:
        lines.append(rf"\NeedsInput{{Draft the introduction from the handout notes: {latex_escape(text)}}}")
    else:
        lines.append(r"\NeedsInput{Draft the introduction from the normalized handout introduction.}")
    return lines


def render_objectives(summary: dict[str, object]) -> list[str]:
    objectives = extract_list_items(section_seed(summary, "objectives"))
    lines = [r"\section{Objectives}"]
    if objectives:
        lines.append(r"\begin{itemize}")
        for item in objectives:
            lines.append(rf"  \item {latex_escape(item)}")
        lines.append(r"\end{itemize}")
    else:
        lines.append(r"\NeedsInput{Add the experiment objectives from the normalized handout.}")
    return lines


def render_equipment(summary: dict[str, object]) -> list[str]:
    equipment = section_seed(summary, "equipment")
    text = clip_text(str(equipment.get("text") or ""))
    lines = [r"\section{Experiment Equipment}"]
    if text:
        lines.append(rf"\NeedsInput{{Expand the equipment section from the handout notes: {latex_escape(text)}}}")
    else:
        lines.append(r"\NeedsInput{Add the main equipment list from the handout or decoded tables.}")
    return lines


def render_principle(summary: dict[str, object]) -> list[str]:
    principle = section_seed(summary, "principle")
    text = clip_text(str(principle.get("text") or ""))
    lines = [r"\section{Experiment Principle}"]
    if text:
        lines.append(rf"\NeedsInput{{Draft the principle overview from the handout notes: {latex_escape(text)}}}")
    else:
        lines.append(r"\NeedsInput{Add the principle overview from the normalized handout.}")
    subheadings = principle.get("subheadings") if isinstance(principle.get("subheadings"), list) else []
    for item in subheadings:
        if not isinstance(item, dict):
            continue
        heading = str(item.get("heading") or "").strip()
        if not heading:
            continue
        lines.append(rf"\subsection{{{latex_escape(heading)}}}")
        lines.append(rf"\NeedsInput{{Explain the principle subsection: {latex_escape(heading)}}}")
    return lines


def render_process(procedures: list[dict[str, str]]) -> list[str]:
    lines = [r"\section{Experimental Process / Experimental Phenomenon}"]
    if not procedures:
        lines.append(r"\NeedsInput{Extract the procedure steps from the normalized handout before drafting this section.}")
        return lines
    for procedure in procedures:
        lines.append(rf"\subsection{{Step {procedure['id']}}}")
        lines.append(f"% procedure:{procedure['id']}")
        lines.append(
            rf"\NeedsInput{{Describe procedure step {procedure['id']} and the matching observations: {latex_escape(procedure['text'])}}}"
        )
    return lines


def render_discussion(summary: dict[str, object]) -> list[str]:
    questions = thinking_questions(summary)
    lines = [r"\section{Experiment Discussion}"]
    if questions:
        lines.append(r"\subsection{Assigned Thinking Questions}")
        for question in questions:
            lines.append(rf"\NeedsInput{{Answer the handout thinking question: {latex_escape(question)}}}")
    else:
        lines.append(r"\NeedsInput{Draft the experiment discussion once results and evidence are stable.}")
    return lines


def render_appendix() -> list[str]:
    return [
        r"\section{Appendix}",
        r"\subsection{Code}",
        r"\NeedsInput{Add code artifacts if this experiment used scripts, notebooks, or simulations.}",
        r"\subsection{Signature Pages}",
        r"\NeedsInput{Add signatory pages if they exist for this experiment.}",
    ]


def render_references(summary: dict[str, object]) -> list[str]:
    references = reference_entries(summary)
    lines = [r"\section{References}"]
    if references:
        lines.append(r"\begin{itemize}")
        for reference in references:
            lines.append(rf"  \item {latex_escape(reference)}")
        lines.append(r"\end{itemize}")
        lines.append(r"\NeedsInput{Verify and format the final reference list for the report.}")
    else:
        lines.append(r"\NeedsInput{Add the references used by the final report.}")
    return lines


def render_tex_scaffold(summary: dict[str, object], procedures: list[dict[str, str]]) -> str:
    blocks = [
        render_introduction(summary),
        render_objectives(summary),
        render_equipment(summary),
        render_principle(summary),
        render_process(procedures),
        render_discussion(summary),
        render_appendix(),
        render_references(summary),
    ]
    lines: list[str] = []
    for block in blocks:
        if lines:
            lines.append("")
        lines.extend(block)
    return "\n".join(lines).rstrip() + "\n"


def procedures_markdown(procedures: list[dict[str, str]]) -> str:
    lines = [
        "# Procedures",
        "",
        "<!-- Keep stable IDs like P01, P02, ... and mirror them in TeX comments as % procedure:P01 -->",
        "",
    ]
    if not procedures:
        lines.append("- No procedure steps were extracted yet.")
    else:
        for procedure in procedures:
            lines.append(f"- {procedure['id']}: {procedure['text']}")
    return "\n".join(lines).rstrip() + "\n"


def scaffold_markdown(scaffold: dict[str, object]) -> str:
    lines = [
        "# Body Scaffold Summary",
        "",
        f"- Title: {scaffold.get('title') or 'TBD'}",
        f"- Template sections found: {', '.join(scaffold['template_sections']) or 'none'}",
        f"- Missing template sections: {', '.join(scaffold['missing_template_sections']) or 'none'}",
        "",
        "## Procedure Coverage",
        "",
    ]
    procedures = scaffold.get("procedures") or []
    if procedures:
        for procedure in procedures:
            lines.append(f"- {procedure['id']}: {procedure['text']}")
    else:
        lines.append("- No procedure steps extracted yet.")
    lines.extend(["", "## Scaffold Sections", ""])
    for entry in scaffold.get("scaffold_sections") or []:
        heading = str(entry.get("heading") or "TBD")
        present = "yes" if entry.get("present_in_template") else "no"
        lines.append(f"- {heading} (present in template: {present})")
    return "\n".join(lines).rstrip() + "\n"


def build_body_scaffold(summary: dict[str, object], template_text: str) -> dict[str, object]:
    template_sections = extract_template_sections(template_text)
    procedures = extract_procedures(summary)
    references = reference_entries(summary)
    scaffold = {
        "title": summary.get("title") or "",
        "template_sections": template_sections,
        "missing_template_sections": [
            heading for _, heading in CANONICAL_SECTIONS if not heading_is_present(heading, template_sections)
        ],
        "procedures": procedures,
        "thinking_questions": thinking_questions(summary),
        "references": references,
    }
    scaffold["scaffold_sections"] = scaffold_sections(summary, template_sections, procedures)
    scaffold["tex_scaffold"] = render_tex_scaffold(summary, procedures)
    return scaffold


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sections-json", required=True)
    parser.add_argument("--template-tex", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-markdown", required=True)
    parser.add_argument("--output-procedures", required=True)
    parser.add_argument("--output-tex", required=True)
    args = parser.parse_args()

    summary = read_json(Path(args.sections_json))
    template_text = Path(args.template_tex).read_text(encoding="utf-8")
    scaffold = build_body_scaffold(summary, template_text)

    write_json(Path(args.output_json), scaffold)
    Path(args.output_markdown).write_text(scaffold_markdown(scaffold), encoding="utf-8")
    Path(args.output_procedures).write_text(procedures_markdown(scaffold["procedures"]), encoding="utf-8")
    Path(args.output_tex).write_text(scaffold["tex_scaffold"], encoding="utf-8")
    print(
        json.dumps(
            {
                "output_json": args.output_json,
                "output_markdown": args.output_markdown,
                "output_procedures": args.output_procedures,
                "output_tex": args.output_tex,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
