from __future__ import annotations

import json
import os
import subprocess
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

    def make_repo_root(self, root: Path) -> Path:
        repo_root = root / "repo"
        resources = repo_root / "AI_works" / "resources"

        (resources / "experiment_handout" / "Advanced Optics Laboratory" / "Interference Lab.pdf").parent.mkdir(
            parents=True, exist_ok=True
        )
        (resources / "experiment_handout" / "Advanced Optics Laboratory" / "Interference Lab.pdf").write_text(
            "handout",
            encoding="utf-8",
        )
        (resources / "experiment_handout" / "Modern Physics Experiments" / "Interference Lab.pdf").parent.mkdir(
            parents=True, exist_ok=True
        )
        (resources / "experiment_handout" / "Modern Physics Experiments" / "Interference Lab.pdf").write_text(
            "handout",
            encoding="utf-8",
        )

        (resources / "lab_report_reference" / "Advanced Optics Laboratory" / "Interference Lab Reference.pdf").parent.mkdir(
            parents=True, exist_ok=True
        )
        (resources / "lab_report_reference" / "Advanced Optics Laboratory" / "Interference Lab Reference.pdf").write_text(
            "reference",
            encoding="utf-8",
        )
        (
            resources
            / "lab_report_reference"
            / "Modern Physics Experiments"
            / "Interference Lab Reference.pdf"
        ).parent.mkdir(parents=True, exist_ok=True)
        (
            resources
            / "lab_report_reference"
            / "Modern Physics Experiments"
            / "Interference Lab Reference.pdf"
        ).write_text("reference", encoding="utf-8")

        (resources / "experiment_data" / "Interference Lab" / "observations.csv").parent.mkdir(parents=True, exist_ok=True)
        (resources / "experiment_data" / "Interference Lab" / "observations.csv").write_text(
            "x,y\n1,2\n",
            encoding="utf-8",
        )

        (resources / "experiment_pic_results" / "Interference Lab" / "pattern-1.png").parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        (resources / "experiment_pic_results" / "Interference Lab" / "pattern-1.png").write_text(
            "image",
            encoding="utf-8",
        )

        (resources / "experiment_signatory" / "Interference Lab" / "page-1.png").parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        (resources / "experiment_signatory" / "Interference Lab" / "page-1.png").write_text(
            "image",
            encoding="utf-8",
        )

        (resources / "latex_templet" / "Interference course.tex").parent.mkdir(parents=True, exist_ok=True)
        (resources / "latex_templet" / "Interference course.tex").write_text("template", encoding="utf-8")
        (resources / "latex_templet" / "General clean.tex").write_text("template", encoding="utf-8")
        (resources / "latex_templet" / "dont use" / "deprecated.tex").parent.mkdir(parents=True, exist_ok=True)
        (resources / "latex_templet" / "dont use" / "deprecated.tex").write_text("template", encoding="utf-8")

        (repo_root / "AI_works" / "results" / "Interference-Lab").mkdir(parents=True, exist_ok=True)
        (repo_root / "AI_works" / "results" / "Interference-Lab" / "main.tex").write_text(
            "report",
            encoding="utf-8",
        )
        return repo_root

    def run_discover_sources(self, repo_root: Path, output_json: Path) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["MODERN_PHYSICS_REPO_ROOT"] = str(repo_root)
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT_DIR / "discover_sources.py"),
                "--course",
                "Advanced Optics Laboratory",
                "--experiment",
                "Interference Lab",
                "--output-json",
                str(output_json),
            ],
            capture_output=True,
            text=True,
            env=env,
        )

    def test_cli_accepts_course_and_prefers_matching_course_subtree(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            repo_root = self.make_repo_root(Path(temp_name))
            output_json = Path(temp_name) / "discover_sources.json"

            result = self.run_discover_sources(repo_root, output_json)

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["course"], "Advanced Optics Laboratory")
            self.assertIn("Advanced Optics Laboratory", payload["handouts"][0]["path"])
            self.assertIn("Advanced Optics Laboratory", payload["reference_reports"][0]["path"])

    def test_cli_reports_broader_library_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            repo_root = self.make_repo_root(Path(temp_name))
            output_json = Path(temp_name) / "discover_sources.json"

            result = self.run_discover_sources(repo_root, output_json)

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["roots"]["handout_root"], str(repo_root / "AI_works" / "resources" / "experiment_handout"))
            self.assertEqual(
                payload["roots"]["reference_root"],
                str(repo_root / "AI_works" / "resources" / "lab_report_reference"),
            )

    def test_cli_returns_all_allowed_templates_for_user_choice(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            repo_root = self.make_repo_root(Path(temp_name))
            output_json = Path(temp_name) / "discover_sources.json"

            result = self.run_discover_sources(repo_root, output_json)

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            template_labels = [item["label"] for item in payload["templates"]]
            self.assertEqual(template_labels, ["General clean.tex", "Interference course.tex"])
            self.assertEqual([item["label"] for item in payload["excluded_templates"]], ["deprecated.tex"])


if __name__ == "__main__":
    unittest.main()
