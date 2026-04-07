from __future__ import annotations

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
PARENT_SKILL_PATH = Path("/root/.config/superpowers/worktrees/skills/course-lab-symbolic-expressing/course-lab-report/SKILL.md")


class CourseLabSymbolicExpressingPackageTests(unittest.TestCase):
    def test_standalone_skill_contract_files_exist(self) -> None:
        required_paths = [
            SKILL_DIR / "SKILL.md",
            SKILL_DIR / "agents" / "openai.yaml",
            SKILL_DIR / "scripts" / "render_symbolic_explanation.py",
            SKILL_DIR / "tests" / "baseline_failures.md",
        ]

        missing = [str(path.relative_to(SKILL_DIR)) for path in required_paths if not path.exists()]
        self.assertEqual(missing, [])

    def test_skill_markdown_documents_optional_path_returning_boundary(self) -> None:
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("course-lab-symbolic-expressing", text)
        self.assertIn("optional", text.lower())
        self.assertIn("standalone", text.lower())
        self.assertIn("temporary", text.lower())
        self.assertIn("tex_path", text)
        self.assertIn("handout", text.lower())
        self.assertIn("calculation code", text.lower())
        self.assertIn("processed result", text.lower())
        self.assertIn("does not mutate", text.lower())
        self.assertIn("main.tex", text)
        self.assertIn("unresolved", text.lower())
        self.assertIn("workspace-local", text.lower())
        self.assertIn("/tmp", text)

    def test_agent_prompt_requires_artifact_only_helper_behavior(self) -> None:
        text = (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("optional", text.lower())
        self.assertIn("temporary", text.lower())
        self.assertIn("tex", text.lower())
        self.assertIn("return", text.lower())
        self.assertIn("do not mutate", text.lower())

    def test_parent_skill_mentions_optional_symbolic_handoff(self) -> None:
        text = PARENT_SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("course-lab-symbolic-expressing", text)
        self.assertIn("optional", text.lower())
        self.assertIn("temp TeX", text)


if __name__ == "__main__":
    unittest.main()
