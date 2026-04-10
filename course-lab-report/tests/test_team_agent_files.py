import unittest
from pathlib import Path


AGENTS_ROOT = Path("/root/.codex/agents")
EXPECTED_AGENT_SNIPPETS = {
    "course-lab-preparer.toml": [
        ['name = "course-lab-preparer"'],
        ["optional course-lab team overlay", "optional overlay"],
        ["standalone leaf tools remain first-class", "standalone leaf-tool use"],
        ["course-lab-discovery"],
        ["course-lab-handout-normalization"],
        ["course-lab-run-plan"],
        ["persistent decoded", "decoded markdown and json artifacts"],
        ["late-stage report prose", "late-stage prose"],
    ],
    "course-lab-data-analyst.toml": [
        ['name = "course-lab-data-analyst"'],
        ["optional course-lab team overlay", "optional overlay"],
        ["standalone leaf tools remain independently usable", "standalone leaf-tool use"],
        ["course-lab-data-processing"],
        ["course-lab-results-interpretation"],
        ["agent_proposed_key_results"],
        [
            "silently promote `agent_proposed_key_results`",
            "silently expand scientific scope",
            "cannot silently promote them",
            "must not promote new key results without leader confirmation",
        ],
        ["final report prose", "must not become the final report writer"],
    ],
    "course-lab-writer.toml": [
        ['name = "course-lab-writer"'],
        ["optional overlay only", "optional overlay"],
        ["standalone leaf-tool use"],
        ["course-lab-experiment-principle"],
        ["course-lab-final-staging"],
        ["course-lab-figure-evidence"],
        [
            "only late-stage `.tex` mutator",
            "only lane that should own late-stage `.tex` mutation",
        ],
    ],
    "course-lab-discussioner.toml": [
        ['name = "course-lab-discussioner"'],
        ["optional overlay only", "optional overlay"],
        ["standalone leaf-tool use"],
        ["course-lab-discussion-ideas"],
        ["course-lab-discussion-synthesis"],
        [
            "must not mutate final tex",
            "must not directly mutate the final tex draft",
            "you do not mutate the final report",
        ],
        ["thinking-question"],
        ["future work", "planned extension"],
    ],
    "course-lab-examiner.toml": [
        ['name = "course-lab-examiner"'],
        ["optional overlay", "optional overlay only"],
        ["standalone leaf-tool use"],
        ["course-lab-finalize-qc"],
        ["references/examiner_rubric.md"],
        ["score/ticket-only", "teacher-style evaluator"],
        ["must not directly repair report prose", "direct report repair"],
        ["downstream rerun requirements"],
    ],
    "course-lab-senior.toml": [
        ['name = "course-lab-senior"'],
        ["optional overlay", "optional overlay only"],
        ["standalone leaf-tool use"],
        ["references/senior_advice_contract.md"],
        ["senior-source"],
        ["reference-report"],
        ["generic"],
        ["style-only"],
        ["must not invent real senior preferences", "invented real senior preferences"],
        ["advisory"],
    ],
}


class TestTeamAgentFiles(unittest.TestCase):
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

    def test_expected_agent_files_exist(self) -> None:
        missing = [
            name for name in EXPECTED_AGENT_SNIPPETS if not (AGENTS_ROOT / name).exists()
        ]
        self.assertEqual([], missing)

    def test_each_agent_file_declares_required_role_contract_snippets(self) -> None:
        for file_name, snippets in EXPECTED_AGENT_SNIPPETS.items():
            text = (AGENTS_ROOT / file_name).read_text(encoding="utf-8").lower()
            for alternatives in snippets:
                with self.subTest(file=file_name, alternatives=alternatives):
                    self.assert_contains_any(
                        text,
                        [option.lower() for option in alternatives],
                        label=file_name,
                    )

    def test_each_agent_file_mentions_non_required_standalone_safety(self) -> None:
        for file_name in EXPECTED_AGENT_SNIPPETS:
            text = (AGENTS_ROOT / file_name).read_text(encoding="utf-8").lower()
            expectations = [[
                "standalone leaf-tool use",
                "standalone leaf tools remain",
                "never required for standalone skill use",
                "prerequisite for independent tool use",
            ]]
            for alternatives in expectations:
                with self.subTest(file=file_name, alternatives=alternatives):
                    self.assert_contains_any(
                        text,
                        [option.lower() for option in alternatives],
                        label=f"{file_name} standalone safety",
                    )

    def test_examiner_and_senior_files_reference_existing_contract_docs(self) -> None:
        examiner_text = (AGENTS_ROOT / "course-lab-examiner.toml").read_text(
            encoding="utf-8"
        )
        senior_text = (AGENTS_ROOT / "course-lab-senior.toml").read_text(
            encoding="utf-8"
        )
        self.assertIn("references/examiner_rubric.md", examiner_text)
        self.assertIn("references/senior_advice_contract.md", senior_text)


if __name__ == "__main__":
    unittest.main()
