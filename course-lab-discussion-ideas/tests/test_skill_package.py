from __future__ import annotations

import unittest
from pathlib import Path


SKILL_DIR = Path("/root/.codex/skills/course-lab-discussion-ideas")
PARENT_SKILL_PATH = Path("/root/.codex/skills/modern-physics-latex-report-rennovated/SKILL.md")


class CourseLabDiscussionIdeasPackageTests(unittest.TestCase):
    def test_standalone_skill_contract_files_exist(self) -> None:
        required_paths = [
            SKILL_DIR / "SKILL.md",
            SKILL_DIR / "agents" / "openai.yaml",
            SKILL_DIR / "scripts" / "common.py",
            SKILL_DIR / "scripts" / "build_discussion_ideas.py",
            SKILL_DIR / "scripts" / "merge_idea_memory.py",
            SKILL_DIR / "scripts" / "render_discussion_ideas_markdown.py",
            SKILL_DIR / "tests" / "baseline_failures.md",
        ]

        missing = [str(path.relative_to(SKILL_DIR)) for path in required_paths if not path.exists()]
        self.assertEqual(missing, [])

    def test_skill_markdown_uses_local_paths_and_idea_only_language(self) -> None:
        skill_path = SKILL_DIR / "SKILL.md"
        self.assertTrue(skill_path.exists(), "SKILL.md must exist before content checks run")

        text = skill_path.read_text(encoding="utf-8")

        self.assertIn(
            "/root/.codex/skills/course-lab-discussion-ideas/scripts/build_discussion_ideas.py",
            text,
        )
        self.assertIn("artifact-only", text.lower())
        self.assertIn("reference report", text.lower())
        self.assertIn("permanent memory", text.lower())
        self.assertIn("broad", text.lower())
        self.assertIn("targeted", text.lower())
        self.assertIn("discussion_synthesis_input.tmp.json", text)
        self.assertIn("synthesis judgment", text.lower())
        self.assertIn("do not", text.lower())
        self.assertNotIn("user approval", text.lower())
        self.assertNotIn("modern-physics-latex-report-rennovated/scripts", text)

    def test_agent_prompt_requires_local_memory_gated_idea_only_behavior(self) -> None:
        agent_path = SKILL_DIR / "agents" / "openai.yaml"
        self.assertTrue(agent_path.exists(), "agents/openai.yaml must exist before prompt checks run")

        text = agent_path.read_text(encoding="utf-8")

        self.assertIn("local", text.lower())
        self.assertIn("reference report", text.lower())
        self.assertIn("permanent memory", text.lower())
        self.assertIn("broad", text.lower())
        self.assertIn("targeted", text.lower())
        self.assertIn("artifact-only", text.lower())
        self.assertIn("do not mutate", text.lower())
        self.assertIn("final harmonized discussion", text.lower())
        self.assertIn("synthesis judgment", text.lower())
        self.assertNotIn("user approval", text.lower())

    def test_parent_skill_mentions_discussion_ideas_subskill(self) -> None:
        self.assertTrue(PARENT_SKILL_PATH.exists(), "parent skill must exist for handoff verification")

        text = PARENT_SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("$course-lab-discussion-ideas", text)


if __name__ == "__main__":
    unittest.main()
