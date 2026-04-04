from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from prepare_family_audit import prepare_family_audit  # noqa: E402


class PrepareFamilyAuditTests(unittest.TestCase):
    def make_temp_root(self) -> Path:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(root))
        return root

    def test_prepare_family_audit_writes_support_artifacts(self) -> None:
        root = self.make_temp_root()
        plans = root / "plans"
        plans.mkdir()
        plan = plans / "2026-03-27-lab-report-skill-family-summary.md"
        plan.write_text(
            "# Lab Report Skill Family Summary\n"
            "## High-Level Skill Tree\n"
            "```text\ncourse-lab-report\n|- course-lab-discovery\n```\n",
            encoding="utf-8",
        )
        skills = root / "skills"
        skill = skills / "course-lab-discovery"
        (skill / "scripts").mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: course-lab-discovery\ndescription: Use when...\n---\n",
            encoding="utf-8",
        )
        output = root / "AI_construction"

        result = prepare_family_audit(plan_root=plans, override=plan, skills_root=skills, output_dir=output)

        support_dir = output / "audit_support" / "2026-03-27-lab-report-skill-family-summary"
        self.assertEqual(Path(result["support_dir"]), support_dir)
        self.assertTrue((support_dir / "family_manifest.json").exists())
        self.assertTrue((support_dir / "current_family_snapshot.json").exists())
        self.assertEqual(
            Path(result["report_path"]),
            output / "lab_report_skill_family_audit_2026-03-27-lab-report-skill-family-summary.md",
        )


if __name__ == "__main__":
    unittest.main()
