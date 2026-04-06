from __future__ import annotations

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
PARENT_SKILL_PATH = Path("/root/.codex/skills/modern-physics-latex-report-rennovated/SKILL.md")


class CourseLabFinalStagingPackageTests(unittest.TestCase):
    def test_standalone_skill_contract_files_exist(self) -> None:
        required_paths = [
            SKILL_DIR / "SKILL.md",
            SKILL_DIR / "agents" / "openai.yaml",
            SKILL_DIR / "references" / "report_structure.md",
            SKILL_DIR / "references" / "shared_draft_contract.md",
            SKILL_DIR / "scripts" / "common.py",
            SKILL_DIR / "scripts" / "collect_staging_inputs.py",
            SKILL_DIR / "scripts" / "render_results_sections.py",
            SKILL_DIR / "scripts" / "render_appendix_materials.py",
            SKILL_DIR / "scripts" / "render_catalog_and_timing.py",
            SKILL_DIR / "scripts" / "build_final_staging.py",
            SKILL_DIR / "tests" / "baseline_failures.md",
        ]

        missing = [str(path.relative_to(SKILL_DIR)) for path in required_paths if not path.exists()]
        self.assertEqual(missing, [])

    def test_skill_markdown_uses_local_paths_and_documents_boundary(self) -> None:
        skill_path = SKILL_DIR / "SKILL.md"
        self.assertTrue(skill_path.exists(), "SKILL.md must exist before content checks run")

        text = skill_path.read_text(encoding="utf-8")

        self.assertIn("/root/.codex/skills/course-lab-final-staging/scripts/build_final_staging.py", text)
        self.assertIn("data-processing", text.lower())
        self.assertIn("uncertainty", text.lower())
        self.assertIn("direct results", text.lower())
        self.assertIn("indirect results", text.lower())
        self.assertIn("modeling", text.lower())
        self.assertIn("appendix", text.lower())
        self.assertIn("20-30", text)
        self.assertIn("course-lab-figure-evidence", text)
        self.assertIn("final qc", text.lower())
        self.assertIn("explicitly provided", text.lower())
        self.assertIn("does not discover", text.lower())
        self.assertIn("partial derivative", text.lower())
        self.assertIn("substituted", text.lower())
        self.assertIn("two-column", text.lower())
        self.assertIn("table", text.lower())
        self.assertIn("calculation details", text.lower())
        self.assertIn("calculation-details-manifest", text.lower())
        self.assertIn("u_a", text)
        self.assertIn("u_b", text)
        self.assertIn("u_c", text)
        self.assertNotIn("modern-physics-latex-report-rennovated/scripts", text)

    def test_agent_prompt_requires_late_stage_local_writer_behavior(self) -> None:
        agent_path = SKILL_DIR / "agents" / "openai.yaml"
        self.assertTrue(agent_path.exists(), "agents/openai.yaml must exist before prompt checks run")

        text = agent_path.read_text(encoding="utf-8")

        self.assertIn("late-stage", text.lower())
        self.assertIn("non-figure", text.lower())
        self.assertIn("local", text.lower())
        self.assertIn("data-processing", text.lower())
        self.assertIn("uncertainty", text.lower())
        self.assertIn("appendix", text.lower())
        self.assertIn("do not place", text.lower())
        self.assertIn("do not compile", text.lower())
        self.assertIn("qc", text.lower())

    def test_parent_skill_mentions_final_staging_subskill(self) -> None:
        self.assertTrue(PARENT_SKILL_PATH.exists(), "parent skill must exist for handoff verification")

        text = PARENT_SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("$course-lab-final-staging", text)


if __name__ == "__main__":
    unittest.main()
