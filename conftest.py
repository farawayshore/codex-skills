from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parent


def _find_duplicate_module_stems() -> set[str]:
    counts: Counter[str] = Counter()
    for pattern in ("course-lab-*/scripts/*.py", "course-lab-*/tests/*.py"):
        for path in SKILLS_ROOT.glob(pattern):
            counts[path.stem] += 1
    return {stem for stem, count in counts.items() if count > 1}


DUPLICATE_MODULE_STEMS = _find_duplicate_module_stems()


def _purge_cached_modules(extra_stems: set[str] | None = None) -> None:
    for stem in DUPLICATE_MODULE_STEMS | (extra_stems or set()):
        sys.modules.pop(stem, None)


def pytest_collect_file(file_path: Path, parent):  # type: ignore[no-untyped-def]
    _purge_cached_modules({Path(str(file_path)).stem})
    return None
