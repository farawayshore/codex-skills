# Run Plan Rules

Use these local rules when turning normalized handout artifacts into a run-plan contract.

## Core Rules

- Keep the package planning-only.
- Route only what the handout actually supports.
- Prefer deterministic extraction over creative summary.
- Keep unresolved gaps visible instead of inventing missing detail.
- Use local tools in this folder only.

## Leaf-Skill Buckets

- `course-lab-body-scaffold`
  Use for procedure steps, process structure, and scaffold-driving section cues.
- `course-lab-experiment-principle`
  Use for introduction, background, principle, and theory-facing section cues.
- `course-lab-data-transfer`
  Use for tables, measurements, records, and data-transcription cues.
- `course-lab-data-processing`
  Use for processing or derived-quantity cues when the handout clearly points to them.
- `course-lab-plotting`
  Use for plots, graphs, chart comparisons, and curve-focused cues.
- `course-lab-results-interpretation`
  Use for analysis, comparison, explanation, and discrepancy-focused cues.
- `course-lab-discussion-ideas`
  Use for thinking questions, discussion prompts, and open reasoning prompts.
- `course-lab-discussion-synthesis`
  Keep empty unless the handout already contains clearly discussion-synthesis-ready prompts.
- `course-lab-final-staging`
  Use only for later report-assembly-facing deliverable cues that clearly belong downstream, including appendix or code-hook cues when the handout explicitly expects modeling or simulation comparison in the final report.
- `course-lab-figure-evidence`
  Use for figures, photos, image captions, and evidence-placement-facing cues.

## Cue Priorities

- Headings and subheadings are stronger than body text.
- List items are stronger than long paragraph summaries for routing concrete required work.
- Tables and images should stay visible as table/image evidence, not flattened into generic prose.
- A single cue may appear in more than one bucket when it genuinely serves multiple later skills.

## Unresolved-Gap Rules

- If a cue includes signals such as `missing`, `TBD`, `unclear`, `to be confirmed`, or `specify which`, keep it in bucket-level `unresolved_gaps`.
- Also copy unresolved cues into `global_unresolved_gaps`.
- Do not replace an unresolved cue with a guessed deliverable or guessed interpretation.

## Do Not Invent

- Do not invent procedure steps that are not in the handout.
- Do not invent missing table contents.
- Do not invent figure captions beyond what the handout or normalized artifact provides.
- Do not write final report wording here.
- Do not treat weak keyword matches as proof of a requirement when the handout stays ambiguous.
