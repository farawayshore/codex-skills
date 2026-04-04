from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]


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


if __name__ == "__main__":
    unittest.main()
