from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = SCRIPT_DIR.parent


class EnsureReportWorkspaceTests(unittest.TestCase):
    def test_workspace_is_created_from_template(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            template = root / "tau_template.tex"
            template.write_text("\\documentclass{article}\n\\begin{document}Hello\\end{document}\n", encoding="utf-8")
            results_root = root / "results"
            output_json = root / "workspace.json"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "ensure_report_workspace.py"),
                    "--experiment",
                    "原子力显微镜",
                    "--mode",
                    "new",
                    "--template",
                    str(template),
                    "--results-root",
                    str(results_root),
                    "--output-json",
                    str(output_json),
                ],
                check=True,
            )

            payload = json.loads(output_json.read_text(encoding="utf-8"))
            workspace = Path(payload["workspace"])
            self.assertTrue((workspace / "main.tex").exists())
            self.assertTrue((workspace / "build.sh").exists())
            self.assertTrue((workspace / "notes" / "workspace_manifest.json").exists())

    def test_workspace_manifest_records_course_and_template(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            template = root / "general_course_template.tex"
            template.write_text("\\documentclass{article}\n\\begin{document}Hello\\end{document}\n", encoding="utf-8")
            results_root = root / "results"
            output_json = root / "workspace.json"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "ensure_report_workspace.py"),
                    "--course",
                    "Advanced Optics Laboratory",
                    "--experiment",
                    "Interference Lab",
                    "--mode",
                    "new",
                    "--template",
                    str(template),
                    "--results-root",
                    str(results_root),
                    "--output-json",
                    str(output_json),
                ],
                check=True,
            )

            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["course"], "Advanced Optics Laboratory")
            self.assertEqual(payload["template"], str(template))
            self.assertTrue(Path(payload["canonical_tex"]).exists())


if __name__ == "__main__":
    unittest.main()
