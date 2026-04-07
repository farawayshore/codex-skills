from __future__ import annotations

import re
from pathlib import Path

from common import latex_escape, maybe_read_json
from sympy import Symbol, latex as sympy_latex, pi as sympy_pi, sqrt as sympy_sqrt
from sympy.parsing.sympy_parser import parse_expr


def _procedure_items(text: str) -> list[str]:
    items: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("- "):
            items.append(line[2:].strip())
    return items


def _render_result_items(items: list[dict[str, object]]) -> list[str]:
    lines = ["\\begin{itemize}"]
    for item in items:
        if not isinstance(item, dict):
            continue
        label = latex_escape(str(item.get("label") or item.get("name") or "Result"))
        value = latex_escape(str(item.get("value") or ""))
        unit = latex_escape(str(item.get("unit") or "")).strip()
        uncertainty = str(item.get("uncertainty") or "").strip()
        rendered = f"{label}: {value}"
        if unit:
            rendered += f" {unit}"
        if uncertainty:
            rendered += f" (uncertainty: {latex_escape(uncertainty)})"
        lines.append(rf"  \item {rendered}")
    lines.append("\\end{itemize}")
    return lines


def _resolve_json_reference(
    source_ref: str,
    *,
    workspace_root: Path,
) -> tuple[Path, str] | None:
    cleaned = source_ref.strip()
    match = re.match(r"^(.*\.json):([^:]+)$", cleaned)
    if match is None:
        return None

    json_path = Path(match.group(1))
    if not json_path.is_absolute():
        json_path = workspace_root / json_path
    return json_path, match.group(2)


def _source_record(
    item: dict[str, object],
    *,
    workspace_root: Path,
) -> dict[str, object] | None:
    for raw_source in item.get("sources", []):
        source_ref = str(raw_source or "").strip()
        if not source_ref:
            continue

        resolved = _resolve_json_reference(source_ref, workspace_root=workspace_root)
        if resolved is None:
            continue

        json_path, key = resolved
        payload = maybe_read_json(json_path)
        if not isinstance(payload, dict):
            continue

        derived = payload.get("derived")
        if isinstance(derived, dict) and isinstance(derived.get(key), dict):
            return {
                "kind": "derived",
                "coverage_k": payload.get("coverage_k"),
                "path": str(json_path),
                "key": key,
                "record": derived[key],
                "payload": payload,
            }

        columns = payload.get("columns")
        if isinstance(columns, dict) and isinstance(columns.get(key), dict):
            return {
                "kind": "column",
                "coverage_k": payload.get("coverage_k"),
                "path": str(json_path),
                "key": key,
                "record": columns[key],
                "payload": payload,
            }

        inputs = payload.get("inputs")
        if isinstance(inputs, dict) and isinstance(inputs.get(key), dict):
            return {
                "kind": "input",
                "coverage_k": payload.get("coverage_k"),
                "path": str(json_path),
                "key": key,
                "record": inputs[key],
                "payload": payload,
            }

    return None


def _format_numeric(value: object) -> str:
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _math_value(value: object, unit: str = "") -> str:
    rendered = _format_numeric(value)
    if unit:
        return rf"{rendered}\,\text{{{latex_escape(unit)}}}"
    return rendered


def _table_math_value(value: object, unit: str = "") -> str:
    return rf"${_math_value(value, unit)}$"


def _display_symbol(name: str, record: dict[str, object] | None) -> str:
    if isinstance(record, dict):
        symbol = str(record.get("symbol") or "").strip()
        if symbol:
            return symbol
    return name


def _expression_context(source: dict[str, object]) -> dict[str, dict[str, object]]:
    payload = source.get("payload")
    if not isinstance(payload, dict):
        return {}

    context: dict[str, dict[str, object]] = {}
    for bucket_name in ("inputs", "derived"):
        bucket = payload.get(bucket_name)
        if not isinstance(bucket, dict):
            continue
        for key, record in bucket.items():
            if isinstance(record, dict):
                context[str(key)] = record
    return context


def _parse_symbolic_expression(
    expression: str,
    *,
    context: dict[str, dict[str, object]],
) -> tuple[object, dict[str, Symbol]] | tuple[None, dict[str, Symbol]]:
    safe_expression = expression
    local_dict = {"sqrt": sympy_sqrt, "pi": sympy_pi}
    symbol_by_key: dict[str, Symbol] = {}

    for index, key in enumerate(sorted(context, key=len, reverse=True)):
        token = f"v{index}"
        pattern = rf"(?<![A-Za-z0-9_]){re.escape(key)}(?![A-Za-z0-9_])"
        replaced_expression, count = re.subn(pattern, token, safe_expression)
        if count == 0:
            continue
        safe_expression = replaced_expression
        symbol = Symbol(_display_symbol(key, context.get(key)))
        symbol_by_key[key] = symbol
        local_dict[token] = symbol

    try:
        return parse_expr(safe_expression, local_dict=local_dict, evaluate=False), symbol_by_key
    except Exception:
        return None, symbol_by_key


def _ordered_dependency_keys(expression: str, symbol_by_key: dict[str, Symbol], expr: object) -> list[str]:
    used = [key for key, symbol in symbol_by_key.items() if symbol in expr.free_symbols]
    return sorted(used, key=lambda key: expression.find(key))


def _column_detail_row(
    item: dict[str, object],
    *,
    workspace_root: Path,
) -> str | None:
    source = _source_record(item, workspace_root=workspace_root)
    if source is None or str(source.get("kind")) != "column":
        return None

    record = source.get("record")
    if not isinstance(record, dict):
        return None

    label = latex_escape(str(item.get("label") or item.get("name") or source.get("key") or "Result"))
    unit = str(record.get("unit") or item.get("unit") or "").strip()
    n = record.get("n")
    sample_stddev = record.get("sample_stddev")
    type_a = record.get("type_a")
    type_b = record.get("type_b")
    type_c = record.get("type_c")
    expanded = record.get("expanded_uncertainty")

    if not any(isinstance(value, (int, float)) for value in (n, sample_stddev, type_a, type_b, type_c, expanded)):
        return None

    rendered_type_b = "$0$"
    if isinstance(type_b, (int, float)):
        rendered_type_b = _table_math_value(type_b, unit)
    if isinstance(type_b, (int, float)) and record.get("resolution") is None and abs(float(type_b)) < 1e-15:
        rendered_type_b = "$0$"

    return " & ".join(
        [
            label,
            _format_numeric(n) if isinstance(n, (int, float)) else "",
            _table_math_value(sample_stddev, unit) if isinstance(sample_stddev, (int, float)) else "",
            _table_math_value(type_a, unit) if isinstance(type_a, (int, float)) else "",
            rendered_type_b,
            _table_math_value(type_c, unit) if isinstance(type_c, (int, float)) else "",
            _table_math_value(expanded, unit) if isinstance(expanded, (int, float)) else "",
        ]
    ) + r" \\"


def _render_direct_uncertainty_details(
    items: list[dict[str, object]],
    *,
    workspace_root: Path,
) -> list[str]:
    rendered_items = [
        line
        for line in (_column_detail_row(item, workspace_root=workspace_root) for item in items)
        if line
    ]
    if not rendered_items:
        return []

    return [
        r"\paragraph{Direct-Result Uncertainty Details}",
        r"\begingroup",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\renewcommand{\arraystretch}{1.15}",
        r"\begin{center}",
        r"\resizebox{\columnwidth}{!}{%",
        r"\begin{tabular}{>{\raggedright\arraybackslash}p{0.22\columnwidth} >{\centering\arraybackslash}p{0.07\columnwidth} >{\centering\arraybackslash}p{0.12\columnwidth} >{\centering\arraybackslash}p{0.12\columnwidth} >{\centering\arraybackslash}p{0.12\columnwidth} >{\centering\arraybackslash}p{0.12\columnwidth} >{\centering\arraybackslash}p{0.12\columnwidth}}",
        r"\toprule",
        r"Quantity & $n$ & $s$ & $u_a$ & $u_b$ & $u_c$ & $U$ \\",
        r"\midrule",
        *rendered_items,
        r"\bottomrule",
        r"\end{tabular}%",
        r"}",
        r"\end{center}",
        r"\endgroup",
        "",
    ]


def _term_chunk_size(terms: list[str]) -> int:
    return 2


def _chunk_terms(terms: list[str]) -> list[str]:
    chunk_size = _term_chunk_size(terms)
    return [" + ".join(terms[index : index + chunk_size]) for index in range(0, len(terms), chunk_size)]


def _aligned_power_half_lines(prefix: str, terms: list[str]) -> list[str]:
    chunks = _chunk_terms(terms)
    if not chunks:
        return []
    if len(chunks) == 1:
        return [rf"{prefix}\Bigl[{chunks[0]}\Bigr]^{{1/2}}"]

    lines = [rf"{prefix}\Bigl[{chunks[0]}"]
    for chunk in chunks[1:-1]:
        lines.append(rf"&\qquad + {chunk}")
    lines.append(rf"&\qquad + {chunks[-1]}\Bigr]^{{1/2}}")
    return lines


def _propagation_detail_block(
    item: dict[str, object],
    *,
    workspace_root: Path,
) -> list[str]:
    source = _source_record(item, workspace_root=workspace_root)
    if source is None or str(source.get("kind")) != "derived":
        return []

    record = source.get("record")
    if not isinstance(record, dict):
        return []

    expression = str(record.get("expression") or "").strip()
    if not expression:
        return []

    context = _expression_context(source)
    expr, symbol_by_key = _parse_symbolic_expression(expression, context=context)
    if expr is None:
        return []

    dependency_keys = _ordered_dependency_keys(expression, symbol_by_key, expr)
    if not dependency_keys:
        return []

    substitutions = {}
    dependency_records: list[tuple[str, Symbol, dict[str, object]]] = []
    for key in dependency_keys:
        symbol = symbol_by_key[key]
        dependency_record = context.get(key) or {}
        dependency_value = dependency_record.get("value")
        dependency_uncertainty = dependency_record.get("std_uncertainty")
        if not isinstance(dependency_value, (int, float)) or not isinstance(dependency_uncertainty, (int, float)):
            continue
        substitutions[symbol] = dependency_value
        dependency_records.append((key, symbol, dependency_record))

    propagated_terms: list[str] = []
    numeric_terms: list[str] = []
    dependency_rows: list[str] = []
    for _, symbol, dependency_record in dependency_records:
        dependency_value = dependency_record.get("value")
        dependency_uncertainty = dependency_record.get("std_uncertainty")
        dependency_unit = str(dependency_record.get("unit") or "").strip()
        dependency_rows.append(
            " & ".join(
                [
                    rf"${sympy_latex(symbol)}$",
                    _table_math_value(dependency_value, dependency_unit),
                    _table_math_value(dependency_uncertainty, dependency_unit),
                ]
            )
            + r" \\"
        )
        derivative_expr = expr.diff(symbol)
        derivative_latex = sympy_latex(derivative_expr)
        derivative_value = float(derivative_expr.evalf(subs=substitutions))
        propagated_terms.append(rf"\left({derivative_latex} u({sympy_latex(symbol)})\right)^2")
        numeric_terms.append(
            rf"\left({_format_numeric(derivative_value)}\times{_format_numeric(dependency_uncertainty)}\right)^2"
        )

    if not propagated_terms or not numeric_terms:
        return []

    label = latex_escape(str(item.get("label") or item.get("name") or source.get("key") or "Result"))
    unit = str(record.get("unit") or item.get("unit") or "").strip()
    std_uncertainty = record.get("std_uncertainty")
    expanded = record.get("expanded_uncertainty")
    coverage_k = source.get("coverage_k")
    lhs = latex_escape(str(item.get("name") or source.get("key") or "result"))
    aligned_lines: list[str] = []
    aligned_lines.extend(_aligned_power_half_lines(rf"u_c(\text{{{lhs}}})=& ", propagated_terms))
    aligned_lines.extend(_aligned_power_half_lines(r"&= ", numeric_terms))
    if isinstance(std_uncertainty, (int, float)):
        final_line = rf"&= {_math_value(std_uncertainty, unit)}"
        if isinstance(expanded, (int, float)):
            if isinstance(coverage_k, (int, float)):
                final_line += rf", \qquad U={_format_numeric(coverage_k)}u_c={_math_value(expanded, unit)}"
            else:
                final_line += rf", \qquad U={_math_value(expanded, unit)}"
        aligned_lines.append(final_line)

    if not aligned_lines:
        return []

    rendered_lines = [rf"\paragraph{{{label}}}", r"\begingroup", r"\scriptsize"]
    if dependency_rows:
        rendered_lines.extend(
            [
                r"\setlength{\tabcolsep}{4pt}",
                r"\renewcommand{\arraystretch}{1.1}",
                r"\begin{center}",
                r"\resizebox{\columnwidth}{!}{%",
                r"\begin{tabular}{>{\centering\arraybackslash}p{0.15\columnwidth} >{\centering\arraybackslash}p{0.18\columnwidth} >{\centering\arraybackslash}p{0.18\columnwidth}}",
                r"\toprule",
                r"Symbol & Value & $u(x)$ \\",
                r"\midrule",
                *dependency_rows,
                r"\bottomrule",
                r"\end{tabular}%",
                r"}",
                r"\end{center}",
            ]
        )
    rendered_lines.extend(
        [
            r"\begin{equation}",
            r"\begin{aligned}",
            *(line + (r" \\" if index < len(aligned_lines) - 1 else "") for index, line in enumerate(aligned_lines)),
            r"\end{aligned}",
            r"\end{equation}",
            r"\endgroup",
            "",
        ]
    )
    return rendered_lines


def _render_propagation_details(
    items: list[dict[str, object]],
    *,
    workspace_root: Path,
) -> list[str]:
    rendered_blocks = [
        block
        for block in (_propagation_detail_block(item, workspace_root=workspace_root) for item in items)
        if block
    ]
    if not rendered_blocks:
        return []

    lines = [r"\paragraph{Indirect-Result Propagation Details}"]
    for block in rendered_blocks:
        lines.extend(block)
    return [*lines, ""]


def _effective_uncertainty(
    item: dict[str, object],
    *,
    workspace_root: Path,
) -> str:
    explicit = str(item.get("uncertainty") or "").strip()
    if explicit:
        return explicit

    source = _source_record(item, workspace_root=workspace_root)
    if source is None:
        return ""

    record = source.get("record")
    if not isinstance(record, dict):
        return ""

    unit = str(record.get("unit") or item.get("unit") or "").strip()
    expanded = record.get("expanded_uncertainty")
    standard = record.get("std_uncertainty")
    type_c = record.get("type_c")

    if isinstance(expanded, (int, float)):
        rendered = f"U={_format_numeric(expanded)}"
        if unit:
            rendered += f" {unit}"
        return rendered
    if isinstance(standard, (int, float)):
        rendered = f"u_c={_format_numeric(standard)}"
        if unit:
            rendered += f" {unit}"
        return rendered
    if isinstance(type_c, (int, float)):
        rendered = f"u_c={_format_numeric(type_c)}"
        if unit:
            rendered += f" {unit}"
        return rendered
    return ""


def _render_indirect_formula_items(
    items: list[dict[str, object]],
    *,
    workspace_root: Path,
) -> list[str]:
    rendered_items: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        source = _source_record(item, workspace_root=workspace_root)
        if source is None or str(source.get("kind")) != "derived":
            continue

        record = source.get("record")
        if not isinstance(record, dict):
            continue

        expression = str(record.get("expression") or "").strip()
        if not expression:
            continue

        label = latex_escape(str(item.get("label") or item.get("name") or source.get("key") or "Result"))
        lhs = str(item.get("name") or source.get("key") or "result")
        formula = latex_escape(f"{lhs} = {expression}")
        unit = str(record.get("unit") or item.get("unit") or "").strip()
        standard = record.get("std_uncertainty")
        expanded = record.get("expanded_uncertainty")
        coverage_k = source.get("coverage_k")

        details: list[str] = [rf"Formula: \texttt{{{formula}}}"]
        if isinstance(standard, (int, float)):
            detail = f"propagated standard uncertainty { _format_numeric(standard) }"
            if unit:
                detail += f" {unit}"
            details.append(detail)
        if isinstance(expanded, (int, float)):
            detail = f"expanded uncertainty { _format_numeric(expanded) }"
            if unit:
                detail += f" {unit}"
            if isinstance(coverage_k, (int, float)):
                detail += f" (k={_format_numeric(coverage_k)})"
            details.append(detail)

        rendered_items.append(f"  \\item {label}: " + "; ".join(latex_escape(part) if index else part for index, part in enumerate(details)))

    if not rendered_items:
        return []

    return [
        r"\paragraph{Indirect-Result Formulae}",
        r"\begin{itemize}",
        *rendered_items,
        r"\end{itemize}",
        "",
    ]


def _uncertainty_definition_lines(has_uncertainty_support: bool) -> list[str]:
    if not has_uncertainty_support:
        return []

    return [
        r"\paragraph{Definitions}",
        r"For repeated direct measurements, the Type A, Type B, combined standard, and expanded uncertainties are written as",
        r"\begin{equation}",
        r"u_a=\frac{s}{\sqrt{n}}, \qquad u_b=\frac{\Delta}{\sqrt{3}}, \qquad u_c=\sqrt{u_a^2+u_b^2}, \qquad U=ku_c.",
        r"\end{equation}",
        r"Here $s$ is the sample standard deviation, $n$ is the repeat count, and $\Delta$ is the instrument resolution. When the staged uncertainty artifacts report expanded uncertainties, they use $k=2$ unless the artifact says otherwise.",
        r"For an indirect quantity $y=f(x_1,\ldots,x_m)$, the propagated standard uncertainty follows",
        r"\begin{equation}",
        r"u_c(y)=\sqrt{\sum_i\left(\frac{\partial f}{\partial x_i}u(x_i)\right)^2}.",
        r"\end{equation}",
        "",
    ]


def _interpretation_index(payload: dict[str, object]) -> dict[str, str]:
    index: dict[str, str] = {}
    for item in payload.get("interpretation_items", []):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        summary = str(item.get("summary") or "").strip()
        if name and summary:
            index[name] = summary
    return index


def _comparison_case_lines(case: dict[str, object]) -> list[str]:
    lines: list[str] = []
    title = latex_escape(str(case.get("title") or case.get("case_id") or "Comparison Case"))
    observed_label = latex_escape(str(case.get("observed_label") or "Observed evidence"))
    observed_summary = str(case.get("observed_summary") or "").strip()
    comparison_label = latex_escape(str(case.get("comparison_label") or "Comparison evidence"))
    comparison_summary = str(case.get("comparison_summary") or "").strip()
    agreement_summary = str(case.get("agreement_summary") or "").strip()
    caveats = [str(item).strip() for item in case.get("caveats", []) if str(item).strip()]
    confidence = str(case.get("confidence") or "").strip()

    lines.append(rf"\paragraph{{{title}}}")
    if observed_summary:
        lines.append(f"{observed_label}: {latex_escape(observed_summary)}")
    if comparison_summary:
        lines.append(f"{comparison_label}: {latex_escape(comparison_summary)}")
    if agreement_summary:
        lines.append(f"Agreement: {latex_escape(agreement_summary)}")
    if confidence:
        lines.append(f"Confidence: {latex_escape(confidence)}")
    for caveat in caveats:
        lines.append(f"Caveat: {latex_escape(caveat)}")
    lines.append("")
    return lines


def _compact_comparison_case_row(case: dict[str, object]) -> str:
    title = latex_escape(str(case.get("title") or case.get("case_id") or "Case"))
    observed_summary = latex_escape(str(case.get("observed_summary") or "").strip())
    comparison_summary = latex_escape(str(case.get("comparison_summary") or "").strip())

    agreement_parts: list[str] = []
    agreement_summary = str(case.get("agreement_summary") or "").strip()
    if agreement_summary:
        agreement_parts.append(agreement_summary)
    confidence = str(case.get("confidence") or "").strip()
    if confidence and confidence.lower() != "low":
        agreement_parts.append(f"Confidence: {confidence}")
    caveats = [str(item).strip() for item in case.get("caveats", []) if str(item).strip()]
    if caveats:
        agreement_parts.append("Caveat: " + " | ".join(caveats))

    agreement_cell = latex_escape(" ".join(part for part in agreement_parts if part))
    return f"{title} & {observed_summary} & {comparison_summary} & {agreement_cell} " + r"\\"


def _render_compact_comparison_cases(cases: list[dict[str, object]]) -> list[str]:
    rendered_rows = [
        _compact_comparison_case_row(case)
        for case in cases
        if isinstance(case, dict)
    ]
    if not rendered_rows:
        return []

    return [
        r"\subsection{Comparison}",
        "",
        r"\paragraph{Compact Case Comparison}",
        r"\begingroup",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\renewcommand{\arraystretch}{1.12}",
        r"\begin{center}",
        r"\resizebox{\columnwidth}{!}{%",
        r"\begin{tabular}{>{\raggedright\arraybackslash}p{0.10\columnwidth} >{\raggedright\arraybackslash}p{0.28\columnwidth} >{\raggedright\arraybackslash}p{0.28\columnwidth} >{\raggedright\arraybackslash}p{0.26\columnwidth}}",
        r"\toprule",
        r"Case & Observed & Comparison & Agreement / Notes \\",
        r"\midrule",
        *rendered_rows,
        r"\bottomrule",
        r"\end{tabular}%",
        r"}",
        r"\end{center}",
        r"\endgroup",
        "",
    ]


def _render_comparison_cases(cases: list[dict[str, object]]) -> list[str]:
    if not cases:
        return []

    if len(cases) >= 3:
        return _render_compact_comparison_cases(cases)

    lines = [r"\subsection{Comparison}", ""]
    for case in cases:
        if not isinstance(case, dict):
            continue
        lines.extend(_comparison_case_lines(case))
    return lines


def _render_literature_reference_context(references: list[dict[str, object]]) -> list[str]:
    if not references:
        return []

    lines = [r"\paragraph{Confirmed Literature Context}", r"\begin{itemize}"]
    for entry in references:
        if not isinstance(entry, dict):
            continue
        label = latex_escape(str(entry.get("label") or entry.get("name") or "Literature reference"))
        source_title = latex_escape(str(entry.get("source_title") or "").strip())
        source = latex_escape(str(entry.get("source") or "").strip())
        summary = latex_escape(str(entry.get("summary") or "").strip())
        lane = latex_escape(str(entry.get("lane") or "").strip())
        value = str(entry.get("value") or "").strip()
        unit = latex_escape(str(entry.get("unit") or "").strip())

        parts = [label]
        if lane:
            parts.append(f"lane {lane}")
        if summary:
            parts.append(summary)
        if value:
            rendered_value = value if not unit else f"{value} {unit}"
            parts.append(f"reported reference value {rendered_value}")
        if source_title:
            parts.append(source_title)
        if source:
            parts.append(source)
        lines.append(rf"  \item {'; '.join(part for part in parts if part)}")
    lines.extend([r"\end{itemize}", ""])
    return lines


def render_results_sections(payload: dict[str, object]) -> dict[str, object]:
    processed_payload = payload["processed_payload"]
    cases = payload["cases"]
    interpretation_payload = payload["results_interpretation"]
    discussion_payload = payload["discussion_synthesis"]
    modeling_payload = payload.get("modeling_payload")
    comparison_cases = list(payload.get("comparison_cases") or [])
    literature_references = list(payload.get("literature_references") or [])
    workspace_root = Path(payload["main_tex_path"]).parent

    unresolved: list[str] = []
    interpretation_index = _interpretation_index(interpretation_payload)
    all_results = [
        item
        for case in cases
        if isinstance(case, dict)
        for item in list(case.get("direct_results") or []) + list(case.get("indirect_results") or [])
        if isinstance(item, dict)
    ]
    has_uncertainty_support = any(
        str(item.get("uncertainty") or "").strip() or _source_record(item, workspace_root=workspace_root) is not None
        for item in all_results
    )

    process_lines = [
        r"\subsection{Data-Processing Procedure}",
        latex_escape(
            " ".join(str(item).strip() for item in processed_payload.get("processing_procedure", []) if str(item).strip())
            or "Processed-data artifacts did not record a full data-processing procedure."
        ),
        "",
    ]

    procedure_items = _procedure_items(str(payload.get("procedures_markdown_text") or ""))
    if procedure_items:
        process_lines.append(r"\begin{itemize}")
        for item in procedure_items:
            process_lines.append(rf"  \item {latex_escape(item)}")
        process_lines.append(r"\end{itemize}")
        process_lines.append("")

    process_lines.extend(
        [
            r"\subsection{Uncertainty Calculation Procedure}",
            latex_escape(
                " ".join(
                    str(item).strip()
                    for item in processed_payload.get("uncertainty_procedure", [])
                    if str(item).strip()
                )
                or "Processed-data artifacts did not record a full uncertainty-calculation procedure."
            ),
            "",
        ]
    )
    process_lines.extend(_uncertainty_definition_lines(has_uncertainty_support))

    results_lines = [r"\subsection{Direct And Indirect Results}", ""]
    case_records: list[dict[str, object]] = []
    for case in cases:
        title = latex_escape(str(case.get("title") or case.get("case_id") or "Case"))
        direct_results = list(case.get("direct_results") or [])
        indirect_results = list(case.get("indirect_results") or [])
        case_records.append(
            {
                "case_id": str(case.get("case_id") or ""),
                "title": str(case.get("title") or ""),
                "direct_result_count": len(direct_results),
                "indirect_result_count": len(indirect_results),
            }
        )

        results_lines.append(rf"\subsection{{{title}}}")
        results_lines.append("")
        results_lines.append(r"\paragraph{Direct Results}")
        normalized_direct_results = []
        for item in direct_results:
            if not isinstance(item, dict):
                continue
            normalized = dict(item)
            normalized["uncertainty"] = _effective_uncertainty(normalized, workspace_root=workspace_root)
            normalized_direct_results.append(normalized)
        results_lines.extend(_render_result_items(normalized_direct_results))
        results_lines.append("")
        results_lines.extend(
            _render_direct_uncertainty_details(
                normalized_direct_results,
                workspace_root=workspace_root,
            )
        )
        results_lines.append(r"\paragraph{Indirect Results}")
        normalized_indirect_results = []
        for item in indirect_results:
            if not isinstance(item, dict):
                continue
            normalized = dict(item)
            normalized["uncertainty"] = _effective_uncertainty(normalized, workspace_root=workspace_root)
            normalized_indirect_results.append(normalized)
        results_lines.extend(_render_result_items(normalized_indirect_results))
        results_lines.append("")
        results_lines.extend(
            _render_indirect_formula_items(
                normalized_indirect_results,
                workspace_root=workspace_root,
            )
        )
        results_lines.extend(
            _render_propagation_details(
                normalized_indirect_results,
                workspace_root=workspace_root,
            )
        )

        matched_names = [
            str(item.get("name") or "")
            for item in normalized_indirect_results + normalized_direct_results
            if isinstance(item, dict)
        ]
        interpretation_lines = [
            interpretation_index[name]
            for name in matched_names
            if name in interpretation_index
        ]
        if interpretation_lines:
            results_lines.append(r"\paragraph{Interpretation Bridge}")
            for line in interpretation_lines:
                results_lines.append(latex_escape(line))
            results_lines.append("")

        if not indirect_results:
            unresolved.append(f"No indirect results were available for {case.get('title') or case.get('case_id')}.")

        for item in normalized_direct_results + normalized_indirect_results:
            if not isinstance(item, dict):
                continue
            if not str(item.get("uncertainty") or "").strip():
                unresolved.append(
                    f"Uncertainty support is missing for {item.get('label') or item.get('name') or 'a result'} in {case.get('title') or case.get('case_id')}."
                )

    results_lines.extend(_render_comparison_cases(comparison_cases))
    results_lines.extend(_render_literature_reference_context(literature_references))

    if isinstance(modeling_payload, dict) and modeling_payload.get("outputs"):
        if results_lines and results_lines[-1] != "":
            results_lines.append("")
        results_lines.append(r"\subsection{Modeling Results}")
        results_lines.append("")
        for output in modeling_payload.get("outputs", []):
            if not isinstance(output, dict):
                continue
            label = latex_escape(str(output.get("label") or output.get("name") or "Modeled result"))
            value = latex_escape(str(output.get("value") or ""))
            unit = latex_escape(str(output.get("unit") or "")).strip()
            line = f"{label}: {value}"
            if unit:
                line += f" {unit}"
            results_lines.append(line)
        results_lines.append("")

    discussion_lines = [r"\subsection{Synthesized Discussion}", ""]
    for block in discussion_payload.get("discussion_blocks", []):
        if not isinstance(block, dict):
            continue
        title = latex_escape(str(block.get("title") or "Discussion Block"))
        prose = latex_escape(str(block.get("polished_markdown") or "").strip())
        discussion_lines.append(rf"\paragraph{{{title}}}")
        discussion_lines.append(prose or "Discussion block remained unresolved.")
        discussion_lines.append("")

    for item in interpretation_payload.get("unresolved", []):
        if str(item).strip():
            unresolved.append(str(item).strip())
    for item in discussion_payload.get("unresolved", []):
        if str(item).strip():
            unresolved.append(str(item).strip())
    for item in payload.get("comparison_case_unresolved", []):
        if str(item).strip():
            unresolved.append(str(item).strip())

    written_sections = {
        "experimental_process": "\n".join(process_lines).rstrip() + "\n",
        "results": "\n".join(results_lines).rstrip() + "\n",
        "discussion": "\n".join(discussion_lines).rstrip() + "\n",
    }

    return {
        "written_sections": written_sections,
        "case_records": case_records,
        "unresolved": unresolved,
    }
