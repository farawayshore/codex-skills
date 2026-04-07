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

    def test_parent_skill_forbids_manual_shortcuts_past_late_stages(self) -> None:
        skill_text = (PACKAGE_ROOT / "SKILL.md").read_text(encoding="utf-8")
        expected_snippets = [
            "must not hand-write a manual short draft",
            "must not bypass `course-lab-final-staging`",
            "must not replace missing appendix staging with a prose-only appendix stub",
            "`final_staging_summary.json`",
            "`appendix_code_manifest.json`",
            "`picture_evidence_plan.json`",
            "`signatory_pages.tex`",
        ]
        for snippet in expected_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, skill_text)

    def test_orchestration_rules_require_late_stage_artifact_proof(self) -> None:
        text = (PACKAGE_ROOT / "references" / "orchestration_rules.md").read_text(
            encoding="utf-8"
        )
        expected_snippets = [
            "`final_staging_summary.json`",
            "`appendix_code_manifest.json`",
            "`picture_evidence_plan.json`",
            "`signatory_pages_manifest.json`",
            "`signatory_pages.tex`",
            "must not treat a manually compiled PDF as proof",
            "must stop instead of claiming completion",
        ]
        for snippet in expected_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, text)

    def test_parent_skill_requires_principle_stage_artifact_proof(self) -> None:
        skill_text = (PACKAGE_ROOT / "SKILL.md").read_text(encoding="utf-8")
        expected_snippets = [
            "must not silently continue past `course-lab-experiment-principle`",
            "`principle_ownership.json`",
            "`principle_figures.json`",
            "`principle_figures.tex`",
            "`principle_unresolved.md`",
            "must not treat manually written theory prose as proof that principle-image staging ran",
        ]
        for snippet in expected_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, skill_text)

    def test_orchestration_rules_require_principle_stage_artifact_gate(self) -> None:
        text = (PACKAGE_ROOT / "references" / "orchestration_rules.md").read_text(
            encoding="utf-8"
        )
        expected_snippets = [
            "`course-lab-experiment-principle` must emit `principle_ownership.json`",
            "`principle_figures.json`",
            "`principle_figures.tex`",
            "`principle_unresolved.md`",
            "must stop instead of claiming the theory stage is complete",
        ]
        for snippet in expected_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, text)

    def test_parent_skill_requires_persistent_handout_decode_proof(self) -> None:
        skill_text = (PACKAGE_ROOT / "SKILL.md").read_text(encoding="utf-8")
        orchestration_text = (PACKAGE_ROOT / "references" / "orchestration_rules.md").read_text(
            encoding="utf-8"
        )
        recovery_text = (PACKAGE_ROOT / "references" / "recovery_matrix.md").read_text(
            encoding="utf-8"
        )
        matrix_text = (PACKAGE_ROOT / "references" / "leaf_responsibility_matrix.md").read_text(
            encoding="utf-8"
        )
        expected_snippets = [
            "must not treat summary-only handout artifacts as proof that handout normalization completed",
            "`AI_works/resources/experiment_handout/Modern Physics Experiments/pdf_decoded/<experiment-name>/<experiment-name>.md`",
            "`AI_works/resources/experiment_handout/Modern Physics Experiments/pdf_decoded/<experiment-name>/<experiment-name>.json`",
            "`notes/sections.md`",
            "`sections.json`",
            "`handout_extract.md`",
            "must stop instead of silently continuing",
            "missing persistent decoded handout artifacts",
        ]
        for snippet in expected_snippets:
            with self.subTest(snippet=snippet):
                joined = "\n".join(
                    [skill_text, orchestration_text, recovery_text, matrix_text]
                )
                self.assertIn(snippet, joined)


if __name__ == "__main__":
    unittest.main()
