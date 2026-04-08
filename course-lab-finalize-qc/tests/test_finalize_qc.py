from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import run_command  # type: ignore
from finalize_qc import DEFAULT_BUILD_ASSET, run_finalize_qc  # type: ignore


def build_fake_pdf(page_count: int, *, extra_bytes: int = 0) -> bytes:
    objects = b"".join(
        f"{index} 0 obj\n<< /Type /Page >>\nendobj\n".encode("utf-8")
        for index in range(1, page_count + 1)
    )
    return b"%PDF-1.4\n" + objects + (b"x" * extra_bytes) + b"\n%%EOF\n"


def write_build_asset(
    path: Path,
    *,
    page_count: int | None = None,
    extra_bytes: int = 0,
    fail: bool = False,
    extra_stdout: str = "",
) -> None:
    if fail:
        text = "#!/usr/bin/env bash\nset -euo pipefail\nexit 7\n"
    else:
        text = f"""#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
pdf = Path("main.pdf")
payload = {build_fake_pdf(page_count or 1, extra_bytes=extra_bytes)!r}
pdf.write_bytes(payload)
PY
cat <<'EOF'
{extra_stdout.rstrip()}
EOF
echo "OK: main.pdf"
"""
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)


def write_procedures(path: Path) -> None:
    path.write_text("- P01 Record the main observation.\n", encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_passing_tex(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                r"\documentclass[twocolumn]{article}",
                r"\usepackage[hidelinks]{hyperref}",
                r"\begin{document}",
                r"\begin{abstract}",
                r"This report summarizes the measured optical behavior and the verified discussion.",
                r"\end{abstract}",
                r"\keywords{optics}",
                r"\tableofcontents",
                r"\section{Introduction}",
                r"P01 is covered here.",
                r"\section{Experiment Discussion}",
                r"The result is partially reliable because it is consistent with the theoretical expectation and literature discussion.\cite{opticspaper}",
                r"The deviation is mainly caused by alignment error and instrument uncertainty.",
                r"Further improvement would come from repeated measurements and better alignment.",
                r"\end{document}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def write_failing_tex(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                r"\documentclass{article}",
                r"\begin{document}",
                r"\section{Results}",
                r"TBD: fill this later",
                r"\end{document}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


class FinalizeQCTests(unittest.TestCase):
    def test_run_command_tolerates_non_utf8_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            result = run_command(
                [
                    sys.executable,
                    "-c",
                    (
                        "import sys; "
                        "sys.stdout.buffer.write(b'prefix:\\xe7\\n\\x9a\\x84:suffix'); "
                        "sys.stderr.buffer.write(b'warning')"
                    ),
                ],
                workspace,
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("prefix:", result.stdout)
            self.assertIn("suffix", result.stdout)
            self.assertEqual(result.stderr, "warning")

    def test_refreshes_build_script_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace = root / "report"
            workspace.mkdir()
            asset = root / "build_asset.sh"
            main_tex = workspace / "main.tex"
            procedures = workspace / "procedures.md"
            summary_json = workspace / "final_qc_summary.json"
            summary_md = workspace / "final_qc_summary.md"
            unresolved = workspace / "final_qc_unresolved.md"

            write_build_asset(asset, page_count=24)
            write_passing_tex(main_tex)
            write_procedures(procedures)

            summary = run_finalize_qc(
                main_tex=main_tex,
                procedures=procedures,
                output_summary_json=summary_json,
                output_summary_markdown=summary_md,
                output_unresolved=unresolved,
                build_asset=asset,
            )

            self.assertEqual(summary["build_script_status"], "installed")
            self.assertTrue((workspace / "build.sh").exists())
            self.assertTrue(summary["build_pass"])
            self.assertTrue(summary["qc_pass"])
            self.assertTrue(summary["pdf_size_ok"])
            self.assertTrue(summary["overall_pass"])
            self.assertEqual(summary["pdf_page_count"], 24)

    def test_installed_owned_build_asset_uses_xelatex(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace = root / "report"
            workspace.mkdir()
            main_tex = workspace / "main.tex"
            procedures = workspace / "procedures.md"
            summary_json = workspace / "final_qc_summary.json"
            summary_md = workspace / "final_qc_summary.md"
            unresolved = workspace / "final_qc_unresolved.md"

            write_passing_tex(main_tex)
            write_procedures(procedures)

            run_finalize_qc(
                main_tex=main_tex,
                procedures=procedures,
                output_summary_json=summary_json,
                output_summary_markdown=summary_md,
                output_unresolved=unresolved,
                build_asset=DEFAULT_BUILD_ASSET,
            )

            installed_build = (workspace / "build.sh").read_text(encoding="utf-8")
            self.assertIn("xelatex -interaction=nonstopmode", installed_build)
            self.assertNotIn("pdflatex -interaction=nonstopmode", installed_build)
            self.assertIn("clone_document_from_reader", installed_build)

    def test_compile_failure_records_failure_and_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace = root / "report"
            workspace.mkdir()
            asset = root / "build_asset.sh"
            main_tex = workspace / "main.tex"
            procedures = workspace / "procedures.md"
            summary_json = workspace / "final_qc_summary.json"
            summary_md = workspace / "final_qc_summary.md"
            unresolved = workspace / "final_qc_unresolved.md"

            write_build_asset(asset, fail=True)
            write_passing_tex(main_tex)
            write_procedures(procedures)

            summary = run_finalize_qc(
                main_tex=main_tex,
                procedures=procedures,
                output_summary_json=summary_json,
                output_summary_markdown=summary_md,
                output_unresolved=unresolved,
                build_asset=asset,
            )

            self.assertFalse(summary["build_pass"])
            self.assertFalse(summary["overall_pass"])
            self.assertIn("Compile failed", unresolved.read_text(encoding="utf-8"))

    def test_qc_failure_records_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace = root / "report"
            workspace.mkdir()
            asset = root / "build_asset.sh"
            main_tex = workspace / "main.tex"
            procedures = workspace / "procedures.md"
            summary_json = workspace / "final_qc_summary.json"
            summary_md = workspace / "final_qc_summary.md"
            unresolved = workspace / "final_qc_unresolved.md"

            write_build_asset(asset, page_count=24)
            write_failing_tex(main_tex)
            write_procedures(procedures)

            summary = run_finalize_qc(
                main_tex=main_tex,
                procedures=procedures,
                output_summary_json=summary_json,
                output_summary_markdown=summary_md,
                output_unresolved=unresolved,
                build_asset=asset,
            )

            self.assertTrue(summary["build_pass"])
            self.assertFalse(summary["qc_pass"])
            self.assertFalse(summary["overall_pass"])
            self.assertIn("QC failed", unresolved.read_text(encoding="utf-8"))

    def test_oversized_pdf_records_compress_png_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace = root / "report"
            workspace.mkdir()
            asset = root / "build_asset.sh"
            main_tex = workspace / "main.tex"
            procedures = workspace / "procedures.md"
            summary_json = workspace / "final_qc_summary.json"
            summary_md = workspace / "final_qc_summary.md"
            unresolved = workspace / "final_qc_unresolved.md"

            write_build_asset(asset, page_count=24, extra_bytes=21 * 1024 * 1024)
            write_passing_tex(main_tex)
            write_procedures(procedures)

            summary = run_finalize_qc(
                main_tex=main_tex,
                procedures=procedures,
                output_summary_json=summary_json,
                output_summary_markdown=summary_md,
                output_unresolved=unresolved,
                build_asset=asset,
            )

            self.assertFalse(summary["pdf_size_ok"])
            self.assertFalse(summary["overall_pass"])
            self.assertIn("$compress-png", unresolved.read_text(encoding="utf-8"))

    def test_page_count_outside_band_is_warning_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace = root / "report"
            workspace.mkdir()
            asset = root / "build_asset.sh"
            main_tex = workspace / "main.tex"
            procedures = workspace / "procedures.md"
            summary_json = workspace / "final_qc_summary.json"
            summary_md = workspace / "final_qc_summary.md"
            unresolved = workspace / "final_qc_unresolved.md"

            write_build_asset(asset, page_count=12)
            write_passing_tex(main_tex)
            write_procedures(procedures)

            summary = run_finalize_qc(
                main_tex=main_tex,
                procedures=procedures,
                output_summary_json=summary_json,
                output_summary_markdown=summary_md,
                output_unresolved=unresolved,
                build_asset=asset,
            )

            self.assertTrue(summary["build_pass"])
            self.assertTrue(summary["qc_pass"])
            self.assertTrue(summary["overall_pass"])
            self.assertTrue(summary["page_count_warning"])
            self.assertIn("20-30", unresolved.read_text(encoding="utf-8"))

    def test_build_overflow_warning_fails_qc_and_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace = root / "report"
            workspace.mkdir()
            asset = root / "build_asset.sh"
            main_tex = workspace / "main.tex"
            procedures = workspace / "procedures.md"
            summary_json = workspace / "final_qc_summary.json"
            summary_md = workspace / "final_qc_summary.md"
            unresolved = workspace / "final_qc_unresolved.md"

            write_build_asset(
                asset,
                page_count=24,
                extra_stdout="Overfull \\\\hbox (36.76004pt too wide) in paragraph at lines 615--632",
            )
            write_passing_tex(main_tex)
            write_procedures(procedures)

            summary = run_finalize_qc(
                main_tex=main_tex,
                procedures=procedures,
                output_summary_json=summary_json,
                output_summary_markdown=summary_md,
                output_unresolved=unresolved,
                build_asset=asset,
            )

            self.assertTrue(summary["build_pass"])
            self.assertFalse(summary["qc_pass"])
            self.assertFalse(summary["overall_pass"])
            self.assertIn("Overfull \\\\hbox", "\n".join(summary.get("build_layout_issues", [])))
            self.assertIn("layout diagnostic", unresolved.read_text(encoding="utf-8"))

    def test_inner_qc_crash_surfaces_stderr_in_unresolved_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace = root / "report"
            workspace.mkdir()
            asset = root / "build_asset.sh"
            main_tex = workspace / "main.tex"
            missing_procedures = workspace / "missing_procedures.md"
            summary_json = workspace / "final_qc_summary.json"
            summary_md = workspace / "final_qc_summary.md"
            unresolved = workspace / "final_qc_unresolved.md"

            write_build_asset(asset, page_count=24)
            write_passing_tex(main_tex)

            summary = run_finalize_qc(
                main_tex=main_tex,
                procedures=missing_procedures,
                output_summary_json=summary_json,
                output_summary_markdown=summary_md,
                output_unresolved=unresolved,
                build_asset=asset,
            )

            self.assertFalse(summary["qc_pass"])
            self.assertIn("FileNotFoundError", summary["qc_stderr"])
            self.assertIn("FileNotFoundError", unresolved.read_text(encoding="utf-8"))

    def test_reference_comparison_runs_only_after_earlier_qc_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace = root / "report"
            workspace.mkdir()
            asset = root / "build_asset.sh"
            main_tex = workspace / "main.tex"
            procedures = workspace / "procedures.md"
            discovery = workspace / "discovery.json"
            summary_json = workspace / "final_qc_summary.json"
            summary_md = workspace / "final_qc_summary.md"
            unresolved = workspace / "final_qc_unresolved.md"

            write_build_asset(asset, fail=True)
            write_passing_tex(main_tex)
            write_procedures(procedures)
            write_json(discovery, {"reference_selection_status": "selected", "selected_reference_reports": []})

            summary = run_finalize_qc(
                main_tex=main_tex,
                procedures=procedures,
                discovery_json=discovery,
                output_summary_json=summary_json,
                output_summary_markdown=summary_md,
                output_unresolved=unresolved,
                build_asset=asset,
            )

            self.assertFalse(summary["build_pass"])
            self.assertFalse(summary["reference_procedure_comparison"].get("enabled"))

    def test_reference_comparison_failure_is_reported_in_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace = root / "report"
            workspace.mkdir()
            asset = root / "build_asset.sh"
            main_tex = workspace / "main.tex"
            procedures = workspace / "procedures.md"
            discovery = workspace / "discovery.json"
            reference_md = workspace / "reference.md"
            summary_json = workspace / "final_qc_summary.json"
            summary_md = workspace / "final_qc_summary.md"
            unresolved = workspace / "final_qc_unresolved.md"

            write_build_asset(asset, page_count=24)
            write_passing_tex(main_tex)
            write_procedures(procedures)
            reference_md.write_text("# 电光调制\n\n## 实验步骤\n\n### 观察倍频失真并测量线性工作区\n", encoding="utf-8")
            write_json(
                discovery,
                {
                    "reference_selection_status": "selected",
                    "selected_reference_reports": [
                        {
                            "pdf_path": str(workspace / "reference.pdf"),
                            "expected_decoded_markdown_path": str(reference_md),
                        }
                    ],
                },
            )

            summary = run_finalize_qc(
                main_tex=main_tex,
                procedures=procedures,
                discovery_json=discovery,
                output_summary_json=summary_json,
                output_summary_markdown=summary_md,
                output_unresolved=unresolved,
                build_asset=asset,
            )

            self.assertFalse(summary["overall_pass"])
            self.assertFalse(summary["reference_procedure_comparison_pass"])
            self.assertIn("recommended_reroutes", summary)
            self.assertIn("reference procedure", unresolved.read_text(encoding="utf-8").lower())

    def test_none_found_reference_selection_records_neutral_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace = root / "report"
            workspace.mkdir()
            asset = root / "build_asset.sh"
            main_tex = workspace / "main.tex"
            procedures = workspace / "procedures.md"
            discovery = workspace / "discovery.json"
            summary_json = workspace / "final_qc_summary.json"
            summary_md = workspace / "final_qc_summary.md"
            unresolved = workspace / "final_qc_unresolved.md"

            write_build_asset(asset, page_count=24)
            write_passing_tex(main_tex)
            write_procedures(procedures)
            write_json(discovery, {"reference_selection_status": "none_found", "selected_reference_reports": []})

            summary = run_finalize_qc(
                main_tex=main_tex,
                procedures=procedures,
                discovery_json=discovery,
                output_summary_json=summary_json,
                output_summary_markdown=summary_md,
                output_unresolved=unresolved,
                build_asset=asset,
            )

            self.assertTrue(summary["overall_pass"])
            self.assertFalse(summary["reference_procedure_comparison_pass"])
            self.assertFalse(summary["reference_procedure_comparison_blocked"])
            self.assertEqual(summary["reference_procedure_comparison"]["selection_status"], "none_found")

    def test_ambiguous_reference_selection_reroutes_to_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace = root / "report"
            workspace.mkdir()
            asset = root / "build_asset.sh"
            main_tex = workspace / "main.tex"
            procedures = workspace / "procedures.md"
            discovery = workspace / "discovery.json"
            summary_json = workspace / "final_qc_summary.json"
            summary_md = workspace / "final_qc_summary.md"
            unresolved = workspace / "final_qc_unresolved.md"

            write_build_asset(asset, page_count=24)
            write_passing_tex(main_tex)
            write_procedures(procedures)
            write_json(discovery, {"reference_selection_status": "ambiguous", "selected_reference_reports": []})

            summary = run_finalize_qc(
                main_tex=main_tex,
                procedures=procedures,
                discovery_json=discovery,
                output_summary_json=summary_json,
                output_summary_markdown=summary_md,
                output_unresolved=unresolved,
                build_asset=asset,
            )

            self.assertFalse(summary["overall_pass"])
            self.assertTrue(summary["reference_procedure_comparison_blocked"])
            self.assertEqual(summary["recommended_reroutes"][0]["target_skill"], "course-lab-discovery")

    def test_declared_unresolved_reference_gap_still_produces_visible_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace = root / "report"
            workspace.mkdir()
            asset = root / "build_asset.sh"
            main_tex = workspace / "main.tex"
            procedures = workspace / "procedures.md"
            discovery = workspace / "discovery.json"
            reference_md = workspace / "reference.md"
            summary_json = workspace / "final_qc_summary.json"
            summary_md = workspace / "final_qc_summary.md"
            unresolved = workspace / "final_qc_unresolved.md"

            write_build_asset(asset, page_count=24)
            write_procedures(procedures)
            main_tex.write_text(
                "\n".join(
                    [
                        r"\documentclass[twocolumn]{article}",
                        r"\usepackage[hidelinks]{hyperref}",
                        r"\begin{document}",
                        r"\begin{abstract}",
                        r"Short abstract.",
                        r"\end{abstract}",
                        r"\keywords{optics}",
                        r"\tableofcontents",
                        r"\section{Introduction}",
                        r"P01 is covered here.",
                        r"\section{实验结果}",
                        r"\subsection{观察倍频失真并测量线性工作区}",
                        r"\NeedsInput{Missing waveform data prevents completion of this lane.}",
                        r"\section{Experiment Discussion}",
                        r"The result is partially reliable because it is consistent with theory.\cite{opticspaper}",
                        r"The deviation is mainly caused by instrument uncertainty.",
                        r"Further improvement would come from repeated measurements.",
                        r"\end{document}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            reference_md.write_text("# 电光调制\n\n## 实验结果\n\n### 观察倍频失真并测量线性工作区\n", encoding="utf-8")
            write_json(
                discovery,
                {
                    "reference_selection_status": "selected",
                    "selected_reference_reports": [
                        {
                            "pdf_path": str(workspace / "reference.pdf"),
                            "expected_decoded_markdown_path": str(reference_md),
                        }
                    ],
                },
            )

            summary = run_finalize_qc(
                main_tex=main_tex,
                procedures=procedures,
                discovery_json=discovery,
                output_summary_json=summary_json,
                output_summary_markdown=summary_md,
                output_unresolved=unresolved,
                build_asset=asset,
            )

            self.assertEqual(len(summary["reference_procedure_comparison"]["declared_unresolved_items"]), 1)
            self.assertIn("warning", unresolved.read_text(encoding="utf-8").lower())

    def test_data_lack_suspected_gap_still_fails_final_qc(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace = root / "report"
            workspace.mkdir()
            asset = root / "build_asset.sh"
            main_tex = workspace / "main.tex"
            procedures = workspace / "procedures.md"
            discovery = workspace / "discovery.json"
            reference_md = workspace / "reference.md"
            summary_json = workspace / "final_qc_summary.json"
            summary_md = workspace / "final_qc_summary.md"
            unresolved = workspace / "final_qc_unresolved.md"

            write_build_asset(asset, page_count=24)
            write_procedures(procedures)
            main_tex.write_text(
                "\n".join(
                    [
                        r"\documentclass[twocolumn]{article}",
                        r"\usepackage[hidelinks]{hyperref}",
                        r"\begin{document}",
                        r"\begin{abstract}",
                        r"Short abstract.",
                        r"\end{abstract}",
                        r"\keywords{optics}",
                        r"\tableofcontents",
                        r"\section{Introduction}",
                        r"P01 is covered here.",
                        r"\section{实验结果}",
                        r"\subsection{观察倍频失真并测量线性工作区}",
                        r"由于本次实验没有保存可用的波形数据，这一部分尚不能完成。",
                        r"\section{Experiment Discussion}",
                        r"The result is partially reliable because it is consistent with theory.\cite{opticspaper}",
                        r"The deviation is mainly caused by instrument uncertainty.",
                        r"Further improvement would come from repeated measurements.",
                        r"\end{document}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            reference_md.write_text("# 电光调制\n\n## 实验结果\n\n### 观察倍频失真并测量线性工作区\n", encoding="utf-8")
            write_json(
                discovery,
                {
                    "reference_selection_status": "selected",
                    "selected_reference_reports": [
                        {
                            "pdf_path": str(workspace / "reference.pdf"),
                            "expected_decoded_markdown_path": str(reference_md),
                        }
                    ],
                },
            )

            summary = run_finalize_qc(
                main_tex=main_tex,
                procedures=procedures,
                discovery_json=discovery,
                output_summary_json=summary_json,
                output_summary_markdown=summary_md,
                output_unresolved=unresolved,
                build_asset=asset,
            )

            self.assertFalse(summary["overall_pass"])
            self.assertEqual(len(summary["reference_procedure_comparison"]["data_lack_suspected_items"]), 1)
            self.assertIn("warning", unresolved.read_text(encoding="utf-8").lower())


if __name__ == "__main__":
    unittest.main()
