from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = SKILL_DIR / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_body_scaffold import build_body_scaffold


FIXTURES = Path(__file__).resolve().parent / "fixtures"
SCRIPT = SCRIPT_DIR / "build_body_scaffold.py"


class BuildBodyScaffoldTests(unittest.TestCase):
    def test_build_body_scaffold_creates_procedure_coverage_and_missing_section_plan(self) -> None:
        sections = json.loads((FIXTURES / "sample_sections.json").read_text(encoding="utf-8"))
        template_text = (FIXTURES / "sample_template.tex").read_text(encoding="utf-8")

        scaffold = build_body_scaffold(sections, template_text)

        section_headings = [entry["heading"] for entry in scaffold["scaffold_sections"]]
        self.assertEqual(section_headings[0], "Introduction")
        self.assertIn("Experimental Process / Experimental Phenomenon", section_headings)
        self.assertIn("Experiment Discussion", section_headings)
        self.assertEqual([item["id"] for item in scaffold["procedures"]], ["P01", "P02", "P03"])
        self.assertIn("Objectives", scaffold["missing_template_sections"])
        self.assertIn("Experiment Equipment", scaffold["missing_template_sections"])
        self.assertIn("% procedure:P01", scaffold["tex_scaffold"])
        self.assertIn(r"\NeedsInput{Describe procedure step P03", scaffold["tex_scaffold"])
        self.assertIn("Assigned Thinking Questions", scaffold["tex_scaffold"])

    def test_build_body_scaffold_separates_reference_entries_from_thinking_questions(self) -> None:
        sections = json.loads((FIXTURES / "sample_sections.json").read_text(encoding="utf-8"))
        sections["sections"]["thinking_questions"] = {
            "heading": "Thinking Questions",
            "pages": [4],
            "text": "[Subheading] References",
            "list_items": [
                "Why does the force curve change with tip-sample distance?",
                "[1] Binnig G, Quate C F, Gerber C. Atomic Force Microscope.",
                "[2] Meyer E. Atomic Force Microscopy.",
            ],
            "equations": [],
            "tables": [],
            "images": [],
            "subheadings": [{"heading": "References", "page": 4}],
        }
        sections["sections"].pop("references")
        sections["section_order"] = [key for key in sections["section_order"] if key != "references"]
        template_text = (FIXTURES / "sample_template.tex").read_text(encoding="utf-8")

        scaffold = build_body_scaffold(sections, template_text)

        self.assertEqual(
            scaffold["thinking_questions"],
            ["Why does the force curve change with tip-sample distance?"],
        )
        self.assertEqual(
            scaffold["references"],
            [
                "[1] Binnig G, Quate C F, Gerber C. Atomic Force Microscope.",
                "[2] Meyer E. Atomic Force Microscopy.",
            ],
        )
        self.assertNotIn("Answer the handout thinking question: [1]", scaffold["tex_scaffold"])
        self.assertIn("Atomic Force Microscope.", scaffold["tex_scaffold"])

    def test_cli_writes_standalone_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            output_json = root / "body_scaffold.json"
            output_markdown = root / "body_scaffold.md"
            output_procedures = root / "sample_procedures.md"
            output_tex = root / "body_scaffold.tex"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--sections-json",
                    str(FIXTURES / "sample_sections.json"),
                    "--template-tex",
                    str(FIXTURES / "sample_template.tex"),
                    "--output-json",
                    str(output_json),
                    "--output-markdown",
                    str(output_markdown),
                    "--output-procedures",
                    str(output_procedures),
                    "--output-tex",
                    str(output_tex),
                ],
                check=True,
            )

            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["template_sections"], ["Introduction", "Experiment Principle", "References"])
            self.assertEqual(payload["procedures"][0]["id"], "P01")
            self.assertTrue(output_markdown.exists())
            self.assertTrue(output_procedures.exists())
            self.assertTrue(output_tex.exists())
            self.assertIn("# Procedures", output_procedures.read_text(encoding="utf-8"))
            self.assertIn("% procedure:P02", output_tex.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
