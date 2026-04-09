from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "ensure_report_workspace.py"
BUILD_TEMPLATE = SKILL_DIR / "assets" / "build.sh"


class EnsureReportWorkspaceTests(unittest.TestCase):
    def test_discovery_manifest_seeds_workspace_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            template = root / "interference_template.tex"
            template.write_text("\\documentclass{article}\n\\begin{document}Hello\\end{document}\n", encoding="utf-8")
            results_root = root / "results-from-discovery"
            discovery_json = root / "course-lab-discovery-interference-lab-en.json"
            output_json = root / "workspace.json"

            discovery_payload = {
                "course": "Advanced Optics Laboratory",
                "experiment_query": "Interference Lab",
                "roots": {
                    "results_root": str(results_root),
                },
                "handouts": [{"path": str(root / "handout.pdf"), "score": 10.0}],
                "reference_reports": [{"path": str(root / "reference.pdf"), "score": 9.0}],
                "data_files": [{"path": str(root / "data.csv"), "score": 8.0}],
                "signatory_files": [{"path": str(root / "signatory.pdf"), "score": 7.0}],
                "templates": [{"path": str(template), "score": 0.0}],
                "result_dirs": [],
                "warnings": [],
            }
            discovery_json.write_text(json.dumps(discovery_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--discovery-json",
                    str(discovery_json),
                    "--mode",
                    "new",
                    "--template",
                    str(template),
                    "--output-json",
                    str(output_json),
                ],
                check=True,
            )

            payload = json.loads(output_json.read_text(encoding="utf-8"))
            workspace = Path(payload["workspace"])
            discovery_cache = discovery_json
            self.assertEqual(payload["course"], "Advanced Optics Laboratory")
            self.assertEqual(payload["experiment"], "Interference Lab")
            self.assertEqual(workspace.parent, results_root)
            self.assertEqual(payload["handouts"], [str(root / "handout.pdf")])
            self.assertEqual(payload["reference_reports"], [str(root / "reference.pdf")])
            self.assertEqual(payload["data_files"], [str(root / "data.csv")])
            self.assertEqual(payload["signatory_files"], [str(root / "signatory.pdf")])
            self.assertEqual(payload["discovery_cache_input"], str(discovery_cache))
            self.assertFalse((workspace / "notes" / "discovery_manifest.json").exists())

    def test_workspace_is_created_from_single_file_template(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            template = root / "AI_works" / "resources" / "latex_templet" / "english" / "tau_templet copy.tex"
            template.parent.mkdir(parents=True, exist_ok=True)
            template.write_text("\\documentclass{article}\n\\begin{document}Hello\\end{document}\n", encoding="utf-8")
            results_root = root / "results"
            output_json = root / "workspace.json"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
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
            main_tex = (workspace / "main.tex").read_text(encoding="utf-8")
            self.assertTrue((workspace / "main.tex").exists())
            self.assertTrue((workspace / "build.sh").exists())
            self.assertEqual((workspace / "build.sh").read_text(encoding="utf-8"), BUILD_TEMPLATE.read_text(encoding="utf-8"))
            self.assertTrue((workspace / "notes" / "workspace_manifest.json").exists())
            self.assertIn(r"\definecolor{NeedsInputRed}{RGB}{220,110,110}", main_tex)
            self.assertIn(r"\newcommand{\NeedsInput}[1]{\textcolor{NeedsInputRed}{#1}}", main_tex)
            self.assertEqual(payload["template_kind"], "file")
            self.assertEqual(payload["template_language"], "english")
            self.assertEqual(payload["template_root"], str(template.parent))
            self.assertEqual(payload["template_entry"], str(template))
            self.assertEqual(payload["copied_companion_assets"], [])

    def test_stock_tau_template_is_normalized_into_skill_owned_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            template = root / "AI_works" / "resources" / "latex_templet" / "english" / "tau_templet copy.tex"
            template.parent.mkdir(parents=True, exist_ok=True)
            template.write_text(
                r"""
\documentclass{article}
\begin{document}
\section{Introduction}
Briefly introduce the physical phenomenon, the scientific background, and the practical value of the experiment.

\section{Experiment Purpose}
\begin{itemize}
  \item State the main physical quantity or phenomenon to be measured or verified.
\end{itemize}

\section{Experiment Principle}
\subsection{Physical Background}
Explain the core theory, define the main variables, and describe the mechanism behind the measurement.

\subsection{Key Equations}
Replace the example formulas below with the equations for your own experiment.

\subsection{Expected Observations}
Describe the qualitative features you expect to observe.

\section{Experiment Steps}
\begin{enumerate}
  \item Perform the safety check and instrument warm-up.
\end{enumerate}

\section{Experiment Process and Results}
Present the original measurements clearly.

\section{Experiment Discussion}
Interpret whether the results support the theory.

% Uncomment the next lines if you need appendices.
% \appendix
% \section{Appendix}
% Put supplementary derivations, extra tables, or code here.
\end{document}
""".strip()
                + "\n",
                encoding="utf-8",
            )
            results_root = root / "results"
            output_json = root / "workspace.json"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--experiment",
                    "Electro-Optic Modulation",
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
            main_tex = Path(payload["canonical_tex"]).read_text(encoding="utf-8")

            self.assertIn(r"\section{Objectives}", main_tex)
            self.assertNotIn(r"\section{Experiment Purpose}", main_tex)
            self.assertIn(r"\section{Experimental Procedure and Observations}", main_tex)
            self.assertNotIn(r"\section{Experiment Steps}", main_tex)
            self.assertIn(r"\section{Results and Analysis}", main_tex)
            self.assertNotIn(r"\section{Experiment Process and Results}", main_tex)
            self.assertGreaterEqual(main_tex.count(r"% course-lab-final-staging:allow-overwrite"), 3)
            self.assertIn(r"\appendix", main_tex)
            self.assertIn(r"\section{Appendix}", main_tex)
            self.assertIn(r"\NeedsInput{", main_tex)

    def test_bundle_template_rewrite_copies_assets_and_records_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            bundle_dir = (
                root
                / "AI_works"
                / "resources"
                / "latex_templet"
                / "chinese"
                / "Rho_Class___Research_Article_Template_CN"
            )
            (bundle_dir / "figures").mkdir(parents=True, exist_ok=True)
            (bundle_dir / "rho-class").mkdir(parents=True, exist_ok=True)
            (bundle_dir / "main.tex").write_text(
                "\\documentclass{article}\n\\begin{document}Bundle\\end{document}\n",
                encoding="utf-8",
            )
            (bundle_dir / "rho.bib").write_text("@book{rho,title={Rho}}\n", encoding="utf-8")
            (bundle_dir / "figures" / "cover.txt").write_text("figure asset\n", encoding="utf-8")
            (bundle_dir / "rho-class" / "rho.cls").write_text("% class asset\n", encoding="utf-8")

            results_root = root / "results"
            workspace = results_root / "晶体光学性质"
            workspace.mkdir(parents=True)
            old_main = workspace / "main.tex"
            old_main.write_text("\\documentclass{article}\n\\begin{document}Old\\end{document}\n", encoding="utf-8")
            (workspace / "figures").mkdir(parents=True, exist_ok=True)
            (workspace / "figures" / "stale.txt").write_text("stale\n", encoding="utf-8")
            output_json = root / "workspace.json"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--experiment",
                    "晶体光学性质",
                    "--mode",
                    "rewrite",
                    "--template",
                    str(bundle_dir),
                    "--results-root",
                    str(results_root),
                    "--output-json",
                    str(output_json),
                ],
                check=True,
            )

            payload = json.loads(output_json.read_text(encoding="utf-8"))
            new_main = workspace / "main.tex"
            self.assertIn("Bundle", new_main.read_text(encoding="utf-8"))
            self.assertTrue((workspace / "rho.bib").exists())
            self.assertTrue((workspace / "figures" / "cover.txt").exists())
            self.assertTrue((workspace / "rho-class" / "rho.cls").exists())
            self.assertTrue(Path(payload["backup_path"]).exists())
            self.assertEqual(payload["template_kind"], "bundle")
            self.assertEqual(payload["template_language"], "chinese")
            self.assertEqual(payload["template_root"], str(bundle_dir))
            self.assertEqual(payload["template_entry"], str(bundle_dir / "main.tex"))
            self.assertEqual(
                sorted(payload["copied_companion_assets"]),
                sorted(["figures/cover.txt", "rho-class/rho.cls", "rho.bib"]),
            )

    def test_modify_mode_reuses_existing_canonical_tex(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            results_root = root / "results"
            workspace = results_root / "Interference-Lab"
            workspace.mkdir(parents=True)
            existing_tex = workspace / "report.tex"
            existing_tex.write_text("\\documentclass{article}\n\\begin{document}Draft\\end{document}\n", encoding="utf-8")
            output_json = root / "workspace.json"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--experiment",
                    "Interference Lab",
                    "--mode",
                    "modify",
                    "--results-root",
                    str(results_root),
                    "--output-json",
                    str(output_json),
                ],
                check=True,
            )

            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(Path(payload["canonical_tex"]), existing_tex)
            self.assertEqual(payload["mode"], "modify")
            self.assertTrue((workspace / "Interference-Lab_procedures.md").exists())


if __name__ == "__main__":
    unittest.main()
