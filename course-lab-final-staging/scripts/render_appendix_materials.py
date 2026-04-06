from __future__ import annotations

import os
from pathlib import Path

from common import latex_escape, normalize_heading


APPENDIX_CODE_FONT_COMMAND = r'\font\appendixcodefont="AR PL UMing CN" at 7pt'
APPENDIX_CODE_BOX_OPTIONS = (
    "enhanced,breakable,colback=blue!3!white,colframe=blue!20!black,"
    "boxrule=0.3pt,arc=2pt,left=1mm,right=1mm,top=1mm,bottom=1mm"
)
APPENDIX_DATA_BOX_OPTIONS = (
    "enhanced,breakable,colback=green!4!white,colframe=green!35!black,"
    "boxrule=0.3pt,arc=2pt,left=1mm,right=1mm,top=1mm,bottom=1mm"
)
APPENDIX_VERBATIM_OPTIONS = r"fontsize=\scriptsize,breaklines,breakanywhere,formatcom=\appendixcodefont"


def normalize_code_lines(source_text: str) -> list[str]:
    lines = source_text.expandtabs(4).splitlines()
    return lines or [""]


def latex_include_path(path: Path, base_dir: Path) -> str:
    rendered = os.path.relpath(path, start=base_dir)
    return rendered.replace("\\", "/")


def data_file_is_cited(entry: dict[str, object], main_tex_text: str) -> bool:
    label = str(entry.get("label") or "").strip()
    source_path = Path(str(entry.get("source_path") or ""))
    candidates = [label, source_path.name]
    if source_path.suffix:
        candidates.append(source_path.stem)
    haystack = main_tex_text or ""
    return any(candidate and candidate in haystack for candidate in candidates)


def render_appendix_materials(payload: dict[str, object], *, top_level_heading: str = "Appendix") -> dict[str, object]:
    entries = list(payload.get("appendix_entries") or [])
    raw_data_entries = list(payload.get("appendix_data_entries") or [])
    calculation_entries = list(payload.get("calculation_detail_entries") or [])
    unresolved: list[str] = []
    code_section_mode = normalize_heading(top_level_heading) in {"code", "appendix code"}
    main_tex_path = Path(str(payload.get("main_tex_path") or ""))
    base_dir = main_tex_path.parent if main_tex_path else Path.cwd()
    main_tex_text = str(payload.get("main_tex_text") or "")
    data_entries = [
        entry
        for entry in raw_data_entries
        if isinstance(entry, dict) and not data_file_is_cited(entry, main_tex_text)
    ]

    if not entries and not data_entries and not calculation_entries:
        appendix_lines: list[str] = []
        if not code_section_mode:
            appendix_lines.extend([r"\subsection{Code}", ""])
        appendix_lines.extend([r"\NeedsInput{No appendix code inputs were provided for final staging.}", ""])
        return {
            "appendix_tex": "\n".join(appendix_lines).rstrip() + "\n",
            "appendix_entries": entries,
            "unresolved": unresolved,
        }

    lines = [r"\clearpage"]
    if calculation_entries:
        lines.append(r"\onecolumn")
    else:
        lines.append(r"\twocolumn")
    lines.append(APPENDIX_CODE_FONT_COMMAND)

    appendix_manifest_entries: list[dict[str, object]] = []

    if calculation_entries:
        lines.append(r"\subsection{Calculation Details}")
        lines.append("")
        for entry in calculation_entries:
            if not isinstance(entry, dict):
                continue
            appendix_manifest_entries.append(entry)
            title = latex_escape(str(entry.get("title") or entry.get("label") or "Calculation Details"))
            source_path = Path(str(entry.get("source_path") or ""))
            exists = bool(entry.get("exists"))

            lines.append(rf"\paragraph{{{title}}}")
            if exists and source_path.exists():
                include_path = latex_include_path(source_path, base_dir)
                lines.append(rf"\input{{{include_path}}}")
            else:
                unresolved.append(f"Missing calculation-details file: {source_path}")
                lines.append(rf"\NeedsInput{{Missing calculation-details file: {latex_escape(str(source_path))}}}")
            lines.append("")

    if entries:
        lines.append(r"\clearpage")
        lines.append(r"\twocolumn")
        lines.append(APPENDIX_CODE_FONT_COMMAND)
        lines.append("")

    if data_entries:
        lines.append(r"\subsection{Data Files}")
        lines.append("")
        for entry in data_entries:
            if not isinstance(entry, dict):
                continue
            appendix_manifest_entries.append(entry)

            label = latex_escape(str(entry.get("label") or "data-file"))
            source_path = Path(str(entry.get("source_path") or ""))
            exists = bool(entry.get("exists"))

            lines.append(rf"\paragraph{{{label}}}")
            if exists and source_path.exists():
                lines.append(rf"\begin{{tcolorbox}}[{APPENDIX_DATA_BOX_OPTIONS}]")
                lines.append(rf"\begin{{Verbatim}}[{APPENDIX_VERBATIM_OPTIONS}]")
                lines.extend(normalize_code_lines(source_path.read_text(encoding="utf-8")))
                lines.append(r"\end{Verbatim}")
                lines.append(r"\end{tcolorbox}")
            else:
                unresolved.append(f"Appendix data file is missing: {source_path}")
                lines.append(rf"\NeedsInput{{Missing appendix data file: {latex_escape(str(source_path))}}}")
            lines.append("")

    if entries and not code_section_mode:
        lines.append(r"\subsection{Code}")
        lines.append("")
    elif not entries and not calculation_entries and not code_section_mode:
        lines.append(r"\subsection{Code}")
        lines.append("")

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        appendix_manifest_entries.append(entry)

        label = latex_escape(str(entry.get("label") or "code"))
        source_path = Path(str(entry.get("source_path") or ""))
        exists = bool(entry.get("exists"))

        lines.append(rf"\{'subsection' if code_section_mode else 'paragraph'}{{{label}}}")
        if exists and source_path.exists():
            lines.append(rf"\begin{{tcolorbox}}[{APPENDIX_CODE_BOX_OPTIONS}]")
            lines.append(rf"\begin{{Verbatim}}[{APPENDIX_VERBATIM_OPTIONS}]")
            lines.extend(normalize_code_lines(source_path.read_text(encoding="utf-8")))
            lines.append(r"\end{Verbatim}")
            lines.append(r"\end{tcolorbox}")
        else:
            unresolved.append(f"Appendix code file is missing: {source_path}")
            lines.append(rf"\NeedsInput{{Missing appendix code file: {latex_escape(str(source_path))}}}")
        lines.append("")

    return {
        "appendix_tex": "\n".join(lines).rstrip() + "\n",
        "appendix_entries": appendix_manifest_entries,
        "unresolved": unresolved,
    }
