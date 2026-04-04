from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "run_modeling_case.py"


def load_module(module_path: Path, module_name: str):
    if not module_path.exists():
        raise AssertionError(f"missing module file: {module_path}")

    script_dir = str(module_path.parent)
    inserted = False
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
        inserted = True

    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise AssertionError(f"unable to load module spec: {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if inserted:
            sys.path.pop(0)


class RunModelingCaseBatchTests(unittest.TestCase):
    def make_config(self, root_dir: str) -> dict:
        return {
            "run_id": "batch-demo",
            "experiment": {
                "name": "demo experiment",
                "safe_name": "demo-experiment",
            },
            "objective": "generate demo artifacts",
            "engine_policy": {
                "preferred": "mathematica",
                "allow_python_fallback": True,
            },
            "inputs": {
                "parameters": {"radius_m": 0.12},
                "constants": {},
                "boundary_conditions": {},
                "comparison_targets": [],
            },
            "workflow": {
                "mode": "patch-existing",
                "source_wl": "/tmp/source.wl",
                "source_py": "/tmp/source.py",
                "template_id": "",
            },
            "outputs": {
                "root_dir": root_dir,
            },
            "artifacts_requested": ["summary_json"],
            "discovery": {
                "enabled": False,
                "picture_results_dir": "",
                "parser": "lx2_filename",
            },
            "handout_cases": [],
            "batch_policy": {
                "strict_required_cases": True,
                "include_picture_result_cases": True,
                "include_handout_only_cases": True,
            },
            "retry_policy": {
                "mathematica_attempts": 3,
                "python_attempts": 3,
            },
            "sanity_checks": {
                "enabled": True,
                "geometry_bound_tolerance_ratio": 0.05,
                "check_monotonic_radii": True,
                "check_mode_topology": True,
                "check_positive_derived_values": True,
            },
            "handout_expectations": {
                "required": False,
                "checks": [],
            },
        }

    def write_case_summary(
        self,
        case_dir: Path,
        case_id: str,
        *,
        node_radii_cm: list[float],
        node_count: int,
        radial_node_count: int,
        azimuthal_node_line_count: int,
        k_cm_inverse: float = 2.45,
    ) -> Path:
        summary_path = case_dir / f"{case_id}-summary.json"
        summary_path.write_text(
            json.dumps(
                {
                    "summary": {
                        "node_radii_cm": node_radii_cm,
                        "outer_node_radius_cm": node_radii_cm[-1],
                        "node_count": node_count,
                        "radial_node_count": radial_node_count,
                        "azimuthal_node_line_count": azimuthal_node_line_count,
                        "k_cm_inverse": k_cm_inverse,
                    }
                },
                ensure_ascii=True,
                indent=2,
            ),
            encoding="utf-8",
        )
        return summary_path

    def test_batch_success_writes_batch_and_case_manifests(self) -> None:
        module = load_module(SCRIPT_PATH, "run_modeling_case_batch_success")

        with tempfile.TemporaryDirectory() as tmpdir:
            root_dir = Path(tmpdir) / "batch"
            config = self.make_config(str(root_dir))
            required_cases = [
                {"case_id": "case-a", "parameters": {"m": 0, "n": 4, "radius_m": 0.12}, "sources": ["picture_results"]},
                {"case_id": "case-b", "parameters": {"m": 5, "n": 5, "radius_m": 0.12}, "sources": ["picture_results"]},
            ]

            def fake_discover(normalized: dict) -> dict:
                return {"required_cases": required_cases}

            def fake_builder(case_config: dict, case_dir: Path, engine: str, attempt_context: dict | None = None) -> Path:
                workflow_path = case_dir / ("workflow.generated.wl" if engine == "mathematica" else "workflow.generated.py")
                workflow_path.parent.mkdir(parents=True, exist_ok=True)
                workflow_path.write_text("generated workflow", encoding="utf-8")
                return workflow_path

            def fake_wolfram(workflow_path: Path, timeout: int = 60) -> dict:
                case_dir = workflow_path.parent
                case_id = case_dir.name
                if case_id == "case-a":
                    self.write_case_summary(case_dir, case_id, node_radii_cm=[3.0, 5.0, 7.0, 9.0], node_count=4, radial_node_count=4, azimuthal_node_line_count=0)
                else:
                    self.write_case_summary(case_dir, case_id, node_radii_cm=[2.0, 4.0, 6.0, 8.0, 10.0], node_count=5, radial_node_count=5, azimuthal_node_line_count=10)
                return {"success": True, "stdout": "", "stderr": "", "returncode": 0, "duration_seconds": 0.1}

            with patch.object(module, "validate_modeling_config", side_effect=lambda value: value), \
                 patch.object(module, "discover_required_cases", side_effect=fake_discover), \
                 patch.object(module, "build_or_patch_workflow", side_effect=fake_builder), \
                 patch.object(module, "run_wolfram_workflow", side_effect=fake_wolfram):
                result = module.run_modeling_case(config)

            self.assertTrue(result["success"])
            self.assertTrue((root_dir / "batch_run_result.json").exists())
            self.assertTrue((root_dir / "case-a" / "case_run_result.json").exists())
            self.assertTrue((root_dir / "case-b" / "case_run_result.json").exists())
            self.assertEqual(sorted(result["passed_cases"]), ["case-a", "case-b"])

    def test_strict_batch_fails_after_three_mathematica_and_three_python_attempts(self) -> None:
        module = load_module(SCRIPT_PATH, "run_modeling_case_batch_failure")

        with tempfile.TemporaryDirectory() as tmpdir:
            root_dir = Path(tmpdir) / "batch"
            config = self.make_config(str(root_dir))
            required_cases = [
                {"case_id": "case-a", "parameters": {"m": 0, "n": 4, "radius_m": 0.12}, "sources": ["picture_results"]},
                {"case_id": "case-b", "parameters": {"m": 5, "n": 5, "radius_m": 0.12}, "sources": ["picture_results"]},
            ]
            call_counts = {"mathematica": 0, "python": 0}

            def fake_discover(normalized: dict) -> dict:
                return {"required_cases": required_cases}

            def fake_builder(case_config: dict, case_dir: Path, engine: str, attempt_context: dict | None = None) -> Path:
                workflow_path = case_dir / ("workflow.generated.wl" if engine == "mathematica" else "workflow.generated.py")
                workflow_path.parent.mkdir(parents=True, exist_ok=True)
                workflow_path.write_text("generated workflow", encoding="utf-8")
                return workflow_path

            def fake_wolfram(workflow_path: Path, timeout: int = 60) -> dict:
                call_counts["mathematica"] += 1
                case_id = workflow_path.parent.name
                if case_id == "case-a":
                    self.write_case_summary(workflow_path.parent, case_id, node_radii_cm=[3.0, 5.0, 7.0, 9.0], node_count=4, radial_node_count=4, azimuthal_node_line_count=0)
                    return {"success": True, "stdout": "", "stderr": "", "returncode": 0, "duration_seconds": 0.1}
                return {"success": False, "stdout": "", "stderr": "bad run", "returncode": 1, "duration_seconds": 0.1}

            def fake_python(workflow_path: Path, timeout: int = 60) -> dict:
                call_counts["python"] += 1
                return {"success": False, "stdout": "", "stderr": "bad run", "returncode": 1, "duration_seconds": 0.1}

            with patch.object(module, "validate_modeling_config", side_effect=lambda value: value), \
                 patch.object(module, "discover_required_cases", side_effect=fake_discover), \
                 patch.object(module, "build_or_patch_workflow", side_effect=fake_builder), \
                 patch.object(module, "run_wolfram_workflow", side_effect=fake_wolfram), \
                 patch.object(module, "run_python_workflow", side_effect=fake_python):
                result = module.run_modeling_case(config)

            self.assertFalse(result["success"])
            self.assertEqual(call_counts["mathematica"], 4)
            self.assertEqual(call_counts["python"], 3)
            self.assertIn("case-b", result["failed_cases"])

    def test_geometry_bound_failure_triggers_retries_and_case_failure(self) -> None:
        module = load_module(SCRIPT_PATH, "run_modeling_case_geometry_retry")

        with tempfile.TemporaryDirectory() as tmpdir:
            root_dir = Path(tmpdir) / "batch"
            config = self.make_config(str(root_dir))
            required_cases = [
                {"case_id": "case-a", "parameters": {"m": 5, "n": 5, "radius_m": 0.12}, "sources": ["picture_results"]},
            ]
            call_counts = {"mathematica": 0, "python": 0}

            def fake_discover(normalized: dict) -> dict:
                return {"required_cases": required_cases}

            def fake_builder(case_config: dict, case_dir: Path, engine: str, attempt_context: dict | None = None) -> Path:
                workflow_path = case_dir / ("workflow.generated.wl" if engine == "mathematica" else "workflow.generated.py")
                workflow_path.parent.mkdir(parents=True, exist_ok=True)
                workflow_path.write_text("generated workflow", encoding="utf-8")
                return workflow_path

            def fake_payload(workflow_path: Path, timeout: int = 60) -> dict:
                self.write_case_summary(
                    workflow_path.parent,
                    workflow_path.parent.name,
                    node_radii_cm=[4.0, 7.0, 9.0, 11.0, 20.0],
                    node_count=5,
                    radial_node_count=5,
                    azimuthal_node_line_count=10,
                )
                return {"success": True, "stdout": "", "stderr": "", "returncode": 0, "duration_seconds": 0.1}

            def fake_wolfram(workflow_path: Path, timeout: int = 60) -> dict:
                call_counts["mathematica"] += 1
                return fake_payload(workflow_path, timeout)

            def fake_python(workflow_path: Path, timeout: int = 60) -> dict:
                call_counts["python"] += 1
                return fake_payload(workflow_path, timeout)

            with patch.object(module, "validate_modeling_config", side_effect=lambda value: value), \
                 patch.object(module, "discover_required_cases", side_effect=fake_discover), \
                 patch.object(module, "build_or_patch_workflow", side_effect=fake_builder), \
                 patch.object(module, "run_wolfram_workflow", side_effect=fake_wolfram), \
                 patch.object(module, "run_python_workflow", side_effect=fake_python):
                result = module.run_modeling_case(config)

            self.assertFalse(result["success"])
            self.assertEqual(call_counts["mathematica"], 3)
            self.assertEqual(call_counts["python"], 3)
            case_manifest = json.loads((root_dir / "case-a" / "case_run_result.json").read_text(encoding="utf-8"))
            self.assertEqual(len(case_manifest["retry_history"]), 6)
            self.assertIn("geometry", " ".join(case_manifest["failure_reasons"]).lower())


if __name__ == "__main__":
    unittest.main()
