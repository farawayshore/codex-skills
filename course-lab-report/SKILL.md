---
name: course-lab-report
description: Use when a course lab-report run needs a standalone parent orchestrator that routes installed leaf skills through explicit stage gates, delegation rules, and QC recovery without re-embedding sibling runtime logic.
---

# Course Lab Report

## Overview

Use this skill as the standalone parent orchestrator for the installed course-lab skill family.

This package is coordination-first. It should stay compact, route work to the installed leaf skills, and avoid re-embedding sibling runtime logic that already belongs in those leaf packages.

The older `/root/.codex/skills/modern-physics-latex-report-rennovated/` package remains legacy reference material. This new parent must not rely on that folder at runtime.

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

## Parent-Only Responsibilities

- Keep stage order and gate decisions visible.
- Decide whether a step should stay inline, use a smaller worker, or stay local.
- The parent must not treat summary-only handout artifacts as proof that handout normalization completed.
- Successful handout normalization must leave persistent decoded handout artifacts at `AI_works/resources/experiment_handout/Modern Physics Experiments/pdf_decoded/<experiment-name>/<experiment-name>.md` and `AI_works/resources/experiment_handout/Modern Physics Experiments/pdf_decoded/<experiment-name>/<experiment-name>.json`.
- The parent must not accept `handout_extract.md`, `notes/sections.md`, or `sections.json` by themselves as substitutes for those persistent decoded handout artifacts.
- Pause when `agent_proposed_key_results` exist and wait for item-level user confirmation instead of silently promoting new scientific scope.
- Track proposal confirmation state per proposed result (`pending_user`, `approved`, `rejected`, `needs_revision`) in the controller-state artifact.
- Reroute only approved proposals back through `course-lab-run-plan`, upstream recomputation leaves, and confirmed-reference reuse.
- Track reroutes after QC instead of treating QC as the terminal step.
- Preserve a compact memory of leaf ownership instead of copying their manuals.
- Keep artifact handoffs explicit, including the `course-lab-data-processing -> course-lab-final-staging` calculation-details appendix manifest flow.
- Keep artifact handoffs explicit, including the `course-lab-final-staging -> course-lab-figure-evidence` comparison-case handoff needed for same-case experiment-versus-simulation figure placement.
- The parent must not silently continue past `course-lab-experiment-principle` without explicit principle-stage artifact proof.
- The parent must not treat manually written theory prose as proof that principle-image staging ran.
- The parent must not hand-write a manual short draft once the run has progressed past setup and planning; late report mutation must remain owned by `course-lab-experiment-principle`, `course-lab-final-staging`, and `course-lab-figure-evidence`.
- The parent must not bypass `course-lab-final-staging` once late-stage report assembly is in scope.
- The parent must not replace missing appendix staging with a prose-only appendix stub.

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
- The parent must not treat `handout_extract.md`, `notes/sections.md`, `sections.json`, or other summary-only handout artifacts as proof that the decode stage completed.
- The parent must stop instead of silently continuing when persistent decoded handout artifacts are missing.

## References

- `references/orchestration_rules.md`
- `references/delegation_policy.md`
- `references/recovery_matrix.md`
- `references/leaf_responsibility_matrix.md`
