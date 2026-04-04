#!/usr/bin/env python3
"""Validate the modeling run contract."""

from __future__ import annotations

import argparse
import copy
import json

from common import load_json


ALLOWED_ENGINES = {"mathematica"}
ALLOWED_ARTIFACTS = {
    "summary_json",
    "summary_txt",
    "plot_png",
    "radial_png",
    "table_csv",
    "params_json",
}
ALLOWED_EXPECTATION_TYPES = {"equals", "range"}
ALLOWED_DISCOVERY_PARSERS = {"lx2_filename"}


def _require_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")
    return value.strip()


def _require_mapping(value: object, field_name: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object.")
    return value


def _require_list(value: object, field_name: str) -> list:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list.")
    return value


def _require_positive_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer.")
    return value


def validate_modeling_config(config: dict) -> dict:
    normalized = copy.deepcopy(_require_mapping(config, "config"))

    normalized["run_id"] = _require_non_empty_string(normalized.get("run_id"), "run_id")

    experiment = _require_mapping(normalized.get("experiment"), "experiment")
    experiment["name"] = _require_non_empty_string(experiment.get("name"), "experiment.name")
    experiment["safe_name"] = _require_non_empty_string(
        experiment.get("safe_name"), "experiment.safe_name"
    )
    normalized["experiment"] = experiment

    engine_policy = _require_mapping(normalized.get("engine_policy"), "engine_policy")
    preferred = _require_non_empty_string(
        engine_policy.get("preferred"), "engine_policy.preferred"
    ).lower()
    if preferred not in ALLOWED_ENGINES:
        raise ValueError(f"engine_policy.preferred must be one of {sorted(ALLOWED_ENGINES)}.")
    allow_python_fallback = engine_policy.get("allow_python_fallback", False)
    if not isinstance(allow_python_fallback, bool):
        raise ValueError("engine_policy.allow_python_fallback must be a boolean.")
    engine_policy["preferred"] = preferred
    engine_policy["allow_python_fallback"] = allow_python_fallback
    normalized["engine_policy"] = engine_policy

    normalized["inputs"] = _require_mapping(normalized.get("inputs"), "inputs")

    workflow = _require_mapping(normalized.get("workflow"), "workflow")
    workflow["mode"] = _require_non_empty_string(workflow.get("mode"), "workflow.mode")
    normalized["workflow"] = workflow

    outputs = _require_mapping(normalized.get("outputs"), "outputs")
    outputs["root_dir"] = _require_non_empty_string(outputs.get("root_dir"), "outputs.root_dir")
    normalized["outputs"] = outputs

    artifacts_requested = _require_list(
        normalized.get("artifacts_requested"), "artifacts_requested"
    )
    if not artifacts_requested:
        raise ValueError("artifacts_requested must not be empty.")
    cleaned_artifacts: list[str] = []
    for artifact in artifacts_requested:
        artifact_name = _require_non_empty_string(artifact, "artifacts_requested[]")
        if artifact_name not in ALLOWED_ARTIFACTS:
            raise ValueError(f"Unsupported artifact requested: {artifact_name}")
        cleaned_artifacts.append(artifact_name)
    normalized["artifacts_requested"] = cleaned_artifacts

    handout_expectations = normalized.get("handout_expectations")
    if handout_expectations is None:
        handout_expectations = {"required": False, "checks": []}
    handout_expectations = _require_mapping(handout_expectations, "handout_expectations")
    required = handout_expectations.get("required", False)
    if not isinstance(required, bool):
        raise ValueError("handout_expectations.required must be a boolean.")
    checks = _require_list(handout_expectations.get("checks", []), "handout_expectations.checks")
    normalized_checks = []
    for check in checks:
        check_dict = _require_mapping(check, "handout_expectations.check")
        check_id = _require_non_empty_string(check_dict.get("id"), "handout_expectations.check.id")
        check_type = _require_non_empty_string(
            check_dict.get("type"), "handout_expectations.check.type"
        ).lower()
        if check_type not in ALLOWED_EXPECTATION_TYPES:
            raise ValueError(
                f"handout_expectations.check.type must be one of {sorted(ALLOWED_EXPECTATION_TYPES)}."
            )
        _require_non_empty_string(check_dict.get("path"), "handout_expectations.check.path")
        normalized_checks.append({**check_dict, "id": check_id, "type": check_type})
    normalized["handout_expectations"] = {
        "required": required,
        "checks": normalized_checks,
    }

    discovery = normalized.get("discovery") or {}
    discovery = _require_mapping(discovery, "discovery")
    discovery_enabled = discovery.get("enabled", False)
    if not isinstance(discovery_enabled, bool):
        raise ValueError("discovery.enabled must be a boolean.")
    picture_results_dir = discovery.get("picture_results_dir", "")
    if picture_results_dir is None:
        picture_results_dir = ""
    if not isinstance(picture_results_dir, str):
        raise ValueError("discovery.picture_results_dir must be a string.")
    parser_name = str(discovery.get("parser", "lx2_filename")).strip().lower() or "lx2_filename"
    if parser_name not in ALLOWED_DISCOVERY_PARSERS:
        raise ValueError(
            f"discovery.parser must be one of {sorted(ALLOWED_DISCOVERY_PARSERS)}."
        )
    if discovery_enabled and not picture_results_dir.strip():
        raise ValueError("discovery.picture_results_dir is required when discovery.enabled is true.")
    normalized["discovery"] = {
        "enabled": discovery_enabled,
        "picture_results_dir": picture_results_dir.strip(),
        "parser": parser_name,
    }

    handout_cases = normalized.get("handout_cases", [])
    handout_cases = _require_list(handout_cases, "handout_cases")
    for index, case in enumerate(handout_cases):
        case_dict = _require_mapping(case, f"handout_cases[{index}]")
        parameters = _require_mapping(case_dict.get("parameters"), f"handout_cases[{index}].parameters")
        if parameters.get("frequency_hz") is None and parameters.get("f_kHz") is None:
            raise ValueError(f"handout_cases[{index}].parameters must include frequency_hz or f_kHz.")
        if "m" not in parameters or "n" not in parameters:
            raise ValueError(f"handout_cases[{index}].parameters must include m and n.")
    normalized["handout_cases"] = handout_cases

    batch_policy = normalized.get("batch_policy") or {}
    batch_policy = _require_mapping(batch_policy, "batch_policy")
    strict_required_cases = batch_policy.get("strict_required_cases", True)
    include_picture_result_cases = batch_policy.get("include_picture_result_cases", True)
    include_handout_only_cases = batch_policy.get("include_handout_only_cases", True)
    if not isinstance(strict_required_cases, bool):
        raise ValueError("batch_policy.strict_required_cases must be a boolean.")
    if not isinstance(include_picture_result_cases, bool):
        raise ValueError("batch_policy.include_picture_result_cases must be a boolean.")
    if not isinstance(include_handout_only_cases, bool):
        raise ValueError("batch_policy.include_handout_only_cases must be a boolean.")
    normalized["batch_policy"] = {
        "strict_required_cases": strict_required_cases,
        "include_picture_result_cases": include_picture_result_cases,
        "include_handout_only_cases": include_handout_only_cases,
    }

    retry_policy = normalized.get("retry_policy") or {}
    retry_policy = _require_mapping(retry_policy, "retry_policy")
    normalized["retry_policy"] = {
        "mathematica_attempts": _require_positive_int(
            retry_policy.get("mathematica_attempts", 3),
            "retry_policy.mathematica_attempts",
        ),
        "python_attempts": _require_positive_int(
            retry_policy.get("python_attempts", 3),
            "retry_policy.python_attempts",
        ),
    }

    sanity_checks = normalized.get("sanity_checks") or {}
    sanity_checks = _require_mapping(sanity_checks, "sanity_checks")
    geometry_bound_tolerance_ratio = sanity_checks.get("geometry_bound_tolerance_ratio", 0.05)
    if not isinstance(geometry_bound_tolerance_ratio, (int, float)) or geometry_bound_tolerance_ratio < 0:
        raise ValueError("sanity_checks.geometry_bound_tolerance_ratio must be a non-negative number.")
    normalized["sanity_checks"] = {
        "enabled": bool(sanity_checks.get("enabled", True)),
        "geometry_bound_tolerance_ratio": float(geometry_bound_tolerance_ratio),
        "check_monotonic_radii": bool(sanity_checks.get("check_monotonic_radii", True)),
        "check_mode_topology": bool(sanity_checks.get("check_mode_topology", True)),
        "check_positive_derived_values": bool(sanity_checks.get("check_positive_derived_values", True)),
        "check_cross_case_consistency": bool(sanity_checks.get("check_cross_case_consistency", True)),
    }

    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a modeling run_config.json file.")
    parser.add_argument("--config", required=True, help="Path to run_config.json")
    args = parser.parse_args()
    config = load_json(args.config)
    normalized = validate_modeling_config(config)
    print(json.dumps(normalized, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
