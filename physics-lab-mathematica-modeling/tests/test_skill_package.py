from __future__ import annotations

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class PhysicsLabMathematicaModelingPackageTests(unittest.TestCase):
    def test_standalone_skill_contract_files_exist(self) -> None:
        required_paths = [
            SKILL_DIR / "SKILL.md",
            SKILL_DIR / "agents" / "openai.yaml",
            SKILL_DIR / "scripts" / "common.py",
            SKILL_DIR / "scripts" / "validate_modeling_config.py",
            SKILL_DIR / "scripts" / "discover_required_cases.py",
            SKILL_DIR / "scripts" / "build_or_patch_workflow.py",
            SKILL_DIR / "scripts" / "run_wolfram_expr.py",
            SKILL_DIR / "scripts" / "run_python_model.py",
            SKILL_DIR / "scripts" / "run_modeling_case.py",
        ]

        missing = [str(path.relative_to(SKILL_DIR)) for path in required_paths if not path.exists()]
        self.assertEqual(missing, [])

    def test_skill_markdown_uses_local_paths_and_mentions_contract(self) -> None:
        skill_path = SKILL_DIR / "SKILL.md"
        self.assertTrue(skill_path.exists(), f"missing skill doc: {skill_path}")
        text = skill_path.read_text(encoding="utf-8")

        self.assertIn("/root/.codex/skills/physics-lab-mathematica-modeling/scripts/validate_modeling_config.py", text)
        self.assertIn("/root/.codex/skills/physics-lab-mathematica-modeling/scripts/discover_required_cases.py", text)
        self.assertIn("/root/.codex/skills/physics-lab-mathematica-modeling/scripts/build_or_patch_workflow.py", text)
        self.assertIn("/root/.codex/skills/physics-lab-mathematica-modeling/scripts/run_modeling_case.py", text)
        self.assertIn("run_config.json", text)
        self.assertIn("batch", text.lower())
        self.assertIn("strict", text.lower())
        self.assertIn("3 Mathematica", text)
        self.assertIn("3 Python", text)
        self.assertIn("Mathematica-first", text)
        self.assertIn("Python fallback", text)
        self.assertIn("handout expectation", text.lower())
        self.assertIn("local copied", text.lower())
        self.assertNotIn("modern-physics-latex-report-rennovated", text)
        self.assertNotIn("mathematica-calculus/scripts/run_calculus.py", text)

    def test_agent_prompt_mentions_fallback_and_handout_expectations(self) -> None:
        prompt_path = SKILL_DIR / "agents" / "openai.yaml"
        self.assertTrue(prompt_path.exists(), f"missing agent prompt: {prompt_path}")
        text = prompt_path.read_text(encoding="utf-8")

        self.assertIn("batch", text.lower())
        self.assertIn("strict", text.lower())
        self.assertIn("Mathematica-first", text)
        self.assertIn("Python fallback", text)
        self.assertIn("handout", text.lower())
        self.assertIn("expectation", text.lower())
        self.assertIn("local copied scripts", text.lower())


if __name__ == "__main__":
    unittest.main()
