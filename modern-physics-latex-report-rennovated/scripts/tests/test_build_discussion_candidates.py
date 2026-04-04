from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]


class BuildDiscussionCandidatesTests(unittest.TestCase):
    def run_builder(self, evidence_plan: dict[str, object]) -> tuple[dict[str, object], str]:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            evidence_plan_path = root / "picture_evidence_plan.json"
            output_json = root / "discussion_candidates.json"
            output_markdown = root / "discussion_candidates.md"
            evidence_plan_path.write_text(json.dumps(evidence_plan, ensure_ascii=False, indent=2), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "build_discussion_candidates.py"),
                    "--evidence-plan",
                    str(evidence_plan_path),
                    "--output-json",
                    str(output_json),
                    "--output-markdown",
                    str(output_markdown),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(output_json.read_text(encoding="utf-8"))
            markdown = output_markdown.read_text(encoding="utf-8")
            self.assertTrue(completed.stdout.strip())
            self.assertTrue(markdown.strip())
            return payload, markdown

    def test_low_confidence_image_group_emits_vague_image_candidate(self) -> None:
        evidence_plan = {
            "evidence_units": [
                {
                    "group_id": "mystery-image",
                    "sample_label": "Mystery sample",
                    "method_label": "unmapped observation",
                    "analysis_focus": "Inspect this evidence manually before drafting a local interpretation.",
                    "mapping_confidence": "low",
                    "warnings": ["Could not confidently map this image group."],
                }
            ]
        }

        payload, markdown = self.run_builder(evidence_plan)
        self.assertEqual(len(payload["discussion_candidates"]), 1)
        candidate = payload["discussion_candidates"][0]
        self.assertEqual(candidate["candidate_type"], "vague_image_interpretation")
        self.assertEqual(candidate["confidence_level"], "low")
        self.assertEqual(candidate["wording_posture"], "may indicate")
        self.assertTrue(candidate["outside_lookup_needed"])
        self.assertIn("Mystery sample", markdown)

    def test_anomaly_signal_emits_candidate_without_erasing_conflicting_fact(self) -> None:
        evidence_plan = {
            "evidence_units": [
                {
                    "group_id": "z-cut-teo2",
                    "sample_label": "z-cut TeO2",
                    "method_label": "z-cut conoscopic observation",
                    "analysis_focus": "Relate conoscopic, accessory-plate, and wedge evidence for optic-sign judgment.",
                    "mapping_confidence": "high",
                    "warnings": [],
                    "anomaly_signals": [
                        "Quartz-wedge result is weaker than the handout expectation even though the first-order red plate suggests a clear sign."
                    ],
                }
            ]
        }

        payload, _ = self.run_builder(evidence_plan)
        candidate = payload["discussion_candidates"][0]
        self.assertEqual(candidate["candidate_type"], "anomaly_explanation")
        self.assertIn("Quartz-wedge result is weaker", " ".join(candidate["observed_facts"]))
        self.assertTrue(candidate["proposed_interpretation"])

    def test_weak_evidence_still_emits_low_confidence_candidate(self) -> None:
        evidence_plan = {
            "evidence_units": [
                {
                    "group_id": "extended-peridotite",
                    "sample_label": "Peridotite",
                    "method_label": "extended sample comparison",
                    "analysis_focus": "Compare how extended samples respond across polarization and conoscopic modes.",
                    "mapping_confidence": "medium",
                    "warnings": ["Only one mode is represented clearly in the current draft."],
                }
            ]
        }

        payload, _ = self.run_builder(evidence_plan)
        self.assertEqual(len(payload["discussion_candidates"]), 1)
        candidate = payload["discussion_candidates"][0]
        self.assertEqual(candidate["candidate_type"], "material_specific_explanation")
        self.assertIn(candidate["confidence_level"], {"low", "medium"})

    def test_no_trigger_means_no_candidate(self) -> None:
        evidence_plan = {
            "evidence_units": [
                {
                    "group_id": "fast-axis-a",
                    "sample_label": "A plate",
                    "method_label": "fast-axis schematic",
                    "analysis_focus": "Support the plate-by-plate fast-axis and retardation interpretation.",
                    "mapping_confidence": "high",
                    "warnings": [],
                }
            ]
        }

        payload, markdown = self.run_builder(evidence_plan)
        self.assertEqual(payload["discussion_candidates"], [])
        self.assertIn("Candidates: 0", markdown)


if __name__ == "__main__":
    unittest.main()
