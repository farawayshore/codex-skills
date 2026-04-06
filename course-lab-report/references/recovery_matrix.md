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
