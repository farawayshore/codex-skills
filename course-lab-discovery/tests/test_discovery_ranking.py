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
    decoded_candidates,
    picture_result_dir_candidates,
    score_paths,
    simulation_dir_candidates,
    simulation_file_candidates,
    template_groups,
)


class DiscoveryRankingTests(unittest.TestCase):
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
