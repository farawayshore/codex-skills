from __future__ import annotations

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class CourseLabBodyScaffoldPackageTests(unittest.TestCase):
    def test_required_package_files_exist(self) -> None:
        required_paths = [
            SKILL_DIR / "SKILL.md",
            SKILL_DIR / "scripts" / "build_body_scaffold.py",
            SKILL_DIR / "references" / "body_scaffold_rules.md",
            SKILL_DIR / "tests" / "test_build_body_scaffold.py",
            SKILL_DIR / "tests" / "test_skill_package.py",
        ]
        missing = [str(path.relative_to(SKILL_DIR)) for path in required_paths if not path.exists()]
        self.assertEqual(missing, [])

    def test_skill_uses_workspace_notes_sections_contract(self) -> None:
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("/path/to/results/<experiment>/notes/sections.json", text)
        self.assertIn("/path/to/results/<experiment>/notes/sections.md", text)
        self.assertIn("% procedure:Pxx", text)


if __name__ == "__main__":
    unittest.main()
