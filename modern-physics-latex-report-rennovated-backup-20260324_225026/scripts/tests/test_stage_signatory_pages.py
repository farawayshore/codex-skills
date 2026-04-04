from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]


class StageSignatoryPagesTests(unittest.TestCase):
    def test_signatory_pages_are_grouped_as_subfigures(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            source_root = root / "signatory"
            source_root.mkdir(parents=True, exist_ok=True)
            (source_root / "page1.jpg").write_text("img1", encoding="utf-8")
            (source_root / "page2.jpg").write_text("img2", encoding="utf-8")
            (source_root / "page3.jpg").write_text("img3", encoding="utf-8")

            output_dir = root / "results" / "sample" / "signatory-pages"
            output_json = root / "results" / "sample" / "signatory_pages_manifest.json"
            output_tex = root / "results" / "sample" / "signatory_pages.tex"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "stage_signatory_pages.py"),
                    "--source-root",
                    str(source_root),
                    "--output-dir",
                    str(output_dir),
                    "--output-json",
                    str(output_json),
                    "--output-tex",
                    str(output_tex),
                ],
                check=True,
            )

            manifest = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(manifest["file_count"], 3)
            tex = output_tex.read_text(encoding="utf-8")
            self.assertIn(r"\begin{figure*}[p]", tex)
            self.assertIn(r"\begin{subfigure}[t]{0.48\textwidth}", tex)
            self.assertIn(r"\caption{Signatory pages}", tex)
            self.assertEqual(tex.count(r"\caption{}"), 3)
            self.assertIn(r"\par\medskip", tex)
            self.assertNotIn("Auto-generated", tex)
            self.assertNotIn("\n\n\\begin{figure}", tex)
            self.assertNotIn("\\end{figure*}\n\n", tex)
            self.assertTrue((output_dir / "signatory-page-01-page1.jpg").exists())

    def test_many_signatory_pages_are_split_into_continued_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            source_root = root / "signatory"
            source_root.mkdir(parents=True, exist_ok=True)
            for index in range(1, 10):
                (source_root / f"page{index}.jpg").write_text(f"img{index}", encoding="utf-8")

            output_dir = root / "results" / "sample" / "signatory-pages"
            output_json = root / "results" / "sample" / "signatory_pages_manifest.json"
            output_tex = root / "results" / "sample" / "signatory_pages.tex"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "stage_signatory_pages.py"),
                    "--source-root",
                    str(source_root),
                    "--output-dir",
                    str(output_dir),
                    "--output-json",
                    str(output_json),
                    "--output-tex",
                    str(output_tex),
                ],
                check=True,
            )

            manifest = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(manifest["file_count"], 9)
            tex = output_tex.read_text(encoding="utf-8")
            self.assertEqual(tex.count(r"\begin{figure*}[p]"), 2)
            self.assertIn(r"\ContinuedFloat", tex)
            self.assertIn(r"\caption{Signatory pages (continued)}", tex)
            self.assertEqual(tex.count(r"\caption{}"), 9)


if __name__ == "__main__":
    unittest.main()
