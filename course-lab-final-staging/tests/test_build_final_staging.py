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


def indent_block(text: str, spaces: int = 16) -> str:
    block = text.rstrip("\n")
    return textwrap.indent(block, " " * spaces)


def slice_between(text: str, start_marker: str, end_marker: str | None = None) -> str:
    start = text.find(start_marker)
    if start == -1:
        raise AssertionError(f"start marker not found: {start_marker}")
    search_from = start + len(start_marker)
    end = text.find(end_marker, search_from) if end_marker is not None else -1
    return text[start : end if end != -1 else len(text)]


class BuildFinalStagingTests(unittest.TestCase):
    def prepare_fixture(
        self,
        root: Path,
        *,
        protect_results_section: bool = False,
        include_modeling: bool = False,
        include_appendix_code: bool = False,
        include_appendix_data: bool = False,
        include_calculation_details: bool = False,
        comparison_cases: list[dict[str, object]] | None = None,
        process_body: str | None = None,
        results_body: str | None = None,
        discussion_body: str | None = None,
        appendix_body: str | None = None,
    ) -> dict[str, Path]:
        main_tex = root / "main.tex"
        body_scaffold_json = root / "body_scaffold.json"
        procedures_markdown = root / "fixture_experiment_procedures.md"
        processed_data_json = root / "analysis" / "processed_data.json"
        direct_uncertainty_json = root / "analysis" / "uncertainty" / "frequency_uncertainty.json"
        derived_uncertainty_json = root / "analysis" / "uncertainty" / "wave_speed_uncertainty.json"
        results_interpretation_json = root / "results_interpretation.json"
        discussion_synthesis_json = root / "discussion_synthesis.json"
        plots_manifest = root / "plots" / "plot_manifest.json"
        modeling_result = root / "modeling" / "batch_run_result.json"
        references_json = root / "analysis" / "reference_values.json"
        output_summary_json = root / "final_staging_summary.json"
        output_summary_markdown = root / "final_staging_summary.md"
        output_unresolved = root / "final_staging_unresolved.md"
        output_appendix_manifest = root / "appendix_code_manifest.json"
        calculation_details_manifest = root / "analysis" / "calculation_details_manifest.json"
        calculation_details_tex = root / "analysis" / "calculation_details" / "case-a-details.tex"
        model_code = root / "modeling" / "model.wl"
        processing_code = root / "analysis" / "process_data.py"
        appendix_data_csv = root / "analysis" / "appendix_data" / "uncited_measurements.csv"
        cited_data_csv = root / "analysis" / "appendix_data" / "cited_measurements.csv"

        process_body = process_body or "\\NeedsInput{Draft the process and data-processing procedure.}\n"
        results_body = results_body or (
            "Measured values are already finalized and should stay untouched.\n"
            if protect_results_section
            else "\\NeedsInput{Draft the results section after processed data, interpretation, and discussion are stable.}\n"
        )
        discussion_body = discussion_body or "\\NeedsInput{Draft the discussion after the synthesized discussion artifacts are stable.}\n"
        appendix_body = appendix_body or "\\NeedsInput{Add code artifacts if this experiment used scripts, notebooks, or simulations.}\n"

        write_text(
            main_tex,
            textwrap.dedent(
                rf"""
                \section{{Experimental Process}}
{indent_block(process_body)}

                \section{{Results}}
{indent_block(results_body)}

                \section{{Experiment Discussion}}
{indent_block(discussion_body)}

                \section{{Appendix}}
{indent_block(appendix_body)}
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
            direct_uncertainty_json,
            {
                "input": str(root / "analysis" / "direct_measurements" / "frequency.csv"),
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
            derived_uncertainty_json,
            {
                "spec": str(root / "analysis" / "specs" / "wave_speed_spec.json"),
                "coverage_k": 2.0,
                "inputs": {
                    "lambda": {
                        "value": 2.0,
                        "std_uncertainty": 0.2,
                        "unit": "m",
                        "label": "lambda",
                        "symbol": "lambda",
                        "canonical_key": "lambda",
                        "raw_label": "lambda/m",
                        "source": "analysis/uncertainty/wavelength_uncertainty.json:lambda/m",
                        "expanded_uncertainty": 0.4,
                    },
                    "f": {
                        "value": 10.2,
                        "std_uncertainty": 0.1,
                        "unit": "Hz",
                        "label": "f",
                        "symbol": "f",
                        "canonical_key": "f",
                        "raw_label": "frequency/Hz",
                        "source": f"{direct_uncertainty_json}:frequency/Hz",
                        "expanded_uncertainty": 0.2,
                    },
                },
                "derived": {
                    "wave_speed": {
                        "label": "wave speed",
                        "expression": "lambda * f",
                        "unit": "m/s",
                        "value": 20.4,
                        "std_uncertainty": 0.25,
                        "expanded_uncertainty": 0.5,
                        "gradient": {
                            "lambda": 10.2,
                            "f": 2.0,
                        },
                        "partials": {
                            "lambda": 10.2,
                            "f": 2.0,
                        },
                    }
                },
            },
        )

        write_json(
            references_json,
            {
                "references": [
                    {
                        "name": "wave_speed",
                        "label": "Published standing-wave reference",
                        "value": 20.1,
                        "unit": "m/s",
                        "comparison_basis": "literature_report",
                        "lane": "literature_report_vs_data",
                        "source": "https://arxiv.org/abs/2401.01234",
                        "source_title": "arXiv standing-wave comparison study",
                        "summary": "The published standing-wave study reports a wave-speed benchmark close to the measured case.",
                    },
                    {
                        "name": "wave_speed",
                        "label": "Handout wave-speed example",
                        "value": 19.8,
                        "unit": "m/s",
                        "comparison_basis": "handout_standard",
                        "source": "notes/sections.md:42",
                    },
                ]
            },
        )

        processed_data_payload: dict[str, object] = {
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
                            "sources": [
                                f"{direct_uncertainty_json}:frequency/Hz",
                            ],
                        }
                    ],
                    "indirect_results": [
                        {
                            "name": "wave_speed",
                            "label": "Wave Speed",
                            "value": 20.4,
                            "unit": "m/s",
                            "uncertainty": "0.5 m/s",
                            "sources": [
                                f"{derived_uncertainty_json}:wave_speed",
                            ],
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
                            "sources": [
                                f"{direct_uncertainty_json}:frequency/Hz",
                            ],
                        }
                    ],
                    "indirect_results": [
                        {
                            "name": "wave_speed",
                            "label": "Wave Speed",
                            "value": 22.3,
                            "unit": "m/s",
                            "uncertainty": "0.6 m/s",
                            "sources": [
                                f"{derived_uncertainty_json}:wave_speed",
                            ],
                        }
                    ],
                },
            ],
        }

        write_json(processed_data_json, processed_data_payload)

        results_interpretation_payload: dict[str, object] = {
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
        }
        discussion_payload: dict[str, object] = {
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
        }

        if comparison_cases is not None:
            results_interpretation_payload["comparison_cases"] = [dict(case) for case in comparison_cases]

        write_json(results_interpretation_json, results_interpretation_payload)
        write_json(discussion_synthesis_json, discussion_payload)

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

        if include_appendix_data:
            write_text(appendix_data_csv, "radius_cm,k_value\n1.2,0.91\n3.4,0.95\n")
            write_text(cited_data_csv, "radius_cm,k_value\n0.8,0.88\n2.9,0.93\n")

        if include_calculation_details:
            write_text(
                calculation_details_tex,
                textwrap.dedent(
                    r"""
                    \subsubsection{Case A Calculation Details}

                    \paragraph{Derived Quantity Chain}

                    Key: \texttt{wave\_speed}
                    """
                ).strip()
                + "\n",
            )
            write_json(
                calculation_details_manifest,
                {
                    "entries": [
                        {
                            "title": "Case A Calculation Details",
                            "path": str(calculation_details_tex),
                            "order": 10,
                            "kind": "calculation_details",
                            "exists": True,
                            "slug": "case-a-details",
                        }
                    ]
                },
            )

        return {
            "main_tex": main_tex,
            "body_scaffold_json": body_scaffold_json,
            "procedures_markdown": procedures_markdown,
            "processed_data_json": processed_data_json,
            "results_interpretation_json": results_interpretation_json,
            "discussion_synthesis_json": discussion_synthesis_json,
            "plots_manifest": plots_manifest,
            "modeling_result": modeling_result,
            "references_json": references_json,
            "output_summary_json": output_summary_json,
            "output_summary_markdown": output_summary_markdown,
            "output_unresolved": output_unresolved,
            "output_appendix_manifest": output_appendix_manifest,
            "calculation_details_manifest": calculation_details_manifest,
            "calculation_details_tex": calculation_details_tex,
            "model_code": model_code,
            "processing_code": processing_code,
            "appendix_data_csv": appendix_data_csv,
            "cited_data_csv": cited_data_csv,
        }

    def add_symbolic_handoff_fixture(
        self,
        fixture: dict[str, Path],
        *,
        include_processed_record: bool = True,
    ) -> None:
        root = fixture["main_tex"].parent
        symbolic_handout = root / "decoded_handout.md"
        symbolic_code = root / "analysis" / "symbolic_route.py"
        symbolic_processed = root / "analysis" / "symbolic_wave_speed.json"
        symbolic_output_dir = root / "analysis" / "symbolic_expressing" / "tmp"

        write_text(
            symbolic_handout,
            "The handout route for Wave Speed uses wave_speed = wavelength * frequency.\n",
        )
        write_text(symbolic_code, "wave_speed = wavelength * frequency\n")

        derived: dict[str, object] = {}
        if include_processed_record:
            derived["wave_speed"] = {
                "label": "Wave Speed",
                "expression": "wavelength * frequency",
                "unit": "m/s",
                "value": 20.4,
            }
        write_json(
            symbolic_processed,
            {
                "derived": derived,
            },
        )

        fixture["symbolic_handout"] = symbolic_handout
        fixture["symbolic_code"] = symbolic_code
        fixture["symbolic_processed"] = symbolic_processed
        fixture["symbolic_output_dir"] = symbolic_output_dir

    def remove_indirect_source_details(self, fixture: dict[str, Path]) -> None:
        payload = json.loads(fixture["processed_data_json"].read_text(encoding="utf-8"))
        for case in payload.get("cases", []):
            if not isinstance(case, dict):
                continue
            for item in case.get("indirect_results", []):
                if isinstance(item, dict):
                    item["sources"] = []
        write_json(fixture["processed_data_json"], payload)

    def prepare_mechanics_synonym_fixture(self, root: Path) -> dict[str, Path]:
        fixture = self.prepare_fixture(root)
        write_text(
            fixture["main_tex"],
            textwrap.dedent(
                r"""
                \section{Introduction}
                Intro text.

                \section{LX1: One-Dimensional Standing Waves}
                \subsection{Experimental Procedure and Observations}
                \NeedsInput{Draft LX1 process.}

                \subsection{Results and Analysis}
                \NeedsInput{Draft LX1 results.}

                \subsection{Local Discussion}
                \NeedsInput{Draft LX1 local discussion.}

                \section{LX2: Circular Thin-Plate Standing Waves}
                \subsection{Experimental Procedure and Observations}
                Existing LX2 process prose should remain untouched.

                \subsection{Results and Analysis}
                Existing LX2 results prose should remain untouched.

                \subsection{Local Discussion}
                Existing LX2 local discussion prose should remain untouched.

                \section{Code}
                \NeedsInput{Add code artifacts if this experiment used scripts, notebooks, or simulations.}
                """
            ).strip()
            + "\n",
        )
        write_json(
            fixture["body_scaffold_json"],
            {
                "title": "Combined Mechanics Design Experiments",
                "staging_mode": "summary_only_existing_draft",
                "scaffold_sections": [
                    {"key": "lx1", "heading": "LX1: One-Dimensional Standing Waves", "present_in_template": True},
                    {"key": "lx2", "heading": "LX2: Circular Thin-Plate Standing Waves", "present_in_template": True},
                    {"key": "appendix_code", "heading": "Code", "present_in_template": True},
                ],
            },
        )
        return fixture

    def prepare_same_block_discussion_fixture(self, root: Path) -> dict[str, Path]:
        fixture = self.prepare_fixture(root)
        write_text(
            fixture["main_tex"],
            textwrap.dedent(
                r"""
                \section{Introduction}
                Intro text.

                \section{LX1: One-Dimensional Standing Waves}
                \subsection{Experimental Procedure and Observations}
                \NeedsInput{Draft LX1 process.}

                \subsection{Results and Analysis}
                \NeedsInput{Draft LX1 results.}

                \subsection{Local Discussion}
                \NeedsInput{Draft LX1 local discussion.}

                \section{LX2: Circular Thin-Plate Standing Waves}
                \subsection{Experimental Procedure and Observations}
                Existing LX2 process prose should remain untouched.

                \subsection{Results and Analysis}
                Existing LX2 results prose should remain untouched.

                \subsection{Local Discussion}
                Existing LX2 local discussion prose should remain untouched.

                \section{Discussion}
                Global discussion prose should remain untouched.

                This section already contains authored synthesis and must not be replaced
                when a local discussion subsection exists inside the active experiment block.

                \section{Code}
                \NeedsInput{Add code artifacts if this experiment used scripts, notebooks, or simulations.}
                """
            ).strip()
            + "\n",
        )
        write_json(
            fixture["body_scaffold_json"],
            {
                "title": "Combined Mechanics Design Experiments",
                "staging_mode": "summary_only_existing_draft",
                "scaffold_sections": [
                    {"key": "lx1", "heading": "LX1: One-Dimensional Standing Waves", "present_in_template": True},
                    {"key": "lx2", "heading": "LX2: Circular Thin-Plate Standing Waves", "present_in_template": True},
                    {"key": "discussion", "heading": "Discussion", "present_in_template": True},
                    {"key": "appendix_code", "heading": "Code", "present_in_template": True},
                ],
            },
        )
        return fixture

    def prepare_ambiguous_synonym_fixture(self, root: Path) -> dict[str, Path]:
        fixture = self.prepare_fixture(root)
        write_text(
            fixture["main_tex"],
            textwrap.dedent(
                r"""
                \section{Experimental Process}
                \NeedsInput{Draft process.}

                \section{Wrapper}
                \subsection{Results and Analysis}
                \NeedsInput{Draft results A.}

                \subsection{Results and Analysis}
                \NeedsInput{Draft results B.}

                \section{Discussion}
                \NeedsInput{Draft discussion.}

                \section{Code}
                \NeedsInput{Add code artifacts if this experiment used scripts, notebooks, or simulations.}
                """
            ).strip()
            + "\n",
        )
        return fixture

    def build_command(
        self,
        fixture: dict[str, Path],
        *,
        include_modeling: bool = False,
        include_appendix_code: bool = False,
        include_appendix_data: bool = False,
        include_calculation_details: bool = False,
        skip_main_tex_mutation: bool = False,
        extra_args: list[str] | None = None,
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

        if include_appendix_data:
            command.extend(
                [
                    "--appendix-data",
                    str(fixture["appendix_data_csv"]),
                    "--appendix-data",
                    str(fixture["cited_data_csv"]),
                ]
            )

        if include_calculation_details:
            command.extend(
                [
                    "--calculation-details-manifest",
                    str(fixture["calculation_details_manifest"]),
                ]
            )

        if skip_main_tex_mutation:
            command.append("--skip-main-tex-mutation")

        if extra_args:
            command.extend(extra_args)

        return command

    def run_builder(
        self,
        fixture: dict[str, Path],
        *,
        include_modeling: bool = False,
        include_appendix_code: bool = False,
        include_appendix_data: bool = False,
        include_calculation_details: bool = False,
        skip_main_tex_mutation: bool = False,
        extra_args: list[str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            self.build_command(
                fixture,
                include_modeling=include_modeling,
                include_appendix_code=include_appendix_code,
                include_appendix_data=include_appendix_data,
                include_calculation_details=include_calculation_details,
                skip_main_tex_mutation=skip_main_tex_mutation,
                extra_args=extra_args,
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

    def test_short_explicit_draft_guidance_is_overwrite_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(
                Path(temp_name),
                results_body="This draft guide is provisional and will be expanded later by final staging.\n",
            )

            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            tex = fixture["main_tex"].read_text(encoding="utf-8")
            self.assertIn("% course-lab-final-staging:results:begin", tex)

    def test_substantive_multi_paragraph_prose_remains_protected_even_if_it_mentions_draft(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(
                Path(temp_name),
                results_body=(
                    "This draft already contains a real analytical narrative with multiple claims about the data. "
                    "It should remain protected until someone explicitly hands the section over.\n\n"
                    "The second paragraph confirms that this is no longer a lightweight guide sentence, even "
                    "though it still contains the word draft.\n"
                ),
            )

            completed = self.run_builder(fixture)
            combined = f"{completed.stdout}\n{completed.stderr}".lower()

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("results", combined)
            self.assertIn("unsafe", combined)

    def test_allow_overwrite_marker_makes_body_safe_to_replace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(
                Path(temp_name),
                results_body=(
                    "% course-lab-final-staging:allow-overwrite\n"
                    "Temporary draft notes prepared by a previous skill.\n"
                ),
            )

            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            tex = fixture["main_tex"].read_text(encoding="utf-8")
            self.assertIn("% course-lab-final-staging:results:begin", tex)

    def test_skip_main_tex_mutation_allows_summary_only_pass_on_existing_draft(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name), protect_results_section=True)
            original_tex = fixture["main_tex"].read_text(encoding="utf-8")

            completed = self.run_builder(fixture, skip_main_tex_mutation=True)

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            self.assertEqual(fixture["main_tex"].read_text(encoding="utf-8"), original_tex)

            payload = json.loads(fixture["output_summary_json"].read_text(encoding="utf-8"))
            self.assertEqual(payload["written_sections"], [])
            self.assertIn("main.tex mutation was skipped", "\n".join(payload["unresolved"]).lower())

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
            self.assertIn(r"process\_data.py", tex)

    def test_uncertainty_section_renders_definitions_and_indirect_formulae(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name))

            completed = self.run_builder(fixture)
            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")

            tex = fixture["main_tex"].read_text(encoding="utf-8")
            self.assertIn(r"u_a=\frac{s}{\sqrt{n}}", tex)
            self.assertIn(r"u_b=\frac{\Delta}{\sqrt{3}}", tex)
            self.assertIn(r"u_c=\sqrt{u_a^2+u_b^2}", tex)
            self.assertIn(r"u_c(y)=\sqrt{\sum_i", tex)
            self.assertIn(r"Quantity & $n$ & $s$ & $u_a$ & $u_b$ & $u_c$ & $U$", tex)
            self.assertIn(r"Frequency & 3 & $0.173205\,\text{Hz}$", tex)
            self.assertIn("Formula:", tex)
            self.assertIn(r"\texttt{wave\_speed = lambda * f}", tex)
            self.assertIn(r"Symbol & Value & $u(x)$", tex)
            self.assertIn(r"$\lambda$ & $2\,\text{m}$ & $0.2\,\text{m}$", tex)
            self.assertIn(r"$f$ & $10.2\,\text{Hz}$ & $0.1\,\text{Hz}$", tex)
            self.assertIn(r"u_c(\text{wave\_speed})=", tex)
            self.assertIn(r"\begin{aligned}", tex)
            self.assertIn(r"\Bigl[", tex)
            self.assertIn(r"\left(f u(\lambda)\right)^2 + \left(\lambda u(f)\right)^2", tex)
            self.assertIn(r"\left(10.2\times0.2\right)^2 + \left(2\times0.1\right)^2", tex)
            self.assertIn(r"&= 0.25\,\text{m/s}", tex)
            self.assertIn(r"U=2u_c=0.5\,\text{m/s}", tex)

    def test_symbolic_handoff_inlines_returned_tex_when_indirect_result_lacks_procedure_detail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name))
            self.add_symbolic_handoff_fixture(fixture)
            self.remove_indirect_source_details(fixture)

            completed = self.run_builder(
                fixture,
                extra_args=[
                    "--symbolic-handout",
                    str(fixture["symbolic_handout"]),
                    "--symbolic-calculation-code",
                    str(fixture["symbolic_code"]),
                    "--symbolic-processed-result",
                    str(fixture["symbolic_processed"]),
                    "--symbolic-result-key",
                    "wave_speed",
                    "--symbolic-output-dir",
                    str(fixture["symbolic_output_dir"]),
                ],
            )

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            response_path = fixture["symbolic_output_dir"] / "wave_speed_symbolic_response.json"
            self.assertTrue(response_path.exists())
            response = json.loads(response_path.read_text(encoding="utf-8"))
            tex_path = Path(response["tex_path"])
            self.assertTrue(tex_path.exists())

            tex = fixture["main_tex"].read_text(encoding="utf-8")
            self.assertIn(r"\paragraph{Symbolic Calculation Route}", tex)
            self.assertIn(r"\paragraph{Calculation route for Wave Speed}", tex)
            self.assertIn(r"calculation code evaluates wave\_speed", tex)
            self.assertIn(r"wavelength * frequency", tex)

    def test_symbolic_handoff_is_optional_and_reports_missing_explicit_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name))

            completed = self.run_builder(
                fixture,
                extra_args=[
                    "--symbolic-result-key",
                    "wave_speed",
                    "--symbolic-output-dir",
                    str(Path(temp_name) / "analysis" / "symbolic_expressing" / "tmp"),
                ],
            )

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            unresolved = fixture["output_unresolved"].read_text(encoding="utf-8")
            self.assertIn("symbolic handout", unresolved.lower())
            self.assertIn("symbolic calculation code", unresolved.lower())
            self.assertIn("symbolic processed result", unresolved.lower())

            tex = fixture["main_tex"].read_text(encoding="utf-8")
            self.assertNotIn(r"\paragraph{Calculation route for Wave Speed}", tex)

    def test_symbolic_handoff_reports_helper_unresolved_when_result_cannot_be_traced(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name))
            self.add_symbolic_handoff_fixture(fixture, include_processed_record=False)
            self.remove_indirect_source_details(fixture)

            completed = self.run_builder(
                fixture,
                extra_args=[
                    "--symbolic-handout",
                    str(fixture["symbolic_handout"]),
                    "--symbolic-calculation-code",
                    str(fixture["symbolic_code"]),
                    "--symbolic-processed-result",
                    str(fixture["symbolic_processed"]),
                    "--symbolic-result-key",
                    "wave_speed",
                    "--symbolic-output-dir",
                    str(fixture["symbolic_output_dir"]),
                ],
            )

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            unresolved = fixture["output_unresolved"].read_text(encoding="utf-8")
            self.assertIn("Processed result key was not found: wave_speed", unresolved)
            tex = fixture["main_tex"].read_text(encoding="utf-8")
            self.assertIn(r"\NeedsInput{Processed result key was not found: wave\_speed.}", tex)

    def test_comparison_cases_with_five_entries_render_compact_comparison_table(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(
                Path(temp_name),
                comparison_cases=[
                    {
                        "case_id": "case-1",
                        "title": "Case 1",
                        "observed_summary": "Observed ring-dominated pattern.",
                        "comparison_summary": "Simulation predicts a ring-dominated mode.",
                        "agreement_summary": "The outer nodal structure agrees well.",
                        "caveats": [],
                    },
                    {
                        "case_id": "case-2",
                        "title": "Case 2",
                        "observed_summary": "Observed a slightly shifted resonance peak.",
                        "comparison_summary": "Theory predicts a mild resonance shift.",
                        "agreement_summary": "The resonance displacement remains within tolerance.",
                        "caveats": [],
                    },
                    {
                        "case_id": "case-3",
                        "title": "Case 3",
                        "observed_summary": "Observed a split-node pattern.",
                        "comparison_summary": "Simulation reproduces the split-node family.",
                        "agreement_summary": "The split-node topology is consistent.",
                        "caveats": [],
                    },
                    {
                        "case_id": "case-4",
                        "title": "Case 4",
                        "observed_summary": "Observed an asymmetric amplitude profile.",
                        "comparison_summary": "Theory anticipates a weak asymmetry.",
                        "agreement_summary": "The asymmetry trend matches the model.",
                        "caveats": [],
                    },
                    {
                        "case_id": "case-5",
                        "title": "Case 5",
                        "observed_summary": "Observed a high-Q peak cluster.",
                        "comparison_summary": "Simulation suggests clustered high-Q peaks.",
                        "agreement_summary": "The clustering behavior aligns well.",
                        "caveats": [],
                    },
                ],
            )

            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            tex = fixture["main_tex"].read_text(encoding="utf-8")
            self.assertIn(r"\subsection{Comparison}", tex)
            self.assertIn(r"\paragraph{Compact Case Comparison}", tex)
            self.assertIn(r"\begin{tabular}", tex)
            self.assertNotIn(r"\paragraph{Case 1}", tex)
            self.assertNotIn(r"\paragraph{Case 5}", tex)
            case_a_block = slice_between(tex, r"\subsection{Case A}", r"\subsection{Case B}")
            case_b_block = slice_between(tex, r"\subsection{Case B}", r"\section{Experiment Discussion}")
            self.assertIn(r"\paragraph{Direct Results}", case_a_block)
            self.assertIn(r"\paragraph{Indirect Results}", case_a_block)
            self.assertIn("Frequency: 10.2 Hz", case_a_block)
            self.assertIn("Wave Speed: 20.4 m/s", case_a_block)
            self.assertIn(r"\paragraph{Direct Results}", case_b_block)
            self.assertIn(r"\paragraph{Indirect Results}", case_b_block)
            self.assertIn("Frequency: 11.1 Hz", case_b_block)
            self.assertIn("Wave Speed: 22.3 m/s", case_b_block)
            for title, observed, comparison, agreement in (
                (
                    "Case 1",
                    "Observed ring-dominated pattern.",
                    "Simulation predicts a ring-dominated mode.",
                    "The outer nodal structure agrees well.",
                ),
                (
                    "Case 2",
                    "Observed a slightly shifted resonance peak.",
                    "Theory predicts a mild resonance shift.",
                    "The resonance displacement remains within tolerance.",
                ),
                (
                    "Case 3",
                    "Observed a split-node pattern.",
                    "Simulation reproduces the split-node family.",
                    "The split-node topology is consistent.",
                ),
                (
                    "Case 4",
                    "Observed an asymmetric amplitude profile.",
                    "Theory anticipates a weak asymmetry.",
                    "The asymmetry trend matches the model.",
                ),
                (
                    "Case 5",
                    "Observed a high-Q peak cluster.",
                    "Simulation suggests clustered high-Q peaks.",
                    "The clustering behavior aligns well.",
                ),
            ):
                self.assertIn(title, tex)
                self.assertIn(observed, tex)
                self.assertIn(comparison, tex)
                self.assertIn(agreement, tex)

    def test_comparison_cases_with_two_entries_render_exactly_two_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(
                Path(temp_name),
                comparison_cases=[
                    {
                        "case_id": "case-1",
                        "title": "Case 1",
                        "observed_summary": "Observed a single dominant lobe.",
                        "comparison_summary": "Simulation predicts one dominant lobe.",
                        "agreement_summary": "The dominant lobe matches the reference solution.",
                        "caveats": [],
                    },
                    {
                        "case_id": "case-2",
                        "title": "Case 2",
                        "observed_summary": "Observed a broader secondary lobe.",
                        "comparison_summary": "Theory predicts a broader secondary lobe.",
                        "agreement_summary": "The secondary lobe width is consistent.",
                        "caveats": [],
                    },
                ],
            )

            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            tex = fixture["main_tex"].read_text(encoding="utf-8")
            self.assertIn(r"\subsection{Comparison}", tex)
            self.assertEqual(tex.count(r"\paragraph{Case "), 2)
            case_a_block = slice_between(tex, r"\subsection{Case A}", r"\subsection{Case B}")
            case_b_block = slice_between(tex, r"\subsection{Case B}", r"\section{Experiment Discussion}")
            self.assertIn(r"\paragraph{Direct Results}", case_a_block)
            self.assertIn(r"\paragraph{Indirect Results}", case_a_block)
            self.assertIn("Frequency: 10.2 Hz", case_a_block)
            self.assertIn("Wave Speed: 20.4 m/s", case_a_block)
            self.assertIn(r"\paragraph{Direct Results}", case_b_block)
            self.assertIn(r"\paragraph{Indirect Results}", case_b_block)
            self.assertIn("Frequency: 11.1 Hz", case_b_block)
            self.assertIn("Wave Speed: 22.3 m/s", case_b_block)
            self.assertIn("Case 1", tex)
            self.assertIn("Case 2", tex)
            case_1_block = slice_between(tex, r"\paragraph{Case 1}", r"\paragraph{Case 2}")
            case_2_block = slice_between(tex, r"\paragraph{Case 2}", r"\section{Experiment Discussion}")
            self.assertIn("Observed a single dominant lobe.", case_1_block)
            self.assertIn("Simulation predicts one dominant lobe.", case_1_block)
            self.assertIn("The dominant lobe matches the reference solution.", case_1_block)
            self.assertIn("Observed a broader secondary lobe.", case_2_block)
            self.assertIn("Theory predicts a broader secondary lobe.", case_2_block)
            self.assertIn("The secondary lobe width is consistent.", case_2_block)
            self.assertNotIn("Case 3", tex)
            self.assertNotIn(r"\paragraph{Compact Case Comparison}", tex)

    def test_results_cases_render_directly_under_results_without_wrapper_subsection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name))

            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            tex = fixture["main_tex"].read_text(encoding="utf-8")
            results_block = slice_between(tex, r"\section{Results}", r"\section{Experiment Discussion}")
            self.assertNotIn(r"\subsection{Direct And Indirect Results}", results_block)
            self.assertIn("% course-lab-final-staging:results:begin", results_block)
            after_marker = results_block.split("% course-lab-final-staging:results:begin", 1)[1].lstrip()
            self.assertTrue(after_marker.startswith(r"\subsection{Case A}"), msg=after_marker[:200])

    def test_appendix_data_files_render_as_data_records_without_csv_label(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(
                Path(temp_name),
                include_appendix_data=True,
                results_body=(
                    "% course-lab-final-staging:allow-overwrite\n"
                    "\\NeedsInput{Draft the results section after processed data, interpretation, and discussion are stable.}\n"
                    "The discussion already references cited_measurements.csv and should not duplicate it in appendix data files.\n"
                ),
            )

            completed = self.run_builder(fixture, include_appendix_data=True)

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            tex = fixture["main_tex"].read_text(encoding="utf-8")
            appendix_block = slice_between(tex, "% course-lab-final-staging:appendix:begin")
            self.assertIn(r"\subsection{Data Files}", appendix_block)
            self.assertIn(r"\paragraph{uncited measurements}", appendix_block)
            self.assertNotIn(r"\paragraph{uncited\_measurements.csv}", appendix_block)
            self.assertIn(r"\begin{tcolorbox}[enhanced,breakable,colback=green!4!white", appendix_block)
            self.assertIn("radius_cm,k_value", appendix_block)
            self.assertIn("1.2,0.91", appendix_block)
            self.assertNotIn(r"\paragraph{cited\_measurements.csv}", appendix_block)

            manifest = json.loads(fixture["output_appendix_manifest"].read_text(encoding="utf-8"))
            labels = [entry.get("label") for entry in manifest["appendix_entries"]]
            roles = {entry.get("label"): entry.get("role") for entry in manifest["appendix_entries"]}
            source_paths = {entry.get("label"): entry.get("source_path") for entry in manifest["appendix_entries"]}
            self.assertIn("uncited measurements", labels)
            self.assertNotIn("uncited_measurements.csv", labels)
            self.assertNotIn("cited_measurements.csv", labels)
            self.assertEqual(roles["uncited measurements"], "data-file")
            self.assertTrue(str(source_paths["uncited measurements"]).endswith("uncited_measurements.csv"))

    def test_aggregate_only_inputs_do_not_invent_fake_comparison_case_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name))

            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            tex = fixture["main_tex"].read_text(encoding="utf-8")
            self.assertIn("Case A", tex)
            self.assertIn("Case B", tex)
            self.assertIn(r"\subsection{Case A}", tex)
            self.assertIn(r"\subsection{Case B}", tex)
            self.assertIn("Frequency: 10.2 Hz", tex)
            self.assertIn("Wave Speed: 20.4 m/s", tex)
            self.assertNotIn(r"\subsection{Comparison}", tex)
            self.assertNotIn(r"\paragraph{Case 1}", tex)
            self.assertNotIn("Case 1", tex)
            self.assertNotIn("Case 2", tex)

    def test_fallback_prefers_primary_comparison_png_over_radial_variant(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            fixture = self.prepare_fixture(root)

            picture_dir = root / "picture-results"
            simulation_dir = root / "lx2_mathematica_simulation"
            write_text(picture_dir / "1.experimental-pattern.jpg", "fixture image\n")
            write_text(simulation_dir / "case-1-f1.8308kHz-m0-n4-summary.txt", "caseId: case-1\nfrequencyHz: 1830.8\nm: 0\nn: 4\n")
            write_text(simulation_dir / "case-1-f1.8308kHz-m0-n4.png", "primary comparison image\n")
            write_text(simulation_dir / "case-1-f1.8308kHz-m0-n4-radial.png", "secondary radial image\n")

            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            tex = fixture["main_tex"].read_text(encoding="utf-8")
            unresolved = fixture["output_unresolved"].read_text(encoding="utf-8")
            summary = json.loads(fixture["output_summary_json"].read_text(encoding="utf-8"))
            self.assertIn(r"\subsection{Comparison}", tex)
            self.assertIn(r"\paragraph{Case 1}", tex)
            self.assertIn("Parsed summary fields: frequencyHz=1830.8, m=0, n=4.", tex)
            self.assertNotIn("Could not uniquely map comparison asset for case-1", unresolved)
            self.assertIn("comparison_cases", summary)
            self.assertEqual(len(summary["comparison_cases"]), 1)
            self.assertTrue(str(summary["comparison_cases"][0]["comparison_asset_path"]).endswith("case-1-f1.8308kHz-m0-n4.png"))
            self.assertFalse(str(summary["comparison_cases"][0]["comparison_asset_path"]).endswith("-radial.png"))

    def test_fallback_prefers_observed_photo_over_measurement_overlay_for_same_case(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            fixture = self.prepare_fixture(root)

            picture_dir = root / "picture-results"
            observed_path = picture_dir / "LX2" / "case1-photo.jpg"
            overlay_path = picture_dir / "LX2" / "fuji_measurement_procedure" / "case1_measuring.png"
            simulation_dir = root / "lx2_mathematica_simulation"

            write_text(observed_path, "observed image\n")
            write_text(overlay_path, "measurement overlay\n")
            write_json(
                root / "picture_results_manifest.json",
                {
                    "entries": [
                        {
                            "copied_path": str(observed_path),
                            "group": "LX2",
                            "case_ids": ["case-1"],
                        },
                        {
                            "copied_path": str(overlay_path),
                            "group": "LX2/fuji_measurement_procedure",
                            "case_ids": ["case-1"],
                        },
                    ]
                },
            )
            write_text(simulation_dir / "case-1-f1.8308kHz-m0-n4-summary.txt", "caseId: case-1\nfrequencyHz: 1830.8\nm: 0\nn: 4\n")
            write_text(simulation_dir / "case-1-f1.8308kHz-m0-n4.png", "primary comparison image\n")

            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            unresolved = fixture["output_unresolved"].read_text(encoding="utf-8")
            summary = json.loads(fixture["output_summary_json"].read_text(encoding="utf-8"))
            self.assertNotIn("Could not uniquely map observed asset for case-1", unresolved)
            self.assertIn("comparison_cases", summary)
            self.assertEqual(len(summary["comparison_cases"]), 1)
            self.assertTrue(str(summary["comparison_cases"][0]["observed_asset_path"]).endswith("case1-photo.jpg"))
            self.assertFalse(str(summary["comparison_cases"][0]["observed_asset_path"]).endswith("case1_measuring.png"))

    def test_fallback_prefers_nested_lx2_photo_over_flat_duplicate_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            fixture = self.prepare_fixture(root)

            flat_photo = root / "picture-results" / "1.experimental-pattern.jpg"
            nested_photo = root / "picture-results" / "LX2" / "1.experimental-pattern.jpg"
            simulation_dir = root / "lx2_mathematica_simulation"

            write_text(flat_photo, "flat duplicate image\n")
            write_text(nested_photo, "nested lx2 image\n")
            write_json(
                root / "picture_results_manifest.json",
                {
                    "entries": [
                        {
                            "copied_path": str(flat_photo),
                            "group": "",
                        },
                        {
                            "copied_path": str(nested_photo),
                            "group": "LX2",
                        },
                    ]
                },
            )
            write_text(simulation_dir / "case-1-f1.8308kHz-m0-n4-summary.txt", "caseId: case-1\nfrequencyHz: 1830.8\nm: 0\nn: 4\n")
            write_text(simulation_dir / "case-1-f1.8308kHz-m0-n4.png", "primary comparison image\n")

            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            unresolved = fixture["output_unresolved"].read_text(encoding="utf-8")
            summary = json.loads(fixture["output_summary_json"].read_text(encoding="utf-8"))
            self.assertNotIn("Could not uniquely map observed asset for case-1", unresolved)
            self.assertEqual(len(summary["comparison_cases"]), 1)
            self.assertTrue(str(summary["comparison_cases"][0]["observed_asset_path"]).endswith("picture-results/LX2/1.experimental-pattern.jpg"))

    def test_case_specific_caveats_stay_attached_to_the_relevant_case(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(
                Path(temp_name),
                comparison_cases=[
                    {
                        "case_id": "case-3",
                        "title": "Case 3",
                        "observed_summary": "Observed a narrow split-ring response.",
                        "comparison_summary": "The reference solution predicts a split-ring response.",
                        "agreement_summary": "Pattern family remains broadly consistent.",
                        "caveats": ["Label mapping remains provisional for this case."],
                    },
                    {
                        "case_id": "case-4",
                        "title": "Case 4",
                        "observed_summary": "Observed a nearby comparison case without caveats.",
                        "comparison_summary": "Theory remains smoothly matched here.",
                        "agreement_summary": "A nearby comparison case without caveats.",
                        "caveats": [],
                    }
                ],
            )

            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            tex = fixture["main_tex"].read_text(encoding="utf-8")
            case_3_block = slice_between(tex, r"\paragraph{Case 3}", r"\paragraph{Case 4}")
            case_4_block = slice_between(tex, r"\paragraph{Case 4}", r"\section{Experiment Discussion}")
            self.assertIn("Observed a narrow split-ring response.", case_3_block)
            self.assertIn("The reference solution predicts a split-ring response.", case_3_block)
            self.assertIn("Pattern family remains broadly consistent.", case_3_block)
            self.assertIn("Label mapping remains provisional for this case.", case_3_block)
            self.assertNotIn("Label mapping remains provisional for this case.", case_4_block)

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

    def test_appendix_code_renders_full_utf8_content_into_two_column_text_blocks_without_source_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name), include_appendix_code=True)
            write_text(
                fixture["model_code"],
                "\n".join(
                    [
                        "ClearAll[",
                        "  alpha,",
                        "  beta,",
                        "  gamma,",
                        "  delta,",
                        "  epsilon,",
                        "  zeta,",
                        "  eta,",
                        "  theta,",
                        "  iota,",
                        "  kappa,",
                        "  lambdaVar,",
                        "  mu,",
                        "  nu,",
                        "  xi,",
                        "  omicron,",
                        "  piVar,",
                        "  rho,",
                        "  sigma,",
                        "  tauVar,",
                        "  upsilon,",
                        "  phi,",
                        "  chi,",
                        "  psi,",
                        "  omega",
                        "]",
                        'sampleFile = "1.f=1.8308kHz,m=0,n=4时的二维驻波图.jpg";',
                        "ParseLX2Filename::invalid = \"invalid file\";",
                    ]
                )
                + "\n",
            )

            completed = self.run_builder(fixture, include_appendix_code=True)
            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")

            tex = fixture["main_tex"].read_text(encoding="utf-8")
            self.assertIn(r"\twocolumn", tex)
            self.assertIn(r"\begin{tcolorbox}", tex)
            self.assertIn(r"\begin{Verbatim}", tex)
            self.assertIn("ParseLX2Filename::invalid", tex)
            self.assertIn("二维驻波图", tex)
            self.assertNotIn("Source path:", tex)
            self.assertNotIn("appendix-code-pages/model/page-001.png", tex)
            self.assertNotIn(r"\includegraphics", tex)
            self.assertNotIn(r"\onecolumn", tex)

            manifest = json.loads(fixture["output_appendix_manifest"].read_text(encoding="utf-8"))
            model_entry = next(
                entry for entry in manifest["appendix_entries"] if entry.get("label") == "model.wl"
            )
            self.assertEqual(model_entry.get("label"), "model.wl")

    def test_flat_processed_results_are_grouped_into_multiple_case_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name))
            write_json(
                fixture["processed_data_json"],
                {
                    "experiment": "mechanics_combined_english",
                    "results": [
                        {
                            "name": "lx1_string_mean_experimental_wave_speed",
                            "label": "LX1 string mean experimental wave speed",
                            "value": 16.54,
                            "unit": "m/s",
                            "kind": "derived",
                        },
                        {
                            "name": "lx1_strip_density",
                            "label": "LX1 strip material density",
                            "value": 8053.28,
                            "unit": "kg/m^3",
                            "kind": "derived",
                        },
                        {
                            "name": "lx2_validated_case_count",
                            "label": "LX2 validated representative case count",
                            "value": 5,
                            "unit": "cases",
                            "kind": "coverage",
                        },
                    ],
                },
            )

            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            payload = json.loads(fixture["output_summary_json"].read_text(encoding="utf-8"))
            titles = [item["title"] for item in payload["case_records"]]
            self.assertEqual(titles, ["LX1 String", "LX1 Strip", "LX2"])

    def test_mechanics_style_subsection_synonyms_are_resolved_and_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_mechanics_synonym_fixture(Path(temp_name))

            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            payload = json.loads(fixture["output_summary_json"].read_text(encoding="utf-8"))
            self.assertEqual(
                payload["written_sections"],
                [
                    "Experimental Procedure and Observations",
                    "Results and Analysis",
                    "Local Discussion",
                    "Code",
                ],
            )
            tex = fixture["main_tex"].read_text(encoding="utf-8")
            self.assertIn("% course-lab-final-staging:experimental-process:begin", tex)
            self.assertIn("% course-lab-final-staging:results:begin", tex)
            self.assertIn("% course-lab-final-staging:discussion:begin", tex)
            self.assertIn("% course-lab-final-staging:appendix:begin", tex)
            self.assertIn("Existing LX2 process prose should remain untouched.", tex)

    def test_same_block_local_discussion_is_preferred_over_global_discussion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_same_block_discussion_fixture(Path(temp_name))

            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            payload = json.loads(fixture["output_summary_json"].read_text(encoding="utf-8"))
            self.assertEqual(
                payload["written_sections"],
                [
                    "Experimental Procedure and Observations",
                    "Results and Analysis",
                    "Local Discussion",
                    "Code",
                ],
            )
            tex = fixture["main_tex"].read_text(encoding="utf-8")
            self.assertIn("% course-lab-final-staging:discussion:begin", tex)
            self.assertIn("Global discussion prose should remain untouched.", tex)

    def test_summary_only_existing_draft_mode_preserves_substantive_mechanics_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_mechanics_synonym_fixture(Path(temp_name))
            write_text(
                fixture["main_tex"],
                textwrap.dedent(
                    r"""
                    \section{Introduction}
                    Intro text.

                    \section{LX1: One-Dimensional Standing Waves}
                    \subsection{Experimental Procedure and Observations}
                    Existing LX1 process prose should remain untouched.

                    \subsection{Results and Analysis}
                    Existing LX1 results prose should remain untouched.

                    \subsection{Local Discussion}
                    Existing LX1 local discussion prose should remain untouched.

                    \section{LX2: Circular Thin-Plate Standing Waves}
                    \subsection{Experimental Procedure and Observations}
                    Existing LX2 process prose should remain untouched.

                    \subsection{Results and Analysis}
                    Existing LX2 results prose should remain untouched.

                    \subsection{Local Discussion}
                    Existing LX2 local discussion prose should remain untouched.

                    \section{Code}
                    \NeedsInput{Add code artifacts if this experiment used scripts, notebooks, or simulations.}
                    """
                ).strip()
                + "\n",
            )

            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            payload = json.loads(fixture["output_summary_json"].read_text(encoding="utf-8"))
            self.assertEqual(payload["written_sections"], ["Code"])
            combined_unresolved = "\n".join(payload["unresolved"]).lower()
            self.assertIn("preserved existing substantive experimental procedure and observations section", combined_unresolved)
            self.assertIn("preserved existing substantive results and analysis section", combined_unresolved)
            self.assertIn("preserved existing substantive local discussion section", combined_unresolved)

            tex = fixture["main_tex"].read_text(encoding="utf-8")
            self.assertIn("Existing LX1 process prose should remain untouched.", tex)
            self.assertIn("Existing LX1 results prose should remain untouched.", tex)
            self.assertIn("Existing LX1 local discussion prose should remain untouched.", tex)
            self.assertIn("% course-lab-final-staging:appendix:begin", tex)

    def test_summary_only_existing_draft_mode_does_not_overwrite_long_sections_with_local_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_mechanics_synonym_fixture(Path(temp_name))
            write_text(
                fixture["main_tex"],
                textwrap.dedent(
                    r"""
                    \section{Introduction}
                    Intro text.

                    \section{LX1: One-Dimensional Standing Waves}
                    \subsection{Experimental Procedure and Observations}
                    Existing LX1 process prose should remain untouched because the section already contains substantive authored content.

                    \NeedsInput{One local evidence gap still remains visible here.}

                    \subsection{Results and Analysis}
                    Existing LX1 results prose should remain untouched because the section already contains substantive authored analysis.

                    \NeedsInput{One local numerical check still needs follow-up here.}

                    \subsection{Local Discussion}
                    Existing LX1 local discussion prose should remain untouched.

                    \section{LX2: Circular Thin-Plate Standing Waves}
                    \subsection{Experimental Procedure and Observations}
                    Existing LX2 process prose should remain untouched.

                    \subsection{Results and Analysis}
                    Existing LX2 results prose should remain untouched.

                    \subsection{Local Discussion}
                    Existing LX2 local discussion prose should remain untouched.

                    \section{Code}
                    \NeedsInput{Add code artifacts if this experiment used scripts, notebooks, or simulations.}
                    """
                ).strip()
                + "\n",
            )

            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            payload = json.loads(fixture["output_summary_json"].read_text(encoding="utf-8"))
            self.assertEqual(payload["written_sections"], ["Code"])
            combined_unresolved = "\n".join(payload["unresolved"]).lower()
            self.assertIn("preserved existing substantive experimental procedure and observations section", combined_unresolved)
            self.assertIn("preserved existing substantive results and analysis section", combined_unresolved)
            self.assertIn("preserved existing substantive local discussion section", combined_unresolved)

            tex = fixture["main_tex"].read_text(encoding="utf-8")
            self.assertIn("Existing LX1 process prose should remain untouched because the section already contains substantive authored content.", tex)
            self.assertIn(r"\NeedsInput{One local evidence gap still remains visible here.}", tex)
            self.assertIn("Existing LX1 results prose should remain untouched because the section already contains substantive authored analysis.", tex)
            self.assertIn(r"\NeedsInput{One local numerical check still needs follow-up here.}", tex)
            self.assertIn("% course-lab-final-staging:appendix:begin", tex)

    def test_repeated_runs_do_not_nest_appendix_code_headings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_mechanics_synonym_fixture(Path(temp_name))

            first = self.run_builder(fixture)
            self.assertEqual(first.returncode, 0, msg=f"{first.stdout}\n{first.stderr}")

            second = self.run_builder(fixture)
            self.assertEqual(second.returncode, 0, msg=f"{second.stdout}\n{second.stderr}")

            tex = fixture["main_tex"].read_text(encoding="utf-8")
            self.assertEqual(tex.count("% course-lab-final-staging:appendix:begin"), 1)
            self.assertEqual(tex.count(r"\subsection{Code}"), 0)
            self.assertIn(r"\NeedsInput{No appendix code inputs were provided for final staging.}", tex)

    def test_code_section_heading_renders_file_labels_as_subsections_when_appendix_code_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_mechanics_synonym_fixture(Path(temp_name))

            completed = self.run_builder(fixture, include_appendix_code=True)
            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")

            tex = fixture["main_tex"].read_text(encoding="utf-8")
            self.assertIn(r"\section{Code}", tex)
            self.assertNotIn(r"\subsection{Code}", tex)
            self.assertIn(r"\subsection{model.wl}", tex)
            self.assertIn(r"\subsection{process\_data.py}", tex)

    def test_calculation_details_appendix_renders_before_code_when_manifest_is_passed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(
                Path(temp_name),
                include_appendix_code=True,
                include_calculation_details=True,
            )

            completed = self.run_builder(
                fixture,
                include_appendix_code=True,
                include_calculation_details=True,
            )

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            tex = fixture["main_tex"].read_text(encoding="utf-8")
            appendix_block = slice_between(tex, "% course-lab-final-staging:appendix:begin")
            self.assertIn(r"\onecolumn", appendix_block)
            self.assertIn(r"\subsection{Calculation Details}", appendix_block)
            self.assertIn(r"\input{analysis/calculation_details/case-a-details.tex}", appendix_block)
            self.assertIn(r"\twocolumn", appendix_block)
            self.assertIn(r"\subsection{Code}", appendix_block)
            self.assertLess(
                appendix_block.find(r"\subsection{Calculation Details}"),
                appendix_block.find(r"\subsection{Code}"),
            )
            self.assertLess(
                appendix_block.find(r"\onecolumn"),
                appendix_block.find(r"\subsection{Calculation Details}"),
            )
            self.assertLess(
                appendix_block.find(r"\twocolumn"),
                appendix_block.find(r"\subsection{Code}"),
            )

    def test_missing_calculation_detail_file_surfaces_in_unresolved_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name), include_calculation_details=True)
            missing_tex = fixture["calculation_details_tex"]
            missing_tex.unlink()
            write_json(
                fixture["calculation_details_manifest"],
                {
                    "entries": [
                        {
                            "title": "Case A Calculation Details",
                            "path": str(missing_tex),
                            "order": 10,
                            "kind": "calculation_details",
                            "exists": False,
                            "slug": "case-a-details",
                        }
                    ]
                },
            )

            completed = self.run_builder(fixture, include_calculation_details=True)

            self.assertEqual(completed.returncode, 0, msg=f"{completed.stdout}\n{completed.stderr}")
            unresolved = fixture["output_unresolved"].read_text(encoding="utf-8")
            self.assertIn("Missing calculation-details file", unresolved)

    def test_confirmed_references_json_renders_literature_context_without_new_search(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name))

            completed = self.run_builder(
                fixture,
                extra_args=[
                    "--references-json",
                    str(fixture["references_json"]),
                ],
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            tex = fixture["main_tex"].read_text(encoding="utf-8")
            self.assertIn("arXiv", tex)
            self.assertIn("Published standing-wave reference", tex)
            self.assertNotIn("search for literature", tex.lower())

            summary_payload = json.loads(fixture["output_summary_json"].read_text(encoding="utf-8"))
            literature_references = summary_payload["literature_references"]
            self.assertEqual(len(literature_references), 1)
            self.assertEqual(literature_references[0]["comparison_basis"], "literature_report")

    def test_ambiguous_synonym_headings_fail_with_candidate_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_ambiguous_synonym_fixture(Path(temp_name))

            completed = self.run_builder(fixture)
            combined = f"{completed.stdout}\n{completed.stderr}"

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("Ambiguous", combined)
            self.assertIn("Results and Analysis", combined)
            self.assertIn("line", combined)

    def test_discussion_renders_assigned_thinking_questions_from_body_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            fixture = self.prepare_fixture(root)
            body_scaffold = json.loads(fixture["body_scaffold_json"].read_text(encoding="utf-8"))
            body_scaffold["scaffold_sections"][2]["source_key"] = "thinking_questions"
            body_scaffold["scaffold_sections"][2]["thinking_questions"] = [
                "1. 试推导其半波电压 U_pi 的表达式。",
                "2. 如果电光晶体的光轴与激光束不平行，如何检查？",
            ]
            write_json(fixture["body_scaffold_json"], body_scaffold)

            subprocess.run(
                [
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
                    "--output-summary-json",
                    str(fixture["output_summary_json"]),
                    "--output-summary-markdown",
                    str(fixture["output_summary_markdown"]),
                    "--output-unresolved",
                    str(fixture["output_unresolved"]),
                    "--output-appendix-manifest",
                    str(fixture["output_appendix_manifest"]),
                ],
                check=True,
            )

            text = fixture["main_tex"].read_text(encoding="utf-8")
            self.assertIn(r"\subsection{Assigned Thinking Questions}", text)
            self.assertIn(r"试推导其半波电压 U\_pi 的表达式", text)
            self.assertIn("如果电光晶体的光轴与激光束不平行", text)


if __name__ == "__main__":
    unittest.main()
