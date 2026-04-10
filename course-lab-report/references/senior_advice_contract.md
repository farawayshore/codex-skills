# Senior Advice Contract

Use this contract when a caller wants senior-style report refinement advice. It is a reference for advice generation, not a native agent definition.

## Accepted Inputs

- User-provided senior notes or preferences.
- Selected same-experiment reference reports and decoded reference artifacts.
- Approved senior-profile snippets provided by the user.
- Current report draft plus relevant data, interpretation, discussion, and QC artifacts.

## Anti-Invention Rules

- Do not invent real senior preferences, grading habits, or lab-specific folklore without an approved source artifact.
- If no senior-source artifact exists, label advice as `generic` and lower confidence.
- Separate source-backed advice from style-only advice.
- Map each suggestion to the relevant standalone tool, such as `course-lab-final-staging`, `course-lab-discussion-synthesis`, `course-lab-figure-evidence`, or `course-lab-finalize-qc`.

## Output Contract

Return ranked suggestions with source label (`senior-source`, `reference-report`, `generic`, or `style-only`), confidence, rationale, owning standalone tool, and whether the suggestion requires upstream data/interpretation support before writing.
