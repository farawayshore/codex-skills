#!/usr/bin/env python3
"""Placeholder LX2 Python fallback workflow.

Replace this scaffold with an experiment-local Python solver before relying on
Python fallback for LX2. It exists so the sample config can carry a concrete
source_py path in the batch contract.
"""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "LX2 Python fallback scaffold reached. Replace this file with a real "
        "experiment-local Python modeling workflow before using Python fallback.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
