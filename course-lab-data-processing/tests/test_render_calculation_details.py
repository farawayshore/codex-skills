from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = SKILL_DIR / "scripts"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class RenderCalculationDetailsTests(unittest.TestCase):
    def build_fixture(self, root: Path) -> dict[str, Path]:
        spec_path = root / "calculation_details_spec.json"
        direct_summary_json = root / "analysis" / "uncertainty" / "direct_summary.json"
        derived_summary_json = root / "analysis" / "uncertainty" / "derived_summary.json"
        output_dir = root / "analysis" / "calculation_details"
        output_manifest = root / "analysis" / "calculation_details_manifest.json"

        write_json(
            direct_summary_json,
            {
                "input": str(root / "analysis" / "direct_measurements.csv"),
                "coverage_k": 2.0,
                "columns": {
                    "frequency/Hz": {
                        "n": 3,
                        "mean": 10.2,
                        "sample_stddev": 0.1732050808,
                        "type_a": 0.1,
                        "resolution": 0.1,
                        "type_b": 0.0577350269,
                        "type_c": 0.1154700538,
                        "expanded_uncertainty": 0.2309401076,
                        "raw_label": "frequency/Hz",
                        "quantity_label": "frequency",
                        "unit": "Hz",
                        "canonical_key": "frequency",
                    }
                },
            },
        )

        write_json(
            derived_summary_json,
            {
                "spec": str(root / "analysis" / "wave_speed_spec.json"),
                "coverage_k": 2.0,
                "inputs": {
                    "lambda": {
                        "value": 2.0,
                        "std_uncertainty": 0.2,
                        "unit": "m",
                        "label": "wavelength",
                        "symbol": "lambda",
                        "canonical_key": "lambda",
                        "raw_label": "lambda/m",
                        "source": "inline",
                        "expanded_uncertainty": 0.4,
                    },
                    "f": {
                        "value": 10.2,
                        "std_uncertainty": 0.1,
                        "unit": "Hz",
                        "label": "frequency",
                        "symbol": "f",
                        "canonical_key": "f",
                        "raw_label": "frequency/Hz",
                        "source": f"{direct_summary_json}:frequency/Hz",
                        "expanded_uncertainty": 0.2,
                    },
                    "unused": {
                        "value": 99.0,
                        "std_uncertainty": 9.9,
                        "unit": "s",
                        "label": "unused quantity",
                        "symbol": "t_unused",
                        "canonical_key": "unused",
                        "raw_label": "unused/s",
                        "source": "inline",
                        "expanded_uncertainty": 19.8,
                    },
                },
                "derived": {
                    "half_lambda": {
                        "label": "half wavelength",
                        "expression": "lambda / 2",
                        "unit": "m",
                        "value": 1.0,
                        "std_uncertainty": 0.1,
                        "expanded_uncertainty": 0.2,
                        "gradient": {"lambda": 0.5, "f": 0.0},
                        "partials": {"lambda": 0.5},
                    },
                    "wave_speed": {
                        "label": "wave speed",
                        "expression": "lambda * f",
                        "unit": "m/s",
                        "value": 20.4,
                        "std_uncertainty": 0.25,
                        "expanded_uncertainty": 0.5,
                        "gradient": {"lambda": 10.2, "f": 2.0},
                        "partials": {"lambda": 10.2, "f": 2.0},
                    },
                },
            },
        )

        write_json(
            spec_path,
            {
                "groups": [
                    {
                        "title": "Case A Calculation Details",
                        "slug": "case-a",
                        "order": 10,
                        "direct_summaries": [str(direct_summary_json)],
                        "derived_summaries": [str(derived_summary_json)],
                    }
                ]
            },
        )

        return {
            "spec_path": spec_path,
            "output_dir": output_dir,
            "output_manifest": output_manifest,
        }

    def run_renderer(self, fixture: dict[str, Path]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT_DIR / "render_calculation_details.py"),
                "--spec",
                str(fixture["spec_path"]),
                "--output-dir",
                str(fixture["output_dir"]),
                "--output-manifest",
                str(fixture["output_manifest"]),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_cli_writes_manifest_and_tex_for_helper_and_final_quantities(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = self.build_fixture(Path(tmpdir))

            completed = self.run_renderer(fixture)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads(fixture["output_manifest"].read_text(encoding="utf-8"))
            self.assertIn("entries", manifest)
            self.assertEqual(len(manifest["entries"]), 1)
            entry = manifest["entries"][0]
            self.assertEqual(entry["title"], "Case A Calculation Details")
            self.assertEqual(entry["kind"], "calculation_details")
            self.assertEqual(entry["order"], 10)
            self.assertTrue(entry["exists"])
            tex_path = Path(entry["path"])
            self.assertTrue(tex_path.exists())

            tex = tex_path.read_text(encoding="utf-8")
            self.assertIn(r"\subsubsection{Case A Calculation Details}", tex)
            self.assertIn(r"\fcolorbox", tex)
            self.assertIn("Appendix Calculation Note", tex)
            self.assertNotIn("Direct Measurement Summary", tex)
            self.assertNotIn("Result Summary", tex)
            self.assertIn("Derived Quantity Chain", tex)
            self.assertLess(tex.find("half wavelength"), tex.find("wave speed"))
            self.assertIn(r"\begin{aligned}", tex)
            self.assertIn(r"wave_{speed}", tex)
            self.assertIn(r"\frac{\partial", tex)
            self.assertIn(r"f \lambda", tex)
            self.assertIn(r"\sqrt{", tex)
            self.assertNotIn(r"\Bigr]^{1/2}", tex)
            self.assertNotIn("unused quantity", tex)
            self.assertNotIn("t\\_unused", tex)
            self.assertNotIn("Adopted Inputs", tex)
            self.assertNotIn(r"\left(10.2\times0.2\right)^2", tex)

    def test_cli_keeps_incomplete_calculation_visible_in_generated_tex(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = self.build_fixture(Path(tmpdir))
            spec = json.loads(fixture["spec_path"].read_text(encoding="utf-8"))
            spec["groups"].append(
                {
                    "title": "Incomplete Calculation Details",
                    "slug": "incomplete-case",
                    "order": 20,
                    "direct_summaries": [],
                    "derived_summaries": [str(Path(tmpdir) / "analysis" / "uncertainty" / "missing.json")],
                }
            )
            write_json(fixture["spec_path"], spec)

            completed = self.run_renderer(fixture)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads(fixture["output_manifest"].read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["entries"]), 2)
            incomplete_entry = manifest["entries"][1]
            tex = Path(incomplete_entry["path"]).read_text(encoding="utf-8")
            self.assertIn(r"\NeedsInput{Missing calculation-detail source", tex)

    def test_cli_can_focus_on_selected_derived_quantities_for_compact_appendix(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = self.build_fixture(Path(tmpdir))
            spec = json.loads(fixture["spec_path"].read_text(encoding="utf-8"))
            spec["groups"][0]["focus_derived"] = ["wave_speed"]
            write_json(fixture["spec_path"], spec)

            completed = self.run_renderer(fixture)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads(fixture["output_manifest"].read_text(encoding="utf-8"))
            tex = Path(manifest["entries"][0]["path"]).read_text(encoding="utf-8")
            self.assertIn("wave speed", tex)
            self.assertNotIn("half wavelength", tex)

    def test_cli_compacts_mean_like_derivations_with_sum_notation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = self.build_fixture(Path(tmpdir))
            spec = json.loads(fixture["spec_path"].read_text(encoding="utf-8"))
            derived_path = Path(spec["groups"][0]["derived_summaries"][0])
            derived_payload = json.loads(derived_path.read_text(encoding="utf-8"))
            derived_payload["inputs"] = {
                f"v{i}": {
                    "value": float(i),
                    "std_uncertainty": 0.1,
                    "unit": "m/s",
                    "label": f"v{i}",
                    "symbol": f"v{i}",
                    "canonical_key": f"v{i}",
                    "raw_label": f"v{i}/(m/s)",
                    "source": "inline",
                    "expanded_uncertainty": 0.2,
                }
                for i in range(1, 6)
            }
            derived_payload["derived"] = {
                "v_mean": {
                    "label": "mean speed",
                    "expression": "(v1 + v2 + v3 + v4 + v5) / 5",
                    "unit": "m/s",
                    "value": 3.0,
                    "std_uncertainty": 0.1,
                    "expanded_uncertainty": 0.2,
                    "gradient": {f"v{i}": 0.2 for i in range(1, 6)},
                    "partials": {f"v{i}": 0.2 for i in range(1, 6)},
                }
            }
            write_json(derived_path, derived_payload)
            spec["groups"][0]["focus_derived"] = ["v_mean"]
            write_json(fixture["spec_path"], spec)

            completed = self.run_renderer(fixture)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads(fixture["output_manifest"].read_text(encoding="utf-8"))
            tex = Path(manifest["entries"][0]["path"]).read_text(encoding="utf-8")
            self.assertIn(r"\sum", tex)
            self.assertIn(r"u\!\left(v_{j}\right)", tex)
            self.assertIn(r"\sqrt{", tex)
            self.assertNotIn(r"\frac{\partial v_{mean}}{\partial v_{1}}", tex)

    def test_cli_uses_appendix_wide_notice_box_instead_of_columnwidth(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = self.build_fixture(Path(tmpdir))

            completed = self.run_renderer(fixture)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads(fixture["output_manifest"].read_text(encoding="utf-8"))
            tex = Path(manifest["entries"][0]["path"]).read_text(encoding="utf-8")
            self.assertIn(r"\parbox{0.96\linewidth}{%", tex)
            self.assertNotIn(r"\columnwidth", tex)


if __name__ == "__main__":
    unittest.main()
