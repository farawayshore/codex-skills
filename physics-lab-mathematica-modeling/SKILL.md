---
name: physics-lab-mathematica-modeling
description: Use when a physics lab needs batch-first, contract-driven modeling artifacts that can expand discovered picture-result cases plus handout-only cases, with Mathematica-first execution, strict acceptance checks, and bounded Python fallback.
---

# Physics Lab Mathematica Modeling

## Overview

Use this skill for artifact-only physics modeling batches that should stay reproducible, machine-readable, and independent from the older report-controller skill.

This skill is standalone with local copied tools. It is batch-first by default, can expand one `run_config.json` into the union of discovered picture-result cases plus handout-only cases, retries up to `3 Mathematica` attempts and `3 Python` attempts per case, and fails a strict batch when any required case still violates explicit handout expectations or default physics-informed sanity checks.

## When to Use

- The experiment already has formulas, parameters, boundary conditions, or case definitions ready for modeling.
- The workflow should be driven by a reusable `run_config.json` contract rather than one-off shell commands.
- The run should auto-discover required cases from picture-result folders and merge them with extra handout-only cases.
- The run needs generated or patched workflow files such as `.wl` or `.py`.
- The output should be artifact-only: plots, tables, summaries, snapshots, case manifests, and batch manifests.
- The run may need Python fallback after Mathematica proves unsatisfactory across bounded retries.

Do not use this skill to write report prose, captions, discussion text, or handout-decoding output.

## Core Contract

- Keep all required tooling local to `/root/.codex/skills/physics-lab-mathematica-modeling/`.
- Use `/root/.codex/skills/physics-lab-mathematica-modeling/scripts/validate_modeling_config.py` to validate `run_config.json`.
- Use `/root/.codex/skills/physics-lab-mathematica-modeling/scripts/discover_required_cases.py` to expand the required case batch from the matching picture-result folder plus any handout-only cases.
- Use `/root/.codex/skills/physics-lab-mathematica-modeling/scripts/build_or_patch_workflow.py` to write run-local generated workflow copies.
- Use `/root/.codex/skills/physics-lab-mathematica-modeling/scripts/run_modeling_case.py` as the top-level orchestrator.
- Treat Mathematica-first execution as the default path.
- Retry each required case with up to `3 Mathematica` attempts and then up to `3 Python` attempts when fallback is allowed.
- Require strict batch success by default: every required discovered or handout-only case must pass.
- If explicit handout expectation checks fail, or default physics-informed sanity checks reject the result, the case fails even when an engine exits successfully.

## Primary Commands

Validate the run config:

```bash
python3 /root/.codex/skills/physics-lab-mathematica-modeling/scripts/validate_modeling_config.py \
  --config "/path/to/run_config.json"
```

Build or patch a run-local workflow:

```bash
python3 /root/.codex/skills/physics-lab-mathematica-modeling/scripts/build_or_patch_workflow.py \
  --config "/path/to/run_config.json" \
  --engine mathematica
```

Discover the required case batch:

```bash
python3 /root/.codex/skills/physics-lab-mathematica-modeling/scripts/discover_required_cases.py \
  --config "/path/to/run_config.json"
```

Run the full modeling batch:

```bash
python3 /root/.codex/skills/physics-lab-mathematica-modeling/scripts/run_modeling_case.py \
  --config "/path/to/run_config.json"
```

## Boundary Rules

- Keep the skill artifact-only.
- Keep source workflow files unchanged; write generated copies into per-case output directories.
- Record one `run_config.snapshot.json`, one `batch_run_result.json`, and one `case_run_result.json` per required case.
- Prefer Mathematica-first execution.
- Use Python fallback only after Mathematica has exhausted its bounded retries.
- Fail the batch when any required case violates explicit handout expectation checks.
- Fail the batch when default sanity checks catch unrealistic geometry, broken radial ordering, mismatched mode topology, or cross-case inconsistency.

## Resources

- `scripts/common.py`: local copied helper functions for JSON and path handling
- `scripts/validate_modeling_config.py`: run-config validator
- `scripts/discover_required_cases.py`: required-case discovery and union logic
- `scripts/build_or_patch_workflow.py`: run-local workflow generator and patcher
- `scripts/run_wolfram_expr.py`: local copied Wolfram runner
- `scripts/run_python_model.py`: Python fallback runner
- `scripts/run_modeling_case.py`: top-level batch orchestrator
