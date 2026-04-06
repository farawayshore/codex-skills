import unittest
from pathlib import Path


PACKAGE_ROOT = Path("/root/.codex/skills/course-lab-report")
INSTALLED_LEAVES = [
    "course-lab-discovery",
    "course-lab-handout-normalization",
    "course-lab-workspace-template",
    "course-lab-metadata-frontmatter",
    "course-lab-run-plan",
    "course-lab-body-scaffold",
    "course-lab-experiment-principle",
    "course-lab-data-transfer",
    "course-lab-data-processing",
    "course-lab-uncertainty-analysis",
    "course-lab-plotting",
    "course-lab-results-interpretation",
    "course-lab-discussion-ideas",
    "course-lab-discussion-synthesis",
    "course-lab-final-staging",
    "course-lab-figure-evidence",
    "course-lab-finalize-qc",
]


class TestCourseLabReportPackageSkeleton(unittest.TestCase):
    def test_package_root_exists(self) -> None:
        self.assertTrue(PACKAGE_ROOT.exists(), "package root must exist")

    def test_required_files_exist(self) -> None:
        required = [
            "SKILL.md",
            "agents/openai.yaml",
            "references/orchestration_rules.md",
            "references/delegation_policy.md",
            "references/recovery_matrix.md",
            "references/leaf_responsibility_matrix.md",
            "tests/baseline_failures.md",
            "tests/test_skill_package.py",
            "tests/test_recovery_matrix.py",
        ]
        missing = [path for path in required if not (PACKAGE_ROOT / path).exists()]
        self.assertEqual([], missing, f"missing required files: {missing}")

    def test_top_level_skill_contract(self) -> None:
        skill_text = (PACKAGE_ROOT / "SKILL.md").read_text(encoding="utf-8")
        agent_text = (PACKAGE_ROOT / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("name: course-lab-report", skill_text)
        self.assertIn("Use when", skill_text)
        self.assertIn("orchestrator", skill_text)
        self.assertIn("coordination-first", skill_text)
        self.assertIn("course-lab-run-plan", skill_text)
        self.assertIn("modern-physics-latex-report-rennovated", skill_text)
        self.assertIn("legacy", skill_text)
        self.assertIn("must not rely on that folder at runtime", skill_text)
        self.assertIn("should stay compact", skill_text)
        self.assertIn("orchestrator", agent_text.lower())

    def test_delegation_and_leaf_matrix_contract(self) -> None:
        delegation_text = (
            PACKAGE_ROOT / "references" / "delegation_policy.md"
        ).read_text(encoding="utf-8")
        matrix_text = (
            PACKAGE_ROOT / "references" / "leaf_responsibility_matrix.md"
        ).read_text(encoding="utf-8")
        for snippet in [
            "Prefer Small Worker",
            "Prefer Inline / Main Agent",
            "Explicit Stay-Local",
            "Conditional Stronger Worker",
            "course-lab-run-plan",
            "course-lab-data-processing",
            "course-lab-uncertainty-analysis",
            "course-lab-plotting",
            "course-lab-finalize-qc",
            "course-lab-discussion-ideas",
            "course-lab-discussion-synthesis",
            "course-lab-final-staging",
            "stable evidence-plan artifact",
            "placement-ready grouping manifest",
            "group-to-target mapping is explicit",
            "remain compact",
        ]:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, delegation_text)

        for leaf in INSTALLED_LEAVES:
            with self.subTest(leaf=leaf):
                self.assertIn(f"## {leaf}", matrix_text)

        for field in [
            "- Invoke when:",
            "- Required inputs:",
            "- Emits:",
            "- Delegation preference:",
            "- QC reroute ownership:",
            "- Does not own:",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, matrix_text)


if __name__ == "__main__":
    unittest.main()
