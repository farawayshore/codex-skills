#!/usr/bin/env python3
"""Top-level orchestration for batch-oriented modeling runs."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from build_or_patch_workflow import build_or_patch_workflow
from common import (
    ensure_dir,
    load_json,
    lookup_path,
    safe_case_stem,
    write_json,
    write_run_result,
)
from discover_required_cases import discover_required_cases
from run_python_model import run_python_workflow
from run_wolfram_expr import run_wolfram_workflow
from validate_modeling_config import validate_modeling_config


ARTIFACT_SUFFIXES = {
    "summary_json": "-summary.json",
    "summary_txt": "-summary.txt",
    "plot_png": "-plot.png",
    "radial_png": "-radial.png",
    "table_csv": "-table.csv",
    "params_json": "-params.json",
}

MATHEMATICA_STRATEGIES = [
    "primary-solve",
    "wider-root-scan",
    "alternate-nearby-root",
]
PYTHON_STRATEGIES = [
    "python-primary",
    "python-wide-scan",
    "python-alternate-root",
]
POSITIVE_DERIVED_KEYS = [
    "k_cm_inverse",
    "k_m_inverse",
    "c_m2_per_s",
    "u_m_per_s",
    "youngs_modulus",
    "youngsModulus",
    "c",
    "u",
]


def _expected_artifact_paths(case_config: dict, case_dir: Path) -> dict[str, Path]:
    stem = safe_case_stem(case_config)
    return {
        artifact: case_dir / f"{stem}{ARTIFACT_SUFFIXES[artifact]}"
        for artifact in case_config["artifacts_requested"]
    }


def _load_summary_payload(artifact_paths: dict[str, Path]) -> dict | None:
    summary_path = artifact_paths.get("summary_json")
    if summary_path is None or not summary_path.exists():
        return None
    return json.loads(summary_path.read_text(encoding="utf-8"))


def _evaluate_handout_expectations(case_config: dict, summary_payload: dict | None):
    expectations = case_config.get("handout_expectations", {"required": False, "checks": []})
    checks = expectations.get("checks", [])
    required = expectations.get("required", False)
    if not checks:
        if required:
            return "not_provided", [], ["handout expectations required but not provided"]
        return "not_provided", [], []

    if summary_payload is None:
        return "not_evaluable", [], ["summary_json artifact missing for handout expectation checks"]

    results = []
    failures = []
    for check in checks:
        try:
            actual = lookup_path(summary_payload, check["path"])
        except KeyError:
            actual = None
            passed = False
            failures.append(f"missing handout expectation path: {check['path']}")
        else:
            if check["type"] == "equals":
                passed = actual == check.get("expected")
            elif check["type"] == "range":
                passed = True
                if "min" in check:
                    passed = passed and actual >= check["min"]
                if "max" in check:
                    passed = passed and actual <= check["max"]
            else:
                passed = False
                failures.append(f"unsupported handout expectation type: {check['type']}")
        results.append(
            {
                "id": check["id"],
                "type": check["type"],
                "path": check["path"],
                "passed": passed,
                "actual": actual,
            }
        )
        if not passed and not any(check["id"] in failure for failure in failures):
            failures.append(f"handout expectation failed: {check['id']}")

    return ("passed" if not failures else "failed"), results, failures


def _evaluate_default_sanity(case_config: dict, summary_payload: dict | None):
    sanity_config = case_config.get("sanity_checks", {})
    if not sanity_config.get("enabled", True):
        return "disabled", [], []
    if summary_payload is None:
        return "not_evaluable", [], ["summary_json artifact missing for sanity checks"]

    summary = summary_payload.get("summary", {})
    parameters = case_config.get("inputs", {}).get("parameters", {})
    checks = []
    failures = []

    node_radii_cm = summary.get("node_radii_cm")
    outer_node_radius_cm = summary.get("outer_node_radius_cm")
    radius_m = parameters.get("radius_m")
    if radius_m is None:
        radius_m = parameters.get("radiusM")
    if radius_m is not None and node_radii_cm:
        allowed_cm = float(radius_m) * 100.0 * (
            1.0 + float(sanity_config.get("geometry_bound_tolerance_ratio", 0.05))
        )
        geometry_passed = max(node_radii_cm) <= allowed_cm
        checks.append(
            {
                "id": "geometry-bound",
                "passed": geometry_passed,
                "actual_outer_node_radius_cm": outer_node_radius_cm,
                "allowed_outer_node_radius_cm": allowed_cm,
            }
        )
        if not geometry_passed:
            failures.append("geometry bound sanity check failed")

    if sanity_config.get("check_monotonic_radii", True) and node_radii_cm:
        monotonic_passed = all(
            node_radii_cm[index] > 0 and node_radii_cm[index] < node_radii_cm[index + 1]
            for index in range(len(node_radii_cm) - 1)
        ) and node_radii_cm[-1] > 0
        checks.append(
            {
                "id": "monotonic-radial-structure",
                "passed": monotonic_passed,
            }
        )
        if not monotonic_passed:
            failures.append("monotonic radial structure sanity check failed")

    if sanity_config.get("check_mode_topology", True):
        expected_n = parameters.get("n")
        if expected_n is not None and (
            "radial_node_count" in summary or "node_count" in summary
        ):
            actual_n = summary.get("radial_node_count", summary.get("node_count"))
            radial_passed = actual_n == expected_n
            checks.append(
                {
                    "id": "radial-node-count",
                    "passed": radial_passed,
                    "expected": expected_n,
                    "actual": actual_n,
                }
            )
            if not radial_passed:
                failures.append("radial node count sanity check failed")

        expected_m = parameters.get("m")
        if expected_m is not None and "azimuthal_node_line_count" in summary:
            expected_line_count = 0 if expected_m == 0 else 2 * expected_m
            actual_line_count = summary["azimuthal_node_line_count"]
            line_passed = actual_line_count == expected_line_count
            checks.append(
                {
                    "id": "azimuthal-line-count",
                    "passed": line_passed,
                    "expected": expected_line_count,
                    "actual": actual_line_count,
                }
            )
            if not line_passed:
                failures.append("azimuthal line count sanity check failed")

    if sanity_config.get("check_positive_derived_values", True):
        for key in POSITIVE_DERIVED_KEYS:
            if key not in summary:
                continue
            actual_value = summary[key]
            passed = isinstance(actual_value, (int, float)) and actual_value > 0
            checks.append({"id": f"positive-{key}", "passed": passed, "actual": actual_value})
            if not passed:
                failures.append(f"positive derived value sanity check failed: {key}")

    return ("passed" if not failures else "failed"), checks, failures


def _evaluate_attempt(case_config: dict, payload: dict, artifact_paths: dict[str, Path]) -> dict:
    technical_success = bool(payload.get("success"))
    artifact_contract_passed = all(path.exists() for path in artifact_paths.values())
    failure_reasons: list[str] = []
    if not technical_success:
        failure_reasons.append("execution failed")
    if not artifact_contract_passed:
        failure_reasons.append("required artifacts missing")

    summary_payload = _load_summary_payload(artifact_paths)
    handout_status, handout_checks, handout_failures = _evaluate_handout_expectations(
        case_config, summary_payload
    )
    sanity_status, sanity_checks, sanity_failures = _evaluate_default_sanity(
        case_config, summary_payload
    )
    failure_reasons.extend(handout_failures)
    failure_reasons.extend(sanity_failures)

    success = technical_success and artifact_contract_passed and handout_status in {
        "passed",
        "not_provided",
    } and sanity_status in {
        "passed",
        "disabled",
    }
    return {
        "success": success,
        "technical_success": technical_success,
        "artifact_contract_passed": artifact_contract_passed,
        "handout_expectation_status": handout_status,
        "handout_expectation_checks": handout_checks,
        "sanity_check_status": sanity_status,
        "sanity_checks": sanity_checks,
        "failure_reasons": failure_reasons,
        "summary_payload": summary_payload,
    }


def _build_case_config(normalized: dict, case: dict) -> dict:
    case_config = copy.deepcopy(normalized)
    case_id = case.get("case_id") or safe_case_stem(case)
    case_config["case_id"] = case_id
    case_config["run_id"] = case_id
    merged_parameters = dict(case_config.get("inputs", {}).get("parameters", {}))
    merged_parameters.update(case.get("parameters", {}))
    case_config["inputs"]["parameters"] = merged_parameters
    case_config["handout_expectations"] = case.get(
        "handout_expectations",
        normalized.get("handout_expectations", {"required": False, "checks": []}),
    )
    return case_config


def _default_case_from_top_level(normalized: dict) -> dict:
    return {
        "case_id": safe_case_stem(normalized),
        "parameters": dict(normalized.get("inputs", {}).get("parameters", {})),
        "sources": ["top_level"],
        "handout_expectations": normalized.get(
            "handout_expectations", {"required": False, "checks": []}
        ),
    }


def _execute_case(case_config: dict, case_dir: Path) -> dict:
    retry_policy = case_config["retry_policy"]
    retry_history = []
    source_workflow_paths: dict[str, str] = {}
    artifact_paths = _expected_artifact_paths(case_config, case_dir)
    final_evaluation: dict | None = None

    for attempt_number, strategy in enumerate(
        MATHEMATICA_STRATEGIES[: retry_policy["mathematica_attempts"]],
        start=1,
    ):
        workflow_path = build_or_patch_workflow(
            case_config,
            case_dir,
            "mathematica",
            attempt_context={
                "case_id": case_config["case_id"],
                "attempt_number": attempt_number,
                "strategy": strategy,
            },
        )
        source_workflow_paths[f"mathematica_{attempt_number}"] = str(workflow_path)
        payload = run_wolfram_workflow(workflow_path)
        evaluation = _evaluate_attempt(case_config, payload, artifact_paths)
        retry_history.append(
            {
                "engine": "mathematica",
                "attempt_number": attempt_number,
                "strategy": strategy,
                "workflow_path": str(workflow_path),
                "success": evaluation["success"],
                "failure_reasons": evaluation["failure_reasons"],
                "duration_seconds": payload.get("duration_seconds", 0.0),
            }
        )
        final_evaluation = evaluation
        if evaluation["success"]:
            break

    if (
        final_evaluation is not None
        and not final_evaluation["success"]
        and case_config["engine_policy"].get("allow_python_fallback", False)
    ):
        for attempt_offset, strategy in enumerate(
            PYTHON_STRATEGIES[: retry_policy["python_attempts"]],
            start=1,
        ):
            workflow_path = build_or_patch_workflow(
                case_config,
                case_dir,
                "python",
                attempt_context={
                    "case_id": case_config["case_id"],
                    "attempt_number": attempt_offset,
                    "strategy": strategy,
                },
            )
            source_workflow_paths[f"python_{attempt_offset}"] = str(workflow_path)
            payload = run_python_workflow(workflow_path)
            evaluation = _evaluate_attempt(case_config, payload, artifact_paths)
            retry_history.append(
                {
                    "engine": "python",
                    "attempt_number": attempt_offset,
                    "strategy": strategy,
                    "workflow_path": str(workflow_path),
                    "success": evaluation["success"],
                    "failure_reasons": evaluation["failure_reasons"],
                    "duration_seconds": payload.get("duration_seconds", 0.0),
                }
            )
            final_evaluation = evaluation
            if evaluation["success"]:
                break

    if final_evaluation is None:
        final_evaluation = {
            "success": False,
            "technical_success": False,
            "artifact_contract_passed": False,
            "handout_expectation_status": "not_evaluable",
            "handout_expectation_checks": [],
            "sanity_check_status": "not_evaluable",
            "sanity_checks": [],
            "failure_reasons": ["no attempts executed"],
            "summary_payload": None,
        }

    case_result = {
        "case_id": case_config["case_id"],
        "success": final_evaluation["success"],
        "technical_success": final_evaluation["technical_success"],
        "artifact_contract_passed": final_evaluation["artifact_contract_passed"],
        "handout_expectation_status": final_evaluation["handout_expectation_status"],
        "handout_expectation_checks": final_evaluation["handout_expectation_checks"],
        "sanity_check_status": final_evaluation["sanity_check_status"],
        "sanity_checks": final_evaluation["sanity_checks"],
        "failure_reasons": final_evaluation["failure_reasons"],
        "retry_history": retry_history,
        "artifacts": {name: str(path) for name, path in artifact_paths.items() if path.exists()},
        "source_workflow_paths": source_workflow_paths,
    }
    write_run_result(case_dir / "case_run_result.json", case_result)
    return case_result


def _apply_cross_case_consistency(batch_result: dict, case_results: list[dict], case_dirs: dict[str, Path]) -> None:
    metrics: dict[str, list[tuple[str, float]]] = {"k_cm_inverse": [], "u_m_per_s": [], "c_m2_per_s": []}
    for case_result in case_results:
        if not case_result["success"]:
            continue
        summary_payload = None
        summary_path = case_result["artifacts"].get("summary_json")
        if summary_path:
            summary_payload = json.loads(Path(summary_path).read_text(encoding="utf-8"))
        if summary_payload is None:
            continue
        summary = summary_payload.get("summary", {})
        for metric in metrics:
            value = summary.get(metric)
            if isinstance(value, (int, float)) and value > 0:
                metrics[metric].append((case_result["case_id"], float(value)))

    failures = set()
    for metric, values in metrics.items():
        if len(values) < 2:
            continue
        numeric_values = [value for _, value in values]
        min_value = min(numeric_values)
        max_value = max(numeric_values)
        if min_value <= 0:
            continue
        if max_value / min_value > 10.0:
            for case_id, _ in values:
                failures.add(case_id)
            batch_result.setdefault("warnings", []).append(
                f"cross-case consistency check failed for metric: {metric}"
            )

    if not failures:
        return

    for case_result in case_results:
        if case_result["case_id"] not in failures:
            continue
        case_result["success"] = False
        case_result["failure_reasons"].append("cross-case consistency check failed")
        write_run_result(case_dirs[case_result["case_id"]] / "case_run_result.json", case_result)


def run_modeling_case(config: dict) -> dict:
    normalized = validate_modeling_config(config)
    batch_root = ensure_dir(normalized["outputs"]["root_dir"])
    snapshot_path = write_json(batch_root / "run_config.snapshot.json", normalized)

    discovery_result = discover_required_cases(normalized)
    required_cases = discovery_result["required_cases"]
    if not required_cases:
        required_cases = [_default_case_from_top_level(normalized)]

    case_results = []
    case_dirs: dict[str, Path] = {}
    for case in required_cases:
        case_config = _build_case_config(normalized, case)
        case_dir = ensure_dir(batch_root / case_config["case_id"])
        case_dirs[case_config["case_id"]] = case_dir
        case_result = _execute_case(case_config, case_dir)
        case_results.append(case_result)

    if normalized["sanity_checks"].get("check_cross_case_consistency", True):
        batch_stub = {"warnings": []}
        _apply_cross_case_consistency(batch_stub, case_results, case_dirs)
        warnings = batch_stub["warnings"]
    else:
        warnings = []

    passed_cases = sorted([case["case_id"] for case in case_results if case["success"]])
    failed_cases = sorted([case["case_id"] for case in case_results if not case["success"]])
    strict = normalized["batch_policy"].get("strict_required_cases", True)
    success = not failed_cases if strict else True
    batch_result = {
        "success": success,
        "run_id": normalized["run_id"],
        "required_cases": [case["case_id"] for case in required_cases],
        "passed_cases": passed_cases,
        "failed_cases": failed_cases,
        "discovered_case_count": len(discovery_result.get("discovered_cases", [])),
        "handout_only_case_count": len(discovery_result.get("handout_only_cases", [])),
        "strict_required_cases": strict,
        "warnings": warnings,
        "case_manifest_paths": {
            case["case_id"]: str(case_dirs[case["case_id"]] / "case_run_result.json")
            for case in case_results
        },
        "config_snapshot_path": str(snapshot_path),
    }
    write_run_result(batch_root / "batch_run_result.json", batch_result)
    return batch_result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a full modeling batch from run_config.json.")
    parser.add_argument("--config", required=True, help="Path to run_config.json")
    args = parser.parse_args()
    config = load_json(args.config)
    result = run_modeling_case(config)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
