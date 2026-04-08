from __future__ import annotations

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class CourseLabDiscoveryPackageTests(unittest.TestCase):
    def test_skill_and_agent_describe_same_experiment_reference_bundle(self) -> None:
        skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        agent_text = (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")

        for text in (skill_text, agent_text):
            self.assertIn("same-experiment", text.lower())
            self.assertIn("reference", text.lower())
            self.assertIn("multiple", text.lower())
            self.assertIn("selected_reference_reports", text)
            self.assertIn("reference_selection_status", text)
            self.assertIn("does not decode", text.lower())


if __name__ == "__main__":
    unittest.main()
