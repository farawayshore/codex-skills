#!/usr/bin/env python3
"""Render appendix-ready calculation detail TeX from staged uncertainty artifacts."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import sympy as sp
from sympy.parsing.sympy_parser import parse_expr

from common import safe_label, write_json


ZERO_TOLERANCE = 1e-12
IDENTIFIER_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")


def latex_escape(text: str) -> str:
    replacements = {
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
    return "".join(replacements.get(ch, ch) for ch in text)


def tex_number(value: float) -> str:
    if value == 0:
        return "0"
    return f"{value:.5g}"


def tex_value(value: float, unit: str | None = None) -> str:
    if unit:
        return rf"${tex_number(value)}\,\text{{{latex_escape(unit)}}}$"
    return rf"${tex_number(value)}$"


def tex_math_value(value: float, unit: str | None = None) -> str:
    if unit:
        return rf"{tex_number(value)}\,\text{{{latex_escape(unit)}}}"
    return tex_number(value)


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def direct_summary_rows(payload: dict[str, object]) -> list[str]:
    columns = payload.get("columns")
    if not isinstance(columns, dict):
        return [r"\NeedsInput{Missing calculation-detail source columns for direct summary.}"]

    lines = [
        r"\paragraph{Direct Measurement Summary}",
        r"\begingroup",
        r"\footnotesize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\begin{center}",
        r"\begin{tabular}{lrrrrrrr}",
        r"Quantity & $n$ & Mean & $s$ & $u_a$ & $u_b$ & $u_c$ & $U$ \\",
        r"\hline",
    ]
    for _, summary in columns.items():
        if not isinstance(summary, dict):
            continue
        quantity = latex_escape(str(summary.get("quantity_label") or summary.get("raw_label") or "quantity"))
        unit = str(summary.get("unit") or "")
        lines.append(
            " & ".join(
                [
                    quantity,
                    str(summary.get("n") or "-"),
                    tex_value(float(summary.get("mean") or 0.0), unit or None),
                    tex_value(float(summary.get("sample_stddev") or 0.0), unit or None),
                    tex_value(float(summary.get("type_a") or 0.0), unit or None),
                    tex_value(float(summary.get("type_b") or 0.0), unit or None),
                    tex_value(float(summary.get("type_c") or 0.0), unit or None),
                    tex_value(float(summary.get("expanded_uncertainty") or 0.0), unit or None),
                ]
            )
            + r" \\"
        )
    lines.extend([r"\end{tabular}", r"\end{center}", ""])
    lines.append(r"\endgroup")
    lines.append("")
    return lines


def appendix_notice_box() -> list[str]:
    return [
        r"\noindent\fcolorbox{black!25}{black!6}{%",
        r"\parbox{0.96\linewidth}{%",
        r"\textbf{Appendix Calculation Note.} This attachment condenses the mathematical calculation procedure for the staged results. Raw source tables and exhaustive numeric listings are intentionally omitted here so the appendix remains a compact supplement rather than body text.%",
        r"}%",
        r"}",
        "",
    ]


def replace_symbol_names(expression: str, names: list[str], replacements: dict[str, str]) -> str:
    rewritten = expression
    for name in sorted(names, key=len, reverse=True):
        rewritten = re.sub(rf"\b{re.escape(name)}\b", replacements[name], rewritten)
    return rewritten


def expression_variable_names(expression: str) -> list[str]:
    return sorted({token for token in IDENTIFIER_RE.findall(expression) if token not in {"sqrt", "pi"}}, key=len, reverse=True)


def parse_symbolic_expression(expression: str) -> tuple[sp.Expr, dict[str, sp.Symbol]]:
    variable_names = expression_variable_names(expression)
    replacements = {name: f"var_{index}" for index, name in enumerate(variable_names)}
    local_dict: dict[str, object] = {"sqrt": sp.sqrt, "pi": sp.pi}
    symbol_map: dict[str, sp.Symbol] = {}
    for name, safe_name in replacements.items():
        symbol = sp.Symbol(name)
        local_dict[safe_name] = symbol
        symbol_map[name] = symbol
    rewritten = replace_symbol_names(expression, variable_names, replacements)
    parsed = parse_expr(rewritten, local_dict=local_dict, evaluate=False)
    return parsed, symbol_map


def latex_symbol(symbol_name: str) -> str:
    return sp.latex(sp.Symbol(symbol_name))


def indexed_variable_notation(names: list[str]) -> tuple[str, str]:
    if not names:
        return (r"x_{j}", r"j=1,\dots,n")
    matched = [re.fullmatch(r"(.+?)(\d+)$", name) for name in names]
    if all(match is not None for match in matched):
        bases = {match.group(1) for match in matched if match is not None}
        indices = sorted(int(match.group(2)) for match in matched if match is not None)
        if len(bases) == 1:
            base = next(iter(bases))
            indexed_name = f"{base}j" if base.endswith("_") else f"{base}_j"
            if indices == list(range(indices[0], indices[-1] + 1)):
                return (sp.latex(sp.Symbol(indexed_name)), rf"j={indices[0]},\dots,{indices[-1]}")
    return (r"x_{j}", rf"j=1,\dots,{len(names)}")


def relevant_input_names(payload: dict[str, object], inputs: dict[str, object]) -> list[str]:
    partials = payload.get("partials")
    if isinstance(partials, dict):
        names = [
            input_name
            for input_name, coeff in partials.items()
            if input_name in inputs and abs(float(coeff or 0.0)) > ZERO_TOLERANCE
        ]
        if names:
            return names

    gradient = payload.get("gradient")
    if isinstance(gradient, dict):
        names = [
            input_name
            for input_name, coeff in gradient.items()
            if input_name in inputs and abs(float(coeff or 0.0)) > ZERO_TOLERANCE
        ]
        if names:
            return names

    return list(inputs.keys())


def input_rows(inputs: dict[str, object], input_names: list[str]) -> list[str]:
    if not input_names:
        return [r"\NeedsInput{No contributing inputs were identified for this derived quantity.}", ""]

    lines = [
        r"\paragraph{Adopted Inputs}",
        r"\begingroup",
        r"\footnotesize",
        r"\setlength{\tabcolsep}{4pt}",
        r"\begin{center}",
        r"\begin{tabular}{lll}",
        r"Symbol & Value & $u(x)$ \\",
        r"\hline",
    ]
    for input_name in input_names:
        payload = inputs.get(input_name)
        if not isinstance(payload, dict):
            continue
        symbol = str(payload.get("symbol") or input_name)
        unit = str(payload.get("unit") or "")
        value = float(payload.get("value") or 0.0)
        uncertainty = float(payload.get("std_uncertainty") or 0.0)
        uncertainty_text = tex_number(uncertainty)
        if unit:
            uncertainty_text += rf"\,\text{{{latex_escape(unit)}}}"
        lines.append(
            " & ".join(
                [
                    rf"${latex_escape(symbol)}$",
                    tex_value(value, unit or None),
                    rf"$u({latex_escape(symbol)})={uncertainty_text}$",
                ]
            )
            + r" \\"
        )
    lines.extend([r"\end{tabular}", r"\end{center}", r"\endgroup", ""])
    return lines


def variance_expression(terms: list[str]) -> str:
    if not terms:
        return "0"
    return " + ".join(terms)


def derived_block(derived_name: str, payload: dict[str, object], coverage_k: float) -> list[str]:
    label = str(payload.get("label") or derived_name).strip()
    expression = str(payload.get("expression") or derived_name)
    symbolic_expression, symbol_map = parse_symbolic_expression(expression)
    derived_symbol_tex = latex_symbol(derived_name)
    referenced_names = [name for name in expression_variable_names(expression) if name in symbol_map]
    derivatives: list[tuple[str, sp.Expr]] = []
    for name in referenced_names:
        symbol = symbol_map[name]
        derivative = sp.diff(symbolic_expression, symbol)
        derivatives.append((name, derivative))

    derivative_lines: list[str] = []
    generic_terms: list[str] = []
    specialized_terms: list[str] = []
    if derivatives:
        common_derivative = derivatives[0][1]
        mean_like = len(derivatives) >= 4 and all(sp.simplify(derivative - common_derivative) == 0 for _, derivative in derivatives[1:])
        if mean_like:
            indexed_variable_tex, index_domain_tex = indexed_variable_notation(referenced_names)
            derivative_tex = sp.latex(common_derivative)
            derivative_lines.append(
                rf"\frac{{\partial {derived_symbol_tex}}}{{\partial {indexed_variable_tex}}} &= {derivative_tex},\quad {index_domain_tex} \\"
            )
            generic_terms.append(
                rf"\sum_{{{index_domain_tex}}}\left(\frac{{\partial {derived_symbol_tex}}}{{\partial {indexed_variable_tex}}}u\!\left({indexed_variable_tex}\right)\right)^2"
            )
            specialized_terms.append(
                rf"\sum_{{{index_domain_tex}}}\left(({derivative_tex})u\!\left({indexed_variable_tex}\right)\right)^2"
            )
        else:
            for name, derivative in derivatives:
                variable_tex = sp.latex(symbol_map[name])
                derivative_tex = sp.latex(derivative)
                derivative_lines.append(rf"\frac{{\partial {derived_symbol_tex}}}{{\partial {variable_tex}}} &= {derivative_tex} \\")
                generic_terms.append(
                    rf"\left(\frac{{\partial {derived_symbol_tex}}}{{\partial {variable_tex}}}u\!\left({variable_tex}\right)\right)^2"
                )
                specialized_terms.append(rf"\left(({derivative_tex})u\!\left({variable_tex}\right)\right)^2")
    else:
        generic_terms.append("0")
        specialized_terms.append("0")

    generic_expression = variance_expression(generic_terms)
    specialized_expression = variance_expression(specialized_terms)

    lines = [
        rf"\paragraph{{{latex_escape(label)}}}",
        r"\[",
        r"\begin{aligned}",
        rf"{derived_symbol_tex} &= {sp.latex(symbolic_expression)} \\",
        *derivative_lines,
        rf"u_c\!\left({derived_symbol_tex}\right) &= \sqrt{{{generic_expression}}} \\",
        rf"&= \sqrt{{{specialized_expression}}} \\",
        rf"U\!\left({derived_symbol_tex}\right) &= {tex_number(coverage_k)}\,u_c\!\left({derived_symbol_tex}\right)",
        r"\end{aligned}",
        r"\]",
        "",
    ]
    return lines


def render_group(group: dict[str, object]) -> str:
    title = str(group.get("title") or "Calculation Details")
    direct_paths = [Path(path) for path in group.get("direct_summaries", []) if str(path).strip()]
    derived_paths = [Path(path) for path in group.get("derived_summaries", []) if str(path).strip()]
    focus_derived_raw = group.get("focus_derived")
    focus_derived = (
        {str(name) for name in focus_derived_raw if str(name).strip()}
        if isinstance(focus_derived_raw, list)
        else None
    )

    lines = [rf"\subsubsection{{{latex_escape(title)}}}", "", *appendix_notice_box()]
    had_content = False

    derived_heading_written = False
    for path in derived_paths:
        if not path.exists():
            lines.append(rf"\NeedsInput{{Missing calculation-detail source: {latex_escape(str(path))}}}")
            lines.append("")
            continue
        payload = load_json(path)
        inputs = payload.get("inputs")
        derived = payload.get("derived")
        coverage_k = float(payload.get("coverage_k") or 2.0)
        if not isinstance(inputs, dict) or not isinstance(derived, dict):
            lines.append(rf"\NeedsInput{{Missing calculation-detail source structure: {latex_escape(str(path))}}}")
            lines.append("")
            continue
        if not derived_heading_written:
            lines.extend([r"\paragraph{Derived Quantity Chain}", ""])
            derived_heading_written = True
        rendered_any = False
        for derived_name, derived_payload in derived.items():
            if not isinstance(derived_payload, dict):
                continue
            if focus_derived is not None and derived_name not in focus_derived:
                continue
            rendered_any = True
            lines.extend(derived_block(str(derived_name), derived_payload, coverage_k))
        had_content = had_content or rendered_any

    if not had_content and not direct_paths:
        lines.append(r"\NeedsInput{No calculation-detail sources were provided for this attachment.}")
        lines.append("")
    elif not had_content and direct_paths:
        lines.append(
            r"\NeedsInput{Only direct-summary sources were provided. Add a derived-summary artifact to render a compact mathematical appendix.}"
        )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output-manifest", required=True)
    args = parser.parse_args()

    spec_path = Path(args.spec)
    spec = load_json(spec_path)
    groups = spec.get("groups")
    if not isinstance(groups, list):
        raise SystemExit("Calculation-details spec must contain a list-valued 'groups'.")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, object]] = []
    for index, raw_group in enumerate(groups):
        if not isinstance(raw_group, dict):
            continue
        title = str(raw_group.get("title") or f"Calculation Details {index + 1}")
        slug = safe_label(str(raw_group.get("slug") or title), default=f"details-{index + 1}")
        output_path = output_dir / f"{slug}.tex"
        output_path.write_text(render_group(raw_group), encoding="utf-8")
        entries.append(
            {
                "title": title,
                "path": str(output_path),
                "order": int(raw_group.get("order") or ((index + 1) * 10)),
                "kind": "calculation_details",
                "exists": output_path.exists(),
                "slug": slug,
            }
        )

    write_json(Path(args.output_manifest), {"entries": entries})
    print(json.dumps({"output_manifest": args.output_manifest, "entry_count": len(entries)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
