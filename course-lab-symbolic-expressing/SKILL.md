---
name: course-lab-symbolic-expressing
description: Use when a course lab-report run has explicit handout, calculation-code, and processed-result artifacts and a selected result needs temporary TeX mathematical procedure support before another skill consumes the returned path.
---

# Course Lab Symbolic Expressing

## Overview

Use this optional standalone helper to explain how a selected processed result follows from the handout and calculation code. It writes temporary TeX-like formula/procedure artifacts and returns the path to the requesting skill.

## Standalone Tool Contract

### Use Independently When
- A selected processed result needs a compact undergraduate-readable TeX formula/procedure explanation before another tool consumes it.
- Handout, calculation-code, and processed-result artifacts are all available for a traceable symbolic handoff.

### Minimum Inputs
- Selected result key or result identifier.
- Handout/normalized section artifact containing the relevant formula or theory context.
- Calculation code or calculation-detail artifact showing how the value was computed.
- Processed-result artifact with expressions, values, units, and uncertainty support.

### Optional Workflow Inputs
- Appendix calculation manifest, uncertainty artifacts, or downstream TeX insertion target.
- Requested notation style or formula depth from the report template or user.

### Procedure
- Read the handout, calculation code/details, and processed-result artifact for the selected result only.
- Write a compact temporary TeX-like formula chain and procedure note that traces inputs to output.
- Return the artifact path to the requesting caller instead of mutating broad report prose.

### Outputs
- Temporary TeX/procedure artifact for the selected result.
- A short handoff note naming the result key, source artifacts, and any unresolved formula/notation gaps.

### Validation
- The formula chain is traceable to the handout and calculation artifacts.
- Values, units, and uncertainty terms match the processed-result artifact.
- The output is scoped to the selected result and has a path that downstream tools can consume.

### Failure / Reroute Signals
- Missing handout, calculation code, or processed result: in standalone mode, stop and request the exact artifact; in full-workflow mode, reroute to the missing upstream data-processing or handout-normalization step.
- Ambiguous result key: list candidate keys and wait for a selection.
- Formula support absent: emit an unresolved notation/procedure gap rather than inventing derivations.

### Non-Ownership
- Does not run calculations, decide scientific scope, edit the canonical report, or draft broad interpretation/discussion prose.
- Does not generalize one selected result's formula route to unrelated results.

## Optional Workflow Metadata
- Suggested future role label: `data-analyst`.
- Typical upstream tools: `course-lab-data-processing`, `course-lab-uncertainty-analysis`, `course-lab-handout-normalization`.
- Typical downstream tools: `course-lab-final-staging`, `course-lab-experiment-principle`, requester-specific TeX insertion tools.

## Primary Command

```bash
python3 /root/.codex/skills/course-lab-symbolic-expressing/scripts/render_symbolic_explanation.py \
  --handout "/path/to/decoded_handout.md" \
  --calculation-code "/path/to/analysis/process_data.py" \
  --processed-result "/path/to/analysis/derived_uncertainty.json" \
  --result-key "wave_speed" \
  --output-dir "/path/to/results/<experiment>/analysis/symbolic_expressing/tmp" \
  --output-response-json "/path/to/results/<experiment>/analysis/symbolic_expressing/tmp/wave_speed_symbolic_response.json"
```

## Workflow

1. Read the handout first for official formulas, symbols, units, and result meaning.
2. Read the calculation code for the actual expression chain used for the selected result.
3. Read the processed result artifact for stored expressions, values, units, and uncertainty support.
4. Write a compact temporary TeX artifact with the formula chain and calculation route.
5. Write response JSON with `tex_path`, source trace, and `unresolved` notes.
6. Return the response path or printed TeX path to the caller.

## Quick Reference

### Contract Notes

- Use local `scripts/render_symbolic_explanation.py`.
- Require explicit `--handout`, `--calculation-code`, `--processed-result`, `--result-key`, `--output-dir`, and `--output-response-json`.
- Return the generated `tex_path` through response JSON.
- Keep unresolved handout/code/result mismatches visible instead of inventing derivations.
- Default callers should use workspace-local temp output such as `analysis/symbolic_expressing/tmp/`; callers may override to `/tmp/...` for one-shot use.
- This skill does not mutate `main.tex` or discover files by scanning the workspace.

## Common Mistakes

- Mutating `main.tex` directly instead of returning a path.
- Treating this helper as a required stage between data processing and final staging.
- Recomputing results instead of explaining the existing calculation route.
- Hiding handout/code mismatches or missing formula evidence.
- Scanning for source files instead of requiring explicit caller-owned paths.
