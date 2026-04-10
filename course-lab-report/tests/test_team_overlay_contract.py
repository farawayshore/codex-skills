import unittest
from pathlib import Path


PACKAGE_ROOT = Path("/root/.codex/skills/course-lab-report")
REFERENCES_ROOT = PACKAGE_ROOT / "references"


def read_package_file(relative_path: str) -> str:
    return (PACKAGE_ROOT / relative_path).read_text(encoding="utf-8")


def read_reference(name: str) -> str:
    return (REFERENCES_ROOT / name).read_text(encoding="utf-8")


class TestTeamOverlayContract(unittest.TestCase):
    def assert_contains_any(
        self,
        text: str,
        alternatives: list[str],
        *,
        label: str,
    ) -> None:
        self.assertTrue(
            any(option in text for option in alternatives),
            f"Expected one of {alternatives!r} for {label}",
        )

    def test_required_overlay_reference_docs_exist(self) -> None:
        required = ["team_roster.md", "team_handoff_contract.md"]
        missing = [name for name in required if not (REFERENCES_ROOT / name).exists()]
        self.assertEqual([], missing)

    def test_parent_skill_describes_optional_overlay_without_changing_standalone_use(
        self,
    ) -> None:
        text = read_package_file("SKILL.md").lower()
        expectations = [
            ["optional team overlay", "optional overlay"],
            ["standalone leaf-tool usage remains unchanged", "standalone leaf-tool use"],
            ["no role label or native agent file becomes mandatory", "no native agent file"],
            ["references/team_roster.md", "team_roster.md"],
            ["references/team_handoff_contract.md", "team_handoff_contract.md"],
        ]
        for alternatives in expectations:
            with self.subTest(alternatives=alternatives):
                self.assert_contains_any(text, alternatives, label="parent skill overlay contract")

    def test_team_roster_lists_leader_and_six_specialists(self) -> None:
        text = read_reference("team_roster.md").lower()
        for snippet in [
            "leader",
            "preparer",
            "data analyst",
            "writer",
            "discussioner",
            "examiner",
            "senior",
            "overlay is optional",
            "standalone leaf-tool usage remains first-class",
        ]:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, text)

    def test_team_roster_keeps_discussion_before_final_staging(self) -> None:
        text = read_reference("team_roster.md").lower()
        self.assert_contains_any(
            text,
            [
                "keeps discussioner upstream of `course-lab-final-staging`",
                "discussioner stays upstream of `course-lab-final-staging`",
            ],
            label="discussion before final staging",
        )
        self.assert_contains_any(
            text,
            [
                "writer remains the only late-stage `.tex` mutator",
                "writer is the only lane that should own late-stage `.tex` mutation after setup",
            ],
            label="writer late-stage ownership",
        )

    def test_team_handoff_contract_keeps_leader_orchestration_only(self) -> None:
        text = read_reference("team_handoff_contract.md").lower()
        expectations = [
            ["orchestration-only"],
            ["does not own: prose writing", "does not own prose writing"],
            ["numerical computation"],
            ["direct qc scoring"],
            ["agent_proposed_key_results"],
            ["pending_user"],
            ["approved"],
            ["rejected"],
            ["needs_revision"],
            ["examiner emits scores and tickets", "examiner may open score/reroute tickets"],
            ["senior suggestions stay advisory"],
        ]
        for alternatives in expectations:
            with self.subTest(alternatives=alternatives):
                self.assert_contains_any(text, alternatives, label="team handoff leader scope")

    def test_overlay_docs_keep_examiner_and_senior_boundaries(self) -> None:
        joined = "\n".join(
            [
                read_reference("team_roster.md"),
                read_reference("team_handoff_contract.md"),
                read_reference("examiner_rubric.md"),
                read_reference("senior_advice_contract.md"),
            ]
        ).lower()
        expectations = [
            ["score/ticket-only"],
            ["course-lab-finalize-qc"],
            ["owner-tagged reroute tickets"],
            ["does not directly patch final report prose", "direct report repair"],
            ["anti-invention"],
            ["senior-source"],
            ["reference-report"],
            ["generic"],
            ["style-only"],
        ]
        for alternatives in expectations:
            with self.subTest(alternatives=alternatives):
                self.assert_contains_any(joined, alternatives, label="examiner/senior boundaries")

    def test_thinking_question_gap_stays_explicit(self) -> None:
        joined = "\n".join(
            [read_reference("team_roster.md"), read_reference("team_handoff_contract.md")]
        )
        lowered = joined.lower()
        self.assertIn("thinking-question", lowered)
        self.assertRegex(
            lowered,
            r"thinking-question.*(future|planned extension|not current)",
        )

    def test_overlay_preserves_reference_selection_and_signatory_contracts(self) -> None:
        joined = "\n".join(
            [
                read_package_file("SKILL.md"),
                read_reference("full_workflow_routing.md"),
                read_reference("recovery_matrix.md"),
                read_reference("team_handoff_contract.md"),
            ]
        ).lower()
        for snippet in [
            "reference_selection_status",
            "none_found",
            "skipped_optional_leaves",
            "signatory_pages_manifest.json",
            "signatory_pages.tex",
            "declared-unresolved",
            "data-lack",
        ]:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, joined)


if __name__ == "__main__":
    unittest.main()
