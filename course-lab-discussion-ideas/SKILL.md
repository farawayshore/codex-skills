---
name: course-lab-discussion-ideas
description: Use when a course lab-report run already has stable interpretation artifacts plus matched reference reports and now needs beyond-handout, non-routine discussion idea selection before discussion synthesis.
---

# Course Lab Discussion Ideas

## Overview

Turn stable interpretation evidence into artifact-only discussion ideas without drifting into final harmonized discussion writing or direct report mutation.

This skill is standalone with local copied tools. It should read stable interpretation artifacts first, require parent-passed reference report paths, and keep only beyond-handout, non-routine directions that require extra analysis, extraction, digitization, fitting, modeling, or other evidence-generation work outside the normal report lane. It must check experiment-local permanent memory before any broad web search, only search for novelty-qualified directions, always record targeted candidate refinement rounds for retained ideas, and write synthesis-judgment-ready approval state into the handoff artifacts instead of prompting for direct approval here.

## When to Use

- The experiment is already confirmed.
- Stable `results_interpretation.json` already exists.
- Matched reference report paths have already been selected by the parent workflow.
- The run needs beyond-handout discussion ideas before `course-lab-discussion-synthesis`.
- The workflow needs reusable snippets and handoff artifacts for synthesis judgment, not final harmonized discussion prose.

Do not use this skill to discover reference reports, run modeling jobs, mutate `main.tex`, ask for a direct approval prompt on discussion ideas, or write the final harmonized discussion section.

Do not treat these as discussion ideas here:

- routine uncertainty analysis
- routine theory comparison
- routine experiment-vs-reference comparison
- ordinary anomaly explanation prose
- ordinary completeness or missing-result bookkeeping

## Output Contract

- Use local `/root/.codex/skills/course-lab-discussion-ideas/scripts/build_discussion_ideas.py` as the main entrypoint.
- Keep runtime dependencies local to `/root/.codex/skills/course-lab-discussion-ideas/`.
- Treat `results_interpretation.json` as required.
- Treat parent-passed reference report paths as required.
- Read experiment-local permanent memory before deciding whether broad search is allowed.
- Only retain beyond-handout, non-routine novelty directions that imply extra analysis or evidence generation.
- Search obeys the same rule: do not browse routine comparison, routine uncertainty, ordinary anomaly prose, or normal report obligations.
- Skip broad first-pass browsing when permanent memory already exists for the experiment.
- Always run targeted refinement for retained novelty candidates and allow one or two targeted rounds.
- A successful run may keep zero discussion ideas if no non-routine direction is justified by the evidence.
- Write per-idea approval state such as `pending_synthesis_judgment` into `discussion_synthesis_input.tmp.*` so `course-lab-discussion-synthesis` can judge what to keep.
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
- This skill requires reference report inputs from the parent workflow.
- This skill updates permanent memory only through local tools in this folder.
- This skill only captures beyond-handout, non-routine discussion ideas.
- This skill does not mutate the report.
- This skill does not write final harmonized discussion prose.
- This skill does not stop for a direct approval prompt; it writes judgment-ready approval state for synthesis instead.
- This skill may emit reusable snippets, but those snippets are not the final discussion section.

## Common Mistakes

- Treating reference reports as optional.
- Treating routine comparison or routine uncertainty as discussion ideas.
- Searching first and filtering later instead of novelty-gating the search itself.
- Re-running broad browsing even when permanent memory already exists.
- Skipping targeted refinement for retained candidates.
- Asking for direct approval on ideas instead of writing synthesis-judgment-ready approval state into the handoff.
- Turning idea artifacts into synthesis-owned final prose.
- Reaching back into sibling skill folders instead of using the local copied scripts.
