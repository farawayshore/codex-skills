---
name: course-lab-run-plan
description: Use when a course lab-report run already has normalized handout artifacts plus an initialized workspace and now needs a planning-only run-plan contract with downstream leaf-skill handoff buckets, JSON output, Markdown output, and visible unresolved gaps before scaffold, data, or later writing work begins.
---

# Course Lab Run Plan

## Overview

Build a planning-only run-plan contract from normalized handout artifacts without drifting into TeX mutation, data transfer, computation, or later report writing.

This standalone package uses only local copied tools under `/root/.codex/skills/course-lab-run-plan/`. It should reread normalized handout JSON and Markdown, route obvious handout cues into downstream leaf-skill buckets, and emit aligned JSON and Markdown artifacts that keep required work, `comparison_obligations`, enrichment opportunities, and unresolved gaps visible.

## When to Use

- `course-lab-handout-normalization` has already produced normalized section JSON and Markdown.
- `course-lab-workspace-template` has already established the target workspace.
- The run needs a deterministic planning checkpoint before body scaffold, data transfer, plotting, interpretation, or final staging work starts.
- Later skills need a stable JSON handoff contract instead of prose-only notes.
- The handout contains obvious procedure, theory, observation, table, figure, or discussion cues that should be routed into later leaf-skill buckets.

Do not use this skill to choose the experiment, decode PDFs, mutate TeX, perform data transfer, do numerical computation, or write final report sections.

## Output Contract

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
