from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
import sys

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from reference_procedure_compare import compare_reference_procedure_coverage  # type: ignore


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class ReferenceProcedureCompareTests(unittest.TestCase):
    def test_experiment_results_heading_alias_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            markdown = root / "reference.md"
            markdown.write_text(
                "# 电光调制\n\n## 实验结果\n\n### 观察倍频失真并测量线性工作区\n\n记录倍频失真与线性工作区。\n",
                encoding="utf-8",
            )
            main_tex = root / "main.tex"
            main_tex.write_text(
                "\\section{实验结果}\n\\subsection{观察倍频失真并测量线性工作区}\n记录倍频失真与线性工作区。\n",
                encoding="utf-8",
            )
            discovery = root / "discovery.json"
            write_json(
                discovery,
                {
                    "reference_selection_status": "selected",
                    "selected_reference_reports": [
                        {
                            "pdf_path": str(root / "reference.pdf"),
                            "expected_decoded_markdown_path": str(markdown),
                        }
                    ],
                },
            )

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertTrue(summary["pass"])
            self.assertEqual(summary["missing_content_items"], [])

    def test_missing_markdown_is_blocking_reroute(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main_tex = root / "main.tex"
            main_tex.write_text("\\section{实验步骤}\nAlready present.\n", encoding="utf-8")
            discovery = root / "discovery.json"
            write_json(
                discovery,
                {
                    "reference_selection_status": "selected",
                    "selected_reference_reports": [
                        {
                            "pdf_path": str(root / "reference.pdf"),
                            "expected_decoded_markdown_path": str(root / "missing-reference.md"),
                        }
                    ],
                },
            )

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertFalse(summary["pass"])
            self.assertTrue(summary["blocked"])
            self.assertEqual(summary["blocked_reference_decode_items"][0]["target_skill"], "course-lab-handout-normalization")

    def test_malformed_discovery_contract_blocks_with_discovery_reroute(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main_tex = root / "main.tex"
            main_tex.write_text("\\section{实验步骤}\n", encoding="utf-8")
            discovery = root / "discovery.json"
            write_json(discovery, {"selected_reference_reports": []})

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertFalse(summary["pass"])
            self.assertTrue(summary["blocked"])
            self.assertEqual(summary["recommended_reroutes"][0]["target_skill"], "course-lab-discovery")

    def test_missing_heading_lane_reroutes_to_body_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            markdown = root / "reference.md"
            markdown.write_text(
                "# 电光调制\n\n## 实验步骤\n\n### 调节黑十字图样水平\n\n通过旋转偏振片调节黑十字图样水平。\n",
                encoding="utf-8",
            )
            main_tex = root / "main.tex"
            main_tex.write_text("\\section{实验步骤}\n只保留了总标题，没有对应子节。\n", encoding="utf-8")
            discovery = root / "discovery.json"
            write_json(
                discovery,
                {
                    "reference_selection_status": "selected",
                    "selected_reference_reports": [
                        {
                            "pdf_path": str(root / "reference.pdf"),
                            "expected_decoded_markdown_path": str(markdown),
                        }
                    ],
                },
            )

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertFalse(summary["pass"])
            self.assertEqual(summary["missing_structure_items"][0]["target_skill"], "course-lab-body-scaffold")

    def test_present_heading_but_thin_lane_reroutes_to_final_staging(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            markdown = root / "reference.md"
            markdown.write_text(
                "# 电光调制\n\n## 实验结果\n\n### 观察倍频失真并测量线性工作区\n\n记录倍频失真与线性工作区。\n",
                encoding="utf-8",
            )
            main_tex = root / "main.tex"
            main_tex.write_text(
                "\\section{实验结果}\n\\subsection{观察倍频失真并测量线性工作区}\n只写了一个非常短的占位句子。\n",
                encoding="utf-8",
            )
            discovery = root / "discovery.json"
            write_json(
                discovery,
                {
                    "reference_selection_status": "selected",
                    "selected_reference_reports": [
                        {
                            "pdf_path": str(root / "reference.pdf"),
                            "expected_decoded_markdown_path": str(markdown),
                        }
                    ],
                },
            )

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertFalse(summary["pass"])
            self.assertEqual(summary["missing_content_items"][0]["target_skill"], "course-lab-final-staging")

    def test_local_input_files_are_expanded_before_matching(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            markdown = root / "reference.md"
            markdown.write_text(
                "# 电光调制\n\n## 实验步骤\n\n### 调节偏振片正交并观测黑十字干涉条纹\n\n记录黑十字干涉条纹。\n",
                encoding="utf-8",
            )
            included = root / "sections" / "procedure.tex"
            included.parent.mkdir(parents=True, exist_ok=True)
            included.write_text(
                "\\subsection{调节偏振片正交并观测黑十字干涉条纹}\n记录黑十字干涉条纹。\n",
                encoding="utf-8",
            )
            main_tex = root / "main.tex"
            main_tex.write_text("\\section{实验步骤}\n\\input{sections/procedure}\n", encoding="utf-8")
            discovery = root / "discovery.json"
            write_json(
                discovery,
                {
                    "reference_selection_status": "selected",
                    "selected_reference_reports": [
                        {
                            "pdf_path": str(root / "reference.pdf"),
                            "expected_decoded_markdown_path": str(markdown),
                        }
                    ],
                },
            )

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertTrue(summary["pass"])
            self.assertEqual(summary["missing_structure_items"], [])

    def test_numbered_heading_alias_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            markdown = root / "reference.md"
            markdown.write_text(
                "# 电光调制\n\n## 5. 实验步骤\n\n### 5.2.3 观察倍频失真并测量线性工作区\n\n记录倍频失真与线性工作区。\n",
                encoding="utf-8",
            )
            main_tex = root / "main.tex"
            main_tex.write_text(
                "\\section{实验步骤}\n\\subsection{观察倍频失真并测量线性工作区}\n记录倍频失真与线性工作区。\n",
                encoding="utf-8",
            )
            discovery = root / "discovery.json"
            write_json(
                discovery,
                {
                    "reference_selection_status": "selected",
                    "selected_reference_reports": [
                        {
                            "pdf_path": str(root / "reference.pdf"),
                            "expected_decoded_markdown_path": str(markdown),
                        }
                    ],
                },
            )

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertTrue(summary["pass"])
            self.assertEqual(summary["missing_structure_items"], [])

    def test_body_anchor_only_extraction_matches_report_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            markdown = root / "reference.md"
            markdown.write_text(
                "# 电光调制\n\n## 实验步骤\n\n- 调节滑轨激光器远近点使其与导轨水平。\n",
                encoding="utf-8",
            )
            main_tex = root / "main.tex"
            main_tex.write_text(
                "\\section{实验步骤}\n我们调节滑轨激光器远近点，使其与导轨保持水平。\n",
                encoding="utf-8",
            )
            discovery = root / "discovery.json"
            write_json(
                discovery,
                {
                    "reference_selection_status": "selected",
                    "selected_reference_reports": [
                        {
                            "pdf_path": str(root / "reference.pdf"),
                            "expected_decoded_markdown_path": str(markdown),
                        }
                    ],
                },
            )

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertTrue(summary["pass"])
            self.assertEqual(summary["missing_content_items"], [])

    def test_needsinput_marker_can_be_declared_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            markdown = root / "reference.md"
            markdown.write_text(
                "# 电光调制\n\n## 实验结果\n\n### 观察倍频失真并测量线性工作区\n\n记录倍频失真与线性工作区。\n",
                encoding="utf-8",
            )
            main_tex = root / "main.tex"
            main_tex.write_text(
                "\\section{实验结果}\n\\subsection{观察倍频失真并测量线性工作区}\n\\NeedsInput{This lane is still blocked because the required waveform data is missing.}\n",
                encoding="utf-8",
            )
            discovery = root / "discovery.json"
            write_json(
                discovery,
                {
                    "reference_selection_status": "selected",
                    "selected_reference_reports": [
                        {
                            "pdf_path": str(root / "reference.pdf"),
                            "expected_decoded_markdown_path": str(markdown),
                        }
                    ],
                },
            )

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertFalse(summary["pass"])
            self.assertEqual(summary["missing_content_items"], [])
            self.assertEqual(len(summary["declared_unresolved_items"]), 1)
            self.assertEqual(summary["declared_unresolved_items"][0]["target_skill"], "course-lab-final-staging")

    def test_ambiguous_selection_reroutes_back_to_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main_tex = root / "main.tex"
            main_tex.write_text("\\section{实验结果}\n", encoding="utf-8")
            discovery = root / "discovery.json"
            write_json(
                discovery,
                {
                    "reference_selection_status": "ambiguous",
                    "selected_reference_reports": [],
                },
            )

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertFalse(summary["pass"])
            self.assertTrue(summary["blocked"])
            self.assertEqual(summary["recommended_reroutes"][0]["target_skill"], "course-lab-discovery")

    def test_comparison_gap_reroutes_to_results_interpretation_when_lane_exists_but_has_no_theory_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            markdown = root / "reference.md"
            markdown.write_text(
                "# 电光调制\n\n## 实验结果\n\n### 计算电光系数并与理论值做比较\n\n根据测得的半波电压计算电光系数，并与理论值做比较。\n",
                encoding="utf-8",
            )
            main_tex = root / "main.tex"
            main_tex.write_text(
                "\\section{实验结果}\n\\subsection{计算电光系数并与理论值做比较}\n我们根据测得的半波电压计算了电光系数。\n",
                encoding="utf-8",
            )
            discovery = root / "discovery.json"
            write_json(
                discovery,
                {
                    "reference_selection_status": "selected",
                    "selected_reference_reports": [
                        {
                            "pdf_path": str(root / "reference.pdf"),
                            "expected_decoded_markdown_path": str(markdown),
                        }
                    ],
                },
            )

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertFalse(summary["pass"])
            self.assertEqual(summary["missing_content_items"][0]["target_skill"], "course-lab-results-interpretation")

    def test_unmarked_data_gap_is_classified_as_data_lack_suspected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            markdown = root / "reference.md"
            markdown.write_text(
                "# 电光调制\n\n## 实验结果\n\n### 观察倍频失真并测量线性工作区\n\n记录倍频失真与线性工作区。\n",
                encoding="utf-8",
            )
            main_tex = root / "main.tex"
            main_tex.write_text(
                "\\section{实验结果}\n\\subsection{观察倍频失真并测量线性工作区}\n由于本次实验没有保存可用的波形数据，这一部分尚不能完成。\n",
                encoding="utf-8",
            )
            discovery = root / "discovery.json"
            write_json(
                discovery,
                {
                    "reference_selection_status": "selected",
                    "selected_reference_reports": [
                        {
                            "pdf_path": str(root / "reference.pdf"),
                            "expected_decoded_markdown_path": str(markdown),
                        }
                    ],
                },
            )

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertFalse(summary["pass"])
            self.assertEqual(summary["missing_content_items"], [])
            self.assertEqual(len(summary["data_lack_suspected_items"]), 1)

    def test_unresolved_include_resolution_becomes_visible_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            markdown = root / "reference.md"
            markdown.write_text("# 电光调制\n\n## 实验步骤\n\n### 调节偏振片\n", encoding="utf-8")
            main_tex = root / "main.tex"
            main_tex.write_text("\\section{实验步骤}\n\\input{sections/missing-procedure}\n", encoding="utf-8")
            discovery = root / "discovery.json"
            write_json(
                discovery,
                {
                    "reference_selection_status": "selected",
                    "selected_reference_reports": [
                        {
                            "pdf_path": str(root / "reference.pdf"),
                            "expected_decoded_markdown_path": str(markdown),
                        }
                    ],
                },
            )

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertFalse(summary["pass"])
            self.assertTrue(summary["blocked"])
            self.assertEqual(summary["recommended_reroutes"][0]["target_skill"], "course-lab-final-staging")


if __name__ == "__main__":
    unittest.main()
