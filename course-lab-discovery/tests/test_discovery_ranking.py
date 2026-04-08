import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from common import HANDOUT_LIBRARY_ROOT, PIC_RESULT_ROOT, REFERENCE_LIBRARY_ROOT, expand_query_variants  # noqa: E402
from discover_sources import (  # noqa: E402
    data_candidates,
    decoded_candidates,
    picture_result_dir_candidates,
    reference_selection_payload,
    score_paths,
    simulation_dir_candidates,
    simulation_file_candidates,
    top_or_all,
    template_groups,
)


class DiscoveryRankingTests(unittest.TestCase):
    def make_data_tree(self) -> Path:
        temp_root = Path(tempfile.mkdtemp())

        mechanics_root = temp_root / "Introductory Physics Experiments for Undergraduates: discovery" / "mechanics"
        (mechanics_root / "LX2" / "fuji_measurements" / "source_exports").mkdir(parents=True)
        (mechanics_root / "LX2" / "fuji_measurements" / "source_images").mkdir(parents=True)

        for name in (
            "case1-f=1.8308kHz,m=0,n=4_measured.csv",
            "case2-f=4.3169kHz,m=7,n=3_measured.csv",
            "case3-f=5.7848kHz,m=4,n=5_measured.csv",
            "case4-f=6.3054kHz,m=5,n=5_measured.csv",
            "case5-f=11.165kHz,m=6,n=7_measured.csv",
        ):
            (mechanics_root / "LX2" / "fuji_measurements" / name).write_text("x,y\n1,2\n", encoding="utf-8")

        for name in (
            "case4-f=6.3054kHz,m=5,n=5_full_export.csv",
            "case5-f=11.165kHz,m=6,n=7_full_export.csv",
        ):
            (mechanics_root / "LX2" / "fuji_measurements" / "source_exports" / name).write_text(
                "x,y\n1,2\n",
                encoding="utf-8",
            )

        (mechanics_root / "mechanics-data.pdf").write_text("% scanned data pages\n", encoding="utf-8")
        for name in (
            "case1-f=1.8308kHz,m=0,n=4_measured.PNG",
            "case2-f=4.3169kHz,m=7,n=3_measured.PNG",
        ):
            (mechanics_root / "LX2" / "fuji_measurements" / "source_images" / name).write_text(
                "fake image bytes\n",
                encoding="utf-8",
            )

        optics_root = temp_root / "Modern Physics Experiments"
        optics_root.mkdir(parents=True)
        (optics_root / "crystal_optics_data.pdf").write_text("% unrelated data\n", encoding="utf-8")

        self.addCleanup(lambda: __import__("shutil").rmtree(temp_root))
        return temp_root

    def make_template_tree(self) -> Path:
        temp_root = Path(tempfile.mkdtemp())

        english_root = temp_root / "english"
        english_root.mkdir()
        (english_root / "tau_templet copy.tex").write_text("% english template\n", encoding="utf-8")
        (english_root / "dont use").mkdir()
        (english_root / "dont use" / "tau_templet.tex").write_text("% excluded english template\n", encoding="utf-8")

        chinese_root = temp_root / "chinese"
        chinese_root.mkdir()
        chinese_bundle = chinese_root / "Rho_Class___Research_Article_Template_CN"
        chinese_bundle.mkdir()
        (chinese_bundle / "main.tex").write_text("% chinese bundle main\n", encoding="utf-8")
        (chinese_bundle / "rho.bib").write_text("% bundle bib\n", encoding="utf-8")
        (chinese_root / "dont use").mkdir()
        excluded_bundle = chinese_root / "dont use" / "Legacy_CN_Template"
        excluded_bundle.mkdir()
        (excluded_bundle / "main.tex").write_text("% excluded chinese bundle\n", encoding="utf-8")

        self.addCleanup(lambda: __import__("shutil").rmtree(temp_root))
        return temp_root

    def test_expand_query_variants_does_not_hardcode_translation(self) -> None:
        self.assertEqual(
            expand_query_variants("Modern Physics Experiments crystal optics"),
            ["Modern Physics Experiments crystal optics"],
        )

    def test_chinese_crystal_optics_handout_ranks_above_unrelated_handout(self) -> None:
        paths = [
            Path("/root/grassman_projects/AI_works/resources/experiment_handout/Modern Physics Experiments/4-1 晶体光学性质的观测分析.pdf"),
            Path("/root/grassman_projects/AI_works/resources/experiment_handout/Modern Physics Experiments/2-1 塞曼效应.pdf"),
        ]

        ranked = score_paths("晶体光学性质", paths, library_root=HANDOUT_LIBRARY_ROOT)

        self.assertEqual(Path(ranked[0].path).name, "4-1 晶体光学性质的观测分析.pdf")
        self.assertGreater(ranked[0].score, ranked[1].score)

    def test_chinese_crystal_optics_decoded_json_ranks_above_unrelated_decoded_json(self) -> None:
        ranked = decoded_candidates(HANDOUT_LIBRARY_ROOT, "晶体光学性质", 5)

        self.assertEqual(Path(ranked[0]["path"]).name, "晶体光学性质.json")

    def test_chinese_crystal_optics_reference_ranks_above_unrelated_reference(self) -> None:
        paths = [
            Path("/root/grassman_projects/AI_works/resources/lab_report_reference/Modern Physics Experiments/272842_sysut_23355030 贾儒恺 晶体光学.pdf"),
            Path("/root/grassman_projects/AI_works/resources/lab_report_reference/Modern Physics Experiments/23355030贾儒恺_光泵磁共振.pdf"),
        ]

        ranked = score_paths("晶体光学", paths, library_root=REFERENCE_LIBRARY_ROOT)

        self.assertEqual(Path(ranked[0].path).name, "272842_sysut_23355030 贾儒恺 晶体光学.pdf")
        self.assertGreater(ranked[0].score, ranked[1].score)

    def test_selected_reference_reports_include_all_strong_same_experiment_matches(self) -> None:
        temp_root = Path(tempfile.mkdtemp())
        course_root = temp_root / "Modern Physics Experiments"
        course_root.mkdir(parents=True)
        for name in (
            "279964_sysut_23355030 A 电光调制.pdf",
            "300001_sysut_23355030 B 电光调制.pdf",
            "23355030贾儒恺_光泵磁共振.pdf",
        ):
            (course_root / name).write_text("% pdf\n", encoding="utf-8")

        self.addCleanup(lambda: __import__("shutil").rmtree(temp_root))

        with mock.patch("discover_sources.REFERENCE_LIBRARY_ROOT", temp_root):
            payload = reference_selection_payload("现代物理实验 电光调制")

        self.assertEqual(payload["reference_selection_status"], "selected")
        selected = payload["selected_reference_reports"]
        self.assertEqual(len(selected), 2)
        self.assertTrue(all(item["pdf_path"].endswith(".pdf") for item in selected))
        self.assertTrue(all("电光调制" in Path(item["pdf_path"]).name for item in selected))

    def test_reference_selection_status_distinguishes_ambiguous_from_none_found(self) -> None:
        temp_root = Path(tempfile.mkdtemp())
        course_root = temp_root / "Modern Physics Experiments"
        course_root.mkdir(parents=True)
        (course_root / "vague optics note.pdf").write_text("% pdf\n", encoding="utf-8")

        self.addCleanup(lambda: __import__("shutil").rmtree(temp_root))

        with mock.patch("discover_sources.REFERENCE_LIBRARY_ROOT", temp_root):
            payload = reference_selection_payload("Electro-Optic Modulation")

        self.assertIn(payload["reference_selection_status"], {"ambiguous", "none_found"})
        self.assertEqual(payload["selected_reference_reports"], [])

    def test_selected_reference_reports_expose_expected_decode_paths(self) -> None:
        temp_root = Path(tempfile.mkdtemp())
        course_root = temp_root / "Modern Physics Experiments"
        course_root.mkdir(parents=True)
        pdf_path = course_root / "279964_sysut_23355030 A 电光调制.pdf"
        pdf_path.write_text("% pdf\n", encoding="utf-8")

        self.addCleanup(lambda: __import__("shutil").rmtree(temp_root))

        with mock.patch("discover_sources.REFERENCE_LIBRARY_ROOT", temp_root):
            payload = reference_selection_payload("电光调制")

        item = payload["selected_reference_reports"][0]
        self.assertTrue(item["expected_decoded_markdown_path"].endswith(".md"))
        self.assertTrue(item["expected_decoded_json_path"].endswith(".json"))
        self.assertIn("pdf_markdown", item["expected_decoded_markdown_path"])
        self.assertIn("pdf_decoded", item["expected_decoded_json_path"])

    def test_selected_reference_reports_are_not_truncated_by_max_results(self) -> None:
        temp_root = Path(tempfile.mkdtemp())
        course_root = temp_root / "Modern Physics Experiments"
        course_root.mkdir(parents=True)
        for name in (
            "279964_sysut_23355030 A 电光调制.pdf",
            "300001_sysut_23355030 B 电光调制.pdf",
            "300002_sysut_23355030 C 电光调制.pdf",
        ):
            (course_root / name).write_text("% pdf\n", encoding="utf-8")

        self.addCleanup(lambda: __import__("shutil").rmtree(temp_root))

        with mock.patch("discover_sources.REFERENCE_LIBRARY_ROOT", temp_root):
            ranked = top_or_all(
                score_paths(
                    "电光调制",
                    list(course_root.glob("*.pdf")),
                    library_root=temp_root,
                ),
                1,
            )
            payload = reference_selection_payload("电光调制")

        self.assertEqual(len(ranked), 1)
        self.assertEqual(payload["reference_selection_status"], "selected")
        self.assertEqual(len(payload["selected_reference_reports"]), 3)

    def test_selected_reference_reports_exclude_weak_unrelated_candidates(self) -> None:
        temp_root = Path(tempfile.mkdtemp())
        course_root = temp_root / "Modern Physics Experiments"
        course_root.mkdir(parents=True)
        for name in (
            "279964_sysut_23355030 A 电光调制.pdf",
            "300001_sysut_23355030 B 电光调制.pdf",
            "optics modulation note 光学调制综述.pdf",
        ):
            (course_root / name).write_text("% pdf\n", encoding="utf-8")

        self.addCleanup(lambda: __import__("shutil").rmtree(temp_root))

        with mock.patch("discover_sources.REFERENCE_LIBRARY_ROOT", temp_root):
            payload = reference_selection_payload("电光调制")

        selected_names = {Path(item["pdf_path"]).name for item in payload["selected_reference_reports"]}
        self.assertEqual(payload["reference_selection_status"], "selected")
        self.assertIn("279964_sysut_23355030 A 电光调制.pdf", selected_names)
        self.assertIn("300001_sysut_23355030 B 电光调制.pdf", selected_names)
        self.assertNotIn("optics modulation note 光学调制综述.pdf", selected_names)

    def test_picture_result_directory_prefers_experiment_named_folder(self) -> None:
        ranked = picture_result_dir_candidates("crystal optics", 5)

        self.assertEqual(
            Path(ranked[0]["path"]).name,
            "cryastal optics picture reports_categorised",
        )
        self.assertTrue(Path(ranked[0]["path"]).is_relative_to(PIC_RESULT_ROOT))

    def test_simulation_directory_finds_lx2_result_folder(self) -> None:
        ranked = simulation_dir_candidates("lx2", 5)

        self.assertIsInstance(ranked, list)
        self.assertEqual(Path(ranked[0]["path"]).name, "lx2_mathematica_simulation")

    def test_simulation_file_finds_wolfram_language_source(self) -> None:
        ranked = simulation_file_candidates("lx2", 5)

        self.assertIsInstance(ranked, list)
        self.assertEqual(Path(ranked[0]["path"]).name, "lx2_plate_simulation.wl")

    def test_unrelated_query_reports_simulation_not_exist(self) -> None:
        self.assertEqual(simulation_dir_candidates("crystal optics", 5), "not exist")
        self.assertEqual(simulation_file_candidates("crystal optics", 5), "not exist")

    def test_data_candidates_include_all_csvs_for_multi_file_experiment_bundle(self) -> None:
        data_root = self.make_data_tree()

        with mock.patch("discover_sources.DATA_ROOT", data_root):
            data_files, data_groups = data_candidates("mechanics", 4)

        csv_names = {
            Path(item["path"]).name
            for item in data_files
            if Path(item["path"]).suffix.lower() == ".csv"
        }
        self.assertEqual(
            csv_names,
            {
                "case1-f=1.8308kHz,m=0,n=4_measured.csv",
                "case2-f=4.3169kHz,m=7,n=3_measured.csv",
                "case3-f=5.7848kHz,m=4,n=5_measured.csv",
                "case4-f=6.3054kHz,m=5,n=5_measured.csv",
                "case5-f=11.165kHz,m=6,n=7_measured.csv",
                "case4-f=6.3054kHz,m=5,n=5_full_export.csv",
                "case5-f=11.165kHz,m=6,n=7_full_export.csv",
            },
        )
        self.assertGreater(len(csv_names), 4)
        self.assertEqual(len(data_groups), 1)
        self.assertEqual(Path(data_groups[0]["path"]).name, "mechanics")
        self.assertEqual(len(data_groups[0]["csv_files"]), 7)
        self.assertEqual(len(data_groups[0]["scan_files"]), 3)

    def test_template_groups_include_english_single_tex_and_chinese_bundle(self) -> None:
        template_root = self.make_template_tree()

        with mock.patch("discover_sources.TEMPLATE_ROOT", template_root):
            templates, excluded_templates = template_groups()

        self.assertEqual(set(templates.keys()), {"english", "chinese"})

        english_template = templates["english"][0]
        self.assertEqual(english_template["template_language"], "english")
        self.assertEqual(english_template["template_kind"], "single_tex")
        self.assertEqual(english_template["template_root"], str(template_root / "english" / "tau_templet copy.tex"))
        self.assertEqual(english_template["template_entry"], str(template_root / "english" / "tau_templet copy.tex"))

        chinese_template = templates["chinese"][0]
        self.assertEqual(chinese_template["template_language"], "chinese")
        self.assertEqual(chinese_template["template_kind"], "bundle")
        self.assertEqual(chinese_template["template_root"], str(template_root / "chinese" / "Rho_Class___Research_Article_Template_CN"))
        self.assertEqual(chinese_template["template_entry"], str(template_root / "chinese" / "Rho_Class___Research_Article_Template_CN" / "main.tex"))
        self.assertNotEqual(chinese_template["label"], "main.tex")

        included_paths = {item["template_entry"] for group in templates.values() for item in group}
        self.assertNotIn(str(template_root / "english" / "dont use" / "tau_templet.tex"), included_paths)
        self.assertNotIn(
            str(template_root / "chinese" / "dont use" / "Legacy_CN_Template" / "main.tex"),
            included_paths,
        )
        self.assertEqual(excluded_templates["english"][0]["template_entry"], str(template_root / "english" / "dont use" / "tau_templet.tex"))
        self.assertEqual(
            excluded_templates["chinese"][0]["template_entry"],
            str(template_root / "chinese" / "dont use" / "Legacy_CN_Template" / "main.tex"),
        )

    def test_template_groups_filter_to_requested_language(self) -> None:
        template_root = self.make_template_tree()

        with mock.patch("discover_sources.TEMPLATE_ROOT", template_root):
            templates, excluded_templates = template_groups("english")

        self.assertEqual(set(templates.keys()), {"english"})
        self.assertEqual(set(excluded_templates.keys()), {"english"})
        self.assertEqual(templates["english"][0]["template_language"], "english")


if __name__ == "__main__":
    unittest.main()
