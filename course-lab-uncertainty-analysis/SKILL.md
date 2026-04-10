---
name: course-lab-uncertainty-analysis
description: Use when a course lab-report run already has user-validated transferred data plus the matching handout and now needs handout-aligned direct uncertainties, notation disambiguation, propagated indirect quantities, or expanded-uncertainty artifacts before interpretation, theory comparison, or discussion prose.
---

# Course Lab Uncertainty Analysis

## Overview

Turn validated measurement data into uncertainty artifacts, but read the handout first so the quantity symbols, units, and required indirect results are resolved before any calculation starts.

This skill is standalone at the contract level, but in the current family layout it reuses the existing family-local calculators under `/root/.codex/skills/course-lab-data-processing/scripts/` because this package does not yet carry its own copied script toolchain. It should not reach back into the old `course-lab-report` folder for uncertainty computation.

## Standalone Tool Contract

### Use Independently When
- Validated data and handout uncertainty requirements are available and the run needs direct uncertainty summaries, propagated indirect uncertainties, or expanded-uncertainty artifacts.
- Uncertainty artifacts must be prepared before interpretation, theory comparison, plotting, or report prose.

### Minimum Inputs
- User-validated transferred data or processed direct-measurement artifacts.
- Matching handout/normalized section artifacts that define symbols, units, formulas, and uncertainty expectations.
- Direct uncertainty assumptions/rules or enough instrument information to state unresolved uncertainty gaps honestly.

### Optional Workflow Inputs
- Processed-data manifests, derived-quantity specs, run-plan obligations, or appendix-calculation destinations.
- Approved user corrections to measurement or instrument uncertainties.

### Procedure
- Read the handout first so uncertainty notation and required indirect results match the experiment.
- Use the existing family-local calculators under `/root/.codex/skills/course-lab-data-processing/scripts/` for supported direct-summary and propagation calculations.
- Keep unsupported or underspecified uncertainty terms as visible unresolved items rather than filling them with guesses.

### Outputs
- Direct uncertainty summaries and propagated uncertainty artifacts.
- Derived-quantity uncertainty results where supported by validated data and formulas.
- Unresolved uncertainty notes naming missing measurements, instrument rules, or formula support.

### Validation
- Symbols, units, and formulas align with the handout and validated data.
- Every propagated value is traceable to a direct input and documented propagation rule.
- Handout-requested uncertainty results that cannot be computed are explicitly unresolved.

### Failure / Reroute Signals
- Missing data validation: in standalone mode, stop for validated transfer artifacts; in full-workflow mode, reroute to data transfer/proofread.
- Missing handout or uncertainty rule: stop or emit unresolved uncertainty notes rather than guessing.
- Formula/input mismatch: report the mismatch and withhold propagated values until resolved.

### Non-Ownership
- Does not perform broad data interpretation, write discussion prose, mutate final TeX, or place figures.
- Does not invent instrument uncertainties or silently compute unsupported indirect quantities.

## Optional Workflow Metadata
- Suggested future role label: `data-analyst`.
- Typical upstream tools: `course-lab-data-transfer`, `course-lab-data-processing`, `course-lab-handout-normalization`.
- Typical downstream tools: `course-lab-results-interpretation`, `course-lab-final-staging`, `course-lab-symbolic-expressing`.

## Core Rule

- Read the handout first.
- Build a handout-aligned quantity contract before computing anything.
- Resolve notation against the handout instead of guessing from the transferred table alone.
- Example: `T/N` may means quantity `T` with unit `N`, not one merged quantity named `T/N`, read the handout to ensure which one is correct.
- If the transferred notation still conflicts with the handout after that read, stop and ask instead of normalizing it silently.

## Primary Commands

Direct measured quantities after the handout notation is resolved:

```bash
python3 /root/.codex/skills/course-lab-data-processing/scripts/compute_uncertainties.py \
  --input "/path/to/results/<experiment>/analysis/direct_measurements.csv" \
  --quantity "T/N" \
  --resolution "T/N=0.001" \
  --output-markdown "/path/to/results/<experiment>/analysis/direct_uncertainty.md" \
  --output-json "/path/to/results/<experiment>/analysis/direct_uncertainty.json"
```

Indirect quantities with propagation rules:

```bash
python3 /root/.codex/skills/course-lab-data-processing/scripts/propagate_uncertainties.py \
  --spec "/path/to/results/<experiment>/analysis/derived_quantity_spec.json" \
  --output-markdown "/path/to/results/<experiment>/analysis/derived_uncertainty.md" \
  --output-json "/path/to/results/<experiment>/analysis/derived_uncertainty.json"
```

Example propagation spec shape:

```json
{
  "coverage_k": 2.0,
  "inputs": {
    "T": {"summary_json": "/path/to/direct_uncertainty.json", "column": "T/N", "value_key": "mean", "uncertainty_key": "type_c", "unit": "N"},
    "m": {"value": 0.01391, "std_uncertainty": 0.00001, "unit": "kg"},
    "L": {"value": 3.0, "std_uncertainty": 0.0001, "unit": "m"}
  },
  "derived": [
    {"name": "rho", "expression": "m / L", "unit": "kg/m", "label": "linear density"},
    {"name": "a", "expression": "sqrt(T / rho)", "unit": "m/s", "label": "wave speed"}
  ]
}
```

## Workflow

1. Read the matching handout before touching the data table.
2. List the handout’s direct measured quantities, notation, units, and every indirect quantity it asks to compute.
3. Build a run-local quantity contract so raw labels from the transfer are mapped to handout meanings before summary work starts.
4. Run `/root/.codex/skills/course-lab-data-processing/scripts/compute_uncertainties.py` for the direct measured quantities and repeated series.
5. Build a derived-quantity spec for every handout-requested indirect result that is supported by the validated data.
6. Run `/root/.codex/skills/course-lab-data-processing/scripts/propagate_uncertainties.py` on that spec.
7. Review the direct and derived outputs together, checking for provisional resolution fields, notation mismatches, and handout-requested quantities that are still unresolved.

## Quick Reference

### Contract Notes

- Use `/root/.codex/skills/course-lab-data-processing/scripts/compute_uncertainties.py` for direct measured quantities and repeated-measurement summaries.
- Use `/root/.codex/skills/course-lab-data-processing/scripts/propagate_uncertainties.py` for indirect quantities and propagation-rule calculations.
- Keep all executable uncertainty computation paths inside the installed course-lab family; do not reach back into the old parent workflow.
- Default the expanded-uncertainty coverage factor to `k=2` unless the handout or experiment rules explicitly require a different value.
- Cover every corresponding indirect measured quantity requested in the handout when the validated data are sufficient.
- If a handout-requested indirect quantity cannot yet be computed from validated data, emit a visible unresolved artifact instead of omitting it quietly.
- Keep missing resolution information visible. If a resolution is not yet known, do not invent it.

| Situation | Action |
|---|---|
| A transferred header uses slash notation such as `T/N` or `f/Hz` | Read the handout first and resolve it as quantity plus unit before calculating |
| Repeated direct measurements are already in CSV or TSV | Run `compute_uncertainties.py` on the resolved direct table |
| A required indirect quantity depends on several direct inputs | Use `propagate_uncertainties.py` with a handout-aligned spec |
| A derived quantity depends on earlier derived quantities | Keep the chained formulas in one propagation spec |
| A direct uncertainty summary already exists in JSON | Reference it from the propagation spec with `summary_json` plus `column` |
| Resolution is unknown | Leave it unresolved and keep the direct result provisional |
| The handout requests a derived result but validated data are incomplete | Emit a visible unresolved artifact instead of faking the calculation |

## Boundary Rules

- This skill starts only after transferred data is confirmed by the user.
- This skill owns uncertainty artifacts, not interpretation prose.
- Handout notation wins over ambiguous transferred shorthand.
- Do not collapse quantity and unit into one name just because the table header uses a slash.
- Do not let uncertainty work expand into theory comparison, reliability judgment, or final discussion drafting.
- Keep parent-skill path dependencies out of the workflow. Use the installed course-lab family calculators under `course-lab-data-processing/scripts/` instead of the old `course-lab-report` folder.

## Common Mistakes

- Running uncertainty calculations before reading the handout.
- Treating `T/N` as one quantity instead of tension `T` in newtons.
- Summarizing only direct measurements and forgetting the handout’s indirect requested quantities.
- Omitting propagation rules for derived quantities that depend on several inputs.
- Hiding missing resolution information by typing in a guessed number.
- Turning uncertainty output into polished conclusions before the interpretation step has the rest of the evidence.

## Resources

- `/root/.codex/skills/course-lab-data-processing/scripts/compute_uncertainties.py`: family-local direct-quantity uncertainty calculator reused by this skill
- `/root/.codex/skills/course-lab-data-processing/scripts/propagate_uncertainties.py`: family-local derived-quantity and propagation-rule calculator reused by this skill
- `/root/.codex/skills/course-lab-data-processing/scripts/common.py`: family-local helper module behind the shared calculator surface
