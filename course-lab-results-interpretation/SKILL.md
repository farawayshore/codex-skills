---
name: course-lab-results-interpretation
description: Use when a course lab-report run already has normalized handout artifacts plus processed-data artifacts and now needs handout-first result reasoning, simulation or theory comparison, anomaly visibility, or completeness checks before discussion generation or final staging.
---

# Course Lab Results Interpretation

## Overview

Turn handout-grounded lab evidence into standalone interpretation artifacts without drifting into discussion generation, direct report mutation, or final QC.

This skill is standalone with local copied tools. It should read the normalized handout first, then interpret processed-data artifacts through explicit comparison lanes against simulation outputs and theory/reference values when those exist, while keeping unresolved comparison gaps visible instead of hiding them inside stronger prose.

## When to Use

- The experiment is already confirmed.
- normalized handout artifacts already exist from `course-lab-handout-normalization`.
- `course-lab-data-processing` has already produced processed-data artifacts.
- Optional plot manifests or modeling outputs may already exist and should be folded into result reasoning when relevant.
- The run needs anomaly visibility, result inventory structure, or completeness checks before `course-lab-discussion-ideas` or `course-lab-final-staging`.
- The workflow needs artifact-only outputs rather than direct writing into `main.tex`.

Do not use this skill to transcribe raw data, compute new derived quantities, run modeling jobs, generate discussion ideas, write directly into the report, or perform final QC.

## Output Contract

- Use local `/root/.codex/skills/course-lab-results-interpretation/scripts/build_results_interpretation.py` as the main synthesis entrypoint.
- Keep runtime dependencies local to `/root/.codex/skills/course-lab-results-interpretation/`.
- Read the normalized handout first and treat it as required interpretation context.
- Treat processed-data JSON as a required base input.
- Prefer normalized handout Markdown first. Fall back to normalized handout JSON only when Markdown is absent.
- Treat processed-data Markdown, plot manifests, modeling outputs, references, and run-plan expectations as optional supporting inputs.
- Emit artifact-only outputs:
  - `results_interpretation.json`
  - `results_interpretation.md`
  - `results_interpretation_unresolved.md`
- Include `comparison_records` in `results_interpretation.json` so handout/data/simulation/theory comparisons stay explicit instead of getting buried in prose.
- If theory or reference support is missing, still emit partial interpretation artifacts when the remaining lanes stay honest.
- If the handout expects simulation comparison and modeling artifacts are missing, keep that gap visible in unresolved output instead of downgrading it silently.
- Keep unresolved comparison gaps, conflicting evidence, and missing expected result families visible instead of inventing stronger conclusions.

## Primary Command

```bash
python3 /root/.codex/skills/course-lab-results-interpretation/scripts/build_results_interpretation.py \
  --handout-sections-markdown "/path/to/results/<experiment>/notes/sections.md" \
  --handout-sections-json "/path/to/results/<experiment>/sections.json" \
  --processed-data-json "/path/to/results/<experiment>/analysis/processed_data.json" \
  --processed-data-markdown "/path/to/results/<experiment>/analysis/processed_data.md" \
  --plots-manifest "/path/to/plottings/plot_manifest.json" \
  --modeling-result "/path/to/modeling/run_result.json" \
  --references-json "/path/to/results/<experiment>/analysis/reference_values.json" \
  --run-plan "/path/to/results/<experiment>/<experiment-safe-name>_run_plan.md" \
  --output-json "/path/to/results/<experiment>/results_interpretation.json" \
  --output-markdown "/path/to/results/<experiment>/results_interpretation.md" \
  --output-unresolved "/path/to/results/<experiment>/results_interpretation_unresolved.md"
```

## Workflow

1. Confirm that processed-data artifacts already exist.
2. Read the normalized handout first.
3. Read optional handout JSON only when handout Markdown is absent.
4. Read processed-data JSON as the primary data evidence base.
5. Read optional processed-data Markdown only as a consistency check against the JSON artifact.
6. Read optional plot manifests, modeling outputs, references, and run-plan expectations when they exist.
7. Build a result inventory before writing interpretation notes.
8. Build explicit `comparison_records` across handout expectations, simulation outputs, and theory/reference values when those lanes are supported.
9. Emit artifact-only JSON and Markdown outputs for downstream consumers.
10. Keep unresolved notes explicit when simulation or theory lanes are missing, evidence conflicts, or expected result families are still absent.

## Quick Reference

| Situation | Action |
|---|---|
| Normalized handout exists and processed data exists | Read the normalized handout first before interpreting the data |
| Processed data exists but no references exist | Emit a partial interpretation artifact and record unresolved theory/reference comparison gaps |
| Plot manifest exists | Mark matching result inventory entries as `plotted` |
| Modeling outputs exist | Compare matching simulation outputs against data and add explicit comparison records |
| Handout says simulation comparison is required but no modeling result exists | Emit an unresolved simulation-comparison gap |
| Processed-data JSON and Markdown disagree | Record an unresolved conflict instead of choosing silently |
| Run plan names a missing result family | Emit a completeness warning in the output artifacts |
| Downstream flow needs report prose | Hand off these artifacts to later discussion or final staging instead of mutating `main.tex` here |

## Boundary Rules

- This skill starts only after normalized handout artifacts and processed-data artifacts are available.
- This skill owns artifact-only interpretation outputs, not report mutation.
- This skill does not run modeling, generate discussion ideas, or perform final QC.
- This skill does not compute new upstream quantities; it interprets already-produced evidence.
- Keep all runtime tool usage local to this standalone folder.
- Do not mutate `main.tex` or any direct report file from this skill.
- Do not write theory/reference or simulation comparisons as confirmed when the supporting values are missing.
- Do not skip the handout. Read the normalized handout first.

## Common Mistakes

- Reaching back into the parent skill or sibling skill folders instead of using the local copied script.
- Interpreting processed data before reading the handout.
- Turning missing references into implicit agreement language.
- Treating simulation outputs as decorative source hints instead of explicit comparison targets.
- Folding discussion generation into the interpretation layer.
- Treating processed-data Markdown as a silent override instead of a consistency check.
- Letting the skill mutate report files instead of staying artifact-only.

## Resources

- `scripts/common.py`: local helpers for JSON and text I/O
- `scripts/build_results_interpretation.py`: local interpretation builder
- `tests/baseline_failures.md`: RED-phase failure record for this skill
- `tests/test_skill_package.py`: standalone package checks
- `tests/test_build_results_interpretation.py`: CLI behavior checks
