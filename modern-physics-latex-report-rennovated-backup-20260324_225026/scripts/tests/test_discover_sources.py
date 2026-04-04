from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import discover_sources


class DiscoverSourcesTests(unittest.TestCase):
    def test_template_filtering_and_scoring(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            handout_root = root / "handouts"
            reference_root = root / "references"
            picture_root = root / "picture_results"
            template_root = root / "templates"
            results_root = root / "results"

            (handout_root / "原子力显微镜的原理与应用.pdf").parent.mkdir(parents=True, exist_ok=True)
            (handout_root / "原子力显微镜的原理与应用.pdf").write_text("handout", encoding="utf-8")
            (reference_root / "299946 原子力.pdf").parent.mkdir(parents=True, exist_ok=True)
            (reference_root / "299946 原子力.pdf").write_text("reference", encoding="utf-8")
            (picture_root / "原子力显微镜" / "force-curve-analysis.png").parent.mkdir(parents=True, exist_ok=True)
            (picture_root / "原子力显微镜" / "force-curve-analysis.png").write_text("image", encoding="utf-8")
            (template_root / "tau_templet copy.tex").parent.mkdir(parents=True, exist_ok=True)
            (template_root / "tau_templet copy.tex").write_text("template", encoding="utf-8")
            (template_root / "dont use" / "old.tex").parent.mkdir(parents=True, exist_ok=True)
            (template_root / "dont use" / "old.tex").write_text("template", encoding="utf-8")
            (results_root / "Atomic-Force-Microscopy-Experiment").mkdir(parents=True, exist_ok=True)
            (results_root / "Atomic-Force-Microscopy-Experiment" / "main.tex").write_text("report", encoding="utf-8")

            old_template_root = discover_sources.TEMPLATE_ROOT
            old_results_root = discover_sources.RESULTS_ROOT
            old_picture_root = discover_sources.PIC_RESULT_ROOT
            try:
                discover_sources.TEMPLATE_ROOT = template_root
                discover_sources.RESULTS_ROOT = results_root
                discover_sources.PIC_RESULT_ROOT = picture_root
                allowed, excluded = discover_sources.template_paths(False)
                self.assertEqual([path.name for path in allowed], ["tau_templet copy.tex"])
                self.assertEqual([path.name for path in excluded], ["old.tex"])

                scored = discover_sources.score_paths("原子力显微镜", [handout_root / "原子力显微镜的原理与应用.pdf"])
                self.assertGreater(scored[0].score, 0.0)

                reference_scored = discover_sources.score_paths("原子力显微镜", [reference_root / "299946 原子力.pdf"])
                self.assertGreater(reference_scored[0].score, 0.0)

                picture_scored = discover_sources.score_paths("原子力显微镜", [picture_root / "原子力显微镜" / "force-curve-analysis.png"])
                self.assertGreater(picture_scored[0].score, 0.0)

                result_dirs = discover_sources.result_candidates("Atomic Force Microscopy", 3)
                self.assertEqual(result_dirs[0]["label"], "Atomic-Force-Microscopy-Experiment")
            finally:
                discover_sources.TEMPLATE_ROOT = old_template_root
                discover_sources.RESULTS_ROOT = old_results_root
                discover_sources.PIC_RESULT_ROOT = old_picture_root


if __name__ == "__main__":
    unittest.main()
