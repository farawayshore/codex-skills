from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_family_manifest import build_family_manifest, choose_plan_document  # noqa: E402


class BuildFamilyManifestTests(unittest.TestCase):
    def make_temp_root(self) -> Path:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(root))
        return root

    def test_choose_plan_prefers_newest_dated_filename(self) -> None:
        root = self.make_temp_root()
        (root / "2026-03-27-lab-report-skill-family-summary.md").write_text("# latest\n", encoding="utf-8")
        (root / "2026-03-24-lab-report-skill-family-summary.md").write_text("# older\n", encoding="utf-8")

        chosen, reason = choose_plan_document(root, None)

        self.assertEqual(chosen.name, "2026-03-27-lab-report-skill-family-summary.md")
        self.assertIn("newest dated filename", reason)

    def test_choose_plan_honors_explicit_override(self) -> None:
        root = self.make_temp_root()
        override = root / "manual-planning.md"
        override.write_text("# chosen manually\n", encoding="utf-8")
        (root / "2026-03-27-lab-report-skill-family-summary.md").write_text("# latest\n", encoding="utf-8")

        chosen, reason = choose_plan_document(root, override)

        self.assertEqual(chosen, override)
        self.assertIn("override", reason)

    def test_build_family_manifest_extracts_tree_and_shared_dependencies(self) -> None:
        root = self.make_temp_root()
        plan = root / "2026-03-27-lab-report-skill-family-summary.md"
        plan.write_text(
            "# Lab Report Skill Family Summary\n"
            "## High-Level Skill Tree\n"
            "```text\n"
            "course-lab-report\n"
            "|- course-lab-discovery\n"
            "`- course-lab-finalize-qc\n"
            "\n"
            "Shared dependencies used by the family:\n"
            "|- mineru-pdf-json\n"
            "`- physics-lab-mathematica-modeling\n"
            "```\n",
            encoding="utf-8",
        )

        manifest = build_family_manifest(plan)

        self.assertIn("course-lab-report", manifest["planned_skills"])
        self.assertIn("course-lab-discovery", manifest["planned_skills"])
        self.assertIn("physics-lab-mathematica-modeling", manifest["shared_dependencies"])

    def test_build_family_manifest_extracts_role_ownership_and_outputs(self) -> None:
        root = self.make_temp_root()
        plan = root / "2026-03-27-lab-report-skill-family-summary.md"
        plan.write_text(
            "# Lab Report Skill Family Summary\n"
            "## Role Of The Parent Skill\n"
            "### `course-lab-report`\n"
            "It should own:\n"
            "- overall run order\n"
            "- choosing which subskill to invoke next\n"
            "It should not directly own:\n"
            "- MinerU decoding logic\n"
            "## Leaf Subskills\n"
            "### `course-lab-run-plan`\n"
            "Owns:\n"
            "- rereading normalized handout Markdown and JSON carefully\n"
            "Expected outputs:\n"
            "- `AI_works/results/<experiment-safe-name>/<experiment-safe-name>_run_plan.md`\n",
            encoding="utf-8",
        )

        manifest = build_family_manifest(plan)

        self.assertEqual(manifest["skill_roles"]["course-lab-report"], "parent")
        self.assertIn("overall run order", manifest["skill_contracts"]["course-lab-report"]["owns"])
        self.assertIn("MinerU decoding logic", manifest["skill_contracts"]["course-lab-report"]["should_not_own"])
        self.assertIn(
            "AI_works/results/<experiment-safe-name>/<experiment-safe-name>_run_plan.md",
            manifest["skill_contracts"]["course-lab-run-plan"]["expected_outputs"],
        )

    def test_build_family_manifest_extracts_relation_order(self) -> None:
        root = self.make_temp_root()
        plan = root / "2026-03-27-lab-report-skill-family-summary.md"
        plan.write_text(
            "# Lab Report Skill Family Summary\n"
            "## Relations Between Skills\n"
            "1. `course-lab-report` starts the run.\n"
            "2. `course-lab-discovery` identifies the experiment.\n"
            "3. `course-lab-handout-normalization` makes the handout usable.\n",
            encoding="utf-8",
        )

        manifest = build_family_manifest(plan)

        self.assertEqual(
            manifest["relation_order"][:3],
            ["course-lab-report", "course-lab-discovery", "course-lab-handout-normalization"],
        )

    def test_build_family_manifest_ignores_good_and_avoid_name_examples(self) -> None:
        root = self.make_temp_root()
        plan = root / "2026-03-27-lab-report-skill-family-summary.md"
        plan.write_text(
            "# Lab Report Skill Family Summary\n"
            "## High-Level Skill Tree\n"
            "```text\n"
            "course-lab-report\n"
            "|- course-lab-discovery\n"
            "`- course-lab-finalize-qc\n"
            "```\n"
            "## Naming Style\n"
            "Good:\n"
            "- `course-lab-results-interpretation`\n"
            "Avoid:\n"
            "- `course-lab-analysis-everything`\n"
            "- `course-lab-final-processing`\n",
            encoding="utf-8",
        )

        manifest = build_family_manifest(plan)

        self.assertIn("course-lab-report", manifest["planned_skills"])
        self.assertIn("course-lab-discovery", manifest["planned_skills"])
        self.assertNotIn("course-lab-analysis-everything", manifest["planned_skills"])
        self.assertNotIn("course-lab-final-processing", manifest["planned_skills"])


if __name__ == "__main__":
    unittest.main()
