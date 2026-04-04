from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from discover_current_family import discover_current_family  # noqa: E402


class DiscoverCurrentFamilyTests(unittest.TestCase):
    def make_temp_root(self) -> Path:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(root))
        return root

    def test_uses_frontmatter_name_when_folder_name_is_legacy_alias(self) -> None:
        root = self.make_temp_root()
        legacy = root / "modern-physics-latex-report-rennovated"
        (legacy / "scripts").mkdir(parents=True)
        (legacy / "SKILL.md").write_text(
            "---\nname: course-lab-report\ndescription: Use when...\n---\n",
            encoding="utf-8",
        )

        snapshot = discover_current_family(root, {"course-lab-report"})

        self.assertIn("course-lab-report", snapshot["skills"])
        self.assertEqual(
            snapshot["skills"]["course-lab-report"]["folder_name"],
            "modern-physics-latex-report-rennovated",
        )
        self.assertTrue(snapshot["skills"]["course-lab-report"]["legacy_alias"])

    def test_snapshot_includes_scripts_references_and_agents(self) -> None:
        root = self.make_temp_root()
        skill = root / "course-lab-discovery"
        (skill / "scripts").mkdir(parents=True)
        (skill / "references").mkdir()
        (skill / "agents").mkdir()
        (skill / "SKILL.md").write_text(
            "---\nname: course-lab-discovery\ndescription: Use when...\n---\n",
            encoding="utf-8",
        )
        (skill / "scripts" / "discover_sources.py").write_text("print('ok')\n", encoding="utf-8")
        (skill / "references" / "notes.md").write_text("# notes\n", encoding="utf-8")
        (skill / "agents" / "openai.yaml").write_text("interface:\n", encoding="utf-8")

        snapshot = discover_current_family(root, {"course-lab-discovery"})

        current = snapshot["skills"]["course-lab-discovery"]
        self.assertIn("scripts/discover_sources.py", current["files"])
        self.assertIn("references/notes.md", current["files"])
        self.assertIn("agents/openai.yaml", current["files"])


if __name__ == "__main__":
    unittest.main()
