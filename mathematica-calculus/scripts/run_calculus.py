#!/usr/bin/env python3
"""Evaluate Wolfram Language calculus expressions via wolframscript."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

RESULT_MARKER = "__CODEX_WOLFRAM_RESULT__"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a Wolfram Language expression and return the final result."
    )
    parser.add_argument(
        "--expr",
        help="Wolfram Language expression or compound expression to evaluate.",
    )
    parser.add_argument(
        "--expr-file",
        help="Path to a file containing Wolfram Language source to evaluate.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Maximum evaluation time in seconds. Default: 60.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON instead of plain text.",
    )
    args = parser.parse_args()
    if bool(args.expr) == bool(args.expr_file):
        parser.error("Provide exactly one of --expr or --expr-file.")
    return args


def resolve_engine() -> str:
    override = os.environ.get("WOLFRAMSCRIPT_BIN")
    if override:
        if Path(override).exists():
            return override
        resolved = shutil.which(override)
        if resolved:
            return resolved
        raise FileNotFoundError(
            f"WOLFRAMSCRIPT_BIN is set but not usable: {override}"
        )

    resolved = shutil.which("wolframscript")
    if resolved:
        return resolved

    raise FileNotFoundError(
        "wolframscript was not found. Install it or set WOLFRAMSCRIPT_BIN."
    )


def read_expression(args: argparse.Namespace) -> str:
    if args.expr_file:
        return Path(args.expr_file).read_text(encoding="utf-8")
    return args.expr


def build_script(expression: str) -> str:
    return (
        "$HistoryLength = 0;\n"
        "result = Quiet@Check[\n"
        "(\n"
        f"{expression}\n"
        "),\n"
        "$Failed\n"
        "];\n"
        "If[result === $Failed,\n"
        '  WriteString[$stderr, "Mathematica evaluation failed.\\n"];\n'
        "  Exit[1]\n"
        "];\n"
        f'WriteString[$Output, "{RESULT_MARKER}\\n"];\n'
        'WriteString[$Output, ToString[result, InputForm] <> "\\n"];\n'
    )


def extract_result(stdout: str) -> str:
    if RESULT_MARKER not in stdout:
        return stdout.strip()
    after_marker = stdout.rsplit(RESULT_MARKER, 1)[-1]
    return after_marker.strip()


def emit(payload: dict[str, object], as_json: bool) -> int:
    if as_json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0 if payload["success"] else 1

    if payload["success"]:
        print(payload["result"])
        return 0

    message = payload.get("error") or "Mathematica evaluation failed."
    stderr = payload.get("stderr") or ""
    stdout = payload.get("stdout") or ""
    parts = [str(message).strip()]
    if stderr:
        parts.append(str(stderr).strip())
    elif stdout:
        parts.append(str(stdout).strip())
    print("\n".join(part for part in parts if part), file=sys.stderr)
    return 1


def main() -> int:
    args = parse_args()

    try:
        engine = resolve_engine()
        expression = read_expression(args)
    except Exception as exc:
        return emit(
            {
                "success": False,
                "error": str(exc),
                "result": "",
                "stdout": "",
                "stderr": "",
                "engine": "",
                "returncode": None,
                "duration_seconds": 0.0,
            },
            args.json,
        )

    script_text = build_script(expression)
    start = time.time()

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".wl", delete=False, encoding="utf-8"
    ) as handle:
        handle.write(script_text)
        temp_path = handle.name

    try:
        completed = subprocess.run(
            [engine, "-file", temp_path],
            capture_output=True,
            text=True,
            timeout=args.timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.time() - start
        return emit(
            {
                "success": False,
                "error": f"Timed out after {args.timeout} seconds.",
                "result": "",
                "stdout": (exc.stdout or "").strip(),
                "stderr": (exc.stderr or "").strip(),
                "engine": engine,
                "returncode": None,
                "duration_seconds": round(duration, 3),
            },
            args.json,
        )
    finally:
        Path(temp_path).unlink(missing_ok=True)

    duration = time.time() - start
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    result = extract_result(completed.stdout)
    success = completed.returncode == 0 and bool(result)

    payload = {
        "success": success,
        "error": "" if success else "Mathematica evaluation failed.",
        "result": result,
        "stdout": stdout,
        "stderr": stderr,
        "engine": engine,
        "returncode": completed.returncode,
        "duration_seconds": round(duration, 3),
    }
    return emit(payload, args.json)


if __name__ == "__main__":
    raise SystemExit(main())
