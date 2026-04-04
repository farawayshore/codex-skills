#!/usr/bin/env python3
"""Compute derived quantities and propagated uncertainties from a handout-aligned spec."""

from __future__ import annotations

import argparse
import ast
import json
import math
from pathlib import Path

from common import write_json
from compute_uncertainties import canonical_symbol_key, parse_quantity_label


ALLOWED_FUNCTIONS = {
    "abs": abs,
    "acos": math.acos,
    "asin": math.asin,
    "atan": math.atan,
    "cos": math.cos,
    "e": math.e,
    "exp": math.exp,
    "log": math.log,
    "log10": math.log10,
    "pi": math.pi,
    "sin": math.sin,
    "sqrt": math.sqrt,
    "tan": math.tan,
}

ALLOWED_AST_NODES = (
    ast.Add,
    ast.BinOp,
    ast.Call,
    ast.Constant,
    ast.Div,
    ast.Expression,
    ast.Load,
    ast.Mult,
    ast.Name,
    ast.Pow,
    ast.Sub,
    ast.UAdd,
    ast.UnaryOp,
    ast.USub,
)


def compile_expression(expression: str) -> tuple[object, set[str]]:
    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_AST_NODES):
            raise SystemExit(f"Unsupported syntax in expression: {expression}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_FUNCTIONS:
                raise SystemExit(f"Unsupported function in expression: {expression}")

    names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id not in ALLOWED_FUNCTIONS
    }
    return compile(tree, "<expression>", "eval"), names


def evaluate_expression(compiled: object, variables: dict[str, float]) -> float:
    env = dict(ALLOWED_FUNCTIONS)
    env.update(variables)
    try:
        value = eval(compiled, {"__builtins__": {}}, env)
    except Exception as exc:
        raise SystemExit(f"Failed to evaluate expression: {exc}") from exc
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise SystemExit("Derived expression did not produce a finite numeric result.")
    return float(value)


def derivative(
    compiled: object,
    variables: dict[str, float],
    variable_name: str,
) -> float:
    x0 = variables[variable_name]
    step = max(abs(x0) * 1e-8, 1e-10)
    plus = dict(variables)
    minus = dict(variables)
    plus[variable_name] = x0 + step
    minus[variable_name] = x0 - step
    return (evaluate_expression(compiled, plus) - evaluate_expression(compiled, minus)) / (2.0 * step)


def load_spec(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_input_from_summary(input_name: str, source: dict[str, object]) -> dict[str, object]:
    summary_path = Path(str(source["summary_json"]))
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    columns = payload.get("columns", {})
    if not isinstance(columns, dict):
        raise SystemExit(f"Summary JSON does not contain columns: {summary_path}")
    column_name = str(source["column"])
    if column_name not in columns:
        raise SystemExit(f"Column '{column_name}' not found in summary JSON: {summary_path}")
    summary = columns[column_name]
    if not isinstance(summary, dict):
        raise SystemExit(f"Column '{column_name}' summary is invalid: {summary_path}")

    parsed = parse_quantity_label(str(summary.get("raw_label") or column_name))
    measured_symbol = str(summary.get("quantity_label") or parsed["quantity_label"])
    expected_key = str(summary.get("canonical_key") or canonical_symbol_key(measured_symbol))
    if input_name != expected_key:
        raise SystemExit(
            f"Direct measured input '{input_name}' must use canonical key '{expected_key}' "
            f"for measured symbol '{measured_symbol}'. Use an explicit derived step if you need a different symbol."
        )

    value_key = str(source.get("value_key", "mean"))
    uncertainty_key = str(source.get("uncertainty_key", "type_c"))
    if value_key not in summary:
        raise SystemExit(f"Value key '{value_key}' not found in summary column '{column_name}'.")
    if uncertainty_key not in summary:
        raise SystemExit(f"Uncertainty key '{uncertainty_key}' not found in summary column '{column_name}'.")

    return {
        "value": float(summary[value_key]),
        "std_uncertainty": float(summary[uncertainty_key]),
        "unit": source.get("unit") or summary.get("unit") or parsed["unit"],
        "label": source.get("label") or measured_symbol,
        "symbol": measured_symbol,
        "canonical_key": expected_key,
        "raw_label": summary.get("raw_label") or column_name,
        "source": f"{summary_path}:{column_name}",
    }


def resolve_input_entry(input_name: str, source: dict[str, object]) -> dict[str, object]:
    if "summary_json" in source:
        return load_input_from_summary(input_name, source)
    if "value" not in source:
        raise SystemExit("Each input entry must define either value or summary_json.")
    symbol = str(source.get("symbol") or input_name)
    expected_key = canonical_symbol_key(symbol)
    if input_name != expected_key:
        raise SystemExit(
            f"Direct measured input '{input_name}' must use canonical key '{expected_key}' "
            f"for measured symbol '{symbol}'. Use an explicit derived step if you need a different symbol."
        )
    return {
        "value": float(source["value"]),
        "std_uncertainty": float(source.get("std_uncertainty", 0.0)),
        "unit": source.get("unit"),
        "label": source.get("label"),
        "symbol": symbol,
        "canonical_key": expected_key,
        "raw_label": source.get("raw_label") or symbol,
        "source": "inline",
    }


def markdown_report(
    spec_path: Path,
    coverage_k: float,
    inputs: dict[str, dict[str, object]],
    derived: dict[str, dict[str, object]],
) -> str:
    lines = [
        "# Propagated Uncertainty Summary",
        "",
        f"- Spec: `{spec_path}`",
        f"- Coverage factor `k`: {coverage_k:g}",
        "",
        "## Inputs",
        "",
        "| Key | Symbol | Label | Unit | Value | Standard Uncertainty | Expanded | Source |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for name, payload in inputs.items():
        lines.append(
            f"| {name} | {payload.get('symbol') or name} | {payload.get('label') or '-'} | {payload.get('unit') or '-'} | "
            f"{payload['value']:.6g} | {payload['std_uncertainty']:.6g} | "
            f"{payload['expanded_uncertainty']:.6g} | {payload.get('source') or '-'} |"
        )

    lines.extend(
        [
            "",
            "## Derived",
            "",
            "| Quantity | Label | Expression | Unit | Value | Standard Uncertainty | Expanded |",
            "| --- | --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for name, payload in derived.items():
        lines.append(
            f"| {name} | {payload.get('label') or '-'} | `{payload['expression']}` | {payload.get('unit') or '-'} | "
            f"{payload['value']:.6g} | {payload['std_uncertainty']:.6g} | {payload['expanded_uncertainty']:.6g} |"
        )

    lines.append("")
    lines.append("Standard uncertainties are propagated from the base inputs through the expression gradients.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output-markdown", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()

    spec_path = Path(args.spec)
    spec = load_spec(spec_path)
    coverage_k = float(spec.get("coverage_k", 2.0))
    raw_inputs = spec.get("inputs", {})
    raw_derived = spec.get("derived", [])
    if not isinstance(raw_inputs, dict) or not isinstance(raw_derived, list):
        raise SystemExit("Spec must define object-valued 'inputs' and list-valued 'derived'.")

    inputs: dict[str, dict[str, object]] = {}
    base_std_uncertainties: dict[str, float] = {}
    quantity_values: dict[str, float] = {}
    gradients: dict[str, dict[str, float]] = {}

    for name, payload in raw_inputs.items():
        if not isinstance(payload, dict):
            raise SystemExit(f"Input '{name}' must be an object.")
        resolved = resolve_input_entry(str(name), payload)
        resolved["expanded_uncertainty"] = coverage_k * float(resolved["std_uncertainty"])
        inputs[name] = resolved
        quantity_values[name] = float(resolved["value"])
        base_std_uncertainties[name] = float(resolved["std_uncertainty"])
        gradients[name] = {key: 1.0 if key == name else 0.0 for key in raw_inputs.keys()}

    derived_outputs: dict[str, dict[str, object]] = {}
    for entry in raw_derived:
        if not isinstance(entry, dict) or "name" not in entry or "expression" not in entry:
            raise SystemExit("Each derived entry must include at least name and expression.")
        name = str(entry["name"])
        expression = str(entry["expression"])
        compiled, expression_names = compile_expression(expression)
        missing = sorted(name for name in expression_names if name not in quantity_values)
        if missing:
            raise SystemExit(f"Expression '{expression}' references unknown quantities: {', '.join(missing)}")

        value = evaluate_expression(compiled, quantity_values)
        local_partials = {var_name: derivative(compiled, quantity_values, var_name) for var_name in expression_names}

        gradient: dict[str, float] = {}
        for base_name in base_std_uncertainties:
            gradient[base_name] = sum(
                local_partials[var_name] * gradients[var_name][base_name]
                for var_name in expression_names
            )
        variance = sum((gradient[base_name] * base_std_uncertainties[base_name]) ** 2 for base_name in base_std_uncertainties)
        std_uncertainty = math.sqrt(max(variance, 0.0))
        derived_outputs[name] = {
            "label": entry.get("label"),
            "expression": expression,
            "unit": entry.get("unit"),
            "value": value,
            "std_uncertainty": std_uncertainty,
            "expanded_uncertainty": coverage_k * std_uncertainty,
            "gradient": gradient,
            "partials": local_partials,
        }
        quantity_values[name] = value
        gradients[name] = gradient

    output_markdown = Path(args.output_markdown)
    output_json = Path(args.output_json)
    output_markdown.write_text(markdown_report(spec_path, coverage_k, inputs, derived_outputs), encoding="utf-8")
    write_json(
        output_json,
        {
            "spec": str(spec_path),
            "coverage_k": coverage_k,
            "inputs": inputs,
            "derived": derived_outputs,
        },
    )
    print(json.dumps({"output_markdown": str(output_markdown), "output_json": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
