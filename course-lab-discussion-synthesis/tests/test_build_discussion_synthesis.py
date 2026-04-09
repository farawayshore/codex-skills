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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class BuildDiscussionSynthesisTests(unittest.TestCase):
    def prepare_fixture(
        self,
        root: Path,
        *,
        approval_status: str = "approved",
        weak_case: bool = False,
        with_prior_synthesis: bool = False,
    ) -> dict[str, Path]:
        synthesis_input_json = root / "discussion_synthesis_input.tmp.json"
        synthesis_input_markdown = root / "discussion_synthesis_input.tmp.md"
        reference_report_a = root / "reference_report_a.json"
        reference_report_b = root / "reference_report_b.json"
        results_interpretation_json = root / "results_interpretation.json"
        output_json = root / "discussion_synthesis.json"
        output_markdown = root / "discussion_synthesis.md"
        output_unresolved = root / "discussion_synthesis_unresolved.md"
        output_staging_json = root / "discussion_staging_input.tmp.json"
        output_staging_markdown = root / "discussion_staging_input.tmp.md"
        prior_synthesis_json = root / "prior_discussion_synthesis.json"

        if weak_case:
            ideas = [
                {
                    "idea_id": "weak-gap-analysis",
                    "title": "Weak gap analysis",
                    "category": "open_followup",
                    "source_evidence": ["single weak observation"],
                    "reference_report_support": ["Reference Report A"],
                    "local_basis_summary": "Only one weak observation supports this direction.",
                    "confidence_level": "low",
                    "wording_posture": "may indicate",
                    "reusable_snippet": "This weak direction may indicate a useful follow-up but needs caution.",
                    "caution_notes": ["Support is thin."],
                    "suggested_synthesis_position": "error-analysis",
                }
            ]
        else:
            ideas = [
                {
                    "idea_id": "wave-speed-interpretation",
                    "title": "Wave speed interpretation",
                    "category": "interpretation_extension",
                    "source_evidence": ["wave_speed", "Measured wave speed stays near the expected band."],
                    "reference_report_support": ["Reference Report A"],
                    "local_basis_summary": "Measured wave speed stays near the expected band.",
                    "confidence_level": "medium",
                    "wording_posture": "likely indicates",
                    "reusable_snippet": "Wave-speed agreement likely indicates good control of the main resonance measurement.",
                    "caution_notes": [],
                    "suggested_synthesis_position": "physical-interpretation",
                },
                {
                    "idea_id": "error-source-alignment",
                    "title": "Error source alignment",
                    "category": "anomaly_explanation",
                    "source_evidence": ["frequency reading drift", "reference mismatch across methods"],
                    "reference_report_support": ["Reference Report B"],
                    "local_basis_summary": "Method-to-method mismatch suggests reading and boundary-condition sensitivity.",
                    "confidence_level": "medium",
                    "wording_posture": "likely indicates",
                    "reusable_snippet": "Method mismatch likely indicates boundary-condition and reading sensitivity.",
                    "caution_notes": [],
                    "suggested_synthesis_position": "error-analysis",
                },
                {
                    "idea_id": "improvement-direction",
                    "title": "Improvement direction",
                    "category": "open_followup",
                    "source_evidence": ["repeat measurements", "tension stabilization"],
                    "reference_report_support": ["Reference Report A", "Reference Report B"],
                    "local_basis_summary": "Repeat measurements and better stabilization would reduce run-to-run drift.",
                    "confidence_level": "medium",
                    "wording_posture": "likely indicates",
                    "reusable_snippet": "Better stabilization likely indicates a clear path to lower scatter.",
                    "caution_notes": [],
                    "suggested_synthesis_position": "improvement-suggestions",
                },
            ]

        payload: dict[str, object] = {
            "candidate_count": len(ideas),
            "approval_status": approval_status,
            "approved_idea_ids": [item["idea_id"] for item in ideas] if approval_status == "approved" else [],
            "discussion_ideas": ideas,
        }

        write_json(synthesis_input_json, payload)
        write_text(synthesis_input_markdown, "# Discussion Synthesis Input\n\nFixture input.\n")
        write_json(
            reference_report_a,
            {
                "title": "Reference Report A",
                "discussion_hints": [
                    "Use wave-speed agreement to anchor physical interpretation.",
                    "Tie improvement suggestions to stabilization and repeatability.",
                ],
            },
        )
        write_json(
            reference_report_b,
            {
                "title": "Reference Report B",
                "discussion_hints": [
                    "Method mismatch should become explicit error analysis.",
                    "Weak support should remain visible in unresolved notes.",
                ],
            },
        )
        write_json(
            results_interpretation_json,
            {
                "interpretation_items": [
                    {"name": "wave_speed", "summary": "Measured wave speed stays near the expected band."}
                ],
                "unresolved": ["Boundary-condition sensitivity may affect the mismatch discussion."],
            },
        )

        if with_prior_synthesis:
            write_json(
                prior_synthesis_json,
                {
                    "overall_confidence": "medium",
                    "discussion_blocks": [{"block_id": "prior-block", "support_strength": "medium"}],
                },
            )

        return {
            "synthesis_input_json": synthesis_input_json,
            "synthesis_input_markdown": synthesis_input_markdown,
            "reference_report_a": reference_report_a,
            "reference_report_b": reference_report_b,
            "results_interpretation_json": results_interpretation_json,
            "output_json": output_json,
            "output_markdown": output_markdown,
            "output_unresolved": output_unresolved,
            "output_staging_json": output_staging_json,
            "output_staging_markdown": output_staging_markdown,
            "prior_synthesis_json": prior_synthesis_json,
        }

    def build_command(
        self,
        fixture: dict[str, Path],
        *,
        include_input_json: bool = True,
        include_reference_reports: bool = True,
        include_prior_synthesis: bool = False,
    ) -> list[str]:
        command = [
            sys.executable,
            str(SCRIPT_DIR / "build_discussion_synthesis.py"),
            "--experiment-name",
            "Fixture Experiment",
            "--experiment-safe-name",
            "fixture_experiment",
            "--synthesis-input-markdown",
            str(fixture["synthesis_input_markdown"]),
            "--results-interpretation-json",
            str(fixture["results_interpretation_json"]),
            "--output-json",
            str(fixture["output_json"]),
            "--output-markdown",
            str(fixture["output_markdown"]),
            "--output-unresolved",
            str(fixture["output_unresolved"]),
            "--output-staging-json",
            str(fixture["output_staging_json"]),
            "--output-staging-markdown",
            str(fixture["output_staging_markdown"]),
        ]

        if include_input_json:
            command.extend(["--synthesis-input-json", str(fixture["synthesis_input_json"])])

        if include_reference_reports:
            command.extend(
                [
                    "--reference-report",
                    str(fixture["reference_report_a"]),
                    "--reference-report",
                    str(fixture["reference_report_b"]),
                ]
            )

        if include_prior_synthesis:
            command.extend(["--prior-synthesis-json", str(fixture["prior_synthesis_json"])])

        return command

    def run_builder(
        self,
        fixture: dict[str, Path],
        *,
        include_input_json: bool = True,
        include_reference_reports: bool = True,
        include_prior_synthesis: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            self.build_command(
                fixture,
                include_input_json=include_input_json,
                include_reference_reports=include_reference_reports,
                include_prior_synthesis=include_prior_synthesis,
            ),
            capture_output=True,
            text=True,
        )

    def test_missing_synthesis_input_json_fails_with_clear_contract_message(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name))
            completed = self.run_builder(fixture, include_input_json=False)
            combined = f"{completed.stdout}\n{completed.stderr}".lower()
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("synthesis-input-json", combined)
            self.assertIn("required", combined)

    def test_unapproved_input_fails_with_clear_approval_message(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name), approval_status="pending")
            completed = self.run_builder(fixture)
            combined = f"{completed.stdout}\n{completed.stderr}".lower()
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("approved", combined)
            self.assertIn("approval", combined)

    def test_synthesis_judgment_input_from_discussion_ideas_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name), approval_status="pending")
            write_json(
                fixture["synthesis_input_json"],
                {
                    "candidate_count": 1,
                    "approval_mode": "synthesis_judgment",
                    "discussion_ideas": [
                        {
                            "idea_id": "wave-speed-interpretation",
                            "title": "Wave speed interpretation",
                            "confidence_level": "medium",
                            "approval_status": "pending_synthesis_judgment",
                            "reusable_snippet": "Wave-speed agreement likely indicates good control.",
                            "reference_report_support": ["Reference Report A"],
                        }
                    ],
                },
            )

            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_missing_reference_report_fails_with_clear_contract_message(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name))
            completed = self.run_builder(fixture, include_reference_reports=False)
            combined = f"{completed.stdout}\n{completed.stderr}".lower()
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("reference-report", combined)
            self.assertIn("required", combined)

    def test_first_run_writes_outputs_and_marks_broad_research(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name))
            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(fixture["output_json"].read_text(encoding="utf-8"))
            self.assertTrue(payload["broad_first_pass_web_research_used"])
            self.assertFalse(payload["targeted_gap_fill_research_used"])
            self.assertGreaterEqual(len(payload["discussion_blocks"]), 3)
            self.assertGreaterEqual(len(payload["support_records"]), 3)

    def test_rerun_skips_broad_research_when_prior_synthesis_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name), with_prior_synthesis=True)
            completed = self.run_builder(fixture, include_prior_synthesis=True)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(fixture["output_json"].read_text(encoding="utf-8"))
            self.assertFalse(payload["broad_first_pass_web_research_used"])
            self.assertFalse(payload["targeted_gap_fill_research_used"])

    def test_weak_support_triggers_targeted_gap_fill_and_unresolved_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name), weak_case=True, with_prior_synthesis=True)
            completed = self.run_builder(fixture, include_prior_synthesis=True)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(fixture["output_json"].read_text(encoding="utf-8"))
            self.assertFalse(payload["broad_first_pass_web_research_used"])
            self.assertTrue(payload["targeted_gap_fill_research_used"])
            self.assertEqual(payload["overall_confidence"], "low")
            self.assertTrue(payload["unresolved"])
            self.assertIn("weak", fixture["output_unresolved"].read_text(encoding="utf-8").lower())

    def test_output_shape_includes_staging_handoff_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            fixture = self.prepare_fixture(Path(temp_name))
            completed = self.run_builder(fixture)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(fixture["output_markdown"].exists())
            self.assertTrue(fixture["output_unresolved"].exists())
            self.assertTrue(fixture["output_staging_json"].exists())
            self.assertTrue(fixture["output_staging_markdown"].exists())

            payload = json.loads(fixture["output_json"].read_text(encoding="utf-8"))
            self.assertIn("discussion_blocks", payload)
            self.assertIn("support_records", payload)
            self.assertIn("overall_confidence", payload)


if __name__ == "__main__":
    unittest.main()
