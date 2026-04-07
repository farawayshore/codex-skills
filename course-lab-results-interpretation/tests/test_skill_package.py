from __future__ import annotations

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
PARENT_SKILL_PATH = Path("/root/.codex/skills/modern-physics-latex-report-rennovated/SKILL.md")


class CourseLabResultsInterpretationPackageTests(unittest.TestCase):
    def test_standalone_skill_contract_files_exist(self) -> None:
        required_paths = [
            SKILL_DIR / "SKILL.md",
            SKILL_DIR / "agents" / "openai.yaml",
            SKILL_DIR / "scripts" / "common.py",
            SKILL_DIR / "scripts" / "build_results_interpretation.py",
            SKILL_DIR / "scripts" / "stage_reference_values.py",
            SKILL_DIR / "tests" / "baseline_failures.md",
        ]

        missing = [str(path.relative_to(SKILL_DIR)) for path in required_paths if not path.exists()]
        self.assertEqual(missing, [])

    def test_skill_markdown_uses_local_paths_and_handout_first_artifact_only_language(self) -> None:
        skill_path = SKILL_DIR / "SKILL.md"
        self.assertTrue(skill_path.exists(), "SKILL.md must exist before content checks run")

        text = skill_path.read_text(encoding="utf-8")

        self.assertIn(
            "/root/.codex/skills/course-lab-results-interpretation/scripts/build_results_interpretation.py",
            text,
        )
        self.assertIn(
            "/root/.codex/skills/course-lab-results-interpretation/scripts/stage_reference_values.py",
            text,
        )
        self.assertIn("artifact-only", text.lower())
        self.assertIn("unresolved", text.lower())
        self.assertIn("handout", text.lower())
        self.assertIn("read the normalized handout first", text.lower())
        self.assertIn("simulation", text.lower())
        self.assertIn("comparison_records", text)
        self.assertIn("comparison_obligations", text)
        self.assertIn("agent_proposed_key_results", text)
        self.assertIn("candidate_literature_sources", text)
        self.assertIn("approved", text.lower())
        self.assertIn("pending_user", text.lower())
        self.assertIn("internet", text.lower())
        self.assertIn("discussion", text.lower())
        self.assertNotIn("modern-physics-latex-report-rennovated/scripts", text)

    def test_agent_prompt_requires_handout_first_local_artifact_only_interpretation(self) -> None:
        agent_path = SKILL_DIR / "agents" / "openai.yaml"
        self.assertTrue(agent_path.exists(), "agents/openai.yaml must exist before prompt checks run")

        text = agent_path.read_text(encoding="utf-8")

        self.assertIn("handout", text.lower())
        self.assertIn("handout-first", text.lower())
        self.assertIn("local", text.lower())
        self.assertIn("artifact-only", text.lower())
        self.assertIn("unresolved", text.lower())
        self.assertIn("processed-data", text.lower())
        self.assertIn("simulation", text.lower())
        self.assertIn("internet", text.lower())
        self.assertIn("do not mutate", text.lower())

    def test_parent_skill_mentions_results_interpretation_subskill(self) -> None:
        self.assertTrue(PARENT_SKILL_PATH.exists(), "parent skill must exist for handoff verification")

        text = PARENT_SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("$course-lab-results-interpretation", text)


if __name__ == "__main__":
    unittest.main()
