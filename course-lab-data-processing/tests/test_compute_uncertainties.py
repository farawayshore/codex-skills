from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = SKILL_DIR / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from compute_uncertainties import canonical_symbol_key, load_rows, parse_quantity_label, summarize_column


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class CourseLabUncertaintyAnalysisTests(unittest.TestCase):
    def test_handout_style_label_splits_quantity_and_unit(self) -> None:
        parsed = parse_quantity_label("T/N")
        self.assertEqual(parsed["quantity_label"], "T")
        self.assertEqual(parsed["unit"], "N")

    def test_composite_measured_symbol_gets_canonical_safe_key(self) -> None:
        parsed = parse_quantity_label("2r/mm")
        self.assertEqual(parsed["quantity_label"], "2r")
        self.assertEqual(parsed["unit"], "mm")
        self.assertEqual(canonical_symbol_key(parsed["quantity_label"]), "two_r")

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

    def test_cli_writes_markdown_and_json_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_markdown = Path(tmpdir) / "uncertainty.md"
            output_json = Path(tmpdir) / "uncertainty.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "compute_uncertainties.py"),
                    "--input",
                    str(FIXTURES / "sample_measurements.csv"),
                    "--quantity",
                    "voltage",
                    "--resolution",
                    "voltage=0.01",
                    "--output-markdown",
                    str(output_markdown),
                    "--output-json",
                    str(output_json),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(output_markdown.exists())
            self.assertTrue(output_json.exists())
            self.assertIn("Processed Uncertainty Summary", output_markdown.read_text(encoding="utf-8"))
            self.assertIn("| voltage |", output_markdown.read_text(encoding="utf-8"))

            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["coverage_k"], 2.0)
            self.assertIn("voltage", payload["columns"])


if __name__ == "__main__":
    unittest.main()
