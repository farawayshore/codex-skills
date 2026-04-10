---
name: course-lab-discussion-ideas
description: Use when a course lab-report run already has stable interpretation artifacts plus matched reference reports and now needs beyond-handout, non-routine discussion idea selection before discussion synthesis.
---

# Course Lab Discussion Ideas

## Overview

Turn stable interpretation evidence into artifact-only discussion ideas without drifting into final harmonized discussion writing or direct report mutation.

This skill is standalone with local copied tools. It should read stable interpretation artifacts first, require caller-provided reference report paths or an explicit `none_found` skip lane, and keep only beyond-handout, non-routine directions that require extra analysis, extraction, digitization, fitting, modeling, or other evidence-generation work outside the normal report lane. It must check experiment-local permanent memory before any broad web search, only search for novelty-qualified directions, always record targeted candidate refinement rounds for retained ideas, and write synthesis-judgment-ready approval state into the handoff artifacts instead of prompting for direct approval here.

## Standalone Tool Contract

### Use Independently When

- A caller already has stable `results_interpretation.json` and wants discussion-idea artifacts, not report prose.
- Reference reports were selected by the caller, or the caller explicitly declares a `none_found` reference-selection lane.
- The desired output is a novelty-gated idea list for later synthesis judgment.
- The run needs thinking-question or beyond-handout prompts tagged by evidence strength before discussion synthesis.
- The run needs reusable snippets and synthesis judgment handoff before `course-lab-discussion-synthesis`, and a `reference_selection_status: none_found` lane should stay a neutral skip rather than a failure.

### Minimum Inputs

- `--experiment-name` and `--experiment-safe-name`.
- `--results-interpretation-json` with stable interpretation evidence.
- At least one existing `--reference-report` path, unless the caller is intentionally recording a standalone `none_found` skip outside the builder script.
- `--idea-gists` and `--memory-root` for experiment-local idea memory checks.
- Output paths for `discussion_ideas.json`, `discussion_ideas.md`, `discussion_ideas_unresolved.md`, `discussion_synthesis_input.tmp.json`, and `discussion_synthesis_input.tmp.md`.

### Optional Workflow Inputs

- `--results-interpretation-markdown`, `--processed-data-json`, `--uncertainty-markdown`, `--plots-manifest`, `--picture-evidence-plan`, and `--modeling-result` when they add evidence context.
- Prior experiment-local memory that can suppress repeated broad search.
- Caller-provided reference-selection status such as `none_found` to justify a neutral zero-idea lane.

### Procedure

- Use only local scripts in `/root/.codex/skills/course-lab-discussion-ideas/scripts/`.
- Load interpretation evidence before searching or reading broad references.
- Filter out routine uncertainty, routine theory comparison, ordinary anomaly bookkeeping, and normal report obligations.
- For every retained candidate, include a thinking-question or follow-up prompt when it helps synthesis decide whether the idea is worth keeping.
- Tag support in each idea with evidence labels such as `handout-backed`, `reference-backed`, `data-backed`, `generic/speculative`, and `unresolved`; mixed support is allowed, but unsupported novelty must stay visibly tentative.
- Preserve `pending_synthesis_judgment` rather than asking for direct approval in this tool.

### Outputs

- `discussion_ideas.json` and `discussion_ideas.md` with `discussion_ideas` as the canonical list.
- Per-idea support tags/evidence tags, source-evidence notes, thinking-question/follow-up prompts where applicable, confidence, and synthesis-position hints.
- `discussion_ideas_unresolved.md` documenting missing references, weak support, `none_found` skips, or no justified non-routine ideas.
- `discussion_synthesis_input.tmp.json` and `.md` carrying synthesis-judgment-ready state for `course-lab-discussion-synthesis`.

### Validation

- Output ideas are beyond-handout and non-routine; routine comparison or uncertainty lanes are absent.
- Each retained idea has evidence/support labels and does not present generic/speculative material as verified.
- Targeted refinement rounds are recorded for retained candidates.
- Zero-idea outputs are acceptable when the evidence does not justify a non-routine idea and the unresolved file records why.
- Local discussion-ideas tests pass.

### Failure / Reroute Signals

- Missing `results_interpretation.json`: stop in standalone mode and request the interpretation artifact; in full-report mode, return a reroute hint to results interpretation.
- Missing reference reports without an explicit `none_found` lane: stop and request caller-provided reference selection.
- Weak or generic-only support: emit no idea or mark the candidate `generic/speculative` or `unresolved` instead of promoting it.
- Permanent memory conflict or stale idea reuse: keep the conflict visible and require targeted refinement before retention.

### Non-Ownership

- This tool does not discover reference reports, run modeling, mutate `main.tex`, approve final discussion directions, synthesize final discussion prose, or write the report.
- This tool does not treat a zero-idea run as a failure when the skip path is explicit.
- This tool does not create native course-lab agent files or require any full-workflow controller to be useful.

## Optional Workflow Metadata

- Suggested future role label: `discussioner`.
- Typical upstream tools: `course-lab-results-interpretation`, optional reference-selection/discovery artifacts.
- Typical downstream tools: `course-lab-discussion-synthesis`, then `course-lab-final-staging`.

## Workflow Notes

- Use local `/root/.codex/skills/course-lab-discussion-ideas/scripts/build_discussion_ideas.py` as the main entrypoint.
- Keep runtime dependencies local to `/root/.codex/skills/course-lab-discussion-ideas/`.
- Treat `results_interpretation.json` as required.
- Treat caller-provided reference report paths as required unless an explicit `none_found` skip lane is being recorded.
- Read experiment-local permanent memory before deciding whether broad search is allowed.
- Only retain beyond-handout, non-routine novelty directions that imply extra analysis or evidence generation.
- Search obeys the same rule: do not browse routine comparison, routine uncertainty, ordinary anomaly prose, or normal report obligations.
- Skip broad first-pass browsing when permanent memory already exists for the experiment.
- Always run targeted refinement for retained novelty candidates and allow one or two targeted rounds.
- A successful run may keep zero discussion ideas if no non-routine direction is justified by the evidence.
- Treat `discussion_ideas` as the canonical idea list in both `discussion_ideas.json` and `discussion_synthesis_input.tmp.json`.
- Write per-idea approval state such as `pending_synthesis_judgment` into `discussion_synthesis_input.tmp.*` so `course-lab-discussion-synthesis` can judge what to keep.
- When reference selection produced `none_found`, keep the zero-idea lane explicit and preserve that neutral skip outcome instead of inventing discussion work.
- Emit artifact-only outputs:
  - `discussion_ideas.json`
  - `discussion_ideas.md`
  - `discussion_ideas_unresolved.md`
  - `discussion_synthesis_input.tmp.json`
  - `discussion_synthesis_input.tmp.md`

## Primary Command

```bash
python3 /root/.codex/skills/course-lab-discussion-ideas/scripts/build_discussion_ideas.py \
  --experiment-name "Mechanics Combined" \
  --experiment-safe-name "mechanics_combined_english" \
  --results-interpretation-json "/path/to/results/<experiment>/results_interpretation.json" \
  --results-interpretation-markdown "/path/to/results/<experiment>/results_interpretation.md" \
  --reference-report "/path/to/reference_report_a.json" \
  --reference-report "/path/to/reference_report_b.json" \
  --idea-gists "/root/grassman_projects/AI_works/resources/experiment_discussion_ideas/idea_gists.md" \
  --memory-root "/root/grassman_projects/AI_works/resources/experiment_discussion_ideas" \
  --output-json "/path/to/results/<experiment>/discussion_ideas.json" \
  --output-markdown "/path/to/results/<experiment>/discussion_ideas.md" \
  --output-unresolved "/path/to/results/<experiment>/discussion_ideas_unresolved.md" \
  --output-synthesis-json "/path/to/results/<experiment>/discussion_synthesis_input.tmp.json" \
  --output-synthesis-markdown "/path/to/results/<experiment>/discussion_synthesis_input.tmp.md"
```

## Boundary Rules

- This skill is artifact-only.
- This skill requires caller-provided reference report inputs or an explicit `none_found` reference-selection lane.
- This skill updates permanent memory only through local tools in this folder.
- This skill only captures beyond-handout, non-routine discussion ideas.
- This skill does not mutate the report.
- This skill does not write final harmonized discussion prose.
- This skill does not stop for a direct approval prompt; it writes judgment-ready approval state for synthesis instead.
- This skill may emit reusable snippets, but those snippets are not the final discussion section.
- If the caller run is on a `none_found` reference-selection lane, this skill may emit zero ideas and must keep that skip path visible rather than forcing fake candidates.

## Common Mistakes

- Treating reference reports as optional.
- Treating routine comparison or routine uncertainty as discussion ideas.
- Searching first and filtering later instead of novelty-gating the search itself.
- Re-running broad browsing even when permanent memory already exists.
- Skipping targeted refinement for retained candidates.
- Asking for direct approval on ideas instead of writing synthesis-judgment-ready approval state into the handoff.
- Turning idea artifacts into synthesis-owned final prose.
- Reaching back into sibling skill folders instead of using the local copied scripts.
