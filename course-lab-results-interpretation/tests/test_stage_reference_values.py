from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import requests


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = SKILL_DIR / "scripts"
SCRIPT_PATH = SKILL_DIR / "scripts" / "stage_reference_values.py"
if str(SCRIPT_DIR) in sys.path:
    sys.path.remove(str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR))
sys.modules.pop("common", None)

from stage_reference_values import stage_internet_reference


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def write_handout_markdown(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "## Experiment Principle",
                "- Normalized key: `principle`",
                "",
                "Required result families: youngs_modulus, characteristic_frequency",
                "Required observations: node_pattern",
                "Simulation comparison is not required.",
                "Compare data with theory when references are available.",
                "The experiment compares measured results with expected behavior from the handout.",
                "",
            ]
        ),
        encoding="utf-8",
    )


class StageReferenceValuesTests(unittest.TestCase):
    def test_cli_stages_internet_reference_and_merges_seed_references(self) -> None:
        self.assertTrue(SCRIPT_PATH.exists(), f"missing script: {SCRIPT_PATH}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            handout_sections_markdown = tmp / "sections.md"
            processed_data_json = tmp / "processed_data.json"
            seed_references_json = tmp / "seed_references.json"
            search_spec_json = tmp / "search_spec.json"
            search_snapshot_json = tmp / "search_snapshot.json"
            page_snapshot_json = tmp / "page_snapshot.json"
            output_json = tmp / "reference_values.json"
            output_unresolved = tmp / "reference_values_unresolved.md"

            write_handout_markdown(handout_sections_markdown)
            processed_data_json.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "name": "youngs_modulus",
                                "label": "Young's modulus",
                                "value": 2.03e11,
                                "unit": "Pa",
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            seed_references_json.write_text(
                json.dumps(
                    {
                        "comparison_requirements": {
                            "required_bases": [
                                "internet_reference",
                                "theoretical_computation",
                            ],
                            "optional_bases": ["handout_standard"],
                        },
                        "references": [
                            {
                                "name": "youngs_modulus",
                                "label": "Handout stainless reference",
                                "value": 1.95e11,
                                "unit": "Pa",
                                "comparison_basis": "handout_standard",
                                "source": "notes/lx1_sections.md:159",
                            },
                            {
                                "name": "youngs_modulus",
                                "label": "Beam-model inversion",
                                "value": 2.01e11,
                                "unit": "Pa",
                                "comparison_basis": "theoretical_computation",
                                "source": "analysis/theory_checks.json:youngs_modulus",
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            search_spec_json.write_text(
                json.dumps(
                    {
                        "targets": [
                            {
                                "name": "youngs_modulus",
                                "query": "stainless steel young's modulus",
                                "comparison_basis": "internet_reference",
                                "label": "Published stainless steel Young's modulus",
                                "value_regex": "([0-9.]+)\\s*GPa",
                                "unit": "Pa",
                                "unit_scale": 1000000000.0,
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            search_snapshot_json.write_text(
                json.dumps(
                    {
                        "queries": {
                            "stainless steel young's modulus": [
                                {
                                    "url": "https://example.org/material",
                                    "title": "Material data sheet",
                                    "snippet": "Young's modulus is 200 GPa for stainless steel.",
                                }
                            ]
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            page_snapshot_json.write_text(
                json.dumps(
                    {
                        "pages": {
                            "https://example.org/material": "Young's modulus is 200 GPa at room temperature.",
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            completed = run_cli(
                "--handout-sections-markdown",
                str(handout_sections_markdown),
                "--processed-data-json",
                str(processed_data_json),
                "--seed-references-json",
                str(seed_references_json),
                "--search-spec-json",
                str(search_spec_json),
                "--search-snapshot-json",
                str(search_snapshot_json),
                "--page-snapshot-json",
                str(page_snapshot_json),
                "--output-json",
                str(output_json),
                "--output-unresolved",
                str(output_unresolved),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(
                payload["comparison_requirements"]["required_bases"],
                ["internet_reference", "theoretical_computation"],
            )
            references = payload["references"]
            bases = {entry["comparison_basis"] for entry in references}
            self.assertEqual(
                bases,
                {"handout_standard", "internet_reference", "theoretical_computation"},
            )
            internet_entry = next(
                entry for entry in references if entry["comparison_basis"] == "internet_reference"
            )
            self.assertEqual(internet_entry["source"], "https://example.org/material")
            self.assertEqual(internet_entry["value"], 2.0e11)
            self.assertEqual(output_unresolved.read_text(encoding="utf-8"), "None.\n")

    def test_cli_records_unresolved_when_required_internet_reference_is_missing(self) -> None:
        self.assertTrue(SCRIPT_PATH.exists(), f"missing script: {SCRIPT_PATH}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            handout_sections_markdown = tmp / "sections.md"
            processed_data_json = tmp / "processed_data.json"
            search_spec_json = tmp / "search_spec.json"
            search_snapshot_json = tmp / "search_snapshot.json"
            output_json = tmp / "reference_values.json"
            output_unresolved = tmp / "reference_values_unresolved.md"

            write_handout_markdown(handout_sections_markdown)
            processed_data_json.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "name": "characteristic_frequency",
                                "label": "characteristic frequency",
                                "value": 1830.8,
                                "unit": "Hz",
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            search_spec_json.write_text(
                json.dumps(
                    {
                        "comparison_requirements": {
                            "required_bases": ["internet_reference"],
                        },
                        "targets": [
                            {
                                "name": "characteristic_frequency",
                                "query": "circular plate characteristic frequency brass",
                                "comparison_basis": "internet_reference",
                                "label": "Published brass plate frequency",
                                "value_regex": "([0-9.]+)\\s*Hz",
                                "unit": "Hz",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            search_snapshot_json.write_text(
                json.dumps(
                    {
                        "queries": {
                            "circular plate characteristic frequency brass": [],
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            completed = run_cli(
                "--handout-sections-markdown",
                str(handout_sections_markdown),
                "--processed-data-json",
                str(processed_data_json),
                "--search-spec-json",
                str(search_spec_json),
                "--search-snapshot-json",
                str(search_snapshot_json),
                "--output-json",
                str(output_json),
                "--output-unresolved",
                str(output_unresolved),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["references"], [])
            unresolved_text = output_unresolved.read_text(encoding="utf-8").lower()
            self.assertIn("internet reference", unresolved_text)
            self.assertIn("characteristic_frequency", unresolved_text)

    def test_cli_promotes_approved_literature_entries_into_reference_values(self) -> None:
        self.assertTrue(SCRIPT_PATH.exists(), f"missing script: {SCRIPT_PATH}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            handout_sections_markdown = tmp / "sections.md"
            processed_data_json = tmp / "processed_data.json"
            approved_literature_json = tmp / "approved_literature.json"
            search_snapshot_json = tmp / "search_snapshot.json"
            output_json = tmp / "reference_values.json"
            output_unresolved = tmp / "reference_values_unresolved.md"

            write_handout_markdown(handout_sections_markdown)
            processed_data_json.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "name": "wave_speed",
                                "label": "wave speed",
                                "value": 12.5,
                                "unit": "m/s",
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            approved_literature_json.write_text(
                json.dumps(
                    {
                        "approved_results": [
                            {
                                "name": "wave_speed",
                                "comparison_basis": "literature_report",
                                "lane": "literature_report_vs_data",
                                "title": "Standing waves in circular plates",
                                "authors": ["A. Author", "B. Author"],
                                "year": 2024,
                                "source": "https://arxiv.org/abs/2401.12345",
                                "qualitative_finding": "Mode-shape topology matches the observed split ring.",
                                "match_reason": "Same boundary condition and mode family.",
                                "confirmation_state": "approved",
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            search_snapshot_json.write_text(
                json.dumps(
                    {"queries": {"wave speed m/s reference value physics": []}},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            completed = run_cli(
                "--handout-sections-markdown",
                str(handout_sections_markdown),
                "--processed-data-json",
                str(processed_data_json),
                "--approved-literature-json",
                str(approved_literature_json),
                "--search-snapshot-json",
                str(search_snapshot_json),
                "--output-json",
                str(output_json),
                "--output-unresolved",
                str(output_unresolved),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            literature_entry = next(
                entry for entry in payload["references"] if entry["comparison_basis"] == "literature_report"
            )
            self.assertEqual(literature_entry["lane"], "literature_report_vs_data")
            self.assertEqual(literature_entry["title"], "Standing waves in circular plates")
            self.assertEqual(literature_entry["authors"], ["A. Author", "B. Author"])

    def test_cli_does_not_promote_pending_candidate_literature_entries(self) -> None:
        self.assertTrue(SCRIPT_PATH.exists(), f"missing script: {SCRIPT_PATH}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            handout_sections_markdown = tmp / "sections.md"
            processed_data_json = tmp / "processed_data.json"
            approved_literature_json = tmp / "approved_literature.json"
            search_snapshot_json = tmp / "search_snapshot.json"
            output_json = tmp / "reference_values.json"
            output_unresolved = tmp / "reference_values_unresolved.md"

            write_handout_markdown(handout_sections_markdown)
            processed_data_json.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "name": "wave_speed",
                                "label": "wave speed",
                                "value": 12.5,
                                "unit": "m/s",
                            }
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            approved_literature_json.write_text(
                json.dumps(
                    {
                        "approved_results": [
                            {
                                "name": "wave_speed",
                                "comparison_basis": "literature_report",
                                "lane": "literature_report_vs_data",
                                "source": "https://example.org/approved",
                                "title": "Approved source",
                                "confirmation_state": "approved",
                            },
                            {
                                "name": "wave_speed",
                                "comparison_basis": "literature_report",
                                "lane": "literature_report_vs_data",
                                "source": "https://example.org/pending",
                                "title": "candidate source should stay provisional",
                                "confirmation_state": "pending_user",
                            },
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            search_snapshot_json.write_text(
                json.dumps(
                    {"queries": {"wave speed m/s reference value physics": []}},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            completed = run_cli(
                "--handout-sections-markdown",
                str(handout_sections_markdown),
                "--processed-data-json",
                str(processed_data_json),
                "--approved-literature-json",
                str(approved_literature_json),
                "--search-snapshot-json",
                str(search_snapshot_json),
                "--output-json",
                str(output_json),
                "--output-unresolved",
                str(output_unresolved),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            output_text = output_json.read_text(encoding="utf-8")
            self.assertIn("Approved source", output_text)
            self.assertNotIn("candidate source should stay provisional", output_text)

    def test_search_transport_failure_leaves_reference_unstaged(self) -> None:
        with mock.patch(
            "stage_reference_values.live_search",
            side_effect=requests.RequestException("offline"),
        ):
            staged = stage_internet_reference(
                spec={"name": "wave_speed", "query": "wave speed reference", "unit": "m/s"},
                search_snapshot_payload=None,
                page_snapshot_payload=None,
                max_results=3,
                timeout=0.1,
            )

        self.assertIsNone(staged)


if __name__ == "__main__":
    unittest.main()
