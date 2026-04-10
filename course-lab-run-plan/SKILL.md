---
name: course-lab-run-plan
description: Use when a course lab-report run already has normalized handout artifacts plus an initialized workspace and now needs a planning-only run-plan contract with downstream leaf-skill handoff buckets, JSON output, Markdown output, and visible unresolved gaps before scaffold, data, or later writing work begins.
---

# Course Lab Run Plan

## Overview

Build a planning-only run-plan contract from normalized handout artifacts without drifting into TeX mutation, data transfer, computation, or later report writing.

This standalone package uses only local copied tools under `/root/.codex/skills/course-lab-run-plan/`. It should reread normalized handout JSON and Markdown, route obvious handout cues into downstream leaf-skill buckets, and emit aligned JSON and Markdown artifacts that keep required work, `comparison_obligations`, enrichment opportunities, and unresolved gaps visible.

Do not use this skill to choose the experiment, decode PDFs, mutate TeX, perform data transfer, do numerical computation, or write final report sections.

## Standalone Tool Contract

### Use Independently When
- Normalized handout artifacts and a workspace target exist, and the next step is a planning-only downstream handoff rather than TeX mutation or analysis.
- Required work, comparison obligations, enrichment opportunities, and unresolved gaps must be captured as aligned JSON and Markdown artifacts.

### Minimum Inputs
- Normalized handout JSON and Markdown artifacts.
- Workspace or notes output directory for run-plan artifacts.
- Experiment/workspace identity so artifact names can be tied to the current report.

### Optional Workflow Inputs
- Workspace manifest and canonical TeX path for context only.
- Discovery manifest, scaffold/procedure notes, or user constraints that should be reflected as handoff buckets.
- Previously approved comparison obligations; pending or rejected proposals must remain separate.

### Procedure
- Use the local run-plan generator under this package to reread normalized handout artifacts and emit planning artifacts only.
- Route obvious handout cues into downstream leaf-tool buckets without invoking those tools.
- Keep unresolved gaps and optional enrichment opportunities visible instead of silently narrowing scope.

### Outputs
- Workspace-local run-plan JSON and Markdown artifacts.
- Downstream handoff buckets for scaffold, data transfer, processing, uncertainty, plotting, interpretation, discussion, figure evidence, and final QC as applicable.
- Visible unresolved gaps and comparison obligations with pending/rejected proposals kept out of confirmed obligations.

### Validation
- JSON and Markdown run-plan artifacts are aligned and name the same required work and unresolved gaps.
- The run plan is planning-only: it does not mutate TeX, data, plots, or interpretation artifacts.
- Pending or rejected agent proposals are not promoted into `comparison_obligations`.

### Failure / Reroute Signals
- Missing normalized handout artifacts: in standalone mode, stop and request them; in full-workflow mode, reroute to `course-lab-handout-normalization`.
- Missing workspace target: emit a path-specific blocker and reroute to workspace setup.
- Handout cues too ambiguous for a bucket: record an unresolved planning gap rather than assigning false ownership.

### Non-Ownership
- Does not choose which later tool to invoke, perform data transfer/calculation, mutate TeX, or write final report prose.
- Does not confirm scientific scope beyond what the handout and explicit user inputs support.

## Optional Workflow Metadata
- Suggested future role label: `preparer`.
- Typical upstream tools: `course-lab-handout-normalization`, `course-lab-workspace-template`.
- Typical downstream tools: all leaf tools that consume run-plan handoff buckets.

## Primary Command

```bash
python3 /root/.codex/skills/course-lab-run-plan/scripts/build_run_plan.py \
  --sections-json "/path/to/results/<experiment>/notes/sections.json" \
  --sections-markdown "/path/to/results/<experiment>/notes/sections.md" \
  --workspace "/path/to/results/<experiment>" \
  --experiment-name "Interference Lab" \
  --experiment-safe-name "interference_lab" \
  --report-language "English" \
  --confirmed-agent-key-results-json "/path/to/results/<experiment>/confirmed_agent_key_results.json" \
  --output-json "/path/to/results/<experiment>/interference_lab_run_plan.json" \
  --output-markdown "/path/to/results/<experiment>/interference_lab_run_plan.md"
```

## Workflow

1. Confirm that normalized handout JSON and Markdown already exist at `/path/to/results/<experiment>/notes/sections.json` and `/path/to/results/<experiment>/notes/sections.md`.
2. Read `references/run_plan_rules.md` before deciding how to route handout cues.
3. Run `scripts/build_run_plan.py` with the normalized inputs and the target workspace path.
4. Review `run_readiness`, `leaf_skill_handoffs`, `comparison_obligations`, and `global_unresolved_gaps` in the JSON output.
5. Review the Markdown rendering to make sure the same bucket structure and unresolved-gap visibility are present.
6. Hand the run-plan artifacts forward to later skills without treating this skill as the parent orchestrator.

## Quick Reference

### Contract Notes

- Use local `/root/.codex/skills/course-lab-run-plan/scripts/build_run_plan.py` as the canonical run-plan builder.
- Feed it workspace-local normalized section JSON plus workspace-local normalized section Markdown from `/path/to/results/<experiment>/notes/sections.json` and `/path/to/results/<experiment>/notes/sections.md`.
- Emit two aligned workspace-local artifacts:
  - `AI_works/results/<experiment-safe-name>/<experiment-safe-name>_run_plan.json`
  - `AI_works/results/<experiment-safe-name>/<experiment-safe-name>_run_plan.md`
- Keep the JSON organized by downstream leaf-skill handoff buckets.
- Keep `comparison_obligations` in the same contract so later interpretation work can compare only handout-required or already confirmed key results.
- Render the Markdown directly from the same contract so the JSON and Markdown do not drift apart.
- Keep unresolved gaps visible instead of inventing missing deliverables or pretending the handout is clearer than it is.
- Accept optional rerun promotion input through `--confirmed-agent-key-results-json` when the parent flow has already approved additional comparison targets.

| Situation | Action |
|---|---|
| Handout clearly names procedure steps | Route them to `course-lab-body-scaffold` inputs |
| Handout clearly names introduction or principle content | Route those headings to `course-lab-experiment-principle` |
| Handout includes tables or measurement records | Route those cues to `course-lab-data-transfer` |
| Handout or approved rerun notes identify comparison-critical results | Keep them in `comparison_obligations` with explicit lane and basis metadata |
| One cue serves multiple later skills | Keep it visible in more than one relevant bucket |
| A cue is incomplete or underspecified | Keep it in local `unresolved_gaps` and `global_unresolved_gaps` |
| Handout cue suggests final report prose | Keep it as planning guidance only; do not write final prose here |

## Boundary Rules

- This skill is planning-only.
- This skill does not mutate `main.tex` or any other TeX file.
- This skill does not perform raw data transfer.
- This skill does not do numerical computation or uncertainty computation.
- This skill does not write final interpretation, discussion, or final-staging report prose.
- This skill does not choose which later leaf skill to invoke; it only emits handoff artifacts.
- This skill does not promote pending or rejected agent proposals into `comparison_obligations`.
- Keep all runtime dependencies local to this standalone folder.

## Common Mistakes

- Turning the run plan into freeform prose with no deterministic JSON contract.
- Smuggling body scaffold, data transfer, or final writing work into the planning step.
- Hiding incomplete deliverables instead of leaving visible unresolved gaps.
- Reaching back into an old parent-skill script path instead of using the local copied toolchain.

## Resources

- `scripts/build_run_plan.py`: local deterministic run-plan builder
- `scripts/common.py`: local helper functions for bucket construction and cue extraction
- `references/run_plan_rules.md`: local routing, ambiguity, and do-not-invent rules
- `tests/test_build_run_plan.py`: local regression tests for contract shape, routing, unresolved gaps, and CLI output
- `tests/test_skill_package.py`: local package-contract tests
