from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"


class StagePrincipleImagesTests(unittest.TestCase):
    def test_principle_images_are_copied_and_titled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            decoded_dir = root / "pdf_decoded" / "sample"
            (decoded_dir / "images").mkdir(parents=True, exist_ok=True)
            shutil.copy2(FIXTURES / "sample_mineru.json", decoded_dir / "sample.json")
            shutil.copy2(FIXTURES / "principle.jpg", decoded_dir / "images" / "principle.jpg")

            out_dir = root / "results" / "sample" / "principle-images"
            out_tex = root / "results" / "sample" / "principle_figures.tex"
            out_json = root / "results" / "sample" / "principle_figures.json"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "stage_principle_images.py"),
                    "--decoded-json",
                    str(decoded_dir / "sample.json"),
                    "--output-dir",
                    str(out_dir),
                    "--output-tex",
                    str(out_tex),
                    "--output-json",
                    str(out_json),
                ],
                check=True,
            )

            manifest = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual(manifest["principle_image_count"], 1)
            entry = manifest["entries"][0]
            self.assertTrue((out_dir / entry["relative_output_path"]).exists())
            self.assertEqual(entry["latex_caption"], "力曲线示意图")
            self.assertEqual(entry["context_subheading"], "4.1 力曲线示意图")
            tex = out_tex.read_text(encoding="utf-8")
            self.assertIn(r"\includegraphics", tex)
            self.assertIn(r"\caption{力曲线示意图}", tex)
            self.assertNotIn("Fig. 1", tex)
            self.assertNotIn("Auto-generated", tex)
            self.assertNotIn("Insert near subsection", tex)
            self.assertNotIn("\n\n\\begin{figure}", tex)
            self.assertNotIn("\\end{figure}\n\n", tex)

    def test_caption_named_fallback_images_are_matched(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            decoded_dir = root / "pdf_decoded" / "sample"
            (decoded_dir / "images").mkdir(parents=True, exist_ok=True)
            shutil.copy2(FIXTURES / "sample_mineru.json", decoded_dir / "sample.json")
            shutil.copy2(FIXTURES / "principle.jpg", decoded_dir / "images" / "图-1-力曲线示意图.jpg")

            out_dir = root / "results" / "sample" / "principle-images"
            out_tex = root / "results" / "sample" / "principle_figures.tex"
            out_json = root / "results" / "sample" / "principle_figures.json"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "stage_principle_images.py"),
                    "--decoded-json",
                    str(decoded_dir / "sample.json"),
                    "--output-dir",
                    str(out_dir),
                    "--output-tex",
                    str(out_tex),
                    "--output-json",
                    str(out_json),
                ],
                check=True,
            )

            manifest = json.loads(out_json.read_text(encoding="utf-8"))
            entry = manifest["entries"][0]
            self.assertFalse(entry["missing_source"])
            self.assertTrue((out_dir / entry["relative_output_path"]).exists())

    def test_related_images_are_grouped_as_subfigures(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            decoded_dir = root / "pdf_decoded" / "sample"
            (decoded_dir / "images").mkdir(parents=True, exist_ok=True)

            payload = [
                {"type": "text", "text": "晶体光学性质", "text_level": 1, "page_idx": 0},
                {"type": "text", "text": "四. 实验原理", "text_level": 1, "page_idx": 0},
                {"type": "text", "text": "4.3 Conoscopic Figures and Optical Sign", "text_level": 1, "page_idx": 0},
                {"type": "image", "img_path": "images/a.jpg", "image_caption": ["(a) 立体图"], "image_footnote": [], "page_idx": 0},
                {"type": "image", "img_path": "images/b.jpg", "image_caption": ["(b) 俯视图", "图 4-3-1 锥光干涉图示意图"], "image_footnote": [], "page_idx": 0},
            ]
            (decoded_dir / "sample.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            shutil.copy2(FIXTURES / "principle.jpg", decoded_dir / "images" / "a.jpg")
            shutil.copy2(FIXTURES / "principle.jpg", decoded_dir / "images" / "b.jpg")

            out_dir = root / "results" / "sample" / "principle-images"
            out_tex = root / "results" / "sample" / "principle_figures.tex"
            out_json = root / "results" / "sample" / "principle_figures.json"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "stage_principle_images.py"),
                    "--decoded-json",
                    str(decoded_dir / "sample.json"),
                    "--output-dir",
                    str(out_dir),
                    "--output-tex",
                    str(out_tex),
                    "--output-json",
                    str(out_json),
                ],
                check=True,
            )

            manifest = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual(manifest["grouping_questions"], [])
            self.assertEqual(manifest["figure_block_count"], 1)
            block = manifest["figure_blocks"][0]
            self.assertEqual(block["type"], "subfigure_group")
            self.assertEqual(block["caption_text"], "锥光干涉图示意图")
            tex = out_tex.read_text(encoding="utf-8")
            self.assertIn(r"\begin{subfigure}", tex)
            self.assertIn(r"\caption{立体图}", tex)
            self.assertIn(r"\caption{俯视图}", tex)
            self.assertIn(r"\caption{锥光干涉图示意图}", tex)
            self.assertNotIn("\n\n\\begin{figure}", tex)
            self.assertNotIn("\\end{figure}\n\n", tex)

    def test_ambiguous_grouping_requests_user_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            decoded_dir = root / "pdf_decoded" / "sample"
            (decoded_dir / "images").mkdir(parents=True, exist_ok=True)

            payload = [
                {"type": "text", "text": "晶体光学性质", "text_level": 1, "page_idx": 0},
                {"type": "text", "text": "四. 实验原理", "text_level": 1, "page_idx": 0},
                {"type": "text", "text": "4.3 Conoscopic Figures and Optical Sign", "text_level": 1, "page_idx": 0},
                {"type": "image", "img_path": "images/a.jpg", "image_caption": ["(a) 同名轴平行"], "image_footnote": [], "page_idx": 0},
            ]
            (decoded_dir / "sample.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            shutil.copy2(FIXTURES / "principle.jpg", decoded_dir / "images" / "a.jpg")

            out_dir = root / "results" / "sample" / "principle-images"
            out_tex = root / "results" / "sample" / "principle_figures.tex"
            out_json = root / "results" / "sample" / "principle_figures.json"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "stage_principle_images.py"),
                    "--decoded-json",
                    str(decoded_dir / "sample.json"),
                    "--output-dir",
                    str(out_dir),
                    "--output-tex",
                    str(out_tex),
                    "--output-json",
                    str(out_json),
                ],
                check=True,
            )

            manifest = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["grouping_questions"]), 1)
            self.assertIn("do they belong to the same group?", manifest["grouping_questions"][0]["question"])
            tex = out_tex.read_text(encoding="utf-8")
            self.assertIn(r"\NeedsInput{Pending picture grouping decision:", tex)
            self.assertNotIn("User confirmation required", tex)


if __name__ == "__main__":
    unittest.main()
