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
- Track reroutes after QC instead of treating QC as the terminal step.
- Preserve a compact memory of leaf ownership instead of copying their manuals.
- Keep artifact handoffs explicit, including the `course-lab-data-processing -> course-lab-final-staging` calculation-details appendix manifest flow.
- Keep artifact handoffs explicit, including the `course-lab-final-staging -> course-lab-figure-evidence` comparison-case handoff needed for same-case experiment-versus-simulation figure placement.

## References

- `references/orchestration_rules.md`
- `references/delegation_policy.md`
- `references/recovery_matrix.md`
- `references/leaf_responsibility_matrix.md`
