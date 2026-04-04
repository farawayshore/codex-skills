from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = SKILL_DIR / "scripts"


class CourseLabPropagateUncertaintiesTests(unittest.TestCase):
    def test_cli_computes_chained_derived_quantities_with_propagation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            spec_path = tmp / "spec.json"
            output_markdown = tmp / "derived.md"
            output_json = tmp / "derived.json"
            spec = {
                "coverage_k": 2.0,
                "inputs": {
                    "T": {"value": 1.402, "std_uncertainty": 0.001, "unit": "N", "label": "tension"},
                    "m": {"value": 0.01391, "std_uncertainty": 0.00001, "unit": "kg", "label": "mass"},
                    "L": {"value": 3.0, "std_uncertainty": 0.0001, "unit": "m", "label": "length"},
                },
                "derived": [
                    {"name": "rho", "expression": "m / L", "unit": "kg/m", "label": "linear density"},
                    {"name": "a", "expression": "sqrt(T / rho)", "unit": "m/s", "label": "wave speed"},
                ],
            }
            spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "propagate_uncertainties.py"),
                    "--spec",
                    str(spec_path),
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
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            rho = payload["derived"]["rho"]
            wave_speed = payload["derived"]["a"]
            self.assertAlmostEqual(rho["value"], 0.01391 / 3.0, places=12)
            self.assertAlmostEqual(wave_speed["value"], math.sqrt(1.402 / (0.01391 / 3.0)), places=9)
            self.assertGreater(rho["std_uncertainty"], 0.0)
            self.assertGreater(wave_speed["std_uncertainty"], 0.0)
            self.assertIn("sqrt(T / rho)", output_markdown.read_text(encoding="utf-8"))

    def test_cli_can_read_direct_summary_json_as_input_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            summary_path = tmp / "summary.json"
            spec_path = tmp / "spec.json"
            output_json = tmp / "derived.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "input": "direct.csv",
                        "coverage_k": 2.0,
                        "columns": {
                            "T/N": {
                                "n": 3,
                                "mean": 1.402,
                                "sample_stddev": 0.0,
                                "type_a": 0.0,
                                "resolution": 0.001,
                                "type_b": 0.001 / math.sqrt(3),
                                "type_c": 0.001 / math.sqrt(3),
                                "expanded_uncertainty": 2 * 0.001 / math.sqrt(3),
                            }
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            spec = {
                "coverage_k": 2.0,
                "inputs": {
                    "T": {
                        "summary_json": str(summary_path),
                        "column": "T/N",
                        "value_key": "mean",
                        "uncertainty_key": "type_c",
                        "unit": "N",
                    }
                },
                "derived": [
                    {"name": "double_tension", "expression": "2 * T", "unit": "N"},
                ],
            }
            spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "propagate_uncertainties.py"),
                    "--spec",
                    str(spec_path),
                    "--output-json",
                    str(output_json),
                    "--output-markdown",
                    str(tmp / "derived.md"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertAlmostEqual(payload["inputs"]["T"]["value"], 1.402, places=12)
            self.assertAlmostEqual(payload["derived"]["double_tension"]["value"], 2.804, places=12)

    def test_direct_summary_import_rejects_alias_that_changes_measured_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            summary_path = tmp / "summary.json"
            spec_path = tmp / "spec.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "input": "ring.csv",
                        "coverage_k": 2.0,
                        "columns": {
                            "2r/mm": {
                                "n": 3,
                                "mean": 0.499333,
                                "sample_stddev": 0.0011547,
                                "type_a": 0.000666667,
                                "resolution": None,
                                "type_b": 0.0,
                                "type_c": 0.000666667,
                                "expanded_uncertainty": 0.00133333,
                                "raw_label": "2r/mm",
                                "quantity_label": "2r",
                                "unit": "mm",
                            }
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            spec = {
                "coverage_k": 2.0,
                "inputs": {
                    "r": {
                        "summary_json": str(summary_path),
                        "column": "2r/mm",
                        "value_key": "mean",
                        "uncertainty_key": "type_c",
                        "unit": "mm",
                    }
                },
                "derived": [],
            }
            spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "propagate_uncertainties.py"),
                    "--spec",
                    str(spec_path),
                    "--output-json",
                    str(tmp / "derived.json"),
                    "--output-markdown",
                    str(tmp / "derived.md"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("canonical", completed.stderr)

    def test_direct_summary_import_allows_derived_symbol_change_after_preserving_measured_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            summary_path = tmp / "summary.json"
            spec_path = tmp / "spec.json"
            output_json = tmp / "derived.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "input": "ring.csv",
                        "coverage_k": 2.0,
                        "columns": {
                            "2r/mm": {
                                "n": 3,
                                "mean": 0.499333,
                                "sample_stddev": 0.0011547,
                                "type_a": 0.000666667,
                                "resolution": None,
                                "type_b": 0.0,
                                "type_c": 0.000666667,
                                "expanded_uncertainty": 0.00133333,
                                "raw_label": "2r/mm",
                                "quantity_label": "2r",
                                "unit": "mm",
                            }
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            spec = {
                "coverage_k": 2.0,
                "inputs": {
                    "two_r": {
                        "summary_json": str(summary_path),
                        "column": "2r/mm",
                        "value_key": "mean",
                        "uncertainty_key": "type_c",
                        "unit": "mm",
                    }
                },
                "derived": [
                    {"name": "r", "expression": "two_r / 2", "unit": "mm"},
                ],
            }
            spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "propagate_uncertainties.py"),
                    "--spec",
                    str(spec_path),
                    "--output-json",
                    str(output_json),
                    "--output-markdown",
                    str(tmp / "derived.md"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertAlmostEqual(payload["inputs"]["two_r"]["value"], 0.499333, places=12)
            self.assertAlmostEqual(payload["derived"]["r"]["value"], 0.2496665, places=12)


if __name__ == "__main__":
    unittest.main()
