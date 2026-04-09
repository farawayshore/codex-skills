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
- `course-lab-handout-normalization` must leave persistent decoded handout artifacts at `AI_works/resources/experiment_handout/Modern Physics Experiments/pdf_decoded/<experiment-name>/<experiment-name>.md` and `AI_works/resources/experiment_handout/Modern Physics Experiments/pdf_decoded/<experiment-name>/<experiment-name>.json`.
- The parent must not treat summary-only handout artifacts as proof that handout normalization completed.
- `handout_extract.md`, `notes/sections.md`, and `notes/sections.json` are useful downstream summaries, but they do not replace the persistent decoded handout artifacts above.
- If the persistent decoded handout artifacts are newer than the workspace section summaries, the parent must rerun handout normalization before downstream theory or scaffold stages, then rerun `course-lab-run-plan` before downstream theory or scaffold stages continue.
- `course-lab-experiment-principle` must emit `principle_ownership.json` before downstream stages may treat the theory-facing section ownership as settled.
- When handout-derived theory-image staging is available or attempted, `course-lab-experiment-principle` must emit `principle_figures.json` and `principle_figures.tex`.
- When theory-image staging is weak, absent, or ambiguous, `course-lab-experiment-principle` must emit `principle_unresolved.md`.
- `course-lab-workspace-template` and `course-lab-metadata-frontmatter` must establish the canonical workspace before later draft-mutating stages.
- `course-lab-data-transfer` must pause for user confirmation before `course-lab-data-processing` or `course-lab-uncertainty-analysis`.
- When discovery exposes companion scan sources such as data.pdf, record-book scans, or source images inside the selected data group, data transfer is incomplete until those sources are transferred or explicitly marked unresolved.
- `course-lab-data-processing` must stabilize processed artifacts before `course-lab-uncertainty-analysis`, `course-lab-plotting`, and `course-lab-results-interpretation`.
- `course-lab-results-interpretation` must stabilize interpretation artifacts before `course-lab-discussion-ideas`, `course-lab-discussion-synthesis`, and `course-lab-final-staging`.
- `course-lab-final-staging` must finish before `course-lab-figure-evidence` and `course-lab-finalize-qc`.
- `course-lab-final-staging` must emit `final_staging_summary.json`, `final_staging_summary.md`, `final_staging_unresolved.md`, and `appendix_code_manifest.json` before the parent may treat late-stage non-figure assembly as complete.
- `course-lab-figure-evidence` must emit `picture_evidence_plan.json` and `picture_evidence_plan.md` before the parent may hand the run to `course-lab-finalize-qc`.
- When signatory sources exist, `course-lab-figure-evidence` must also emit `signatory_pages_manifest.json` and `signatory_pages.tex`.
- When signatory sources do not exist, `course-lab-figure-evidence` must leave an explicit unresolved late-stage artifact instead of relying on manual appendix prose.

## Run-Plan-Centered Routing

After the early setup stages, run-plan artifacts become the main routing aid.

- `course-lab-run-plan` should emit the artifacts the parent uses to decide what happens next.
- optional leaves may be skipped only when the run plan makes that safe and explicit.
- The parent should keep unresolved handout gaps visible instead of silently assuming a later leaf is optional.
- If `course-lab-results-interpretation` emits `agent_proposed_key_results`, the parent should pause instead of silently broadening official scope.
- The parent should store proposal confirmation state per item, not as one batch flag.
- Valid proposal confirmation states are `pending_user`, `approved`, `rejected`, and `needs_revision`.
- Only approved proposals may update the official run-plan scope or confirmed-reference artifacts.
- `needs_revision` should reroute only to `course-lab-results-interpretation`; it should not promote plan scope.
- Approved reroutes may revisit `course-lab-data-processing`, modeling, plotting, and `course-lab-results-interpretation` when newly confirmed scope requires upstream recomputation.

## Stop Points

- Stop when discovery does not yield a confirmed experiment target.
- Stop when canonical workspace information is still ambiguous.
- Stop when required upstream artifacts are missing.
- Stop when persistent decoded handout artifacts are missing.
- The parent must stop instead of silently continuing when only `handout_extract.md`, `notes/sections.md`, `sections.json`, or other summary-only handout artifacts are present.
- Stop when a later stage depends on user confirmation that has not yet happened.
- Stop when proposal confirmation state is still `pending_user` for any item that would change comparison scope.
- Stop when `course-lab-experiment-principle` has not emitted `principle_ownership.json`.
- Stop when `principle_figures.json` or `principle_figures.tex` is expected but missing.
- Stop when theory-image staging is unresolved and `principle_unresolved.md` is missing.
- The parent must stop instead of claiming the theory stage is complete until the principle-stage artifact gate is satisfied.
- Stop when `final_staging_summary.json`, `appendix_code_manifest.json`, or `picture_evidence_plan.json` is missing at the point where the parent would otherwise claim report completion.
- Stop when signatory sources exist but `signatory_pages_manifest.json` or `signatory_pages.tex` is missing.
- The parent must not treat a manually compiled PDF as proof that the late stages ran; it must stop instead of claiming completion until the artifact gate is satisfied.

## Controller State Contract

The parent should keep one workspace-local controller-state artifact:

`AI_works/results/<experiment-safe-name>/course_lab_report_state.json`

The parent must not claim completion when `course_lab_report_state.json` is absent.

It should record:

- confirmed discovery selections
- canonical workspace and TeX target
- stage completion status with emitted artifact paths and stage artifact paths
- `skipped_optional_leaves`
- `agent_proposed_key_results` and each proposal confirmation state
- stable evidence-plan state
- late-stage ownership log
- last mutating leaf for each owned late-stage region or bucket
- rerun history and the reason for each reroute
- `reference_selection_status`, including the neutral `none_found` state

## Proposal Reroute Loop

When `agent_proposed_key_results` exist, the parent owns the pause / confirm / reroute loop.

1. Pause and surface each proposal with its current proposal confirmation state.
2. Wait for user confirmation and record `pending_user`, `approved`, `rejected`, or `needs_revision` item by item.
3. Reroute only approved proposals through `course-lab-run-plan`, required upstream recomputation leaves, and confirmed-reference promotion.
4. Keep rejected items and needs-revision items out of official scope promotion.
5. Repeat until no unresolved proposal confirmation state remains for scope-changing items.

## Conservative Error Handling

- preserve unresolved gaps instead of masking them.
- Multi-leaf late-stage failures should return to the parent for sequential repair planning.
- When delegation safety is unclear after a failure, prefer inline recovery.
- The parent must not bypass late-stage ownership by hand-writing a manual short draft or by replacing missing appendix staging with a prose-only appendix stub.
