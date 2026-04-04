#!/usr/bin/env python3
"""Build or patch a run-local workflow file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import ensure_dir, load_json
from validate_modeling_config import validate_modeling_config


def _generated_name_for_engine(engine: str) -> str:
    if engine == "mathematica":
        return "workflow.generated.wl"
    if engine == "python":
        return "workflow.generated.py"
    raise ValueError(f"Unsupported engine: {engine}")


def _source_path_for_engine(config: dict, engine: str) -> Path:
    workflow = config["workflow"]
    if engine == "mathematica":
        source = workflow.get("source_wl")
    elif engine == "python":
        source = workflow.get("source_py")
    else:
        raise ValueError(f"Unsupported engine: {engine}")

    if not isinstance(source, str) or not source.strip():
        raise ValueError(f"workflow source for {engine} is required.")
    return Path(source)


def _generated_header(config: dict, engine: str, source_path: Path, attempt_context: dict | None) -> str:
    payload = {
        "run_id": config["run_id"],
        "engine": engine,
        "source_path": str(source_path),
        "generated_for_run": True,
    }
    if attempt_context:
        payload["attempt_context"] = attempt_context
    if engine == "mathematica":
        return (
            "(* Generated workflow file. Do not edit in place. *)\n"
            f"(* {json.dumps(payload, ensure_ascii=True)} *)\n"
        )
    return (
        "# Generated workflow file. Do not edit in place.\n"
        f"# {json.dumps(payload, ensure_ascii=True)}\n"
    )


def build_or_patch_workflow(
    config: dict,
    run_dir: Path,
    engine: str,
    attempt_context: dict | None = None,
) -> Path:
    mode = config["workflow"]["mode"]
    output_dir = ensure_dir(run_dir)

    if mode != "patch-existing":
        raise ValueError(f"Unsupported workflow.mode for v1: {mode}")

    source_path = _source_path_for_engine(config, engine)
    if not source_path.exists():
        raise ValueError(f"Source workflow does not exist: {source_path}")

    generated_path = output_dir / _generated_name_for_engine(engine)
    generated_text = _generated_header(config, engine, source_path, attempt_context) + source_path.read_text(
        encoding="utf-8"
    )
    generated_path.write_text(generated_text, encoding="utf-8")
    return generated_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or patch a run-local modeling workflow.")
    parser.add_argument("--config", required=True, help="Path to run_config.json")
    parser.add_argument("--engine", required=True, choices=["mathematica", "python"])
    args = parser.parse_args()
    config = validate_modeling_config(load_json(args.config))
    output_path = build_or_patch_workflow(config, Path(config["outputs"]["root_dir"]), args.engine)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
