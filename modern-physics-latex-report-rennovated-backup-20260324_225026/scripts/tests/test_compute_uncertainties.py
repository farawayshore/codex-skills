from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from compute_uncertainties import load_rows, summarize_column


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class ComputeUncertaintiesTests(unittest.TestCase):
    def test_csv_rows_load_and_summary(self) -> None:
        rows = load_rows(FIXTURES / "sample_measurements.csv", None)
        self.assertEqual(len(rows), 3)
        values = [float(row["voltage"]) for row in rows]
        summary = summarize_column(values, 0.01, 2.0)
        self.assertEqual(summary["n"], 3)
        self.assertAlmostEqual(summary["mean"], 1.0, places=6)
        self.assertGreater(summary["type_a"], 0.0)
        self.assertGreater(summary["type_b"], 0.0)
        self.assertGreater(summary["expanded_uncertainty"], summary["type_c"])


if __name__ == "__main__":
    unittest.main()
