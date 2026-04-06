# Delegation Policy

## Purpose

The parent should remain compact and route to sibling skills instead of copying sibling runtime procedures.

## Default Rule

If a leaf has bounded scope and deterministic behavior once inputs are stable, the parent may use a small worker.

## Prefer Small Worker

- `course-lab-handout-normalization`
- `course-lab-workspace-template`
- `course-lab-body-scaffold`
- `course-lab-data-transfer`

## Prefer Inline / Main Agent

- `course-lab-discovery`
- `course-lab-metadata-frontmatter`
- `course-lab-run-plan`
- `course-lab-experiment-principle`
- `course-lab-data-processing`
- `course-lab-uncertainty-analysis`
- `course-lab-plotting`
- `course-lab-results-interpretation`
- `course-lab-finalize-qc`

## Explicit Stay-Local

- `course-lab-discussion-ideas`
- `course-lab-discussion-synthesis`
- `course-lab-final-staging`

## Conditional Stronger Worker

- `course-lab-figure-evidence` may use a stronger worker only when a stable evidence-plan artifact or equivalent placement-ready grouping manifest already exists and the group-to-target mapping is explicit.

## Parent-Only Decisions

- Interpret QC outcomes.
- Decide reroutes and rerun chains.
- Prefer inline recovery when delegation safety becomes uncertain after a failure.
