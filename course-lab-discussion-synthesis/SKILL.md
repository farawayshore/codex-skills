---
name: course-lab-discussion-synthesis
description: Use when a course lab-report run already has approved discussion-idea handoff artifacts plus matched reference reports and now needs artifact-only discussion harmonization for course-lab-final-staging.
---

# Course Lab Discussion Synthesis

## Overview

Turn approved discussion directions into polished, confidence-aware, artifact-only discussion outputs for `course-lab-final-staging`.

This skill is standalone with local copied tools. It should read approved synthesis-input artifacts first, require parent-passed reference report paths, accept the canonical `discussion_ideas` handoff that `course-lab-discussion-ideas` emits, run one bounded web-enrichment pass on the first accepted-ideas run, allow targeted gap filling later only when the approved ideas are still not enough, and do not mutate `main.tex`.

## When to Use

- The experiment is already confirmed.
- `discussion_synthesis_input.tmp.json` already exists, either as an approved bundle or as a `synthesis_judgment` handoff from `course-lab-discussion-ideas`.
- Matched reference report paths have already been selected by the parent workflow.
- The run needs discussion harmonization before `course-lab-final-staging`.
- The workflow needs polished discussion artifacts rather than direct writing into the report.
- When the parent records `reference_selection_status: none_found`, this lane is optional and the skip should be recorded in `skipped_optional_leaves` instead of treated as a failed prerequisite.

Do not use this skill to generate initial discussion ideas, approve major directions, discover reference reports, mutate `main.tex`, or perform final staging.

## Output Contract

- Use local `/root/.codex/skills/course-lab-discussion-synthesis/scripts/build_discussion_synthesis.py` as the main synthesis entrypoint.
- Keep runtime dependencies local to `/root/.codex/skills/course-lab-discussion-synthesis/`.
- Treat synthesis-input JSON as required.
- Accept `discussion_ideas` as the canonical pre-synthesis list.
- Accept `approval_mode: synthesis_judgment` when the input came directly from `course-lab-discussion-ideas`.
- Treat parent-passed reference report paths as required.
- Perform one bounded first accepted-ideas web-enrichment pass on the first synthesis run.
- Skip repeated broad browsing on reruns unless the approved ideas are still weak enough to justify targeted gap fill.
- Emit artifact-only outputs:
  - `discussion_synthesis.json`
  - `discussion_synthesis.md`
  - `discussion_synthesis_unresolved.md`
  - `discussion_staging_input.tmp.json`
  - `discussion_staging_input.tmp.md`

## Primary Command

```bash
python3 /root/.codex/skills/course-lab-discussion-synthesis/scripts/build_discussion_synthesis.py \
  --experiment-name "Mechanics Combined" \
  --experiment-safe-name "mechanics_combined_english" \
  --synthesis-input-json "/path/to/results/<experiment>/discussion_synthesis_input.tmp.json" \
  --synthesis-input-markdown "/path/to/results/<experiment>/discussion_synthesis_input.tmp.md" \
  --reference-report "/path/to/reference_report_a.json" \
  --reference-report "/path/to/reference_report_b.json" \
  --results-interpretation-json "/path/to/results/<experiment>/results_interpretation.json" \
  --prior-synthesis-json "/path/to/results/<experiment>/discussion_synthesis.json" \
  --output-json "/path/to/results/<experiment>/discussion_synthesis.json" \
  --output-markdown "/path/to/results/<experiment>/discussion_synthesis.md" \
  --output-unresolved "/path/to/results/<experiment>/discussion_synthesis_unresolved.md" \
  --output-staging-json "/path/to/results/<experiment>/discussion_staging_input.tmp.json" \
  --output-staging-markdown "/path/to/results/<experiment>/discussion_staging_input.tmp.md"
```

## Workflow

1. Confirm that synthesis-input artifacts already exist.
2. Read the synthesis-input JSON first and fail clearly if it is neither approved nor a valid `synthesis_judgment` handoff with `discussion_ideas`.
3. Read the parent-passed reference report artifacts.
4. Read optional results-interpretation artifacts when they exist so synthesis stays grounded in experiment evidence.
5. Decide whether this is the first accepted-ideas synthesis run.
6. On the first accepted-ideas run, record one bounded broad enrichment pass.
7. On later runs, use targeted gap fill only when approved ideas remain weak.
8. Emit artifact-only JSON and Markdown outputs for `course-lab-final-staging`.
9. Keep unresolved support gaps visible instead of writing overconfident prose.

## Boundary Rules

- This skill is artifact-only.
- This skill requires approved discussion inputs or a valid `synthesis_judgment` handoff from `course-lab-discussion-ideas`.
- This skill requires reference report inputs from the parent workflow.
- This skill does not mutate the report.
- This skill does not write directly into `main.tex`.
- This skill does not invent new unapproved major discussion directions during research.
- This skill does not perform final staging or final QC.

## Common Mistakes

- Treating malformed `synthesis_judgment` input without `discussion_ideas` as acceptable synthesis input.
- Treating reference reports as optional.
- Repeating broad browsing on later reruns.
- Hiding weak support instead of surfacing it in unresolved output.
- Reaching back into sibling skill folders instead of using the local copied scripts.
