---
name: course-lab-report
description: Use when a course lab-report run needs a standalone parent orchestrator that routes installed leaf skills through explicit stage gates, delegation rules, and QC recovery without re-embedding sibling runtime logic.
---

# Course Lab Report

## Overview

Use this skill as the standalone parent orchestrator for the installed course-lab skill family.

This package is coordination-first. It should stay compact, route work to the installed leaf skills, and avoid re-embedding sibling runtime logic that already belongs in those leaf packages.

## When To Use

- A course lab-report run needs one parent controller rather than a monolithic executor.
- The workflow should move through explicit stage gates, stop points, delegation rules, and QC reroutes.
- Installed leaf skills should keep their own execution logic while this parent chooses what happens next.

## Default Stage Order

1. `course-lab-discovery`
2. `course-lab-handout-normalization`
3. `course-lab-workspace-template`
4. `course-lab-metadata-frontmatter`
5. `course-lab-run-plan`
6. `course-lab-body-scaffold`
7. `course-lab-experiment-principle`
8. `course-lab-data-transfer`
9. `course-lab-data-processing`
10. `course-lab-uncertainty-analysis`
11. `course-lab-plotting`
12. `course-lab-results-interpretation`
13. `course-lab-discussion-ideas`
14. `course-lab-discussion-synthesis`
15. `course-lab-final-staging`
16. `course-lab-figure-evidence`
17. `course-lab-finalize-qc`

## Optional Helper Leaves

- `course-lab-symbolic-expressing`: optional result-explanation helper that reads explicit handout, calculation-code, processed-result, result-key, and output paths, then returns a temp TeX path plus unresolved notes to the caller. It is not a required stage between `course-lab-data-processing` and `course-lab-final-staging`.

## Parent-Only Responsibilities

- Keep stage order and gate decisions visible.
- Decide whether a step should stay inline, use a smaller worker, or stay local.
- The parent must not treat summary-only handout artifacts as proof that handout normalization completed.
- Successful handout normalization must leave persistent decoded handout artifacts at `AI_works/resources/experiment_handout/Modern Physics Experiments/pdf_decoded/<experiment-name>/<experiment-name>.md` and `AI_works/resources/experiment_handout/Modern Physics Experiments/pdf_decoded/<experiment-name>/<experiment-name>.json`.
- The parent must not accept `handout_extract.md`, `notes/sections.md`, or `notes/sections.json` by themselves as substitutes for those persistent decoded handout artifacts.
- If the persistent decoded handout artifacts are newer than the workspace section summaries (`notes/sections.json` or `notes/sections.md`), the parent must rerun handout normalization before downstream theory or scaffold stages, then rerun `course-lab-run-plan` before `course-lab-body-scaffold` or `course-lab-experiment-principle`.
- The parent must keep `AI_works/results/<experiment-safe-name>/course_lab_report_state.json` and must not claim completion when that controller-state artifact is absent.
- The controller state must record stage artifact paths, `skipped_optional_leaves`, the last mutating leaf for each owned bucket, rerun history, and the current reference-selection contract state.
- When discovery exposes companion scan sources such as data.pdf, record-book scans, or source images inside the selected data group, data transfer is incomplete until those sources are transferred or explicitly marked unresolved.
- The parent must route source-coverage gaps back to `course-lab-data-transfer` instead of flattening the gap into generic discussion prose.
- Pause when `agent_proposed_key_results` exist and wait for item-level user confirmation instead of silently promoting new scientific scope.
- Track proposal confirmation state per proposed result (`pending_user`, `approved`, `rejected`, `needs_revision`) in the controller-state artifact.
- Reroute only approved proposals back through `course-lab-run-plan`, upstream recomputation leaves, and confirmed-reference reuse.
- Track reroutes after QC instead of treating QC as the terminal step.
- Preserve a compact memory of leaf ownership instead of copying their manuals.
- Keep artifact handoffs explicit, including the `course-lab-data-processing -> course-lab-final-staging` calculation-details appendix manifest flow.
- Keep artifact handoffs explicit for optional `course-lab-symbolic-expressing` calls: callers must pass source paths and consume the returned temp TeX path; the parent must not treat this helper as proof that final-staging ran.
- Keep artifact handoffs explicit, including the `course-lab-final-staging -> course-lab-figure-evidence` comparison-case handoff needed for same-case experiment-versus-simulation figure placement.
- Keep artifact handoffs explicit for the discovery-driven same-experiment reference comparison path: the parent must treat `selected_reference_reports` plus `reference_selection_status` as the only accepted finalize-QC reference-selection contract.
- Each `selected_reference_reports` entry must preserve `pdf_path`, `expected_decoded_markdown_path`, and `expected_decoded_json_path`; plain strings are malformed and must reroute to `course-lab-discovery`.
- `reference_selection_status: none_found` is a neutral state, not a hidden failure; when that state applies, optional discussion/reference leaves must be recorded in `skipped_optional_leaves` instead of being reported as broken.
- The parent must not silently continue past `course-lab-experiment-principle` without explicit principle-stage artifact proof.
- The parent must not treat manually written theory prose as proof that principle-image staging ran.
- The parent must not hand-write a manual short draft once the run has progressed past setup and planning; late report mutation must remain owned by `course-lab-experiment-principle`, `course-lab-final-staging`, and `course-lab-figure-evidence`.
- The parent must not bypass `course-lab-final-staging` once late-stage report assembly is in scope.
- The parent must not replace missing appendix staging with a prose-only appendix stub.
- The parent must route malformed same-experiment reference selection back to `course-lab-discovery` instead of letting final QC guess.
- The parent must route missing decoded Markdown for selected same-experiment references back to `course-lab-handout-normalization`.
- The parent must route weak interpretation-only reference-procedure gaps to `course-lab-results-interpretation` instead of flattening them into generic staging reruns.
- The parent must preserve declared-unresolved and data-lack states explicitly after reference-procedure comparison so the final handoff stays honest about remaining gaps.

## Theory-Stage Completion Gate

- The parent must require `course-lab-experiment-principle` to emit `principle_ownership.json` before the theory stage can be considered complete.
- When handout-derived theory images are available or image staging was attempted, the parent must require `principle_figures.json` and `principle_figures.tex`.
- When theory-image staging is weak, absent, or ambiguous, the parent must require `principle_unresolved.md` instead of silently treating the theory stage as complete.
- The parent must stop instead of claiming the theory stage is complete when the required principle-stage artifacts above are missing.

## Late-Stage Completion Gate

- The parent must not treat a manually compiled PDF as proof that the late report stages ran.
- The parent must require `course-lab-final-staging` to emit `final_staging_summary.json`, `final_staging_summary.md`, `final_staging_unresolved.md`, and `appendix_code_manifest.json` before it can hand late-stage ownership forward.
- The parent must require `course-lab-figure-evidence` to emit `picture_evidence_plan.json` and `picture_evidence_plan.md` before completion can be claimed.
- When signatory sources exist, the parent must require `signatory_pages_manifest.json` and `signatory_pages.tex` from `course-lab-figure-evidence`.
- When signatory sources do not exist, the parent must preserve that state as an explicit unresolved late-stage output instead of inserting a manual placeholder appendix.
- The parent must stop instead of claiming completion when the required late-stage artifacts above are missing.

## Handout-Normalization Completion Gate

- The parent must require persistent decoded handout artifacts at `AI_works/resources/experiment_handout/Modern Physics Experiments/pdf_decoded/<experiment-name>/<experiment-name>.md` and `AI_works/resources/experiment_handout/Modern Physics Experiments/pdf_decoded/<experiment-name>/<experiment-name>.json` when `course-lab-handout-normalization` succeeds.
- The parent must not treat `handout_extract.md`, `notes/sections.md`, `notes/sections.json`, or other summary-only handout artifacts as proof that the decode stage completed.
- The parent must stop instead of silently continuing when persistent decoded handout artifacts are missing.

## References

- `references/orchestration_rules.md`
- `references/delegation_policy.md`
- `references/recovery_matrix.md`
- `references/leaf_responsibility_matrix.md`
