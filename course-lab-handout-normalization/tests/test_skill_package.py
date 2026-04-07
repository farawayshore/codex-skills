import unittest
from pathlib import Path


PACKAGE_ROOT = Path("/root/.codex/skills/course-lab-handout-normalization")


class TestCourseLabHandoutNormalizationPackage(unittest.TestCase):
    def test_required_files_exist(self) -> None:
        required = [
            "SKILL.md",
            "agents/openai.yaml",
            "scripts/extract_decoded_sections.py",
            "tests/test_extract_decoded_sections.py",
            "tests/test_skill_package.py",
        ]
        missing = [path for path in required if not (PACKAGE_ROOT / path).exists()]
        self.assertEqual([], missing, f"missing required files: {missing}")

    def test_skill_requires_canonical_pdf_decoded_success_paths(self) -> None:
        skill_text = (PACKAGE_ROOT / "SKILL.md").read_text(encoding="utf-8")
        agent_text = (PACKAGE_ROOT / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )
        expected_snippets = [
            "AI_works/resources/experiment_handout/Modern Physics Experiments/pdf_decoded/<experiment-name>/<experiment-name>.md",
            "AI_works/resources/experiment_handout/Modern Physics Experiments/pdf_decoded/<experiment-name>/<experiment-name>.json",
            "successful handout normalization",
            "persistent decoded handout artifacts",
            "must not treat ad hoc extracts as equivalent",
            "handout_extract.md",
            "summary-only",
        ]
        for snippet in expected_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, "\n".join([skill_text, agent_text]))

    def test_skill_requires_mineru_only_decode_order_and_bans_pdftotext(self) -> None:
        skill_text = (PACKAGE_ROOT / "SKILL.md").read_text(encoding="utf-8")
        agent_text = (PACKAGE_ROOT / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )
        combined = "\n".join([skill_text, agent_text]).lower()

        required_snippets = [
            "mineru markdown",
            "mineru json",
            "markdown-first",
            "json-second",
            "vision",
            "complement",
            "pdftotext",
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, combined)

        banned_expectations = [
            "never use pdftotext",
            "do not use pdftotext",
            "strictly prohibit pdftotext",
        ]
        self.assertTrue(
            any(snippet in combined for snippet in banned_expectations),
            "skill must explicitly ban pdftotext",
        )


if __name__ == "__main__":
    unittest.main()
