from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "detect_special_points.py"


def load_module():
    assert SCRIPT_PATH.exists(), f"missing script: {SCRIPT_PATH}"
    spec = importlib.util.spec_from_file_location("course_lab_plotting_detect_special_points", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DetectSpecialPointsTests(unittest.TestCase):
    def test_detects_max_min_and_exact_zero(self) -> None:
        module = load_module()

        points = module.detect_special_points(
            x_values=[0.0, 1.0, 2.0, 3.0],
            y_values=[2.0, 0.0, 5.0, -1.0],
        )

        kinds = {point["kind"] for point in points}
        self.assertEqual(kinds, {"max", "min", "zero"})

    def test_detects_zero_crossing_from_sign_change(self) -> None:
        module = load_module()

        points = module.detect_special_points(
            x_values=[0.0, 1.0, 2.0],
            y_values=[-1.0, 1.0, 2.0],
            requested_kinds=["zero"],
        )

        self.assertEqual(len(points), 1)
        self.assertAlmostEqual(points[0]["x"], 0.5, places=4)


if __name__ == "__main__":
    unittest.main()
