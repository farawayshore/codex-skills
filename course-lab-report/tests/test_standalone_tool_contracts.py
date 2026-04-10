import unittest
from pathlib import Path
import re

PACKAGE_ROOT = Path("/root/.codex/skills/course-lab-report")
SKILLS_ROOT = Path("/root/.codex/skills")
COURSE_LAB_DIRS = [
    path for path in sorted(SKILLS_ROOT.glob("course-lab-*")) if path.is_dir()
]
SKILL_PACKAGES = [path for path in COURSE_LAB_DIRS if (path / "SKILL.md").exists()]
LEAF_SKILLS = [
    path / "SKILL.md" for path in SKILL_PACKAGES if path.name != "course-lab-report"
]
NON_SKILL_PACKAGE_ALLOWLIST: set[str] = set()
REQUIRED_STANDALONE_SECTIONS = [
    "## Standalone Tool Contract",
    "### Use Independently When",
    "### Minimum Inputs",
    "### Optional Workflow Inputs",
    "### Procedure",
    "### Outputs",
    "### Validation",
    "### Failure / Reroute Signals",
    "### Non-Ownership",
    "## Optional Workflow Metadata",
]
REDUNDANT_TOP_LEVEL_HEADING_PATTERNS = {
    "## When to Use": re.compile(r"^## When [Tt]o Use\s*$", re.MULTILINE),
    "## Output Contract": re.compile(r"^## Output Contract\s*$", re.MULTILINE),
}
REDUNDANT_TOP_LEVEL_HEADING_ALLOWLIST: dict[str, set[str]] = {}
RELATIVE_ASSET_REFERENCE_RE = re.compile(
    r"`((?:scripts|tests|references|agents)/[^`\s]+)`"
)


class TestStandaloneToolContracts(unittest.TestCase):
    def test_course_lab_directories_have_skill_markdown_unless_allowlisted(self) -> None:
        unexpected = [
            path.name
            for path in COURSE_LAB_DIRS
            if path.name not in NON_SKILL_PACKAGE_ALLOWLIST and not (path / "SKILL.md").exists()
        ]
        self.assertEqual(
            [],
            unexpected,
            "Every course-lab-* package directory must either ship SKILL.md or be "
            f"explicitly allowlisted: {unexpected}",
        )

    def test_catalog_references_exist(self) -> None:
        required = [
            "tool_catalog.md",
            "full_workflow_routing.md",
            "examiner_rubric.md",
            "senior_advice_contract.md",
        ]
        missing = [
            name for name in required if not (PACKAGE_ROOT / "references" / name).exists()
        ]
        self.assertEqual([], missing)

    def test_parent_is_optional_catalog_not_required_for_leaf_tools(self) -> None:
        text = (PACKAGE_ROOT / "SKILL.md").read_text(encoding="utf-8")
        for snippet in [
            "optional full-workflow catalog/router",
            "leaf tools remain independently usable",
            "not required for standalone leaf-tool use",
            "controller-state requirements apply only to full-report orchestration",
        ]:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, text)

    def test_every_leaf_has_complete_standalone_tool_contract(self) -> None:
        self.assertGreaterEqual(len(LEAF_SKILLS), 17)
        for skill_path in LEAF_SKILLS:
            text = skill_path.read_text(encoding="utf-8")
            for section in REQUIRED_STANDALONE_SECTIONS:
                with self.subTest(skill=skill_path.parent.name, section=section):
                    self.assertIn(section, text)

    def test_redundant_heading_allowlist_is_explicit_and_valid(self) -> None:
        known_skills = {skill_path.parent.name for skill_path in LEAF_SKILLS}
        known_headings = set(REDUNDANT_TOP_LEVEL_HEADING_PATTERNS)
        for skill_name, headings in REDUNDANT_TOP_LEVEL_HEADING_ALLOWLIST.items():
            with self.subTest(skill=skill_name):
                self.assertIn(skill_name, known_skills)
            for heading in headings:
                with self.subTest(skill=skill_name, heading=heading):
                    self.assertIn(heading, known_headings)

    def test_leaf_skills_do_not_keep_redundant_top_level_headings_unless_allowlisted(
        self,
    ) -> None:
        unexpected = []
        for skill_path in LEAF_SKILLS:
            skill_name = skill_path.parent.name
            text = skill_path.read_text(encoding="utf-8")
            allowlisted = REDUNDANT_TOP_LEVEL_HEADING_ALLOWLIST.get(skill_name, set())
            for heading, pattern in REDUNDANT_TOP_LEVEL_HEADING_PATTERNS.items():
                if pattern.search(text) and heading not in allowlisted:
                    unexpected.append((skill_name, heading))

        self.assertEqual(
            [],
            unexpected,
            "Leaf skills still contain redundant top-level headings; fold unique "
            "content into the standalone contract/body or add an explicit allowlist "
            f"entry: {unexpected}",
        )

    def test_allowlisted_redundant_headings_still_exist(self) -> None:
        for skill_path in LEAF_SKILLS:
            skill_name = skill_path.parent.name
            text = skill_path.read_text(encoding="utf-8")
            for heading in REDUNDANT_TOP_LEVEL_HEADING_ALLOWLIST.get(skill_name, set()):
                pattern = REDUNDANT_TOP_LEVEL_HEADING_PATTERNS[heading]
                with self.subTest(skill=skill_name, heading=heading):
                    self.assertRegex(text, pattern)

    def test_leaf_contracts_do_not_require_parent_or_native_agents_for_standalone_use(self) -> None:
        forbidden_phrases = [
            "must invoke `course-lab-report` first",
            "requires `course-lab-report`",
            "requires the parent controller",
            "requires a native course-lab agent",
            "requires `/root/.codex/agents/course-lab-",
        ]
        for skill_path in LEAF_SKILLS:
            text = skill_path.read_text(encoding="utf-8")
            for phrase in forbidden_phrases:
                with self.subTest(skill=skill_path.parent.name, phrase=phrase):
                    self.assertNotIn(phrase, text)

    def test_relative_asset_references_exist_within_each_skill_package(self) -> None:
        missing: list[tuple[str, str]] = []
        for skill_dir in SKILL_PACKAGES:
            text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
            for rel_path in sorted(set(RELATIVE_ASSET_REFERENCE_RE.findall(text))):
                if not (skill_dir / rel_path).exists():
                    missing.append((skill_dir.name, rel_path))

        self.assertEqual(
            [],
            missing,
            "Relative asset references inside skill docs must resolve within the same "
            f"skill package: {missing}",
        )

    def test_no_native_course_lab_agent_files_created(self) -> None:
        self.assertEqual([], sorted(Path("/root/.codex/agents").glob("course-lab-*.toml")))


if __name__ == "__main__":
    unittest.main()
