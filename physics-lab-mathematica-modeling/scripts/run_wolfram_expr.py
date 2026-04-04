#!/usr/bin/env python3
"""Evaluate Wolfram Language expressions via wolframscript."""

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
        description="Run a Wolfram Language expression or file and return structured output."
    )
    parser.add_argument("--expr", help="Wolfram Language expression to evaluate.")
    parser.add_argument("--expr-file", help="Path to a .wl file to evaluate.")
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Maximum evaluation time in seconds. Default: 60.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of plain output.",
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
        raise FileNotFoundError(f"WOLFRAMSCRIPT_BIN is set but not usable: {override}")

    resolved = shutil.which("wolframscript")
    if resolved:
        return resolved

    raise FileNotFoundError("wolframscript was not found. Install it or set WOLFRAMSCRIPT_BIN.")


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
    return stdout.rsplit(RESULT_MARKER, 1)[-1].strip()


def emit(payload: dict[str, object], as_json: bool) -> int:
    if as_json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0 if payload["success"] else 1

    if payload["success"]:
        print(payload["result"])
        return 0

    message = payload.get("error") or "Mathematica evaluation failed."
    print(str(message), file=sys.stderr)
    return 1


def run_wolfram_workflow(workflow_path: Path, timeout: int = 60) -> dict[str, object]:
    engine = resolve_engine()
    start = time.time()
    completed = subprocess.run(
        [engine, "-file", str(workflow_path)],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    duration = time.time() - start
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    result = extract_result(completed.stdout)
    success = completed.returncode == 0
    return {
        "success": success,
        "result": result,
        "stdout": stdout,
        "stderr": stderr,
        "engine": engine,
        "returncode": completed.returncode,
        "duration_seconds": round(duration, 3),
    }


def main() -> int:
    args = parse_args()
    expression = args.expr
    if args.expr_file:
        expression = Path(args.expr_file).read_text(encoding="utf-8")
    script_text = build_script(expression)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".wl", delete=False, encoding="utf-8") as handle:
        handle.write(script_text)
        temp_path = Path(handle.name)

    try:
        payload = run_wolfram_workflow(temp_path, timeout=args.timeout)
    except subprocess.TimeoutExpired as exc:
        payload = {
            "success": False,
            "error": f"Timed out after {args.timeout} seconds.",
            "result": "",
            "stdout": (exc.stdout or "").strip(),
            "stderr": (exc.stderr or "").strip(),
            "engine": "",
            "returncode": None,
            "duration_seconds": round(args.timeout, 3),
        }
    except Exception as exc:
        payload = {
            "success": False,
            "error": str(exc),
            "result": "",
            "stdout": "",
            "stderr": "",
            "engine": "",
            "returncode": None,
            "duration_seconds": 0.0,
        }
    finally:
        temp_path.unlink(missing_ok=True)

    return emit(payload, args.json)


if __name__ == "__main__":
    raise SystemExit(main())
