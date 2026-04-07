from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = SKILL_DIR / "scripts"
if str(SCRIPT_DIR) in sys.path:
    sys.path.remove(str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR))
sys.modules.pop("common", None)

from build_run_plan import build_run_plan


FIXTURES = Path(__file__).resolve().parent / "fixtures"
SCRIPT = SCRIPT_DIR / "build_run_plan.py"
EXPECTED_LEAF_SKILL_BUCKET_KEYS = (
    "course-lab-body-scaffold",
    "course-lab-experiment-principle",
    "course-lab-data-transfer",
    "course-lab-data-processing",
    "course-lab-plotting",
    "course-lab-results-interpretation",
    "course-lab-discussion-ideas",
    "course-lab-discussion-synthesis",
    "course-lab-final-staging",
    "course-lab-figure-evidence",
)
EXPECTED_BUCKET_SHAPE_KEYS = (
    "status",
    "required_inputs_from_handout",
    "candidate_sections",
    "required_outputs_or_deliverables",
    "suggested_focus",
    "enrichment_opportunities",
    "unresolved_gaps",
)


class BuildRunPlanTests(unittest.TestCase):
    def load_sections(self) -> dict[str, object]:
        return json.loads((FIXTURES / "sample_sections.json").read_text(encoding="utf-8"))

    def test_build_run_plan_emits_top_level_contract_and_bucket_keys(self) -> None:
        plan = build_run_plan(
            sections=self.load_sections(),
            sections_markdown=(FIXTURES / "sample_sections.md").read_text(encoding="utf-8"),
            workspace=Path("/tmp/demo"),
            experiment_name="Interference Lab",
            experiment_safe_name="interference_lab",
            report_language="English",
        )

        self.assertEqual(
            set(plan.keys()),
            {
                "plan_metadata",
                "source_artifacts",
                "run_readiness",
                "leaf_skill_handoffs",
                "comparison_obligations",
                "global_enrichment_opportunities",
                "global_unresolved_gaps",
            },
        )
        self.assertEqual(plan["plan_metadata"]["experiment_safe_name"], "interference_lab")
        self.assertEqual(plan["plan_metadata"]["experiment_name"], "Interference Lab")
        self.assertEqual(plan["plan_metadata"]["workspace"], "/tmp/demo")
        self.assertEqual(plan["source_artifacts"]["workspace"], "/tmp/demo")
        self.assertEqual(
            set(plan["leaf_skill_handoffs"].keys()),
            set(EXPECTED_LEAF_SKILL_BUCKET_KEYS),
        )
        for bucket in plan["leaf_skill_handoffs"].values():
            self.assertEqual(set(bucket.keys()), set(EXPECTED_BUCKET_SHAPE_KEYS))
            self.assertEqual(bucket["status"], "pending")
            for field_name in EXPECTED_BUCKET_SHAPE_KEYS[1:]:
                self.assertIsInstance(bucket[field_name], list)
        self.assertEqual(
            set(plan["run_readiness"].keys()),
            {
                "has_procedure_content",
                "has_required_observations",
                "has_explicit_deliverables",
                "has_data_tables",
                "has_plotting_requirements",
                "has_thinking_questions",
                "has_figure_or_photo_requirements",
            },
        )
        self.assertTrue(plan["run_readiness"]["has_procedure_content"])
        self.assertTrue(plan["run_readiness"]["has_required_observations"])
        self.assertFalse(plan["run_readiness"]["has_explicit_deliverables"])
        self.assertIsInstance(plan["comparison_obligations"], list)
        self.assertFalse(plan["global_unresolved_gaps"])

    def test_build_run_plan_emits_comparison_obligations_for_handout_required_results(self) -> None:
        plan = build_run_plan(
            sections=self.load_sections(),
            sections_markdown=(FIXTURES / "sample_sections.md").read_text(encoding="utf-8"),
            workspace=Path("/tmp/demo"),
            experiment_name="Interference Lab",
            experiment_safe_name="interference_lab",
            report_language="English",
        )

        obligation_names = {item["name"] for item in plan["comparison_obligations"]}
        self.assertIn("fringe_spacing", obligation_names)
        self.assertIn("wavelength", obligation_names)

        fringe_spacing = next(item for item in plan["comparison_obligations"] if item["name"] == "fringe_spacing")
        self.assertEqual(fringe_spacing["importance_origin"], "handout_required")
        self.assertEqual(fringe_spacing["confirmation_state"], "confirmed")
        self.assertIn("theory_vs_data", fringe_spacing["required_lanes"])
        self.assertIn("handout_standard", fringe_spacing["supporting_bases"])

    def test_build_run_plan_promotes_approved_agent_results_without_promoting_pending_ones(self) -> None:
        plan = build_run_plan(
            sections=self.load_sections(),
            sections_markdown=(FIXTURES / "sample_sections.md").read_text(encoding="utf-8"),
            workspace=Path("/tmp/demo"),
            experiment_name="Interference Lab",
            experiment_safe_name="interference_lab",
            report_language="English",
            confirmed_agent_key_results=[
                {
                    "name": "mode_shape_case_4",
                    "label": "Case 4 mode shape",
                    "result_kind": "qualitative",
                    "importance_reason": "Central mode-identification result",
                },
                {
                    "name": "candidate_pending_result",
                    "label": "Pending user result",
                    "confirmation_state": "pending_user",
                    "result_kind": "qualitative",
                },
            ],
        )

        obligation_names = {item["name"] for item in plan["comparison_obligations"]}
        self.assertIn("mode_shape_case_4", obligation_names)
        self.assertNotIn("candidate_pending_result", obligation_names)

        promoted = next(item for item in plan["comparison_obligations"] if item["name"] == "mode_shape_case_4")
        self.assertEqual(promoted["importance_origin"], "agent_confirmed")
        self.assertEqual(promoted["confirmation_state"], "confirmed")

    def test_build_run_plan_rejects_helper_variables_and_keeps_lane_whitelists(self) -> None:
        plan = build_run_plan(
            sections=self.load_sections(),
            sections_markdown=(FIXTURES / "sample_sections.md").read_text(encoding="utf-8"),
            workspace=Path("/tmp/demo"),
            experiment_name="Interference Lab",
            experiment_safe_name="interference_lab",
            report_language="English",
            confirmed_agent_key_results=[
                {
                    "name": "lambda_helper",
                    "label": "Lambda helper",
                    "result_kind": "quantitative",
                }
            ],
        )

        obligation_names = {item["name"] for item in plan["comparison_obligations"]}
        self.assertNotIn("lambda_helper", obligation_names)
        for obligation in plan["comparison_obligations"]:
            self.assertTrue(
                set(obligation["required_lanes"]).issubset(
                    {"theory_vs_data", "simulation_vs_data", "literature_report_vs_data"}
                )
            )
            self.assertTrue(
                set(obligation.get("optional_lanes", [])).issubset(
                    {"theory_vs_data", "simulation_vs_data", "literature_report_vs_data"}
                )
            )
            self.assertTrue(
                set(obligation.get("supporting_bases", [])).issubset(
                    {"handout_standard", "internet_reference"}
                )
            )

    def test_builder_synthesizes_deliverables_focus_and_enrichment_for_each_bucket(self) -> None:
        plan = build_run_plan(
            sections=self.load_sections(),
            sections_markdown=(FIXTURES / "sample_sections.md").read_text(encoding="utf-8"),
            workspace=Path("/tmp/demo"),
            experiment_name="Interference Lab",
            experiment_safe_name="interference_lab",
            report_language="English",
        )

        for bucket_key, bucket in plan["leaf_skill_handoffs"].items():
            self.assertTrue(
                bucket["required_outputs_or_deliverables"],
                msg=f"{bucket_key} should expose at least one downstream deliverable",
            )
            self.assertTrue(
                bucket["suggested_focus"],
                msg=f"{bucket_key} should expose at least one suggested focus",
            )
            self.assertTrue(
                bucket["enrichment_opportunities"],
                msg=f"{bucket_key} should expose at least one enrichment opportunity",
            )

        self.assertTrue(plan["global_enrichment_opportunities"])
        self.assertTrue(
            any(
                "theory" in item.lower() or "compare" in item.lower()
                for item in plan["leaf_skill_handoffs"]["course-lab-results-interpretation"]["suggested_focus"]
            )
        )
        self.assertTrue(
            any(
                "photo" in item.lower() or "figure" in item.lower()
                for item in plan["leaf_skill_handoffs"]["course-lab-figure-evidence"]["enrichment_opportunities"]
            )
        )

    def test_builder_routes_known_handout_cues_to_expected_leaf_skills(self) -> None:
        plan = build_run_plan(
            sections=self.load_sections(),
            sections_markdown=(FIXTURES / "sample_sections.md").read_text(encoding="utf-8"),
            workspace=Path("/tmp/demo"),
            experiment_name="Interference Lab",
            experiment_safe_name="interference_lab",
            report_language="English",
        )

        self.assertTrue(
            any(
                "procedure" in item.lower()
                for item in plan["leaf_skill_handoffs"]["course-lab-body-scaffold"]["required_inputs_from_handout"]
            )
        )
        self.assertTrue(
            any(
                "principle" in item.lower() or "introduction" in item.lower()
                for item in plan["leaf_skill_handoffs"]["course-lab-experiment-principle"]["candidate_sections"]
            )
        )
        self.assertTrue(
            any(
                "table" in item.lower() or "data" in item.lower()
                for item in plan["leaf_skill_handoffs"]["course-lab-data-transfer"]["required_inputs_from_handout"]
            )
        )

    def test_builder_allows_multi_bucket_routing_when_one_item_serves_multiple_skills(self) -> None:
        sections = self.load_sections()
        cue = "Compare the plotted curve with the photographed pattern for each configuration."
        sections["sections"]["analysis_cues"]["list_items"].append(cue)

        plan = build_run_plan(
            sections=sections,
            sections_markdown=(FIXTURES / "sample_sections.md").read_text(encoding="utf-8"),
            workspace=Path("/tmp/demo"),
            experiment_name="Interference Lab",
            experiment_safe_name="interference_lab",
            report_language="English",
        )

        self.assertIn(
            cue,
            plan["leaf_skill_handoffs"]["course-lab-plotting"]["required_inputs_from_handout"],
        )
        self.assertIn(
            cue,
            plan["leaf_skill_handoffs"]["course-lab-figure-evidence"]["required_inputs_from_handout"],
        )

    def test_builder_surfaces_simulation_cues_as_final_staging_appendix_hooks(self) -> None:
        sections = self.load_sections()
        cue = (
            "Use Mathematica or Matlab to simulate the mode pattern and attach the major code in the appendix "
            "for the final report comparison."
        )
        sections["sections"]["analysis_cues"]["list_items"].append(cue)

        plan = build_run_plan(
            sections=sections,
            sections_markdown=(FIXTURES / "sample_sections.md").read_text(encoding="utf-8"),
            workspace=Path("/tmp/demo"),
            experiment_name="Interference Lab",
            experiment_safe_name="interference_lab",
            report_language="English",
        )

        final_staging_bucket = plan["leaf_skill_handoffs"]["course-lab-final-staging"]
        combined_text = "\n".join(
            final_staging_bucket["required_outputs_or_deliverables"]
            + final_staging_bucket["suggested_focus"]
            + final_staging_bucket["enrichment_opportunities"]
        ).lower()

        self.assertIn("appendix", combined_text)
        self.assertTrue("code" in combined_text or "mathematica" in combined_text or "matlab" in combined_text)
        self.assertNotIn("/tmp/demo", combined_text)

    def test_builder_surfaces_ambiguous_items_in_local_and_global_unresolved_gaps(self) -> None:
        sections = self.load_sections()
        unresolved_note = "Deliverable details missing: specify which comparison figure to submit."
        sections["sections"]["analysis_cues"]["list_items"].append(unresolved_note)

        plan = build_run_plan(
            sections=sections,
            sections_markdown=(FIXTURES / "sample_sections.md").read_text(encoding="utf-8"),
            workspace=Path("/tmp/demo"),
            experiment_name="Interference Lab",
            experiment_safe_name="interference_lab",
            report_language="English",
        )

        self.assertIn(
            unresolved_note,
            plan["leaf_skill_handoffs"]["course-lab-figure-evidence"]["unresolved_gaps"],
        )
        self.assertIn(
            unresolved_note,
            plan["global_unresolved_gaps"],
        )

    def test_cli_writes_json_and_markdown_from_same_contract(self) -> None:
        sections = self.load_sections()
        unresolved_note = "Deliverable details missing: specify which comparison figure to submit."
        sections["sections"]["analysis_cues"]["list_items"].append(unresolved_note)

        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            sections_json = root / "sample_sections.json"
            sections_markdown = root / "sample_sections.md"
            confirmed_agent_key_results_json = root / "confirmed_agent_key_results.json"
            output_json = root / "interference_lab_run_plan.json"
            output_markdown = root / "interference_lab_run_plan.md"

            sections_json.write_text(json.dumps(sections, indent=2), encoding="utf-8")
            sections_markdown.write_text((FIXTURES / "sample_sections.md").read_text(encoding="utf-8"), encoding="utf-8")
            confirmed_agent_key_results_json.write_text(
                json.dumps(
                    [
                        {
                            "name": "mode_shape_case_4",
                            "label": "Case 4 mode shape",
                            "result_kind": "qualitative",
                            "importance_reason": "Central mode-identification result",
                        }
                    ],
                    indent=2,
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--sections-json",
                    str(sections_json),
                    "--sections-markdown",
                    str(sections_markdown),
                    "--workspace",
                    str(root),
                    "--experiment-name",
                    "Interference Lab",
                    "--experiment-safe-name",
                    "interference_lab",
                    "--report-language",
                    "English",
                    "--confirmed-agent-key-results-json",
                    str(confirmed_agent_key_results_json),
                    "--output-json",
                    str(output_json),
                    "--output-markdown",
                    str(output_markdown),
                ],
                check=True,
            )

            payload = json.loads(output_json.read_text(encoding="utf-8"))
            markdown = output_markdown.read_text(encoding="utf-8")

            self.assertTrue(output_json.exists())
            self.assertTrue(output_markdown.exists())
            for bucket_key in payload["leaf_skill_handoffs"]:
                self.assertIn(bucket_key, markdown)
            self.assertIn("Comparison Obligations", markdown)
            self.assertTrue(any(item["name"] == "mode_shape_case_4" for item in payload["comparison_obligations"]))
            self.assertIn("Global Unresolved Gaps", markdown)
            self.assertIn(unresolved_note, markdown)
