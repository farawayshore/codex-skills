---
name: course-lab-discussion-synthesis
description: Use when a course lab-report run already has approved discussion-idea handoff artifacts plus matched reference reports and now needs artifact-only discussion harmonization for course-lab-final-staging.
---

# Course Lab Discussion Synthesis

## Overview

Turn approved discussion directions into polished, confidence-aware, artifact-only discussion outputs for `course-lab-final-staging`.

This skill is standalone with local copied tools. It should read approved synthesis-input artifacts first, require caller-provided reference report paths, accept the canonical `discussion_ideas` handoff that `course-lab-discussion-ideas` emits, run one bounded web-enrichment pass on the first accepted-ideas run, allow targeted gap filling later only when the approved ideas are still not enough, and do not mutate `main.tex`.

## Standalone Tool Contract

### Use Independently When

- A caller has `discussion_synthesis_input.tmp.json` from discussion-ideas or an approved equivalent bundle.
- Reference report paths are supplied by the caller and should ground synthesis support.
- The needed output is artifact-only discussion harmonization for later staging, not direct TeX mutation.
- Thinking-question, support-tag, and unresolved-evidence state need to be preserved into final-staging inputs.
- The run needs polished discussion artifacts before `course-lab-final-staging`, and a `reference_selection_status: none_found` lane should stay an optional skip instead of a failed prerequisite.

### Minimum Inputs

- `--experiment-name` and `--experiment-safe-name`.
- `--synthesis-input-json` that is approved or uses `approval_mode: synthesis_judgment` with a canonical `discussion_ideas` list.
- Existing caller-provided `--reference-report` paths.
- Output paths for `discussion_synthesis.json`, `discussion_synthesis.md`, `discussion_synthesis_unresolved.md`, `discussion_staging_input.tmp.json`, and `discussion_staging_input.tmp.md`.

### Optional Workflow Inputs

- `--synthesis-input-markdown` for human-readable context.
- `--results-interpretation-json` and `--results-interpretation-markdown` for data-backed grounding.
- `--prior-synthesis-json` to distinguish first accepted-ideas enrichment from later targeted gap filling.
- Upstream thinking-question prompts and evidence tags from `course-lab-discussion-ideas`.

### Procedure

- Use only local scripts in `/root/.codex/skills/course-lab-discussion-synthesis/scripts/`.
- Validate that input is approved or a valid `synthesis_judgment` handoff before writing synthesis artifacts.
- Preserve evidence labels such as `handout-backed`, `reference-backed`, `data-backed`, `generic/speculative`, and `unresolved` from the idea handoff when deciding wording posture.
- Convert thinking-question prompts into explicit discussion blocks or unresolved notes rather than dropping them.
- Run only one bounded enrichment pass on the first accepted-ideas run; later reruns use targeted gap fill only when weak support remains.

### Outputs

- `discussion_synthesis.json` and `discussion_synthesis.md` with polished, support-aware discussion blocks.
- `discussion_synthesis_unresolved.md` preserving weak support, missing evidence tags, unanswerable thinking questions, or unresolved data-lack notes.
- `discussion_staging_input.tmp.json` and `.md` for final staging, including support strength, source references, approved idea IDs, and any unresolved constraints.

### Validation

- Every synthesized block traces to an approved idea or valid synthesis-judgment item.
- Low-confidence, generic/speculative, or unresolved support remains visibly cautious.
- Thinking-question outputs are either represented in a discussion block or explicitly listed as unresolved.
- No direct mutation of `main.tex` occurs.
- Local discussion-synthesis tests pass.

### Failure / Reroute Signals

- Missing or malformed synthesis input: stop in standalone mode and request a valid discussion-ideas handoff; in full-report mode, reroute to discussion ideas.
- Missing reference reports: stop and request caller-provided reference paths rather than inventing support.
- Weak approved ideas after enrichment: emit cautious wording plus unresolved notes; do not create new major directions without approval.
- Missing data-backed support: keep a visible `data-backed` gap or unresolved/data-lack note instead of smoothing it over.

### Non-Ownership

- This tool does not generate initial ideas, approve major directions, discover references, mutate `main.tex`, perform final staging, or run final QC.
- This tool does not hide weak support just to make final-staging input look complete.
- This tool does not require a full-workflow controller or native agent file for standalone use.

## Optional Workflow Metadata

- Suggested future role label: `discussioner`.
- Typical upstream tools: `course-lab-discussion-ideas`, caller-provided reference selection, optional results interpretation.
- Typical downstream tools: `course-lab-final-staging`, then `course-lab-finalize-qc`.

## Workflow Notes

- Use local `/root/.codex/skills/course-lab-discussion-synthesis/scripts/build_discussion_synthesis.py` as the main synthesis entrypoint.
- Keep runtime dependencies local to `/root/.codex/skills/course-lab-discussion-synthesis/`.
- Treat synthesis-input JSON as required.
- Accept `discussion_ideas` as the canonical pre-synthesis list.
- Accept `approval_mode: synthesis_judgment` when the input came directly from `course-lab-discussion-ideas`.
- Treat caller-provided reference report paths as required.
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
3. Read the caller-provided reference report artifacts.
4. Read optional results-interpretation artifacts when they exist so synthesis stays grounded in experiment evidence.
5. Decide whether this is the first accepted-ideas synthesis run.
6. On the first accepted-ideas run, record one bounded broad enrichment pass.
7. On later runs, use targeted gap fill only when approved ideas remain weak.
8. Emit artifact-only JSON and Markdown outputs for `course-lab-final-staging`.
9. Keep unresolved support gaps visible instead of writing overconfident prose.

## Boundary Rules

- This skill is artifact-only.
- This skill requires approved discussion inputs or a valid `synthesis_judgment` handoff from `course-lab-discussion-ideas`.
- This skill requires caller-provided reference report inputs.
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
