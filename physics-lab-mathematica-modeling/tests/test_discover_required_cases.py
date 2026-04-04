from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "discover_required_cases.py"


def load_module(module_path: Path, module_name: str):
    if not module_path.exists():
        raise AssertionError(f"missing module file: {module_path}")

    script_dir = str(module_path.parent)
    inserted = False
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
        inserted = True

    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise AssertionError(f"unable to load module spec: {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if inserted:
            sys.path.pop(0)


class DiscoverRequiredCasesTests(unittest.TestCase):
    def test_discovers_picture_result_cases_and_merges_with_handout_only_cases(self) -> None:
        module = load_module(SCRIPT_PATH, "discover_required_cases_merge")

        with tempfile.TemporaryDirectory() as tmpdir:
            picture_dir = Path(tmpdir)
            (picture_dir / "1.f=1.8308kHz,m=0,n=4时的二维驻波图.jpg").write_text("", encoding="utf-8")
            (picture_dir / "4.f=6.3054kHz,m=5,n=5时的二维驻波图.jpg").write_text("", encoding="utf-8")
            config = {
                "discovery": {
                    "enabled": True,
                    "picture_results_dir": str(picture_dir),
                    "parser": "lx2_filename",
                },
                "handout_cases": [
                    {
                        "case_id": "handout-extra",
                        "parameters": {"frequency_hz": 10197.0, "m": 5, "n": 7},
                    }
                ],
            }

            result = module.discover_required_cases(config)

            self.assertEqual(len(result["required_cases"]), 3)
            case_keys = {(case["parameters"]["m"], case["parameters"]["n"]) for case in result["required_cases"]}
            self.assertIn((0, 4), case_keys)
            self.assertIn((5, 5), case_keys)
            self.assertIn((5, 7), case_keys)

    def test_deduplicates_duplicate_handout_and_picture_cases(self) -> None:
        module = load_module(SCRIPT_PATH, "discover_required_cases_deduplicate")

        with tempfile.TemporaryDirectory() as tmpdir:
            picture_dir = Path(tmpdir)
            (picture_dir / "4.f=6.3054kHz,m=5,n=5时的二维驻波图.jpg").write_text("", encoding="utf-8")
            config = {
                "discovery": {
                    "enabled": True,
                    "picture_results_dir": str(picture_dir),
                    "parser": "lx2_filename",
                },
                "handout_cases": [
                    {
                        "case_id": "handout-duplicate",
                        "parameters": {"frequency_hz": 6305.4, "m": 5, "n": 5},
                    }
                ],
            }

            result = module.discover_required_cases(config)

            self.assertEqual(len(result["required_cases"]), 1)
            merged_case = result["required_cases"][0]
            self.assertIn("picture_results", merged_case["sources"])
            self.assertIn("handout", merged_case["sources"])


if __name__ == "__main__":
    unittest.main()
