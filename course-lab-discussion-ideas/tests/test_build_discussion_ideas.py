from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path("/root/.codex/skills/course-lab-discussion-ideas")
SCRIPT_DIR = SKILL_DIR / "scripts"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class BuildDiscussionIdeasTests(unittest.TestCase):
    def prepare_fixture(
        self,
        root: Path,
        *,
        with_memory: bool = False,
        weak_case: bool = False,
        routine_only_case: bool = False,
    ) -> dict[str, Path]:
        results_interpretation_json = root / "results_interpretation.json"
        results_interpretation_markdown = root / "results_interpretation.md"
        idea_gists = root / "idea_gists.md"
        memory_root = root / "experiment_discussion_ideas"
        reference_report_a = root / "reference_report_a.json"
        reference_report_b = root / "reference_report_b.json"
        output_json = root / "discussion_ideas.json"
        output_markdown = root / "discussion_ideas.md"
        output_unresolved = root / "discussion_ideas_unresolved.md"
        output_synthesis_json = root / "discussion_synthesis_input.tmp.json"
        output_synthesis_markdown = root / "discussion_synthesis_input.tmp.md"

        if routine_only_case:
            payload = {
                "comparison_records": [
                    {"lane": "handout_expectation_vs_data", "name": "wave_speed", "status": "covered"},
                    {"lane": "theory_reference_vs_data", "name": "youngs_modulus", "status": "compared"},
                    {"lane": "handout_expectation_vs_data", "name": "loss_factor", "status": "missing"},
                ],
                "interpretation_items": [
                    {"name": "wave_speed", "summary": "Measured wave speed tracks the expected band closely."},
                    {"name": "youngs_modulus", "summary": "Young's modulus differs slightly from the theoretical value."},
                ],
                "anomalies": [
                    "Representative case labels conflict in two staged observations.",
                ],
                "completeness_checks": [
                    "loss_factor missing from processed-data results",
                ],
                "unresolved": [
                    "Routine uncertainty analysis should explain the remaining deviation.",
                    "Compare the measured value with the theoretical result in the discussion.",
                ],
            }
        elif weak_case:
            payload = {
                "comparison_records": [
                    {"lane": "handout_expectation_vs_data", "name": "single_value", "status": "covered"}
                ],
                "interpretation_items": [
                    {"name": "single_value", "summary": "Only one tentative result is available."}
                ],
                "anomalies": [],
                "completeness_checks": [],
                "unresolved": ["Only one tentative observation is available."],
            }
        else:
            payload = {
                "comparison_records": [
                    {"lane": "handout_expectation_vs_data", "name": "wave_speed", "status": "covered"},
                    {"lane": "theory_reference_vs_data", "name": "youngs_modulus", "status": "compared"},
                    {"lane": "simulation_vs_data", "name": "mode_shape", "status": "compared"},
                ],
                "interpretation_items": [
                    {"name": "wave_speed", "summary": "Measured wave speed tracks the expected band closely."},
                    {"name": "youngs_modulus", "summary": "Young's modulus differs across methods."},
                ],
                "anomalies": [
                    "Strip modulus and ring modulus diverge more than expected.",
                    "Representative case labels conflict in two staged observations.",
                ],
                "completeness_checks": [
                    "full survey modulus trend missing from results inventory",
                ],
                "unresolved": [
                    "Use Mathematica code to extract the interference-pattern brightness profile from CCD images and quantify fringe symmetry.",
                    "Weak interference images may need a second-pass Python digitization and radial brightness fit before drafting.",
                    "Reference report suggests damping sensitivity may explain the method disagreement.",
                ],
            }

        write_json(results_interpretation_json, payload)
        write_text(results_interpretation_markdown, "# Results Interpretation\n\nFixture run.\n")
        write_text(
            idea_gists,
            "# Idea Gists\n\n- Crystal optics: prioritize only non-handout extensions such as brightness extraction or custom image analysis.\n",
        )
        write_json(
            reference_report_a,
            {
                "title": "Reference Report A",
                "discussion_hints": [
                    "Mathematica brightness extraction from interference images can support a novel discussion section.",
                    "Do not treat ordinary theory comparison as a novel discussion idea.",
                ],
            },
        )
        write_json(
            reference_report_b,
            {
                "title": "Reference Report B",
                "discussion_hints": [
                    "Python image digitization and fitting can extend the report beyond the handout.",
                    "Routine uncertainty and discrepancy prose should stay out of discussion-idea harvesting.",
                ],
            },
        )

        if with_memory:
            memory_dir = memory_root / "fixture_experiment"
            write_json(
                memory_dir / "idea_memory.json",
                {
                    "discussion_ideas": [
                        {
                            "idea_id": "prior-brightness-extraction",
                            "title": "Prior brightness extraction workflow",
                            "reuse_status": "reused",
                            "outside_lookup_summary": "Earlier run used Mathematica code to extract brightness from interference images.",
                        }
                    ]
                },
            )
            write_text(memory_dir / "idea_notes.md", "# Prior Idea Notes\n\n- Reused brightness extraction workflow.\n")

        return {
            "results_interpretation_json": results_interpretation_json,
            "results_interpretation_markdown": results_interpretation_markdown,
            "idea_gists": idea_gists,
            "memory_root": memory_root,
            "reference_report_a": reference_report_a,
            "reference_report_b": reference_report_b,
            "output_json": output_json,
            "output_markdown": output_markdown,
            "output_unresolved": output_unresolved,
            "output_synthesis_json": output_synthesis_json,
            "output_synthesis_markdown": output_synthesis_markdown,
        }

    def build_command(
        self,
        fixture: dict[str, Path],
        *,
        include_results_json: bool = True,
        include_reference_reports: bool = True,
    ) -> list[str]:
        command = [
            sys.executable,
            str(SCRIPT_DIR / "build_discussion_ideas.py"),
            "--experiment-name",
            "Fixture Experiment",
            "--experiment-safe-name",
            "fixture_experiment",
            "--results-interpretation-markdown",
            str(fixture["results_interpretation_markdown"]),
            "--idea-gists",
            str(fixture["idea_gists"]),
            "--memory-root",
            str(fixture["memory_root"]),
            "--output-json",
            str(fixture["output_json"]),
            "--output-markdown",
            str(fixture["output_markdown"]),
            "--output-unresolved",
            str(fixture["output_unresolved"]),
            "--output-synthesis-json",
            str(fixture["output_synthesis_json"]),
            "--output-synthesis-markdown",
            str(fixture["output_synthesis_markdown"]),
        ]

        if include_results_json:
            command.extend(
                [
                    "--results-interpretation-json",
                    str(fixture["results_interpretation_json"]),
                ]
            )

        if include_reference_reports:
            command.extend(
                [
                    "--reference-report",
                    str(fixture["reference_report_a"]),
                    "--reference-report",
                    str(fixture["reference_report_b"]),
                ]
            )

        return command

    def run_builder(
        self,
        fixture: dict[str, Path],
        *,
        include_results_json: bool = True,
        include_reference_reports: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            self.build_command(
                fixture,
                include_results_json=include_results_json,
                include_reference_reports=include_reference_reports,
            ),
            capture_output=True,
            text=True,
        )

    def test_missing_reference_report_fails_with_clear_contract_message(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name))
            completed = self.run_builder(fixture, include_reference_reports=False)
            combined = f"{completed.stdout}\n{completed.stderr}".lower()
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("reference-report", combined)
            self.assertIn("required", combined)

    def test_missing_results_interpretation_json_fails_with_clear_contract_message(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name))
            completed = self.run_builder(fixture, include_results_json=False)
            combined = f"{completed.stdout}\n{completed.stderr}".lower()
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("results-interpretation-json", combined)
            self.assertIn("required", combined)

    def test_mixed_input_writes_required_outputs_and_retains_only_novelty_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name))
            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(fixture["output_json"].exists())
            self.assertTrue(fixture["output_markdown"].exists())
            self.assertTrue(fixture["output_synthesis_json"].exists())
            self.assertTrue(fixture["output_synthesis_markdown"].exists())

            payload = json.loads(fixture["output_json"].read_text(encoding="utf-8"))
            synthesis_payload = json.loads(fixture["output_synthesis_json"].read_text(encoding="utf-8"))
            synthesis_markdown = fixture["output_synthesis_markdown"].read_text(encoding="utf-8").lower()
            self.assertEqual(payload["candidate_count"], 2)
            self.assertTrue(payload["broad_first_pass_search_used"])
            self.assertEqual(len(payload["discussion_ideas"]), 2)
            self.assertTrue(all(item["beyond_handout"] for item in payload["discussion_ideas"]))
            self.assertTrue(all(item["targeted_web_round_count"] >= 1 for item in payload["discussion_ideas"]))
            self.assertTrue(all(item["suggests_extraction_or_analysis_code"] for item in payload["discussion_ideas"]))
            titles = {str(item["title"]).lower() for item in payload["discussion_ideas"]}
            self.assertTrue(any("brightness" in title for title in titles))
            self.assertFalse(any("wave speed" in title for title in titles))
            self.assertFalse(any("young" in title for title in titles))
            self.assertTrue(
                all(item["approval_status"] == "pending_synthesis_judgment" for item in synthesis_payload["discussion_ideas"])
            )
            self.assertIn("approval status: pending_synthesis_judgment", synthesis_markdown)
            self.assertIn("approval basis:", synthesis_markdown)

    def test_routine_only_input_produces_zero_candidates_and_skips_search(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name), routine_only_case=True)
            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(fixture["output_json"].read_text(encoding="utf-8"))
            unresolved_text = fixture["output_unresolved"].read_text(encoding="utf-8").lower()
            self.assertEqual(payload["candidate_count"], 0)
            self.assertEqual(payload["discussion_ideas"], [])
            self.assertFalse(payload["broad_first_pass_search_used"])
            self.assertIn("no non-routine discussion ideas", unresolved_text)

    def test_existing_memory_skips_broad_first_pass_search(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name), with_memory=True)
            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(fixture["output_json"].read_text(encoding="utf-8"))
            self.assertFalse(payload["broad_first_pass_search_used"])
            self.assertTrue(any(item["reuse_status"] == "reused" for item in payload["discussion_ideas"]))

    def test_retained_weak_candidate_can_take_two_targeted_rounds(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name))
            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(fixture["output_json"].read_text(encoding="utf-8"))
            self.assertIn(2, {item["targeted_web_round_count"] for item in payload["discussion_ideas"]})

    def test_novelty_candidates_update_experiment_local_memory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name))
            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            memory_dir = fixture["memory_root"] / "fixture_experiment"
            self.assertTrue((memory_dir / "idea_memory.json").exists())
            self.assertTrue((memory_dir / "idea_notes.md").exists())

            memory_payload = json.loads((memory_dir / "idea_memory.json").read_text(encoding="utf-8"))
            self.assertEqual(len(memory_payload["discussion_ideas"]), 2)

    def test_weak_input_writes_unresolved_output_without_fake_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name), weak_case=True)
            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(fixture["output_json"].read_text(encoding="utf-8"))
            unresolved_text = fixture["output_unresolved"].read_text(encoding="utf-8").lower()
            self.assertEqual(payload["candidate_count"], 0)
            self.assertIn("no non-routine discussion ideas", unresolved_text)


if __name__ == "__main__":
    unittest.main()
