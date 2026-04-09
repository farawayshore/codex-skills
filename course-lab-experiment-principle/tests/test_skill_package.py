from __future__ import annotations

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class CourseLabExperimentPrinciplePackageTests(unittest.TestCase):
    def test_standalone_skill_contract_files_exist(self) -> None:
        required_paths = [
            SKILL_DIR / "SKILL.md",
            SKILL_DIR / "agents" / "openai.yaml",
            SKILL_DIR / "scripts" / "common.py",
            SKILL_DIR / "scripts" / "extract_decoded_sections.py",
            SKILL_DIR / "scripts" / "stage_principle_images.py",
            SKILL_DIR / "scripts" / "write_experiment_principle.py",
        ]

        missing = [str(path.relative_to(SKILL_DIR)) for path in required_paths if not path.exists()]
        self.assertEqual(missing, [])

    def test_skill_markdown_uses_local_paths_only(self) -> None:
        skill_path = SKILL_DIR / "SKILL.md"
        self.assertTrue(skill_path.exists(), "SKILL.md must exist before content checks run")

        text = skill_path.read_text(encoding="utf-8")

        self.assertIn("/root/.codex/skills/course-lab-experiment-principle/scripts/stage_principle_images.py", text)
        self.assertIn("/root/.codex/skills/course-lab-experiment-principle/scripts/write_experiment_principle.py", text)
        self.assertIn("introduction", text.lower())
        self.assertIn("background", text.lower())
        self.assertIn("experiment principle", text.lower())
        self.assertIn("handout-derived", text.lower())
        self.assertIn("part-scoped", text.lower())
        self.assertIn("markdown", text.lower())
        self.assertIn("json", text.lower())
        self.assertNotIn("modern-physics-latex-report-rennovated", text)

    def test_skill_uses_workspace_notes_sections_contract(self) -> None:
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("/path/to/results/<experiment>/notes/sections.md", text)
        self.assertIn("/path/to/results/<experiment>/notes/sections.json", text)
        self.assertIn("markdown first", text.lower())


if __name__ == "__main__":
    unittest.main()
