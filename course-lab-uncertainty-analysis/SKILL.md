---
name: course-lab-uncertainty-analysis
description: Use when a course lab-report run already has user-validated transferred data plus the matching handout and now needs handout-aligned direct uncertainties, notation disambiguation, propagated indirect quantities, or expanded-uncertainty artifacts before interpretation, theory comparison, or discussion prose.
---

# Course Lab Uncertainty Analysis

## Overview

Turn validated measurement data into uncertainty artifacts, but read the handout first so the quantity symbols, units, and required indirect results are resolved before any calculation starts.

This skill is standalone with local copied tools. It should not reach back into the old `course-lab-report` folder for uncertainty computation.

## When to Use

- The experiment is already confirmed.
- The transferred data has already been shown to the user and explicitly validated.
- The matching handout is available and can be read before the calculation pass.
- The run needs direct uncertainty summaries, indirect quantities, or propagated uncertainty artifacts before interpretation starts.
- Measurement resolution or instrument information is known, or the run needs a visible provisional state for missing resolution data.

Do not use this skill to choose the experiment, transcribe raw data, stage figures, write interpretation prose, compare with theory, or draft the final discussion.

## Core Rule

- Read the handout first.
- Build a handout-aligned quantity contract before computing anything.
- Resolve notation against the handout instead of guessing from the transferred table alone.
- Example: `T/N` may means quantity `T` with unit `N`, not one merged quantity named `T/N`, read the handout to ensure which one is correct.
- If the transferred notation still conflicts with the handout after that read, stop and ask instead of normalizing it silently.

## Output Contract

- Use local `scripts/compute_uncertainties.py` for direct measured quantities and repeated-measurement summaries.
- Use local `scripts/propagate_uncertainties.py` for indirect quantities and propagation-rule calculations.
- Keep all uncertainty computation paths local to `/root/.codex/skills/course-lab-uncertainty-analysis/`.
- Default the expanded-uncertainty coverage factor to `k=2` unless the handout or experiment rules explicitly require a different value.
- Cover every corresponding indirect measured quantity requested in the handout when the validated data are sufficient.
- If a handout-requested indirect quantity cannot yet be computed from validated data, emit a visible unresolved artifact instead of omitting it quietly.
- Keep missing resolution information visible. If a resolution is not yet known, do not invent it.

## Primary Commands

Direct measured quantities after the handout notation is resolved:

```bash
python3 /root/.codex/skills/course-lab-uncertainty-analysis/scripts/compute_uncertainties.py \
  --input "/path/to/results/<experiment>/analysis/direct_measurements.csv" \
  --quantity "T/N" \
  --resolution "T/N=0.001" \
  --output-markdown "/path/to/results/<experiment>/analysis/direct_uncertainty.md" \
  --output-json "/path/to/results/<experiment>/analysis/direct_uncertainty.json"
```

Indirect quantities with propagation rules:

```bash
python3 /root/.codex/skills/course-lab-uncertainty-analysis/scripts/propagate_uncertainties.py \
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
4. Run `scripts/compute_uncertainties.py` for the direct measured quantities and repeated series.
5. Build a derived-quantity spec for every handout-requested indirect result that is supported by the validated data.
6. Run `scripts/propagate_uncertainties.py` on that spec.
7. Review the direct and derived outputs together, checking for provisional resolution fields, notation mismatches, and handout-requested quantities that are still unresolved.

## Quick Reference

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
- Keep parent-skill path dependencies out of the workflow. Use the copied local scripts in this folder instead of the old `course-lab-report` folder.

## Common Mistakes

- Running uncertainty calculations before reading the handout.
- Treating `T/N` as one quantity instead of tension `T` in newtons.
- Summarizing only direct measurements and forgetting the handout’s indirect requested quantities.
- Omitting propagation rules for derived quantities that depend on several inputs.
- Hiding missing resolution information by typing in a guessed number.
- Turning uncertainty output into polished conclusions before the interpretation step has the rest of the evidence.

## Resources

- `scripts/compute_uncertainties.py`: local direct-quantity uncertainty calculator
- `scripts/propagate_uncertainties.py`: local derived-quantity and propagation-rule calculator
- `scripts/common.py`: local copied helper module for standalone packaging
- `tests/test_compute_uncertainties.py`: local regression tests for direct summaries and handout-style labels
- `tests/test_propagate_uncertainties.py`: local regression tests for derived quantities and propagation
- `tests/test_skill_package.py`: local standalone packaging tests
