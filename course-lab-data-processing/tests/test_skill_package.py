from __future__ import annotations

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
PARENT_SKILL_PATH = Path("/root/.codex/skills/modern-physics-latex-report-rennovated/SKILL.md")


class CourseLabDataProcessingPackageTests(unittest.TestCase):
    def test_standalone_skill_contract_files_exist(self) -> None:
        required_paths = [
            SKILL_DIR / "SKILL.md",
            SKILL_DIR / "agents" / "openai.yaml",
            SKILL_DIR / "scripts" / "common.py",
            SKILL_DIR / "scripts" / "compute_uncertainties.py",
            SKILL_DIR / "scripts" / "propagate_uncertainties.py",
        ]

        missing = [str(path.relative_to(SKILL_DIR)) for path in required_paths if not path.exists()]
        self.assertEqual(missing, [])

    def test_skill_markdown_uses_local_paths_and_documents_handout_first_rules(self) -> None:
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("/root/.codex/skills/course-lab-data-processing/scripts/compute_uncertainties.py", text)
        self.assertIn("/root/.codex/skills/course-lab-data-processing/scripts/propagate_uncertainties.py", text)
        self.assertIn("k=2", text)
        self.assertIn("standalone", text)
        self.assertIn("read the handout first", text.lower())
        self.assertIn("T/N", text)
        self.assertIn("2r", text)
        self.assertIn("two_r / 2", text)
        self.assertIn("propagation", text.lower())
        self.assertNotIn("modern-physics-latex-report-rennovated/scripts/compute_uncertainties.py", text)

    def test_parent_skill_mentions_uncertainty_subskill(self) -> None:
        text = PARENT_SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("$course-lab-data-processing", text)

    def test_agent_prompt_requires_handout_first_and_derived_quantities(self) -> None:
        text = (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("handout", text.lower())
        self.assertIn("notation", text.lower())
        self.assertIn("indirect", text.lower())
        self.assertIn("propagation", text.lower())


if __name__ == "__main__":
    unittest.main()
