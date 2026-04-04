from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "validate_modeling_config.py"


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


class ValidateModelingConfigTests(unittest.TestCase):
    def base_config(self) -> dict:
        return {
            "run_id": "case-demo",
            "experiment": {
                "name": "demo experiment",
                "safe_name": "demo-experiment",
            },
            "objective": "generate demo artifacts",
            "engine_policy": {
                "preferred": "mathematica",
            },
            "inputs": {
                "parameters": {"frequency_hz": 123.4},
                "constants": {},
                "boundary_conditions": {},
                "comparison_targets": [],
            },
            "workflow": {
                "mode": "patch-existing",
                "source_wl": "/tmp/source.wl",
                "source_py": "",
                "template_id": "",
            },
            "outputs": {
                "root_dir": "/tmp/modeling-run",
            },
            "artifacts_requested": ["summary_json"],
        }

    def test_batch_defaults_are_normalized(self) -> None:
        module = load_module(SCRIPT_PATH, "validate_modeling_config_batch_defaults")
        config = copy.deepcopy(self.base_config())

        normalized = module.validate_modeling_config(config)

        self.assertEqual(
            normalized["discovery"],
            {
                "enabled": False,
                "picture_results_dir": "",
                "parser": "lx2_filename",
            },
        )
        self.assertEqual(normalized["handout_cases"], [])
        self.assertEqual(
            normalized["batch_policy"],
            {
                "strict_required_cases": True,
                "include_picture_result_cases": True,
                "include_handout_only_cases": True,
            },
        )
        self.assertEqual(
            normalized["retry_policy"],
            {
                "mathematica_attempts": 3,
                "python_attempts": 3,
            },
        )
        self.assertTrue(normalized["sanity_checks"]["enabled"])

    def test_discovery_requires_picture_results_dir_when_enabled(self) -> None:
        module = load_module(SCRIPT_PATH, "validate_modeling_config_bad_discovery")
        config = copy.deepcopy(self.base_config())
        config["discovery"] = {
            "enabled": True,
            "picture_results_dir": "",
            "parser": "lx2_filename",
        }

        with self.assertRaises(ValueError):
            module.validate_modeling_config(config)

    def test_retry_policy_rejects_non_positive_attempt_counts(self) -> None:
        module = load_module(SCRIPT_PATH, "validate_modeling_config_bad_retry_counts")
        config = copy.deepcopy(self.base_config())
        config["retry_policy"] = {
            "mathematica_attempts": 0,
            "python_attempts": -1,
        }

        with self.assertRaises(ValueError):
            module.validate_modeling_config(config)

    def test_lx2_fixture_sample_uses_batch_contract(self) -> None:
        module = load_module(SCRIPT_PATH, "validate_modeling_config_fixture_sample")
        fixture_path = (
            SKILL_DIR / "fixtures" / "lx2_circular_plate" / "run_config.sample.json"
        )
        config = json.loads(fixture_path.read_text(encoding="utf-8"))

        normalized = module.validate_modeling_config(config)

        self.assertTrue(normalized["discovery"]["enabled"])
        self.assertTrue(normalized["batch_policy"]["strict_required_cases"])
        self.assertEqual(normalized["retry_policy"]["mathematica_attempts"], 3)
        self.assertEqual(normalized["retry_policy"]["python_attempts"], 3)
        self.assertTrue(normalized["engine_policy"]["allow_python_fallback"])

    def test_missing_run_id_is_rejected(self) -> None:
        module = load_module(SCRIPT_PATH, "validate_modeling_config_missing_run_id")
        config = self.base_config()
        config.pop("run_id")

        with self.assertRaises(ValueError):
            module.validate_modeling_config(config)

    def test_missing_experiment_safe_name_is_rejected(self) -> None:
        module = load_module(SCRIPT_PATH, "validate_modeling_config_missing_safe_name")
        config = self.base_config()
        config["experiment"].pop("safe_name")

        with self.assertRaises(ValueError):
            module.validate_modeling_config(config)

    def test_invalid_preferred_engine_is_rejected(self) -> None:
        module = load_module(SCRIPT_PATH, "validate_modeling_config_invalid_engine")
        config = self.base_config()
        config["engine_policy"]["preferred"] = "python"

        with self.assertRaises(ValueError):
            module.validate_modeling_config(config)

    def test_invalid_requested_artifact_is_rejected(self) -> None:
        module = load_module(SCRIPT_PATH, "validate_modeling_config_invalid_artifact")
        config = self.base_config()
        config["artifacts_requested"] = ["summary_json", "bad_artifact"]

        with self.assertRaises(ValueError):
            module.validate_modeling_config(config)

    def test_malformed_handout_expectations_are_rejected(self) -> None:
        module = load_module(SCRIPT_PATH, "validate_modeling_config_bad_expectations")
        config = self.base_config()
        config["handout_expectations"] = {
            "required": True,
            "checks": [{"id": "node-count", "type": "equals"}],
        }

        with self.assertRaises(ValueError):
            module.validate_modeling_config(config)

    def test_minimal_config_is_normalized(self) -> None:
        module = load_module(SCRIPT_PATH, "validate_modeling_config_normalized")
        config = copy.deepcopy(self.base_config())

        normalized = module.validate_modeling_config(config)

        self.assertEqual(normalized["run_id"], "case-demo")
        self.assertFalse(normalized["engine_policy"]["allow_python_fallback"])
        self.assertEqual(
            normalized["handout_expectations"],
            {"required": False, "checks": []},
        )
        self.assertEqual(normalized["artifacts_requested"], ["summary_json"])


if __name__ == "__main__":
    unittest.main()
