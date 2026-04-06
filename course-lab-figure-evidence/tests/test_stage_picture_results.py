from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = SKILL_DIR / "scripts"


class StagePictureResultsTests(unittest.TestCase):
    def test_picture_results_are_copied_with_group_structure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            source_root = root / "picture_results"
            (source_root / "z切LN" / "石英锥").mkdir(parents=True, exist_ok=True)
            (source_root / "z切LN" / "石英锥" / "1.png").write_text("img1", encoding="utf-8")
            (source_root / "z切LN" / "一级红片.png").write_text("img2", encoding="utf-8")

            output_dir = root / "results" / "sample" / "picture-results"
            output_json = root / "results" / "sample" / "picture_results_manifest.json"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "stage_picture_results.py"),
                    "--source-root",
                    str(source_root),
                    "--output-dir",
                    str(output_dir),
                    "--output-json",
                    str(output_json),
                ],
                check=True,
            )

            manifest = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(manifest["file_count"], 2)
            copied_paths = [Path(entry["copied_path"]) for entry in manifest["entries"]]
            self.assertTrue(all(path.exists() for path in copied_paths))
            groups = {entry["group"] for entry in manifest["entries"]}
            self.assertIn("z切LN/石英锥", groups)

    def test_serial_numbered_picture_results_are_grouped_as_process_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            source_root = root / "picture_results"
            (source_root / "石英楔推进").mkdir(parents=True, exist_ok=True)
            (source_root / "石英楔推进" / "quartz_wedge_1.png").write_text("img1", encoding="utf-8")
            (source_root / "石英楔推进" / "quartz_wedge_2.png").write_text("img2", encoding="utf-8")
            (source_root / "石英楔推进" / "quartz_wedge_3.png").write_text("img3", encoding="utf-8")
            (source_root / "石英楔推进" / "single_note.png").write_text("img4", encoding="utf-8")

            output_dir = root / "results" / "sample" / "picture-results"
            output_json = root / "results" / "sample" / "picture_results_manifest.json"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "stage_picture_results.py"),
                    "--source-root",
                    str(source_root),
                    "--output-dir",
                    str(output_dir),
                    "--output-json",
                    str(output_json),
                ],
                check=True,
            )

            manifest = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(manifest["sequence_group_count"], 1)
            sequence_group = manifest["sequence_groups"][0]
            self.assertEqual(sequence_group["group"], "石英楔推进")
            self.assertEqual(sequence_group["sequence_base"], "quartz_wedge")
            self.assertEqual([entry["sequence_serial"] for entry in sequence_group["entries"]], [1, 2, 3])

    def test_comparison_cases_are_staged_into_report_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            source_root = root / "picture_results"
            (source_root / "LX2").mkdir(parents=True, exist_ok=True)
            (source_root / "LX2" / "1.experimental-pattern.jpg").write_text("observed", encoding="utf-8")

            simulation_dir = root / "lx2_mathematica_simulation"
            simulation_dir.mkdir(parents=True, exist_ok=True)
            comparison_path = simulation_dir / "case-1-f1.8308kHz-m0-n4.png"
            comparison_path.write_text("comparison", encoding="utf-8")

            comparison_cases_path = root / "final_staging_summary.json"
            comparison_cases_path.write_text(
                json.dumps(
                    {
                        "comparison_cases": [
                            {
                                "case_id": "case-1",
                                "observed_asset_path": str(source_root / "LX2" / "1.experimental-pattern.jpg"),
                                "comparison_asset_path": str(comparison_path),
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            output_dir = root / "results" / "sample" / "picture-results"
            output_json = root / "results" / "sample" / "picture_results_manifest.json"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "stage_picture_results.py"),
                    "--source-root",
                    str(source_root),
                    "--comparison-cases-json",
                    str(comparison_cases_path),
                    "--output-dir",
                    str(output_dir),
                    "--output-json",
                    str(output_json),
                ],
                check=True,
            )

            manifest = json.loads(output_json.read_text(encoding="utf-8"))
            comparison_entries = [entry for entry in manifest["entries"] if entry.get("evidence_role") == "comparison"]
            self.assertEqual(len(comparison_entries), 1)
            self.assertEqual(comparison_entries[0]["case_ids"], ["case-1"])
            self.assertTrue(Path(comparison_entries[0]["copied_path"]).exists())
            self.assertIn("comparison-cases/case-1", comparison_entries[0]["relative_output_path"])


if __name__ == "__main__":
    unittest.main()
