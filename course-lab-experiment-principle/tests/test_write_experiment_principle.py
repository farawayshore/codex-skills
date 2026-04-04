from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = SKILL_DIR / "scripts"


class WriteExperimentPrincipleTests(unittest.TestCase):
    def run_writer(
        self,
        report_tex: str,
        sections_payload: dict[str, object],
        figures_payload: dict[str, object],
        *,
        sections_markdown: str | None = None,
        provide_sections_markdown_path: bool = False,
        parent_section: str | None = None,
    ) -> tuple[dict[str, object], str, str]:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            report_path = root / "main.tex"
            sections_path = root / "sections.json"
            sections_markdown_path = root / "sections.md"
            figures_path = root / "principle_figures.json"
            output_json = root / "principle_ownership.json"
            output_unresolved = root / "principle_unresolved.md"

            report_path.write_text(report_tex, encoding="utf-8")
            sections_path.write_text(json.dumps(sections_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            if sections_markdown is not None:
                sections_markdown_path.write_text(sections_markdown, encoding="utf-8")
            figures_path.write_text(json.dumps(figures_payload, ensure_ascii=False, indent=2), encoding="utf-8")

            command = [
                sys.executable,
                str(SCRIPT_DIR / "write_experiment_principle.py"),
                "--sections-json",
                str(sections_path),
                "--report-tex",
                str(report_path),
                "--figures-json",
                str(figures_path),
                "--output-json",
                str(output_json),
                "--output-unresolved",
                str(output_unresolved),
            ]
            if sections_markdown is not None or provide_sections_markdown_path:
                command.extend(["--sections-markdown", str(sections_markdown_path)])
            if parent_section is not None:
                command.extend(["--parent-section", parent_section])

            subprocess.run(command, check=True)

            payload = json.loads(output_json.read_text(encoding="utf-8"))
            tex = report_path.read_text(encoding="utf-8")
            unresolved = output_unresolved.read_text(encoding="utf-8")
            return payload, tex, unresolved

    def run_writer_failure(
        self,
        report_tex: str,
        sections_payload: dict[str, object],
        figures_payload: dict[str, object],
        *,
        sections_markdown: str | None = None,
        provide_sections_markdown_path: bool = False,
        parent_section: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            report_path = root / "main.tex"
            sections_path = root / "sections.json"
            sections_markdown_path = root / "sections.md"
            figures_path = root / "principle_figures.json"
            output_json = root / "principle_ownership.json"
            output_unresolved = root / "principle_unresolved.md"

            report_path.write_text(report_tex, encoding="utf-8")
            sections_path.write_text(json.dumps(sections_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            if sections_markdown is not None:
                sections_markdown_path.write_text(sections_markdown, encoding="utf-8")
            figures_path.write_text(json.dumps(figures_payload, ensure_ascii=False, indent=2), encoding="utf-8")

            command = [
                sys.executable,
                str(SCRIPT_DIR / "write_experiment_principle.py"),
                "--sections-json",
                str(sections_path),
                "--report-tex",
                str(report_path),
                "--figures-json",
                str(figures_path),
                "--output-json",
                str(output_json),
                "--output-unresolved",
                str(output_unresolved),
            ]
            if sections_markdown is not None or provide_sections_markdown_path:
                command.extend(["--sections-markdown", str(sections_markdown_path)])
            if parent_section is not None:
                command.extend(["--parent-section", parent_section])

            return subprocess.run(command, check=False, capture_output=True, text=True)

    def test_writer_replaces_owned_sections_and_emits_manifest(self) -> None:
        report_tex = r"""
\section{Introduction}
\NeedsInput{intro}

\section{Background}
\NeedsInput{background}

\section{Experiment Principle}
\NeedsInput{principle}

\section{Results}
KEEP RESULTS
""".strip()

        sections_payload = {
            "sections": {
                "introduction": {"text": "Intro from handout."},
                "background": {"text": "Background from handout."},
                "principle": {"text": "Principle from handout."},
            }
        }
        figures_payload = {"figure_blocks": [], "entries": [], "grouping_questions": []}

        payload, tex, unresolved = self.run_writer(report_tex, sections_payload, figures_payload)

        self.assertIn("Intro from handout.", tex)
        self.assertIn("Background from handout.", tex)
        self.assertIn("Principle from handout.", tex)
        self.assertIn("KEEP RESULTS", tex)
        self.assertEqual(
            payload["owned_sections"],
            ["Introduction", "Background", "Experiment Principle"],
        )
        self.assertEqual(payload["inserted_figures"], [])
        self.assertEqual(payload["unresolved_items"], [])
        self.assertNotIn(r"\NeedsInput{intro}", tex)
        self.assertEqual(unresolved.strip(), "")

    def test_writer_inserts_figures_only_inside_owned_sections(self) -> None:
        report_tex = r"""
\section{Introduction}
\NeedsInput{intro}

\section{Background}
\NeedsInput{background}

\section{Experiment Principle}
\NeedsInput{principle}

\section{Results}
KEEP RESULTS
""".strip()

        sections_payload = {
            "sections": {
                "introduction": {"text": "Intro from handout."},
                "background": {"text": "Background from handout."},
                "principle": {"text": "Principle from handout."},
            }
        }
        figures_payload = {
            "figure_blocks": [
                {
                    "type": "standalone",
                    "label": "fig:principle-01",
                    "caption_text": "Principle schematic",
                    "entries": [
                        {
                            "relative_output_path": "fig-01-principle.jpg",
                            "latex_caption": "Principle schematic",
                            "caption_text": "Principle schematic",
                            "missing_source": False,
                        }
                    ],
                }
            ],
            "entries": [
                {
                    "relative_output_path": "fig-01-principle.jpg",
                    "caption_text": "Principle schematic",
                    "missing_source": False,
                }
            ],
            "grouping_questions": [],
        }

        payload, tex, _ = self.run_writer(report_tex, sections_payload, figures_payload)

        self.assertIn(r"\includegraphics[width=0.92\columnwidth]{principle-images/fig-01-principle.jpg}", tex)
        self.assertLess(
            tex.index(r"\includegraphics[width=0.92\columnwidth]{principle-images/fig-01-principle.jpg}"),
            tex.index(r"\section{Results}"),
        )
        self.assertEqual(payload["inserted_figures"], ["fig-01-principle.jpg"])

    def test_writer_emits_unresolved_for_ambiguous_grouping(self) -> None:
        report_tex = r"""
\section{Introduction}
\NeedsInput{intro}

\section{Background}
\NeedsInput{background}

\section{Experiment Principle}
\NeedsInput{principle}
""".strip()

        sections_payload = {
            "sections": {
                "introduction": {"text": "Intro from handout."},
                "background": {"text": "Background from handout."},
                "principle": {"text": "Principle from handout."},
            }
        }
        figures_payload = {
            "figure_blocks": [
                {
                    "type": "needs_user_grouping",
                    "question": "Pictures A and B, do they belong to the same group?",
                    "entries": [],
                }
            ],
            "entries": [],
            "grouping_questions": [
                {
                    "question": "Pictures A and B, do they belong to the same group?",
                }
            ],
        }

        payload, tex, unresolved = self.run_writer(report_tex, sections_payload, figures_payload)

        self.assertIn(r"\NeedsInput{Pending picture grouping decision:", tex)
        self.assertTrue(payload["unresolved_items"])
        self.assertIn("grouping", json.dumps(payload["unresolved_items"], ensure_ascii=False).lower())
        self.assertIn("Pictures A and B", unresolved)

    def test_writer_preserves_conflicting_user_text(self) -> None:
        report_tex = r"""
\section{Introduction}
\NeedsInput{intro}

\section{Background}
\NeedsInput{background}

\section{Experiment Principle}
User custom principle text.

\section{Results}
KEEP RESULTS
""".strip()

        sections_payload = {
            "sections": {
                "introduction": {"text": "Intro from handout."},
                "background": {"text": "Background from handout."},
                "principle": {"text": "Principle from handout."},
            }
        }
        figures_payload = {"figure_blocks": [], "entries": [], "grouping_questions": []}

        payload, tex, unresolved = self.run_writer(report_tex, sections_payload, figures_payload)

        self.assertIn("User custom principle text.", tex)
        self.assertNotIn("Principle from handout.", tex)
        self.assertIn("Intro from handout.", tex)
        self.assertTrue(payload["unresolved_items"])
        self.assertIn("Experiment Principle", unresolved)

    def test_writer_part_scoped_updates_only_targeted_parent_section(self) -> None:
        report_tex = r"""
\section{Introduction}
KEEP SHARED INTRO

\section{LX1: One-Dimensional Standing Waves}
\subsection{Experiment Principle}
\NeedsInput{lx1 principle}

\section{LX2: Circular Thin-Plate Standing Waves}
\subsection{Experiment Principle}
\NeedsInput{lx2 principle}
""".strip()

        sections_payload = {
            "sections": {
                "principle": {"text": "LX1 principle from handout."},
            }
        }
        figures_payload = {"figure_blocks": [], "entries": [], "grouping_questions": []}

        payload, tex, unresolved = self.run_writer(
            report_tex,
            sections_payload,
            figures_payload,
            parent_section="LX1: One-Dimensional Standing Waves",
        )

        self.assertIn("LX1 principle from handout.", tex)
        self.assertIn(r"\NeedsInput{lx2 principle}", tex)
        self.assertIn("KEEP SHARED INTRO", tex)
        self.assertEqual(payload["mode"], "part-scoped")
        self.assertEqual(payload["target_parent_section"], "LX1: One-Dimensional Standing Waves")
        self.assertNotIn("LX2", unresolved)

    def test_writer_prefers_markdown_over_conflicting_json(self) -> None:
        report_tex = r"""
\section{Introduction}
\NeedsInput{intro}

\section{Background}
\NeedsInput{background}

\section{Experiment Principle}
\NeedsInput{principle}
""".strip()

        sections_payload = {
            "sections": {
                "introduction": {"text": "Intro from JSON."},
                "background": {"text": "Background from JSON."},
                "principle": {"text": "Principle from JSON."},
            }
        }
        sections_markdown = """# Decoded Section Summary

- Title: Sample

## Intro Source

- Normalized key: `introduction`

Intro from Markdown.

## Background Source

- Normalized key: `background`

Background from Markdown.

## Principle Source

- Normalized key: `principle`

Principle from Markdown.
"""
        figures_payload = {"figure_blocks": [], "entries": [], "grouping_questions": []}

        _, tex, _ = self.run_writer(
            report_tex,
            sections_payload,
            figures_payload,
            sections_markdown=sections_markdown,
        )

        self.assertIn("Intro from Markdown.", tex)
        self.assertIn("Background from Markdown.", tex)
        self.assertIn("Principle from Markdown.", tex)
        self.assertNotIn("Intro from JSON.", tex)
        self.assertNotIn("Background from JSON.", tex)
        self.assertNotIn("Principle from JSON.", tex)

    def test_writer_falls_back_to_json_when_markdown_is_missing(self) -> None:
        report_tex = r"""
\section{Introduction}
\NeedsInput{intro}

\section{Background}
\NeedsInput{background}

\section{Experiment Principle}
\NeedsInput{principle}
""".strip()

        sections_payload = {
            "sections": {
                "introduction": {"text": "Intro from JSON."},
                "background": {"text": "Background from JSON."},
                "principle": {"text": "Principle from JSON."},
            }
        }
        figures_payload = {"figure_blocks": [], "entries": [], "grouping_questions": []}

        _, tex, _ = self.run_writer(
            report_tex,
            sections_payload,
            figures_payload,
            provide_sections_markdown_path=True,
        )

        self.assertIn("Intro from JSON.", tex)
        self.assertIn("Background from JSON.", tex)
        self.assertIn("Principle from JSON.", tex)

    def test_writer_rejects_malformed_markdown_instead_of_silent_json_fallback(self) -> None:
        report_tex = r"""
\section{Introduction}
\NeedsInput{intro}

\section{Background}
\NeedsInput{background}

\section{Experiment Principle}
\NeedsInput{principle}
""".strip()

        sections_payload = {
            "sections": {
                "introduction": {"text": "Intro from JSON."},
                "background": {"text": "Background from JSON."},
                "principle": {"text": "Principle from JSON."},
            }
        }
        sections_markdown = """# Decoded Section Summary

## Intro Source

Intro without normalized key metadata.
"""
        figures_payload = {"figure_blocks": [], "entries": [], "grouping_questions": []}

        result = self.run_writer_failure(
            report_tex,
            sections_payload,
            figures_payload,
            sections_markdown=sections_markdown,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Malformed normalized sections markdown", result.stderr)


if __name__ == "__main__":
    unittest.main()
