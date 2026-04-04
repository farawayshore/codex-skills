from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = SKILL_DIR / "scripts"


class PlanPictureEvidenceTests(unittest.TestCase):
    def run_planner(self, manifest: dict[str, object]) -> tuple[dict[str, object], str]:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            manifest_path = root / "picture_results_manifest.json"
            output_json = root / "picture_evidence_plan.json"
            output_markdown = root / "picture_evidence_plan.md"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "plan_picture_evidence.py"),
                    "--manifest-json",
                    str(manifest_path),
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
            self.assertTrue(markdown.strip())
            self.assertTrue(completed.stdout.strip())
            return payload, markdown

    def test_planner_emits_stable_evidence_units_for_common_group_types(self) -> None:
        manifest = {
            "entries": [
                {
                    "group": "conoscopic mode/z-cut material/z-cut LN",
                    "relative_output_path": "conoscopic-mode/z-cut-material/z-cut-LN/pure-conoscopic-image.png",
                    "sequence_serial": None,
                },
                {
                    "group": "conoscopic mode/z-cut material/z-cut LN/quartz wedge",
                    "relative_output_path": "conoscopic-mode/z-cut-material/z-cut-LN/quartz-wedge/1.png",
                    "sequence_serial": 1,
                },
                {
                    "group": "conoscopic mode/Airy-spiral",
                    "relative_output_path": "conoscopic-mode/Airy-spiral/quartz-square-on-quartz-disk.png",
                    "sequence_serial": None,
                },
                {
                    "group": "conoscopic mode/oblique-cut material/oblique-cut TeO2",
                    "relative_output_path": "conoscopic-mode/oblique-cut-material/oblique-cut-TeO2/1.png",
                    "sequence_serial": 1,
                },
                {
                    "group": "polarization mode/extended samples/peridotite",
                    "relative_output_path": "polarization-mode/extended-samples/peridotite/10x-without-Bertrand-lens-without-accessory-plate-1.png",
                    "sequence_serial": 1,
                },
            ],
            "sequence_groups": [],
        }

        payload, markdown = self.run_planner(manifest)

        units = payload["evidence_units"]
        self.assertTrue(units)
        self.assertTrue(all(unit["group_id"] for unit in units))
        self.assertTrue(all(unit["target_subsection"] for unit in units))
        self.assertTrue(all("selection_policy" in unit for unit in units))
        self.assertTrue(all("selected_entries" in unit for unit in units))
        self.assertTrue(all("omitted_entries" in unit for unit in units))
        self.assertIn("z-cut", markdown)
        self.assertIn("Airy", markdown)

    def test_planner_keeps_paired_comparisons_and_summarizes_repetitive_sequences(self) -> None:
        manifest = {
            "entries": [
                {
                    "group": "conoscopic mode/Airy-spiral",
                    "relative_output_path": "conoscopic-mode/Airy-spiral/quartz-square-on-quartz-disk.png",
                    "sequence_serial": None,
                },
                {
                    "group": "conoscopic mode/Airy-spiral",
                    "relative_output_path": "conoscopic-mode/Airy-spiral/quartz-disk-on-quartz-square.png",
                    "sequence_serial": None,
                },
                {
                    "group": "conoscopic mode/oblique-cut material/oblique-cut thin LN",
                    "relative_output_path": "conoscopic-mode/oblique-cut-material/oblique-cut-thin-LN/1.png",
                    "sequence_serial": 1,
                },
                {
                    "group": "conoscopic mode/oblique-cut material/oblique-cut thin LN",
                    "relative_output_path": "conoscopic-mode/oblique-cut-material/oblique-cut-thin-LN/2.png",
                    "sequence_serial": 2,
                },
                {
                    "group": "conoscopic mode/oblique-cut material/oblique-cut thin LN",
                    "relative_output_path": "conoscopic-mode/oblique-cut-material/oblique-cut-thin-LN/3.png",
                    "sequence_serial": 3,
                },
                {
                    "group": "conoscopic mode/oblique-cut material/oblique-cut thin LN",
                    "relative_output_path": "conoscopic-mode/oblique-cut-material/oblique-cut-thin-LN/4.png",
                    "sequence_serial": 4,
                },
            ],
            "sequence_groups": [
                {
                    "group": "conoscopic mode/oblique-cut material/oblique-cut thin LN",
                    "sequence_base": "oblique-cut-thin-LN",
                    "entries": [
                        {
                            "relative_output_path": "conoscopic-mode/oblique-cut-material/oblique-cut-thin-LN/1.png",
                            "sequence_serial": 1,
                        },
                        {
                            "relative_output_path": "conoscopic-mode/oblique-cut-material/oblique-cut-thin-LN/2.png",
                            "sequence_serial": 2,
                        },
                        {
                            "relative_output_path": "conoscopic-mode/oblique-cut-material/oblique-cut-thin-LN/3.png",
                            "sequence_serial": 3,
                        },
                        {
                            "relative_output_path": "conoscopic-mode/oblique-cut-material/oblique-cut-thin-LN/4.png",
                            "sequence_serial": 4,
                        },
                    ],
                }
            ],
        }

        payload, _ = self.run_planner(manifest)
        units = {unit["group_id"]: unit for unit in payload["evidence_units"]}

        airy_unit = next(unit for unit in units.values() if unit["method_label"] == "Airy spiral")
        self.assertEqual(airy_unit["selection_policy"], "paired_comparison")
        self.assertEqual(len(airy_unit["selected_entries"]), 2)
        self.assertEqual(airy_unit["omitted_entries"], [])

        oblique_unit = next(unit for unit in units.values() if "oblique" in unit["group_id"])
        self.assertEqual(oblique_unit["selection_policy"], "representative_subset")
        self.assertLess(len(oblique_unit["selected_entries"]), 4)
        self.assertGreater(len(oblique_unit["omitted_entries"]), 0)

    def test_uncertain_groups_are_preserved_with_warning_metadata(self) -> None:
        manifest = {
            "entries": [
                {
                    "group": "mystery bucket/weird contrast image",
                    "relative_output_path": "mystery-bucket/weird-contrast-image.png",
                    "sequence_serial": None,
                }
            ],
            "sequence_groups": [],
        }

        payload, _ = self.run_planner(manifest)
        self.assertEqual(len(payload["evidence_units"]), 1)
        unit = payload["evidence_units"][0]
        self.assertEqual(unit["group_id"], "mystery-bucket-weird-contrast-image")
        self.assertTrue(unit["warnings"])
        self.assertEqual(unit["mapping_confidence"], "low")


if __name__ == "__main__":
    unittest.main()
