from __future__ import annotations

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
PARENT_SKILL_PATH = Path("/root/.codex/skills/modern-physics-latex-report-rennovated/SKILL.md")


class CourseLabDiscussionSynthesisPackageTests(unittest.TestCase):
    def test_standalone_skill_contract_files_exist(self) -> None:
        required_paths = [
            SKILL_DIR / "SKILL.md",
            SKILL_DIR / "agents" / "openai.yaml",
            SKILL_DIR / "scripts" / "common.py",
            SKILL_DIR / "scripts" / "build_discussion_synthesis.py",
            SKILL_DIR / "tests" / "baseline_failures.md",
        ]

        missing = [str(path.relative_to(SKILL_DIR)) for path in required_paths if not path.exists()]
        self.assertEqual(missing, [])

    def test_skill_markdown_uses_local_paths_and_synthesis_boundary_language(self) -> None:
        skill_path = SKILL_DIR / "SKILL.md"
        self.assertTrue(skill_path.exists(), "SKILL.md must exist before content checks run")

        text = skill_path.read_text(encoding="utf-8")

        self.assertIn(
            "/root/.codex/skills/course-lab-discussion-synthesis/scripts/build_discussion_synthesis.py",
            text,
        )
        self.assertIn("artifact-only", text.lower())
        self.assertIn("approved", text.lower())
        self.assertIn("reference report", text.lower())
        self.assertIn("first accepted-ideas", text.lower())
        self.assertIn("targeted", text.lower())
        self.assertIn("final-staging", text.lower())
        self.assertIn("main.tex", text)
        self.assertNotIn("modern-physics-latex-report-rennovated/scripts", text)

    def test_agent_prompt_requires_local_approval_first_support_aware_behavior(self) -> None:
        agent_path = SKILL_DIR / "agents" / "openai.yaml"
        self.assertTrue(agent_path.exists(), "agents/openai.yaml must exist before prompt checks run")

        text = agent_path.read_text(encoding="utf-8")

        self.assertIn("approved", text.lower())
        self.assertIn("reference report", text.lower())
        self.assertIn("first", text.lower())
        self.assertIn("targeted", text.lower())
        self.assertIn("artifact-only", text.lower())
        self.assertIn("final-staging", text.lower())
        self.assertIn("do not mutate", text.lower())
        self.assertIn("main.tex", text)

    def test_parent_skill_mentions_discussion_synthesis_subskill(self) -> None:
        self.assertTrue(PARENT_SKILL_PATH.exists(), "parent skill must exist for handoff verification")

        text = PARENT_SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("$course-lab-discussion-synthesis", text)


if __name__ == "__main__":
    unittest.main()
