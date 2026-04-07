#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def safe_slug(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", text.strip()).strip("-")
    return slug or "symbolic-result"


def expression_to_tex(expression: str) -> str:
    return re.sub(r"sqrt\(([^()]+)\)", r"\\sqrt{\1}", expression)


def python_expr_to_text(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return "<unparsed expression>"


def extract_assignments(code_text: str) -> dict[str, str]:
    assignments: dict[str, str] = {}
    try:
        tree = ast.parse(code_text)
    except SyntaxError:
        return assignments
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        expression = python_expr_to_text(node.value)
        for target in node.targets:
            if isinstance(target, ast.Name):
                assignments[target.id] = expression
    return assignments


def result_record(processed: dict[str, object], result_key: str) -> dict[str, object] | None:
    for bucket_name in ("derived", "results", "indirect_results"):
        bucket = processed.get(bucket_name)
        if isinstance(bucket, dict):
            record = bucket.get(result_key)
            if isinstance(record, dict):
                return record
        if isinstance(bucket, list):
            for item in bucket:
                if isinstance(item, dict) and str(item.get("name") or item.get("key") or "") == result_key:
                    return item
    return None


def render_tex(
    result_key: str,
    handout_text: str,
    code_assignments: dict[str, str],
    record: dict[str, object] | None,
) -> tuple[str, list[str]]:
    unresolved: list[str] = []
    label = str(record.get("label") if record else result_key) if record else result_key
    expression = str(record.get("expression") or "").strip() if record else ""
    code_expression = code_assignments.get(result_key, "")

    lines = [rf"\paragraph{{Calculation route for {latex_escape(label)}}}"]
    if not record:
        unresolved.append(f"Processed result key was not found: {result_key}")
        lines.append(rf"\NeedsInput{{Processed result key was not found: {latex_escape(result_key)}.}}")
        return "\n".join(lines) + "\n", unresolved

    lower_handout = handout_text.casefold()
    if result_key.casefold() in lower_handout or label.casefold() in lower_handout:
        handout_hint = "The handout text mentions this result or its label."
    elif expression and any(token in lower_handout for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expression.casefold())):
        handout_hint = "The handout text contains symbols used in the processed expression."
    else:
        unresolved.append(f"Handout formula evidence was weak for result: {result_key}")
        handout_hint = "The handout formula evidence was incomplete, so this route is provisional."

    if not code_expression:
        unresolved.append(f"Calculation code assignment was not found for result: {result_key}")
        code_expression = expression or "unresolved"

    lines.append(latex_escape(handout_hint))
    if expression:
        lines.extend(["", r"\[", rf"{latex_escape(result_key)} = {expression_to_tex(expression)}", r"\]"])
    lines.append(
        latex_escape(
            f"The calculation code evaluates {result_key} using `{code_expression}` and the processed result artifact records "
            f"the expression `{expression or code_expression}`."
        )
    )
    return "\n".join(lines) + "\n", unresolved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--handout", required=True)
    parser.add_argument("--calculation-code", action="append", required=True)
    parser.add_argument("--processed-result", required=True)
    parser.add_argument("--result-key", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output-response-json", required=True)
    args = parser.parse_args()

    handout_path = Path(args.handout)
    processed_path = Path(args.processed_result)
    code_paths = [Path(path) for path in args.calculation_code]
    for path in [handout_path, processed_path, *code_paths]:
        if not path.exists():
            raise FileNotFoundError(path)

    handout_text = handout_path.read_text(encoding="utf-8")
    code_assignments: dict[str, str] = {}
    for path in code_paths:
        code_assignments.update(extract_assignments(path.read_text(encoding="utf-8")))
    processed = load_json(processed_path)
    record = result_record(processed, args.result_key)
    tex, unresolved = render_tex(args.result_key, handout_text, code_assignments, record)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    tex_path = output_dir / f"{safe_slug(args.result_key)}_symbolic_explanation.tex"
    tex_path.write_text(tex, encoding="utf-8")
    response_path = Path(args.output_response_json)
    response_path.parent.mkdir(parents=True, exist_ok=True)
    response = {
        "result_key": args.result_key,
        "tex_path": str(tex_path),
        "sources": {
            "handout": str(handout_path),
            "calculation_code": [str(path) for path in code_paths],
            "processed_result": str(processed_path),
        },
        "unresolved": unresolved,
    }
    response_path.write_text(json.dumps(response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(tex_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
