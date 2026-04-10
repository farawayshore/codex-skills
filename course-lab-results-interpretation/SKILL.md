---
name: course-lab-results-interpretation
description: Use when a course lab-report run already has normalized handout artifacts plus processed-data artifacts and now needs handout-first result justification, explicit handout/internet/theory comparison lanes, anomaly visibility, or completeness checks before discussion generation or final staging.
---

# Course Lab Results Interpretation

## Overview

Turn handout-grounded lab evidence into standalone interpretation artifacts without drifting into discussion generation, direct report mutation, or final QC.

This skill is standalone with local copied tools. It should read the normalized handout first, then justify processed-data artifacts through explicit comparison lanes against simulation outputs, handout standard/example values, internet references, and theory-based comparison values when those exist, while keeping unresolved comparison gaps visible instead of hiding them inside stronger prose.

## Standalone Tool Contract

### Use Independently When
- Normalized handout artifacts and processed-data artifacts exist and the task is to produce artifact-only result interpretation, not report mutation.
- The run needs handout-first justification, comparison lanes, anomaly visibility, completeness checks, or proposal artifacts before discussion or final staging.

### Minimum Inputs
- Normalized handout JSON/Markdown artifacts.
- Processed-data JSON/Markdown artifacts or result inventory produced from validated data.
- Output destination for interpretation JSON/Markdown artifacts.

### Optional Workflow Inputs
- Plot manifests, modeling outputs, simulation outputs, reference/literature artifacts, run-plan comparison obligations, and approved proposal metadata.
- Theoretical comparison values or upstream theory artifacts when explicitly available.
- Existing `agent_proposed_key_results` state for pending/approved/rejected proposal tracking.

### Procedure
- Read the handout before interpreting processed results and build explicit comparison lanes only from available support.
- Emit support/credibility labels such as handout-backed, data-backed, plot-backed, simulation-backed, reference-backed, theory-backed, generic/speculative, or unresolved.
- Keep `agent_proposed_key_results` and `candidate_literature_sources` artifact-only and `pending_user` until a user marks them `approved`, `rejected`, or `needs_revision`.
- Preserve unresolved comparison gaps instead of downgrading or hiding them in stronger prose.

### Outputs
- Artifact-only interpretation JSON and Markdown.
- `comparison_records` across supported handout expectations, simulation outputs, handout standards, internet/reference values, theory values, and approved literature values.
- `agent_proposed_key_results`, `candidate_literature_sources`, completeness warnings, and unresolved justification gaps where applicable.

### Validation
- Every confirmed comparison record has an explicit support source and credibility/support label.
- Pending proposals are not promoted into confirmed comparison sets or canonical references.
- Missing modeling/reference/theory support remains visible in unresolved output while still allowing honest partial interpretation artifacts.

### Failure / Reroute Signals
- Missing processed data or normalized handout: in standalone mode, stop and request the artifact; in full-workflow mode, reroute to the missing upstream tool.
- Missing optional reference/model lane: emit partial interpretation plus unresolved gap rather than blocking all output unless that lane is required by the handout.
- Extra comparison-worthy result discovered: emit it as `pending_user` proposal, not final scope.

### Non-Ownership
- Does not mutate `main.tex`, draft broad final discussion prose, stage figures, or run final QC.
- Does not silently confirm internet/theory/simulation comparisons without source support.

## Optional Workflow Metadata
- Suggested future role label: `data-analyst`.
- Typical upstream tools: `course-lab-data-processing`, `course-lab-uncertainty-analysis`, `course-lab-plotting`, modeling/reference tools.
- Typical downstream tools: `course-lab-discussion-ideas`, `course-lab-discussion-synthesis`, `course-lab-final-staging`.

## Primary Command

```bash
python3 /root/.codex/skills/course-lab-results-interpretation/scripts/build_results_interpretation.py \
  --handout-sections-markdown "/path/to/results/<experiment>/notes/sections.md" \
  --handout-sections-json "/path/to/results/<experiment>/notes/sections.json" \
  --processed-data-json "/path/to/results/<experiment>/analysis/processed_data.json" \
  --processed-data-markdown "/path/to/results/<experiment>/analysis/processed_data.md" \
  --plots-manifest "/path/to/plottings/plot_manifest.json" \
  --modeling-result "/path/to/modeling/run_result.json" \
  --references-json "/path/to/results/<experiment>/analysis/reference_values.json" \
  --run-plan-json "/path/to/results/<experiment>/<experiment-safe-name>_run_plan.json" \
  --run-plan "/path/to/results/<experiment>/<experiment-safe-name>_run_plan.md" \
  --output-json "/path/to/results/<experiment>/results_interpretation.json" \
  --output-markdown "/path/to/results/<experiment>/results_interpretation.md" \
  --output-unresolved "/path/to/results/<experiment>/results_interpretation_unresolved.md"
```

Reference staging helper before the interpretation pass:

```bash
python3 /root/.codex/skills/course-lab-results-interpretation/scripts/stage_reference_values.py \
  --handout-sections-markdown "/path/to/results/<experiment>/notes/sections.md" \
  --handout-sections-json "/path/to/results/<experiment>/notes/sections.json" \
  --processed-data-json "/path/to/results/<experiment>/analysis/processed_data.json" \
  --seed-references-json "/path/to/results/<experiment>/analysis/reference_seed_values.json" \
  --search-spec-json "/path/to/results/<experiment>/analysis/reference_search_spec.json" \
  --approved-literature-json "/path/to/results/<experiment>/analysis/approved_literature.json" \
  --output-json "/path/to/results/<experiment>/analysis/reference_values.json" \
  --output-unresolved "/path/to/results/<experiment>/analysis/reference_values_unresolved.md"
```

Recommended `references-json` shape when justification needs multiple lanes:

```json
{
  "comparison_requirements": {
    "required_bases": ["internet_reference", "theoretical_computation"],
    "optional_bases": ["handout_standard"]
  },
  "references": [
    {
      "name": "youngs_modulus",
      "label": "Handout stainless reference",
      "value": 1.95e11,
      "unit": "Pa",
      "comparison_basis": "handout_standard",
      "source": "notes/sections.md:157"
    },
    {
      "name": "youngs_modulus",
      "label": "Published alloy reference",
      "value": 2.00e11,
      "unit": "Pa",
      "comparison_basis": "internet_reference",
      "source": "https://example.org/material-data"
    },
    {
      "name": "youngs_modulus",
      "label": "Beam-model inversion",
      "value": 2.01e11,
      "unit": "Pa",
      "comparison_basis": "theoretical_computation",
      "source": "analysis/theory_checks.json:youngs_modulus"
    }
  ]
}
```

## Workflow

1. Confirm that processed-data artifacts already exist.
2. Read the normalized handout first.
3. Read optional handout JSON only when handout Markdown is absent.
4. Read processed-data JSON as the primary data evidence base.
5. Read optional processed-data Markdown only as a consistency check against the JSON artifact.
6. Gather justification evidence for the processed results that need checking.
7. Prefer running `/root/.codex/skills/course-lab-results-interpretation/scripts/stage_reference_values.py` before the interpretation pass when internet-reference staging is needed.
8. Read optional plot manifests, modeling outputs, references, run-plan expectations, and confirmed run-plan JSON obligations when they exist.
9. For each important processed result, compare against:
   - handout standard/example values when the handout provides them
   - internet references gathered from credible sources with preserved links
   - relevant theoretical comparison values or upstream theory artifacts
10. When `comparison_obligations` are confirmed upstream, use them to drive primary lanes such as `theory_vs_data`, `simulation_vs_data`, and `literature_report_vs_data`.
11. Build a result inventory before writing interpretation notes.
12. Build explicit `comparison_records` across handout expectations, simulation outputs, handout standards, internet references, theory values, and approved literature values when those lanes are supported.
13. Emit `agent_proposed_key_results` and `candidate_literature_sources` for extra results that still need confirmation; keep those proposals artifact-only and pending until the user marks them `approved`, `rejected`, or `needs_revision`.
14. Emit artifact-only JSON and Markdown outputs for downstream consumers.
15. Keep unresolved notes explicit when simulation or justification lanes are missing, evidence conflicts, or expected result families are still absent.

## Quick Reference

### Contract Notes

- Use local `/root/.codex/skills/course-lab-results-interpretation/scripts/build_results_interpretation.py` as the main synthesis entrypoint.
- Use local `/root/.codex/skills/course-lab-results-interpretation/scripts/stage_reference_values.py` to stage `reference_values.json` by merging local handout/theory seeds with live internet search results.
- Keep runtime dependencies local to `/root/.codex/skills/course-lab-results-interpretation/`.
- Read the normalized handout first and treat it as required interpretation context.
- Treat processed-data JSON as a required base input.
- Prefer normalized handout Markdown first. Fall back to normalized handout JSON only when Markdown is absent.
- Treat processed-data Markdown, plot manifests, modeling outputs, references, run-plan expectations, and confirmed `comparison_obligations` as optional supporting inputs.
- Emit artifact-only outputs:
  - `results_interpretation.json`
  - `results_interpretation.md`
  - `results_interpretation_unresolved.md`
- Include `comparison_records` in `results_interpretation.json` so handout/data/simulation/theory comparisons stay explicit instead of getting buried in prose.
- When a confirmed run-plan JSON exists, read `comparison_obligations` from it and treat those obligations as the primary comparison contract.
- Emit `agent_proposed_key_results` when interpretation discovers extra comparison-worthy results that still need user confirmation.
- Mark proposals explicitly with states such as `pending_user`, and keep only later `approved` proposals eligible for promotion into downstream reference artifacts.
- Emit `candidate_literature_sources` only for proposal paths; do not silently promote those sources into the confirmed comparison set.
- Prefer one reference artifact that can hold multiple entries per processed result, distinguished by `comparison_basis` such as `handout_standard`, `internet_reference`, and `theoretical_computation`.
- Preserve approved literature promotion with explicit `comparison_basis: literature_report` and `lane: literature_report_vs_data`.
- When internet references are used, preserve the concrete source link and enough citation metadata for later attribution.
- Use `comparison_requirements` in `references-json` when a run should explicitly require some justification lanes, for example `internet_reference` and `theoretical_computation`.
- If theory or reference support is missing, still emit partial interpretation artifacts when the remaining lanes stay honest.
- If a required justification lane is missing for a processed result, keep that gap explicit in unresolved output instead of silently downgrading the check.
- If the handout expects simulation comparison and modeling artifacts are missing, keep that gap visible in unresolved output instead of downgrading it silently.
- Keep unresolved comparison gaps, conflicting evidence, and missing expected result families visible instead of inventing stronger conclusions.

| Situation | Action |
|---|---|
| Normalized handout exists and processed data exists | Read the normalized handout first before interpreting the data |
| Processed data exists but no references exist | Emit a partial interpretation artifact and record unresolved justification gaps |
| A result such as Young's modulus or a characteristic frequency needs justification | Seek a handout value if present, search the internet for a credible comparison source, and include a theory-based comparison value when available |
| Plot manifest exists | Mark matching result inventory entries as `plotted` |
| Modeling outputs exist | Compare matching simulation outputs against data and add explicit comparison records |
| Handout says simulation comparison is required but no modeling result exists | Emit an unresolved simulation-comparison gap |
| `references-json` includes multiple entries for one result | Emit one comparison record per `comparison_basis` instead of collapsing them into one generic reference lane |
| Confirmed run-plan JSON includes `comparison_obligations` | Treat those obligations as the source of truth for primary comparison lanes |
| Interpretation finds an extra qualitative or literature-backed result | Emit it in `agent_proposed_key_results` with `pending_user` instead of silently promoting it |
| Approved literature metadata exists upstream | Promote only the approved entries into the canonical reference artifact with explicit literature lanes |
| `comparison_requirements` demands a lane that is absent | Emit an unresolved missing-justification note for that result |
| Processed-data JSON and Markdown disagree | Record an unresolved conflict instead of choosing silently |
| Run plan names a missing result family | Emit a completeness warning in the output artifacts |
| Downstream flow needs report prose | Hand off these artifacts to later discussion or final staging instead of mutating `main.tex` here |

## Boundary Rules

- This skill starts only after normalized handout artifacts and processed-data artifacts are available.
- This skill owns artifact-only interpretation outputs, not report mutation.
- This skill does not run modeling, generate discussion ideas, or perform final QC.
- This skill does not rerun upstream raw-data processing or full modeling jobs, but it may compute lightweight comparison deltas once the comparison values already exist.
- Keep all runtime tool usage local to this standalone folder.
- Do not mutate `main.tex` or any direct report file from this skill.
- Do not write handout, internet, theory, or simulation comparisons as confirmed when the supporting values are missing.
- Do not silently move `pending_user` proposal items into the confirmed comparison set.
- Do not promote candidate literature sources unless the parent flow has marked them `approved`.
- Do not skip the handout. Read the normalized handout first.

## Common Mistakes

- Reaching back into the parent skill or sibling skill folders instead of using the local copied script.
- Interpreting processed data before reading the handout.
- Turning missing handout/internet/theory lanes into implicit agreement language.
- Treating simulation outputs as decorative source hints instead of explicit comparison targets.
- Collapsing handout standards, internet references, and theory calculations into one vague comparison bucket.
- Folding discussion generation into the interpretation layer.
- Treating processed-data Markdown as a silent override instead of a consistency check.
- Letting the skill mutate report files instead of staying artifact-only.

## Resources

- `scripts/common.py`: local helpers for JSON and text I/O
- `scripts/build_results_interpretation.py`: local interpretation builder
- `scripts/stage_reference_values.py`: local helper that searches the web and stages `reference_values.json`
- `tests/baseline_failures.md`: RED-phase failure record for this skill
- `tests/test_skill_package.py`: standalone package checks
- `tests/test_build_results_interpretation.py`: CLI behavior checks
- `tests/test_stage_reference_values.py`: staged reference helper checks
