---
name: course-lab-data-processing
description: Use when a course lab-report run already has user-validated transferred data plus the matching handout and now needs handout-aligned direct measurements, notation disambiguation, propagated indirect quantities, or data-processing artifacts before interpretation, theory comparison, or discussion prose.
---

# Course Lab Data Processing

## Overview

Turn validated measurement data into handout-aligned processing artifacts, including direct summaries and propagated derived quantities, but read the handout first so the quantity symbols, units, and required indirect results are resolved before any calculation starts.

This skill is standalone with local copied tools. It should not reach back into the old `course-lab-report` folder for uncertainty computation.

## Standalone Tool Contract

### Use Independently When
- User-validated transferred data and matching handout requirements are available and must be converted into handout-aligned direct summaries, derived quantities, and calculation artifacts.
- Appendix-ready calculation details are needed before interpretation or report assembly.

### Minimum Inputs
- User-validated transferred data artifact(s); unproofread transfer drafts are not sufficient.
- Matching handout/normalized section artifacts that define quantity symbols, units, required direct measurements, and required indirect results.
- A calculation or derived-quantity specification for each computable handout-requested result, including uncertainty inputs when propagation is required.

### Optional Workflow Inputs
- Run-plan comparison obligations, procedure anchors, plotting requirements, or interpretation inventory expectations.
- Existing uncertainty rules, processed-data manifests, or approved user corrections.
- Output directory for analysis artifacts and appendix-ready TeX supplements.

### Procedure
- Read the handout first and align symbols, units, and required quantities before calculating.
- Use local `scripts/propagate_uncertainties.py` for derived quantities and propagation-rule calculations, and local rendering helpers for calculation-detail artifacts.
- Emit visible unresolved artifacts for handout-requested quantities that validated data cannot support.
- Add credibility/support labels to processed outputs, distinguishing handout-backed, data-backed, computed, assumed, and unresolved items.

### Outputs
- Direct-measurement summaries and processed-data JSON/Markdown artifacts.
- Derived-quantity specs/results and propagation artifacts where supported.
- `calculation_details_manifest.json` plus generated TeX attachments when appendix-ready calculation detail is requested.
- Visible unresolved artifacts for missing or unsupported handout-requested quantities.

### Validation
- Every computed quantity is traceable to validated transferred data and handout symbols/units.
- Required indirect quantities are either computed with a documented formula/procedure or recorded as unresolved with the missing input named.
- Credibility/support labels are present for processed results so later interpretation does not overstate weak support.

### Failure / Reroute Signals
- Unproofread or missing transferred data: in standalone mode, stop and request validation; in full-workflow mode, reroute to `course-lab-data-transfer` and the proofread gate.
- Missing handout requirements: stop or reroute to handout normalization/run-plan before calculating.
- Incomplete data for a required indirect result: emit unresolved artifacts instead of fabricating or omitting the result.

### Non-Ownership
- Does not write interpretation, broad discussion prose, final report sections, or figure placement.
- Does not silently promote unsupported calculations or pending proposal results into official scope.

## Optional Workflow Metadata
- Suggested future role label: `data-analyst`.
- Typical upstream tools: `course-lab-data-transfer`, `course-lab-handout-normalization`, `course-lab-run-plan`.
- Typical downstream tools: `course-lab-uncertainty-analysis`, `course-lab-plotting`, `course-lab-results-interpretation`, `course-lab-symbolic-expressing`.

## Core Rule

- Read the handout first.
- Build a handout-aligned quantity contract before computing anything.
- Resolve notation against the handout instead of guessing from the transferred table alone.
- Example: `T/N` means quantity `T` with unit `N`, not one merged quantity named `T/N`.
- Preserve direct measured symbols exactly as the handout defines them, even when they look algebraically reducible.
- Example: if the handout measures `2r`, then the direct measured quantity is still `2r`, not `r`.
- If the workflow needs `r`, derive it explicitly later, for example `r = two_r / 2`.
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

For a measured handout symbol like `2r/mm`, keep the direct summary under the preserved measured symbol and use its canonical safe key only in later derived specs:

```json
{
  "measured_symbol": "2r",
  "canonical_key": "two_r",
  "derived_later": "r = two_r / 2"
}
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

Appendix-ready calculation-detail attachments for later `course-lab-final-staging` handoff:

```bash
python3 /root/.codex/skills/course-lab-data-processing/scripts/render_calculation_details.py \
  --spec "/path/to/results/<experiment>/analysis/calculation_details_spec.json" \
  --output-dir "/path/to/results/<experiment>/analysis/calculation_details" \
  --output-manifest "/path/to/results/<experiment>/analysis/calculation_details_manifest.json"
```

Example compact appendix spec shape:

```json
{
  "groups": [
    {
      "title": "LX1 String Calculation Details",
      "slug": "lx1-string-calculation-details",
      "derived_summaries": ["/path/to/results/<experiment>/analysis/uncertainty/string_processing_summary.json"],
      "focus_derived": ["rho", "a", "v_mean"]
    }
  ]
}
```

## Workflow

1. Read the matching handout before touching the data table.
2. List the handout’s direct measured quantities, notation, units, and every indirect quantity it asks to compute.
3. Build a run-local quantity contract so raw labels from the transfer are mapped to handout meanings before summary work starts.
4. Preserve each direct measured symbol exactly in that contract, and assign a canonical safe key only for computation usage.
5. Run `scripts/compute_uncertainties.py` for the direct measured quantities and repeated series.
6. Build a derived-quantity spec for every handout-requested indirect result that is supported by the validated data.
7. Use explicit derived formulas whenever a new quantity symbol differs from the measured symbol, such as `r = two_r / 2`.
8. Run `scripts/propagate_uncertainties.py` on that spec.
9. If the report will need appendix-side calculation detail, run `scripts/render_calculation_details.py` so the derivation chain is preserved outside the main body in a compact appendix style.
10. When the appendix would otherwise become too long, set `focus_derived` in the spec so only the key formulas and propagation steps are emitted.
11. On parent-driven reruns, limit the processing update to the newly confirmed quantities that became official scope while preserving earlier validated outputs unless the new contract explicitly supersedes them.
12. Review the direct and derived outputs together, checking for provisional resolution fields, notation mismatches, handout-requested quantities that are still unresolved, and whether the generated appendix attachments emphasize derivation structure instead of raw numeric repetition.

## Quick Reference

### Contract Notes

- Use local `scripts/compute_uncertainties.py` for direct measured quantities and repeated-measurement summaries.
- Use local `scripts/propagate_uncertainties.py` for indirect quantities and propagation-rule calculations.
- Use local `scripts/render_calculation_details.py` when the run needs appendix-ready calculation-detail attachments for later report staging.
- Keep all data-processing computation paths local to `/root/.codex/skills/course-lab-data-processing/`.
- Keep a quantity contract that preserves the measured symbol and its canonical safe key together.
- Default the expanded-uncertainty coverage factor to `k=2` unless the handout or experiment rules explicitly require a different value.
- Cover every corresponding indirect measured quantity requested in the handout when the validated data are sufficient.
- If a handout-requested indirect quantity cannot yet be computed from validated data, emit a visible unresolved artifact instead of omitting it quietly.
- Keep missing resolution information visible. If a resolution is not yet known, do not invent it.
- On reruns, recompute only the newly confirmed or newly required quantities that upstream comparison obligations added, and keep those outputs comparison-ready for later interpretation.
- When later report assembly needs appendix-ready calculation detail, emit `calculation_details_manifest.json` plus generated `.tex` attachments that present a compact formula-first derivation supplement rather than a raw numeric dump.
- Prefer symbolic calculation flow, partial-derivative propagation structure, and a visible appendix-style callout block over exhaustive value tables.
- Treat those generated calculation-detail attachments as appendix material that may use full-width pages, so readable derivation notation such as `\sqrt{...}` is preferred over special compressed formatting that only exists to protect narrow two-column layouts.
- Allow the calculation-details spec to narrow the appendix with a `focus_derived` list when only key derivations should appear so the appendix stays within a practical page budget.

| Situation | Action |
|---|---|
| A transferred header uses slash notation such as `T/N` or `f/Hz` | Read the handout first and resolve it as quantity plus unit before calculating |
| A measured symbol is composite, such as `2r`, `δl`, or `k_mn` | Preserve that exact measured symbol first; only change it in an explicit derived step |
| Repeated direct measurements are already in CSV or TSV | Run `compute_uncertainties.py` on the resolved direct table |
| A required indirect quantity depends on several direct inputs | Use `propagate_uncertainties.py` with a handout-aligned spec |
| A derived quantity depends on earlier derived quantities | Keep the chained formulas in one propagation spec |
| A direct uncertainty summary already exists in JSON | Reference it from the propagation spec with `summary_json` plus `column` |
| Resolution is unknown | Leave it unresolved and keep the direct result provisional |
| The handout requests a derived result but validated data are incomplete | Emit a visible unresolved artifact instead of faking the calculation |

## Boundary Rules

- This skill starts only after transferred data is confirmed by the user.
- This skill owns uncertainty artifacts, not interpretation prose.
- This skill may rerun for newly confirmed key quantities, but it still does not own importance judgment or interpretation prose.
- Handout notation wins over ambiguous transferred shorthand.
- Do not collapse quantity and unit into one name just because the table header uses a slash.
- Do not algebraically simplify a direct measured symbol just because it contains a numeric factor or familiar sub-expression.
- Do not let uncertainty work expand into theory comparison, reliability judgment, or final discussion drafting.
- Keep parent-skill path dependencies out of the workflow. Use the copied local scripts in this folder instead of the old `course-lab-report` folder.

## Common Mistakes

- Running uncertainty calculations before reading the handout.
- Treating `T/N` as one quantity instead of tension `T` in newtons.
- Treating a measured `2r` row as if it directly measured `r`.
- Summarizing only direct measurements and forgetting the handout’s indirect requested quantities.
- Omitting propagation rules for derived quantities that depend on several inputs.
- Emitting only the final derived number and forgetting the helper quantity chain that later appendix staging needs.
- Hiding missing resolution information by typing in a guessed number.
- Turning uncertainty output into polished conclusions before the interpretation step has the rest of the evidence.

## Resources

- `scripts/compute_uncertainties.py`: local direct-quantity uncertainty calculator
- `scripts/propagate_uncertainties.py`: local derived-quantity and propagation-rule calculator
- `scripts/render_calculation_details.py`: local appendix-ready calculation-detail renderer for later final-staging handoff
- `scripts/common.py`: local copied helper module for standalone packaging
- `tests/test_compute_uncertainties.py`: local regression tests for direct summaries and handout-style labels
- `tests/test_propagate_uncertainties.py`: local regression tests for derived quantities and propagation
- `tests/test_render_calculation_details.py`: local regression tests for appendix-ready calculation-detail artifacts
- `tests/test_skill_package.py`: local standalone packaging tests
