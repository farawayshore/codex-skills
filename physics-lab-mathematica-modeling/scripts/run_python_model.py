#!/usr/bin/env python3
"""Run a generated Python modeling workflow."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import time


def run_python_workflow(workflow_path: Path, timeout: int = 60) -> dict:
    start = time.time()
    completed = subprocess.run(
        ["python3", str(workflow_path)],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    duration = time.time() - start
    return {
        "success": completed.returncode == 0,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "returncode": completed.returncode,
        "duration_seconds": round(duration, 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a generated Python modeling workflow.")
    parser.add_argument("--workflow", required=True, help="Path to generated Python workflow")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout in seconds. Default: 60.")
    args = parser.parse_args()
    payload = run_python_workflow(Path(args.workflow), timeout=args.timeout)
    if payload["success"]:
        print(payload["stdout"])
        return 0
    print(payload["stderr"] or "Python modeling workflow failed.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
