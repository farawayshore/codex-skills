import unittest
from pathlib import Path


PACKAGE_ROOT = Path("/root/.codex/skills/course-lab-report")


class TestRecoveryContractPlaceholder(unittest.TestCase):
    def test_recovery_docs_exist(self) -> None:
        required = [
            PACKAGE_ROOT / "references" / "orchestration_rules.md",
            PACKAGE_ROOT / "references" / "recovery_matrix.md",
        ]
        missing = [str(path) for path in required if not path.exists()]
        self.assertEqual([], missing, f"missing recovery docs: {missing}")

    def test_orchestration_rules_contract(self) -> None:
        text = (PACKAGE_ROOT / "references" / "orchestration_rules.md").read_text(
            encoding="utf-8"
        )
        expected_snippets = [
            "course-lab-discovery",
            "course-lab-finalize-qc",
            "confirmed experiment target",
            "run-plan artifacts",
            "optional leaves",
            "course-lab-handout-normalization",
            "course-lab-run-plan",
            "course-lab-body-scaffold",
            "course-lab-experiment-principle",
            "user confirmation",
            "course-lab-data-processing",
            "course-lab-uncertainty-analysis",
            "course-lab-plotting",
            "course-lab-results-interpretation",
            "course-lab-discussion-ideas",
            "course-lab-final-staging",
            "course-lab-figure-evidence",
            "AI_works/results/<experiment-safe-name>/course_lab_report_state.json",
            "confirmed discovery selections",
            "canonical workspace",
            "artifact paths",
            "stable evidence-plan state",
            "late-stage ownership log",
            "last mutating leaf for each owned late-stage region or bucket",
            "rerun history and the reason for each reroute",
            "agent_proposed_key_results",
            "proposal confirmation state",
            "pending_user",
            "approved",
            "rejected",
            "needs_revision",
            "only approved proposals",
            "preserve unresolved gaps",
            "sequential repair planning",
            "prefer inline recovery",
        ]
        for snippet in expected_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, text)

    def test_leaf_responsibility_matrix_covers_proposal_and_reference_ownership(self) -> None:
        text = (PACKAGE_ROOT / "references" / "leaf_responsibility_matrix.md").read_text(
            encoding="utf-8"
        )
        expected_snippets = [
            "reroute only approved proposals",
            "confirmed-reference reuse",
            "compute newly required confirmed quantities on rerun",
            "comparison-ready",
            "consume confirmed comparison artifacts and confirmed references",
            "literature search",
        ]
        for snippet in expected_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, text)

    def test_recovery_matrix_contract(self) -> None:
        text = (PACKAGE_ROOT / "references" / "recovery_matrix.md").read_text(
            encoding="utf-8"
        )
        expected_snippets = [
            "controller-state ownership log",
            "last mutating owner",
            "earliest upstream leaf that can safely re-own the broken region",
            "record that fallback",
            "course-lab-body-scaffold",
            "course-lab-run-plan",
            "course-lab-results-interpretation",
            "course-lab-discussion-ideas",
            "course-lab-discussion-synthesis",
            "course-lab-final-staging",
            "course-lab-data-processing",
            "course-lab-uncertainty-analysis",
            "course-lab-plotting",
            "compress-png",
            "page-count shortfall",
            "more detail",
            "mathematical procedures",
            "downstream late-stage reruns",
            "record that fallback in the controller state",
            "unresolved gaps stay visible",
            "sequential repair planning",
            "inline repair",
        ]
        for snippet in expected_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, text)


if __name__ == "__main__":
    unittest.main()
