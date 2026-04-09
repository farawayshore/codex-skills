from __future__ import annotations

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
PARENT_SKILL_PATH = Path("/root/.codex/skills/course-lab-report/SKILL.md")


class CourseLabFinalizeQCPackageTests(unittest.TestCase):
    def test_standalone_skill_contract_files_exist(self) -> None:
        required_paths = [
            SKILL_DIR / "SKILL.md",
            SKILL_DIR / "agents" / "openai.yaml",
            SKILL_DIR / "references" / "quality_gate.md",
            SKILL_DIR / "assets" / "build.sh",
            SKILL_DIR / "scripts" / "common.py",
            SKILL_DIR / "scripts" / "report_qc.py",
            SKILL_DIR / "scripts" / "finalize_qc.py",
            SKILL_DIR / "scripts" / "reference_procedure_compare.py",
            SKILL_DIR / "tests" / "baseline_failures.md",
        ]

        missing = [str(path.relative_to(SKILL_DIR)) for path in required_paths if not path.exists()]
        self.assertEqual(missing, [])

    def test_skill_markdown_uses_local_paths_and_documents_boundary(self) -> None:
        skill_path = SKILL_DIR / "SKILL.md"
        self.assertTrue(skill_path.exists(), "SKILL.md must exist before content checks run")

        text = skill_path.read_text(encoding="utf-8")

        self.assertIn("/root/.codex/skills/course-lab-finalize-qc/scripts/finalize_qc.py", text)
        self.assertIn("/root/.codex/skills/course-lab-finalize-qc/scripts/report_qc.py", text)
        self.assertIn("compile", text.lower())
        self.assertIn("qc", text.lower())
        self.assertIn("handoff", text.lower())
        self.assertIn("20 mb", text.lower())
        self.assertIn("20-30", text)
        self.assertIn("$compress-png", text)
        self.assertIn("--discovery-json", text)
        self.assertIn("selected_reference_reports", text)
        self.assertIn("detector", text.lower())
        self.assertIn("reroute", text.lower())
        self.assertIn("same-experiment", text.lower())
        self.assertIn("do not use this skill to", text.lower())
        self.assertIn("direct report writing", text.lower())
        self.assertNotIn("modern-physics-latex-report-rennovated/scripts", text)

    def test_agent_prompt_requires_local_qc_only_behavior(self) -> None:
        agent_path = SKILL_DIR / "agents" / "openai.yaml"
        self.assertTrue(agent_path.exists(), "agents/openai.yaml must exist before prompt checks run")

        text = agent_path.read_text(encoding="utf-8")

        self.assertIn("compile", text.lower())
        self.assertIn("qc", text.lower())
        self.assertIn("local", text.lower())
        self.assertIn("20 mb", text.lower())
        self.assertIn("20-30", text)
        self.assertIn("compress-png", text.lower())
        self.assertIn("do not", text.lower())
        self.assertIn("write", text.lower())

    def test_parent_skill_mentions_finalize_qc_subskill(self) -> None:
        self.assertTrue(PARENT_SKILL_PATH.exists(), "parent skill must exist for handoff verification")

        text = PARENT_SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("`course-lab-finalize-qc`", text)


if __name__ == "__main__":
    unittest.main()
