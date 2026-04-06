# Orchestration Rules

## Purpose

This document defines the parent orchestrator's stage order, artifact gates, stop points, run-plan-centered routing, and controller-state contract.

Keep it focused on routing and prerequisites rather than leaf internals.

## Required Stage Order

1. `course-lab-discovery`
2. `course-lab-handout-normalization`
3. `course-lab-workspace-template`
4. `course-lab-metadata-frontmatter`
5. `course-lab-run-plan`
6. `course-lab-body-scaffold`
7. `course-lab-experiment-principle`
8. `course-lab-data-transfer`
9. `course-lab-data-processing`
10. `course-lab-uncertainty-analysis` when needed
11. `course-lab-plotting` when needed
12. `course-lab-results-interpretation`
13. `course-lab-discussion-ideas`
14. `course-lab-discussion-synthesis`
15. `course-lab-final-staging`
16. `course-lab-figure-evidence`
17. `course-lab-finalize-qc`

## Artifact Gates

- `course-lab-discovery` must surface a confirmed experiment target plus selected or user-confirmed handout, reference-report, template, and result-folder state before normalization or workspace setup can proceed.
- `course-lab-handout-normalization` must complete before `course-lab-run-plan`, `course-lab-body-scaffold`, and `course-lab-experiment-principle`.
- `course-lab-workspace-template` and `course-lab-metadata-frontmatter` must establish the canonical workspace before later draft-mutating stages.
- `course-lab-data-transfer` must pause for user confirmation before `course-lab-data-processing` or `course-lab-uncertainty-analysis`.
- `course-lab-data-processing` must stabilize processed artifacts before `course-lab-uncertainty-analysis`, `course-lab-plotting`, and `course-lab-results-interpretation`.
- `course-lab-results-interpretation` must stabilize interpretation artifacts before `course-lab-discussion-ideas`, `course-lab-discussion-synthesis`, and `course-lab-final-staging`.
- `course-lab-final-staging` must finish before `course-lab-figure-evidence` and `course-lab-finalize-qc`.

## Run-Plan-Centered Routing

After the early setup stages, run-plan artifacts become the main routing aid.

- `course-lab-run-plan` should emit the artifacts the parent uses to decide what happens next.
- optional leaves may be skipped only when the run plan makes that safe and explicit.
- The parent should keep unresolved handout gaps visible instead of silently assuming a later leaf is optional.

## Stop Points

- Stop when discovery does not yield a confirmed experiment target.
- Stop when canonical workspace information is still ambiguous.
- Stop when required upstream artifacts are missing.
- Stop when a later stage depends on user confirmation that has not yet happened.

## Controller State Contract

The parent should keep one workspace-local controller-state artifact:

`AI_works/results/<experiment-safe-name>/course_lab_report_state.json`

It should record:

- confirmed discovery selections
- canonical workspace and TeX target
- stage completion status with emitted artifact paths
- stable evidence-plan state
- late-stage ownership log
- last mutating leaf for each owned late-stage region or bucket
- rerun history and the reason for each reroute

## Conservative Error Handling

- preserve unresolved gaps instead of masking them.
- Multi-leaf late-stage failures should return to the parent for sequential repair planning.
- When delegation safety is unclear after a failure, prefer inline recovery.
