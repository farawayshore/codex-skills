from __future__ import annotations

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class CourseLabPlottingPackageTests(unittest.TestCase):
    def test_standalone_skill_contract_files_exist(self) -> None:
        required_paths = [
            SKILL_DIR / "SKILL.md",
            SKILL_DIR / "agents" / "openai.yaml",
            SKILL_DIR / "vendor" / "matplotlib",
            SKILL_DIR / "scripts" / "common.py",
            SKILL_DIR / "scripts" / "build_plot_job.py",
            SKILL_DIR / "scripts" / "detect_special_points.py",
            SKILL_DIR / "scripts" / "write_plot_manifest.py",
            SKILL_DIR / "scripts" / "render_plot.py",
        ]

        missing = [str(path.relative_to(SKILL_DIR)) for path in required_paths if not path.exists()]
        self.assertEqual(missing, [])

    def test_skill_markdown_uses_local_paths_only(self) -> None:
        skill_path = SKILL_DIR / "SKILL.md"
        self.assertTrue(skill_path.exists(), "SKILL.md must exist before content checks run")

        text = skill_path.read_text(encoding="utf-8")

        self.assertIn("/root/.codex/skills/course-lab-plotting/scripts/build_plot_job.py", text)
        self.assertIn("/root/.codex/skills/course-lab-plotting/scripts/detect_special_points.py", text)
        self.assertIn("/root/.codex/skills/course-lab-plotting/scripts/write_plot_manifest.py", text)
        self.assertIn("/root/.codex/skills/course-lab-plotting/scripts/render_plot.py", text)
        self.assertIn("matplotlib", text.lower())
        self.assertIn("vendor", text.lower())
        self.assertIn("special point", text.lower())
        self.assertIn("color", text.lower())
        self.assertIn("standalone", text.lower())
        self.assertNotIn("modern-physics-latex-report-rennovated", text)

    def test_agent_prompt_requires_honest_annotations_and_styling(self) -> None:
        agent_path = SKILL_DIR / "agents" / "openai.yaml"
        self.assertTrue(agent_path.exists(), "agents/openai.yaml must exist before prompt checks run")

        text = agent_path.read_text(encoding="utf-8")

        self.assertIn("plot", text.lower())
        self.assertIn("special", text.lower())
        self.assertIn("unresolved", text.lower())
        self.assertIn("color", text.lower())
        self.assertIn("local", text.lower())
        self.assertIn("matplotlib", text.lower())


if __name__ == "__main__":
    unittest.main()
