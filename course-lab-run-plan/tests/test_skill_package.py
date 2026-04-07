from __future__ import annotations

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class CourseLabRunPlanPackageTests(unittest.TestCase):
    def test_required_shell_files_exist(self) -> None:
        required_paths = [
            SKILL_DIR / "SKILL.md",
            SKILL_DIR / "agents" / "openai.yaml",
            SKILL_DIR / "references" / "run_plan_rules.md",
            SKILL_DIR / "scripts" / "common.py",
            SKILL_DIR / "scripts" / "build_run_plan.py",
            SKILL_DIR / "tests" / "baseline_failures.md",
        ]
        missing = [str(path.relative_to(SKILL_DIR)) for path in required_paths if not path.exists()]
        self.assertEqual(missing, [])

    def test_skill_markdown_uses_local_paths_and_documents_boundary(self) -> None:
        skill_path = SKILL_DIR / "SKILL.md"
        self.assertTrue(skill_path.exists(), "SKILL.md must exist before content checks run")

        text = skill_path.read_text(encoding="utf-8")
        forbidden_parent_path = "modern-physics-latex-report-rennovated" + "/scripts"

        self.assertIn("/root/.codex/skills/course-lab-run-plan/scripts/build_run_plan.py", text)
        self.assertIn("planning-only", text.lower())
        self.assertIn("json", text.lower())
        self.assertIn("markdown", text.lower())
        self.assertIn("comparison_obligations", text)
        self.assertIn("confirmed-agent-key-results-json", text)
        self.assertIn("do not use this skill to", text.lower())
        self.assertIn("tex", text.lower())
        self.assertIn("data transfer", text.lower())
        self.assertIn("computation", text.lower())
        self.assertIn("write final", text.lower())
        self.assertNotIn(forbidden_parent_path, text)

    def test_agent_prompt_requires_local_planning_only_behavior(self) -> None:
        agent_path = SKILL_DIR / "agents" / "openai.yaml"
        self.assertTrue(agent_path.exists(), "agents/openai.yaml must exist before prompt checks run")

        text = agent_path.read_text(encoding="utf-8")

        self.assertIn("local", text.lower())
        self.assertIn("planning", text.lower())
        self.assertIn("json", text.lower())
        self.assertIn("markdown", text.lower())
        self.assertIn("do not", text.lower())
        self.assertIn("tex", text.lower())
