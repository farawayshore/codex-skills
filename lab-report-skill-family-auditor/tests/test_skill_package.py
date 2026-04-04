from __future__ import annotations

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class LabReportSkillFamilyAuditorPackageTests(unittest.TestCase):
    def test_required_paths_exist(self) -> None:
        required = [
            SKILL_DIR / "SKILL.md",
            SKILL_DIR / "agents" / "openai.yaml",
            SKILL_DIR / "scripts" / "common.py",
            SKILL_DIR / "scripts" / "build_family_manifest.py",
            SKILL_DIR / "scripts" / "discover_current_family.py",
            SKILL_DIR / "scripts" / "prepare_family_audit.py",
        ]
        missing = [str(path.relative_to(SKILL_DIR)) for path in required if not path.exists()]
        self.assertEqual(missing, [])

    def test_skill_markdown_mentions_local_scripts_and_minimum_change_rules(self) -> None:
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("/root/.codex/skills/lab-report-skill-family-auditor/scripts/prepare_family_audit.py", text)
        self.assertIn("AI_construction", text)
        self.assertIn("minimum-change", text.lower())
        self.assertIn("aligned", text)
        self.assertIn("needs refinement", text)
        self.assertIn("missing", text)
        self.assertIn("boundary/coherency risk", text)
        self.assertIn("do not edit skills automatically", text.lower())
        self.assertIn("frontmatter", text.lower())

    def test_agent_prompt_mentions_latest_plan_and_audit_only_behavior(self) -> None:
        text = (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("newest", text.lower())
        self.assertIn("family summary", text.lower())
        self.assertIn("minimum-change", text.lower())
        self.assertIn("AI_construction", text)
        self.assertIn("do not edit", text.lower())


if __name__ == "__main__":
    unittest.main()
