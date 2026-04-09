# Recovery Matrix

## Purpose

This matrix turns final QC into a routing checkpoint instead of a terminal step.

## Compile Or Structure Failures

- Read the controller-state ownership log.
- Route first to the recorded last mutating owner of the affected region.
- Common owners are `course-lab-final-staging` and `course-lab-figure-evidence`.
- If provenance is ambiguous, route to the earliest upstream leaf that can safely re-own the broken region.
- Always record that fallback in the controller state.

## Missing Coverage Or Required Section Failures

- Route procedure coverage, placeholder gaps, or scaffold mismatch to `course-lab-body-scaffold`.
- Revisit `course-lab-run-plan` if the missing section suggests a planning omission.
- Route missing persistent decoded handout artifacts back to `course-lab-handout-normalization`.
- Treat `handout_extract.md`, `notes/sections.md`, `notes/sections.json`, or other summary-only handout artifacts as insufficient when the persistent decode proof is missing.
- If the persistent decoded handout artifacts are newer than the workspace section summaries, rerun handout normalization before downstream theory or scaffold stages, then rerun `course-lab-run-plan` before downstream theory or scaffold stages resume.
- Route missing theory-stage artifact proof such as `principle_ownership.json`, `principle_figures.json`, `principle_figures.tex`, or `principle_unresolved.md` back to `course-lab-experiment-principle`.
- Route missing late-stage artifact proof such as `final_staging_summary.json`, `appendix_code_manifest.json`, `picture_evidence_plan.json`, `signatory_pages_manifest.json`, or `signatory_pages.tex` back to the responsible late-stage leaf instead of accepting a manual shortcut.
- route source-coverage gaps back to `course-lab-data-transfer` when companion scan sources such as data.pdf, record-book scans, or source images were discovered but not transferred or explicitly marked unresolved.

## Reference-Procedure Comparison Failures

- Treat the discovery-driven reference-procedure comparison as a routing checkpoint, not as a terminal verdict.
- Route malformed same-experiment reference selection or missing `selected_reference_reports` contract fields back to `course-lab-discovery`.
- Route selected same-experiment references that still lack decoded Markdown back to `course-lab-handout-normalization`.
- Treat `reference_selection_status: none_found` as a neutral disabled lane; record the skip in controller state instead of inventing a reroute.
- Route missing reference-procedure heading lanes to `course-lab-body-scaffold`.
- Route thin staged lane content to `course-lab-final-staging`.
- Route weak theory/comparison/evidence support inside an existing lane to `course-lab-results-interpretation`.
- Keep `declared-unresolved` items visible and require their warnings to survive reruns.
- Treat unmarked `data-lack` items as a failing reroute state until the owning leaf converts them into an explicit visible `TBD` or `\NeedsInput{...}` lane.
- After any of these reroutes, rerun downstream late-stage leaves and then rerun `course-lab-finalize-qc`.

## Content Or Support Failures

Use this precedence order:

1. `course-lab-results-interpretation`
2. `course-lab-discussion-ideas`
3. `course-lab-discussion-synthesis`
4. `course-lab-final-staging`

- `course-lab-results-interpretation` owns weak or contradictory evidence support.
- `course-lab-discussion-ideas` owns missing discussion directions or weak candidate breadth.
- `course-lab-discussion-synthesis` owns harmonization and confidence-calibration problems.
- `course-lab-final-staging` owns staged prose that is too thin, too compressed, or missing mathematical procedures.

## Data And Uncertainty Failures

- Route data or table inconsistency to `course-lab-data-processing`.
- Route weak uncertainty support to `course-lab-uncertainty-analysis`.

## Plotting Failures

- Route missing or weak plot support to `course-lab-plotting`.

## Oversized PDF

- Hand off image-size repair to `compress-png`.
- Rerun final QC after image-size remediation.

## Page-Count Shortfall

- Treat page-count shortfall as a reroute signal.
- Route back to `course-lab-final-staging`.
- Ask for richer staging with more detail, fuller mathematical procedures, stronger case-by-case coverage, and fuller processing narration where the artifacts support it.
- After restaging, rerun downstream late-stage reruns such as `course-lab-figure-evidence` when anchors changed, then rerun `course-lab-finalize-qc`.

## Conservative Error Handling

- unresolved gaps stay visible
- multi-leaf late-stage failures return to the parent for sequential repair planning
- when recovery safety is unclear, prefer inline repair
- manual short-draft fallbacks and prose-only appendix stubs are not acceptable recovery paths for missing late-stage artifacts
