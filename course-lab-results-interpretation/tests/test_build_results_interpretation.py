from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "build_results_interpretation.py"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def write_handout_markdown(
    path: Path,
    *,
    simulation_required: bool = False,
    compare_simulation_to_theory: bool = False,
    required_result_families: tuple[str, ...] = ("wave_speed",),
    required_observations: tuple[str, ...] = ("node_pattern",),
) -> None:
    simulation_line = (
        "Simulation comparison is required."
        if simulation_required
        else "Simulation comparison is not required."
    )
    theory_line = (
        "Compare simulation with theory when both are available."
        if compare_simulation_to_theory
        else "Compare data with theory when references are available."
    )
    path.write_text(
        "\n".join(
            [
                "## Experiment Principle",
                "- Normalized key: `principle`",
                "",
                f"Required result families: {', '.join(required_result_families)}",
                f"Required observations: {', '.join(required_observations)}",
                simulation_line,
                theory_line,
                "The experiment compares measured results with expected behavior from the handout.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_handout_json(
    path: Path,
    *,
    simulation_required: bool = False,
    required_result_families: tuple[str, ...] = ("wave_speed",),
    required_observations: tuple[str, ...] = ("node_pattern",),
) -> None:
    path.write_text(
        json.dumps(
            {
                "section_order": ["principle"],
                "sections": {
                    "principle": {
                        "heading": "Experiment Principle",
                        "text": "\n".join(
                            [
                                f"Required result families: {', '.join(required_result_families)}",
                                f"Required observations: {', '.join(required_observations)}",
                                (
                                    "Simulation comparison is required."
                                    if simulation_required
                                    else "Simulation comparison is not required."
                                ),
                            ]
                        ),
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


class CourseLabResultsInterpretationTests(unittest.TestCase):
    def test_cli_requires_handout_input(self) -> None:
        self.assertTrue(SCRIPT_PATH.exists(), f"missing script: {SCRIPT_PATH}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            processed_data_json = tmp / "processed_data.json"
            output_json = tmp / "results_interpretation.json"
            output_markdown = tmp / "results_interpretation.md"
            output_unresolved = tmp / "results_interpretation_unresolved.md"

            processed_data_json.write_text(
                json.dumps(
                    {
                        "results": [
                            {"name": "wave_speed", "label": "wave speed", "value": 12.5, "unit": "m/s"}
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            completed = run_cli(
                "--processed-data-json",
                str(processed_data_json),
                "--output-json",
                str(output_json),
                "--output-markdown",
                str(output_markdown),
                "--output-unresolved",
                str(output_unresolved),
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("handout", (completed.stderr or completed.stdout).lower())

    def test_cli_emits_normal_interpretation_outputs_with_handout_and_reference_comparison(self) -> None:
        self.assertTrue(SCRIPT_PATH.exists(), f"missing script: {SCRIPT_PATH}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            handout_sections_markdown = tmp / "sections.md"
            processed_data_json = tmp / "processed_data.json"
            references_json = tmp / "reference_values.json"
            output_json = tmp / "results_interpretation.json"
            output_markdown = tmp / "results_interpretation.md"
            output_unresolved = tmp / "results_interpretation_unresolved.md"

            write_handout_markdown(handout_sections_markdown)
            processed_data_json.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "name": "wave_speed",
                                "label": "wave speed",
                                "value": 12.5,
                                "unit": "m/s",
                                "kind": "derived",
                                "sources": ["processed-data"],
                            }
                        ],
                        "observations": [
                            {
                                "name": "node_pattern",
                                "summary": "Clear standing-wave nodes were observed.",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            references_json.write_text(
                json.dumps(
                    {
                        "references": [
                            {
                                "name": "wave_speed",
                                "label": "theory wave speed",
                                "value": 12.0,
                                "unit": "m/s",
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            completed = run_cli(
                "--handout-sections-markdown",
                str(handout_sections_markdown),
                "--processed-data-json",
                str(processed_data_json),
                "--references-json",
                str(references_json),
                "--output-json",
                str(output_json),
                "--output-markdown",
                str(output_markdown),
                "--output-unresolved",
                str(output_unresolved),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertIn("result_inventory", payload)
            self.assertIn("comparison_records", payload)
            self.assertIn("interpretation_items", payload)
            self.assertIn("anomalies", payload)
            self.assertIn("completeness_checks", payload)
            self.assertIn("unresolved", payload)
            self.assertEqual(payload["result_inventory"][0]["name"], "wave_speed")
            lanes = {entry["lane"] for entry in payload["comparison_records"]}
            self.assertIn("handout_expectation_vs_data", lanes)
            self.assertIn("theory_reference_vs_data", lanes)
            self.assertIn("wave speed", output_markdown.read_text(encoding="utf-8").lower())

    def test_cli_prefers_handout_markdown_over_conflicting_json(self) -> None:
        self.assertTrue(SCRIPT_PATH.exists(), f"missing script: {SCRIPT_PATH}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            handout_sections_markdown = tmp / "sections.md"
            handout_sections_json = tmp / "sections.json"
            processed_data_json = tmp / "processed_data.json"
            output_json = tmp / "results_interpretation.json"
            output_markdown = tmp / "results_interpretation.md"
            output_unresolved = tmp / "results_interpretation_unresolved.md"

            write_handout_markdown(handout_sections_markdown, simulation_required=True)
            write_handout_json(handout_sections_json, simulation_required=False)
            processed_data_json.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "name": "wave_speed",
                                "label": "wave speed",
                                "value": 12.5,
                                "unit": "m/s",
                                "kind": "derived",
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            completed = run_cli(
                "--handout-sections-markdown",
                str(handout_sections_markdown),
                "--handout-sections-json",
                str(handout_sections_json),
                "--processed-data-json",
                str(processed_data_json),
                "--output-json",
                str(output_json),
                "--output-markdown",
                str(output_markdown),
                "--output-unresolved",
                str(output_unresolved),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            unresolved_text = output_unresolved.read_text(encoding="utf-8")
            self.assertEqual(payload["result_inventory"][0]["name"], "wave_speed")
            self.assertTrue(payload["unresolved"])
            self.assertIn("simulation", unresolved_text.lower())

    def test_cli_fails_when_handout_markdown_is_malformed_even_if_json_exists(self) -> None:
        self.assertTrue(SCRIPT_PATH.exists(), f"missing script: {SCRIPT_PATH}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            handout_sections_markdown = tmp / "sections.md"
            handout_sections_json = tmp / "sections.json"
            processed_data_json = tmp / "processed_data.json"
            output_json = tmp / "results_interpretation.json"
            output_markdown = tmp / "results_interpretation.md"
            output_unresolved = tmp / "results_interpretation_unresolved.md"

            handout_sections_markdown.write_text(
                "## Experiment Principle\nThis block has no normalized key.\n",
                encoding="utf-8",
            )
            write_handout_json(handout_sections_json, simulation_required=False)
            processed_data_json.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "name": "wave_speed",
                                "label": "wave speed",
                                "value": 12.5,
                                "unit": "m/s",
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            completed = run_cli(
                "--handout-sections-markdown",
                str(handout_sections_markdown),
                "--handout-sections-json",
                str(handout_sections_json),
                "--processed-data-json",
                str(processed_data_json),
                "--output-json",
                str(output_json),
                "--output-markdown",
                str(output_markdown),
                "--output-unresolved",
                str(output_unresolved),
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("malformed", completed.stderr.lower())

    def test_cli_records_simulation_and_theory_comparisons_as_explicit_lanes(self) -> None:
        self.assertTrue(SCRIPT_PATH.exists(), f"missing script: {SCRIPT_PATH}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            handout_sections_markdown = tmp / "sections.md"
            processed_data_json = tmp / "processed_data.json"
            modeling_result = tmp / "run_result.json"
            references_json = tmp / "reference_values.json"
            output_json = tmp / "results_interpretation.json"
            output_markdown = tmp / "results_interpretation.md"
            output_unresolved = tmp / "results_interpretation_unresolved.md"

            write_handout_markdown(
                handout_sections_markdown,
                simulation_required=True,
                compare_simulation_to_theory=True,
            )
            processed_data_json.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "name": "wave_speed",
                                "label": "wave speed",
                                "value": 12.5,
                                "unit": "m/s",
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            modeling_result.write_text(
                json.dumps(
                    {
                        "outputs": [
                            {"name": "wave_speed", "value": 12.2, "unit": "m/s"},
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            references_json.write_text(
                json.dumps(
                    {
                        "references": [
                            {
                                "name": "wave_speed",
                                "label": "theory wave speed",
                                "value": 12.0,
                                "unit": "m/s",
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            completed = run_cli(
                "--handout-sections-markdown",
                str(handout_sections_markdown),
                "--processed-data-json",
                str(processed_data_json),
                "--modeling-result",
                str(modeling_result),
                "--references-json",
                str(references_json),
                "--output-json",
                str(output_json),
                "--output-markdown",
                str(output_markdown),
                "--output-unresolved",
                str(output_unresolved),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            lanes = {entry["lane"] for entry in payload["comparison_records"]}
            self.assertEqual(
                lanes,
                {
                    "handout_expectation_vs_data",
                    "simulation_vs_data",
                    "theory_reference_vs_data",
                    "simulation_vs_theory_reference",
                },
            )
            self.assertIn("comparison records", output_markdown.read_text(encoding="utf-8").lower())

    def test_cli_separates_handout_internet_and_theory_justification_lanes(self) -> None:
        self.assertTrue(SCRIPT_PATH.exists(), f"missing script: {SCRIPT_PATH}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            handout_sections_markdown = tmp / "sections.md"
            processed_data_json = tmp / "processed_data.json"
            references_json = tmp / "reference_values.json"
            output_json = tmp / "results_interpretation.json"
            output_markdown = tmp / "results_interpretation.md"
            output_unresolved = tmp / "results_interpretation_unresolved.md"

            write_handout_markdown(
                handout_sections_markdown,
                required_result_families=("youngs_modulus",),
            )
            processed_data_json.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "name": "youngs_modulus",
                                "label": "Young's modulus",
                                "value": 2.03e11,
                                "unit": "Pa",
                                "kind": "derived",
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            references_json.write_text(
                json.dumps(
                    {
                        "comparison_requirements": {
                            "required_bases": [
                                "internet_reference",
                                "theoretical_computation",
                            ],
                            "optional_bases": ["handout_standard"],
                        },
                        "references": [
                            {
                                "name": "youngs_modulus",
                                "label": "Handout stainless reference",
                                "value": 1.95e11,
                                "unit": "Pa",
                                "comparison_basis": "handout_standard",
                                "source": "notes/lx1_sections.md:159",
                            },
                            {
                                "name": "youngs_modulus",
                                "label": "MatWeb stainless steel reference",
                                "value": 2.00e11,
                                "unit": "Pa",
                                "comparison_basis": "internet_reference",
                                "source": "https://example.com/matweb",
                            },
                            {
                                "name": "youngs_modulus",
                                "label": "Beam-model inversion",
                                "value": 2.01e11,
                                "unit": "Pa",
                                "comparison_basis": "theoretical_computation",
                                "source": "analysis/theory_checks.json:youngs_modulus",
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            completed = run_cli(
                "--handout-sections-markdown",
                str(handout_sections_markdown),
                "--processed-data-json",
                str(processed_data_json),
                "--references-json",
                str(references_json),
                "--output-json",
                str(output_json),
                "--output-markdown",
                str(output_markdown),
                "--output-unresolved",
                str(output_unresolved),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            lanes = {entry["lane"] for entry in payload["comparison_records"]}
            self.assertIn("handout_standard_vs_data", lanes)
            self.assertIn("internet_reference_vs_data", lanes)
            self.assertIn("theoretical_computation_vs_data", lanes)
            self.assertIn("young's modulus", output_markdown.read_text(encoding="utf-8").lower())

    def test_cli_records_unresolved_when_required_justification_lane_is_missing(self) -> None:
        self.assertTrue(SCRIPT_PATH.exists(), f"missing script: {SCRIPT_PATH}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            handout_sections_markdown = tmp / "sections.md"
            processed_data_json = tmp / "processed_data.json"
            references_json = tmp / "reference_values.json"
            output_json = tmp / "results_interpretation.json"
            output_markdown = tmp / "results_interpretation.md"
            output_unresolved = tmp / "results_interpretation_unresolved.md"

            write_handout_markdown(
                handout_sections_markdown,
                required_result_families=("characteristic_frequency",),
            )
            processed_data_json.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "name": "characteristic_frequency",
                                "label": "characteristic frequency",
                                "value": 1830.8,
                                "unit": "Hz",
                                "kind": "reported",
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            references_json.write_text(
                json.dumps(
                    {
                        "comparison_requirements": {
                            "required_bases": [
                                "internet_reference",
                                "theoretical_computation",
                            ]
                        },
                        "references": [
                            {
                                "name": "characteristic_frequency",
                                "label": "Published brass plate mode range",
                                "value": 1800.0,
                                "unit": "Hz",
                                "comparison_basis": "internet_reference",
                                "source": "https://example.com/brass-plate",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            completed = run_cli(
                "--handout-sections-markdown",
                str(handout_sections_markdown),
                "--processed-data-json",
                str(processed_data_json),
                "--references-json",
                str(references_json),
                "--output-json",
                str(output_json),
                "--output-markdown",
                str(output_markdown),
                "--output-unresolved",
                str(output_unresolved),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertTrue(payload["unresolved"])
            unresolved_text = output_unresolved.read_text(encoding="utf-8").lower()
            self.assertIn("theoretical computation", unresolved_text)
            self.assertIn("characteristic_frequency", unresolved_text)

    def test_cli_records_unresolved_conflict_when_json_and_markdown_disagree(self) -> None:
        self.assertTrue(SCRIPT_PATH.exists(), f"missing script: {SCRIPT_PATH}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            handout_sections_markdown = tmp / "sections.md"
            processed_data_json = tmp / "processed_data.json"
            processed_data_markdown = tmp / "processed_data.md"
            output_json = tmp / "results_interpretation.json"
            output_markdown = tmp / "results_interpretation.md"
            output_unresolved = tmp / "results_interpretation_unresolved.md"

            write_handout_markdown(handout_sections_markdown)
            processed_data_json.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "name": "wave_speed",
                                "label": "wave speed",
                                "value": 12.5,
                                "unit": "m/s",
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            processed_data_markdown.write_text(
                "# Processed Data\n\n## Results\n- wave_speed: 11.8 m/s\n",
                encoding="utf-8",
            )

            completed = run_cli(
                "--handout-sections-markdown",
                str(handout_sections_markdown),
                "--processed-data-json",
                str(processed_data_json),
                "--processed-data-markdown",
                str(processed_data_markdown),
                "--output-json",
                str(output_json),
                "--output-markdown",
                str(output_markdown),
                "--output-unresolved",
                str(output_unresolved),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertTrue(payload["unresolved"])
            self.assertIn("conflict", output_unresolved.read_text(encoding="utf-8").lower())

    def test_cli_records_missing_required_result_family_from_run_plan(self) -> None:
        self.assertTrue(SCRIPT_PATH.exists(), f"missing script: {SCRIPT_PATH}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            handout_sections_markdown = tmp / "sections.md"
            processed_data_json = tmp / "processed_data.json"
            run_plan = tmp / "run_plan.md"
            output_json = tmp / "results_interpretation.json"
            output_markdown = tmp / "results_interpretation.md"
            output_unresolved = tmp / "results_interpretation_unresolved.md"

            write_handout_markdown(handout_sections_markdown)
            processed_data_json.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "name": "wave_speed",
                                "label": "wave speed",
                                "value": 12.5,
                                "unit": "m/s",
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            run_plan.write_text(
                "## course-lab-results-interpretation\n- Required result families: wave_speed, damping_ratio\n",
                encoding="utf-8",
            )

            completed = run_cli(
                "--handout-sections-markdown",
                str(handout_sections_markdown),
                "--processed-data-json",
                str(processed_data_json),
                "--run-plan",
                str(run_plan),
                "--output-json",
                str(output_json),
                "--output-markdown",
                str(output_markdown),
                "--output-unresolved",
                str(output_unresolved),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertTrue(payload["completeness_checks"])
            self.assertEqual(payload["completeness_checks"][0]["name"], "damping_ratio")
            self.assertEqual(payload["completeness_checks"][0]["status"], "missing")

    def test_cli_does_not_mutate_main_tex(self) -> None:
        self.assertTrue(SCRIPT_PATH.exists(), f"missing script: {SCRIPT_PATH}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            handout_sections_markdown = tmp / "sections.md"
            processed_data_json = tmp / "processed_data.json"
            output_json = tmp / "results_interpretation.json"
            output_markdown = tmp / "results_interpretation.md"
            output_unresolved = tmp / "results_interpretation_unresolved.md"
            main_tex = tmp / "main.tex"

            write_handout_markdown(handout_sections_markdown)
            processed_data_json.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "name": "wave_speed",
                                "label": "wave speed",
                                "value": 12.5,
                                "unit": "m/s",
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            original_tex = "\\section{Results}\n\\NeedsInput{results}\n"
            main_tex.write_text(original_tex, encoding="utf-8")

            completed = run_cli(
                "--handout-sections-markdown",
                str(handout_sections_markdown),
                "--processed-data-json",
                str(processed_data_json),
                "--output-json",
                str(output_json),
                "--output-markdown",
                str(output_markdown),
                "--output-unresolved",
                str(output_unresolved),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(main_tex.read_text(encoding="utf-8"), original_tex)


if __name__ == "__main__":
    unittest.main()
