from __future__ import annotations

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class CourseLabFigureEvidencePackageTests(unittest.TestCase):
    def test_standalone_skill_contract_files_exist(self) -> None:
        required_paths = [
            SKILL_DIR / "SKILL.md",
            SKILL_DIR / "agents" / "openai.yaml",
            SKILL_DIR / "scripts" / "common.py",
            SKILL_DIR / "scripts" / "extract_decoded_sections.py",
            SKILL_DIR / "scripts" / "stage_principle_images.py",
            SKILL_DIR / "scripts" / "stage_picture_results.py",
            SKILL_DIR / "scripts" / "plan_picture_evidence.py",
            SKILL_DIR / "scripts" / "stage_signatory_pages.py",
        ]

        missing = [str(path.relative_to(SKILL_DIR)) for path in required_paths if not path.exists()]
        self.assertEqual(missing, [])

    def test_skill_markdown_uses_local_paths_only(self) -> None:
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("/root/.codex/skills/course-lab-figure-evidence/scripts/stage_picture_results.py", text)
        self.assertIn("/root/.codex/skills/course-lab-figure-evidence/scripts/plan_picture_evidence.py", text)
        self.assertIn("/root/.codex/skills/course-lab-figure-evidence/scripts/stage_signatory_pages.py", text)
        self.assertIn("course-lab-experiment-principle", text)
        self.assertIn("compress-png", text)
        self.assertNotIn("modern-physics-latex-report-rennovated", text)

    def test_skill_documents_15mb_limit_and_confirmation_before_format_switch(self) -> None:
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        agent_prompt = (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("15 MB", text)
        self.assertIn("Do not switch", text)
        self.assertIn("ask the user for confirmation first", text)
        self.assertIn("15 MB", agent_prompt)
        self.assertIn("ask for confirmation", agent_prompt)

    def test_skill_contract_is_late_stage_after_final_staging(self) -> None:
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        agent_prompt = (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("course-lab-final-staging", text)
        self.assertIn("course-lab-experiment-principle", text)
        self.assertIn("staged draft", text)
        self.assertIn("late picture placement", text)
        self.assertIn("does not own handout-derived theory images", text)
        self.assertIn("does not own non-figure prose writing", text)
        self.assertIn("does not own final compile or QC decisions", text)
        self.assertNotIn("before interpretation starts", text)
        self.assertNotIn("before interpretation, discussion, or final compile", text)
        self.assertIn("after course-lab-final-staging", agent_prompt)
        self.assertIn("course-lab-experiment-principle", agent_prompt)
        self.assertIn("late picture placement", agent_prompt)


if __name__ == "__main__":
    unittest.main()
