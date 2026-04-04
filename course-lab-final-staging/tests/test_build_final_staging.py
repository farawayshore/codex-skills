from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = SKILL_DIR / "scripts"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class BuildFinalStagingTests(unittest.TestCase):
    def prepare_fixture(
        self,
        root: Path,
        *,
        protect_results_section: bool = False,
        include_modeling: bool = False,
        include_appendix_code: bool = False,
    ) -> dict[str, Path]:
        main_tex = root / "main.tex"
        body_scaffold_json = root / "body_scaffold.json"
        procedures_markdown = root / "fixture_experiment_procedures.md"
        processed_data_json = root / "analysis" / "processed_data.json"
        results_interpretation_json = root / "results_interpretation.json"
        discussion_synthesis_json = root / "discussion_synthesis.json"
        plots_manifest = root / "plots" / "plot_manifest.json"
        modeling_result = root / "modeling" / "batch_run_result.json"
        output_summary_json = root / "final_staging_summary.json"
        output_summary_markdown = root / "final_staging_summary.md"
        output_unresolved = root / "final_staging_unresolved.md"
        output_appendix_manifest = root / "appendix_code_manifest.json"
        model_code = root / "modeling" / "model.wl"
        processing_code = root / "analysis" / "process_data.py"

        results_body = (
            "Measured values are already finalized and should stay untouched.\n"
            if protect_results_section
            else "\\NeedsInput{Draft the results section after processed data, interpretation, and discussion are stable.}\n"
        )

        write_text(
            main_tex,
            textwrap.dedent(
                rf"""
                \section{{Experimental Process}}
                \NeedsInput{{Draft the process and data-processing procedure.}}

                \section{{Results}}
                {results_body}

                \section{{Experiment Discussion}}
                \NeedsInput{{Draft the discussion after the synthesized discussion artifacts are stable.}}

                \section{{Appendix}}
                \NeedsInput{{Add code artifacts if this experiment used scripts, notebooks, or simulations.}}
                """
            ).strip()
            + "\n",
        )

        write_json(
            body_scaffold_json,
            {
                "scaffold_sections": [
                    {"heading": "Experimental Process"},
                    {"heading": "Results"},
                    {"heading": "Experiment Discussion"},
                    {"heading": "Appendix"},
                ]
            },
        )

        write_text(
            procedures_markdown,
            textwrap.dedent(
                """
                # Procedures

                - P01: Measure repeated frequencies for each mode and group them by case.
                - P02: Compute averaged direct quantities and the handout-demanded indirect quantities.
                - P03: Propagate uncertainty from resolution and repeatability into the final reported values.
                """
            ).strip()
            + "\n",
        )

        write_json(
            processed_data_json,
            {
                "processing_procedure": [
                    "Grouped repeated measurements by mode and averaged each case before deriving report quantities."
                ],
                "uncertainty_procedure": [
                    "Combined instrument resolution and repeatability, then propagated those terms into the indirect results."
                ],
                "cases": [
                    {
                        "case_id": "case-a",
                        "title": "Case A",
                        "direct_results": [
                            {
                                "name": "frequency",
                                "label": "Frequency",
                                "value": 10.2,
                                "unit": "Hz",
                                "uncertainty": "0.1 Hz",
                            }
                        ],
                        "indirect_results": [
                            {
                                "name": "wave_speed",
                                "label": "Wave Speed",
                                "value": 20.4,
                                "unit": "m/s",
                                "uncertainty": "0.5 m/s",
                            }
                        ],
                    },
                    {
                        "case_id": "case-b",
                        "title": "Case B",
                        "direct_results": [
                            {
                                "name": "frequency",
                                "label": "Frequency",
                                "value": 11.1,
                                "unit": "Hz",
                                "uncertainty": "0.1 Hz",
                            }
                        ],
                        "indirect_results": [
                            {
                                "name": "wave_speed",
                                "label": "Wave Speed",
                                "value": 22.3,
                                "unit": "m/s",
                                "uncertainty": "0.6 m/s",
                            }
                        ],
                    },
                ],
            },
        )

        write_json(
            results_interpretation_json,
            {
                "interpretation_items": [
                    {
                        "name": "wave_speed",
                        "summary": "Wave-speed agreement stays within the expected band for both cases.",
                    }
                ],
                "comparison_records": [
                    {
                        "lane": "theory_reference_vs_data",
                        "name": "wave_speed",
                        "status": "compared",
                    }
                ],
                "unresolved": [],
            },
        )

        write_json(
            discussion_synthesis_json,
            {
                "overall_confidence": "medium",
                "discussion_blocks": [
                    {
                        "block_id": "wave-speed-interpretation",
                        "title": "Wave speed interpretation",
                        "polished_markdown": "Wave-speed agreement likely indicates that the main measurement procedure stayed under control.",
                        "support_strength": "medium",
                        "block_type": "physical-interpretation",
                    }
                ],
                "unresolved": [],
            },
        )

        write_json(
            plots_manifest,
            {
                "plots": [
                    {"plot_id": "wave-speed-plot", "related_results": ["wave_speed"]},
                ]
            },
        )

        if include_modeling:
            write_json(
                modeling_result,
                {
                    "outputs": [
                        {
                            "name": "wave_speed",
                            "value": 20.0,
                            "unit": "m/s",
                            "label": "Modeled wave speed",
                        }
                    ]
                },
            )

        if include_appendix_code:
            write_text(model_code, "(* model code fixture *)\n")
            write_text(processing_code, "print('process data fixture')\n")

        return {
            "main_tex": main_tex,
            "body_scaffold_json": body_scaffold_json,
            "procedures_markdown": procedures_markdown,
            "processed_data_json": processed_data_json,
            "results_interpretation_json": results_interpretation_json,
            "discussion_synthesis_json": discussion_synthesis_json,
            "plots_manifest": plots_manifest,
            "modeling_result": modeling_result,
            "output_summary_json": output_summary_json,
            "output_summary_markdown": output_summary_markdown,
            "output_unresolved": output_unresolved,
            "output_appendix_manifest": output_appendix_manifest,
            "model_code": model_code,
            "processing_code": processing_code,
        }

    def build_command(
        self,
        fixture: dict[str, Path],
        *,
        include_modeling: bool = False,
        include_appendix_code: bool = False,
    ) -> list[str]:
        command = [
            sys.executable,
            str(SCRIPT_DIR / "build_final_staging.py"),
            "--main-tex",
            str(fixture["main_tex"]),
            "--body-scaffold-json",
            str(fixture["body_scaffold_json"]),
            "--procedures-markdown",
            str(fixture["procedures_markdown"]),
            "--processed-data-json",
            str(fixture["processed_data_json"]),
            "--results-interpretation-json",
            str(fixture["results_interpretation_json"]),
            "--discussion-synthesis-json",
            str(fixture["discussion_synthesis_json"]),
            "--plots-manifest",
            str(fixture["plots_manifest"]),
            "--output-summary-json",
            str(fixture["output_summary_json"]),
            "--output-summary-markdown",
            str(fixture["output_summary_markdown"]),
            "--output-unresolved",
            str(fixture["output_unresolved"]),
            "--output-appendix-manifest",
            str(fixture["output_appendix_manifest"]),
        ]

        if include_modeling:
            command.extend(["--modeling-result", str(fixture["modeling_result"])])

        if include_appendix_code:
            command.extend(
                [
                    "--appendix-code",
                    str(fixture["model_code"]),
                    "--appendix-code",
                    str(fixture["processing_code"]),
                ]
            )

        return command

    def run_builder(
        self,
        fixture: dict[str, Path],
        *,
        include_modeling: bool = False,
        include_appendix_code: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            self.build_command(
                fixture,
                include_modeling=include_modeling,
                include_appendix_code=include_appendix_code,
            ),
            capture_output=True,
            text=True,
        )

    def test_missing_main_tex_fails_with_clear_contract_message(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name))
            fixture["main_tex"].unlink()

            completed = self.run_builder(fixture)
            combined = f"{completed.stdout}\n{completed.stderr}".lower()

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("main-tex", combined)
            self.assertIn("required", combined)

    def test_missing_processed_data_json_fails_with_clear_contract_message(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name))
            fixture["processed_data_json"].unlink()

            completed = self.run_builder(fixture)
            combined = f"{completed.stdout}\n{completed.stderr}".lower()

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("processed-data", combined)
            self.assertIn("required", combined)

    def test_missing_results_interpretation_json_fails_with_clear_contract_message(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name))
            fixture["results_interpretation_json"].unlink()

            completed = self.run_builder(fixture)
            combined = f"{completed.stdout}\n{completed.stderr}".lower()

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("results-interpretation", combined)
            self.assertIn("required", combined)

    def test_missing_discussion_synthesis_json_fails_with_clear_contract_message(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name))
            fixture["discussion_synthesis_json"].unlink()

            completed = self.run_builder(fixture)
            combined = f"{completed.stdout}\n{completed.stderr}".lower()

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("discussion-synthesis", combined)
            self.assertIn("required", combined)

    def test_refuses_to_overwrite_results_section_without_placeholder_or_owned_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name), protect_results_section=True)

            completed = self.run_builder(fixture)
            combined = f"{completed.stdout}\n{completed.stderr}".lower()

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("results", combined)
            self.assertIn("unsafe", combined)

    def test_success_writes_summary_outputs_and_updates_main_tex(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name))

            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            self.assertTrue(fixture["output_summary_json"].exists())
            self.assertTrue(fixture["output_summary_markdown"].exists())
            self.assertTrue(fixture["output_unresolved"].exists())
            self.assertTrue(fixture["output_appendix_manifest"].exists())

            payload = json.loads(fixture["output_summary_json"].read_text(encoding="utf-8"))
            self.assertIn("written_sections", payload)
            self.assertIn("case_records", payload)
            self.assertIn("appendix_entries", payload)
            self.assertIn("unresolved", payload)
            self.assertIn("length_goal", payload)

    def test_success_writes_processing_uncertainty_and_per_case_results(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name), include_appendix_code=True)

            completed = self.run_builder(fixture, include_appendix_code=True)
            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")

            tex = fixture["main_tex"].read_text(encoding="utf-8")
            self.assertIn("Data-Processing Procedure", tex)
            self.assertIn("Uncertainty Calculation Procedure", tex)
            self.assertIn("Case A", tex)
            self.assertIn("Case B", tex)
            self.assertIn("Wave Speed", tex)
            self.assertIn("Wave-speed agreement likely indicates", tex)
            self.assertIn("process_data.py", tex)

    def test_success_includes_modeling_results_and_appendix_manifest_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(
                Path(temp_name),
                include_modeling=True,
                include_appendix_code=True,
            )

            completed = self.run_builder(
                fixture,
                include_modeling=True,
                include_appendix_code=True,
            )
            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")

            tex = fixture["main_tex"].read_text(encoding="utf-8")
            self.assertIn("Modeled wave speed", tex)
            manifest = json.loads(fixture["output_appendix_manifest"].read_text(encoding="utf-8"))
            labels = json.dumps(manifest, ensure_ascii=False)
            self.assertIn("model.wl", labels)
            self.assertIn("process_data.py", labels)


if __name__ == "__main__":
    unittest.main()
