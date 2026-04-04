# Parallel Workflow

Use this guide when the report run reaches the mid-run analysis phase and the inputs are stable enough for coordinated parallel drafting.

## Sequential Prerequisites

Stay sequential until all of the following are true:

- the experiment is confirmed;
- the canonical TeX file is known;
- transferred data is user-validated;
- picture-result staging is complete; and
- `picture_evidence_plan.json` exists.

If any of these are still unstable, do not enter parallel mode.

## Coordination Directory

Use `AI_works/results/<experiment-safe-name>/parallel-run/` as the run-local coordination directory.

Refresh or clear that directory at the start of each new run so stale assignments, merge notes, and wave summaries do not carry forward.

## Barrier Model

Parallel work happens in waves.

For each wave:

1. Prepare the whole wave first.
2. Write `parallel_wave_plan.md`.
3. Write one assignment file per worker under `parallel_assignments/`.
4. Dispatch the whole wave together.
5. Reconcile only at the checkpoint.

Do not use this pattern for independent work:

1. spawn worker A
2. wait
3. spawn worker B
4. wait
5. spawn worker C

## Wave Sequence

### Wave A: Results Subsection Drafting

Use Wave A for subsection-local results drafting driven by evidence ownership.

Group by:

- `target_subsection`, or
- another evidence-family boundary that maps cleanly to the current report structure.

Worker-count rule of thumb:

- use `2` workers when the evidence plan yields only a couple of substantial subsection clusters;
- use `3` workers when there are at least three clearly isolated subsection clusters with non-overlapping ownership;
- use a smaller wave only when there is no second cleanly isolated subsection cluster.

### Checkpoint A

At the checkpoint, verify:

- each worker stayed inside owned regions;
- each owned `group_id` has nearby `% evidence:<group_id>` coverage;
- figure blocks stay in the same subsection as their analysis; and
- region boundaries remain intact.

### Wave B: Further Discussion And Synthesis

Use Wave B after subsection-local evidence regions stabilize.

Typical Wave B workers:

- anomaly-backed discussion;
- material-specific interpretation;
- comparison-to-common-outcomes when needed.

Wave B claims must stay grounded in `discussion_candidates.json`.

### Checkpoint B

At the checkpoint, verify:

- every `Further Discussion` claim maps back to candidate-backed evidence;
- wording strength matches candidate confidence; and
- unresolved conflicts remain visible.

### Wave C: QC And Local Repair

Use Wave C for targeted checks and localized fixes before the ordinary compile/QC loop.

Typical Wave C workers:

- evidence-placement checker;
- reasoning-strength and placeholder-hygiene checker;
- localized repair worker when the fix stays inside clear ownership boundaries.

## When Not To Parallelize

Do not parallelize when:

- the subsection boundary is unclear;
- two workers would need the same region;
- a worker would need preamble or global-structure edits;
- evidence ownership is ambiguous; or
- the run is small enough that a second cleanly isolated slice does not exist.

In those cases, keep the affected work sequential.

## Escalation Rules

Workers must escalate to the controller instead of improvising when they discover:

- preamble edits;
- section reordering;
- cross-region edits;
- ownership collisions; or
- evidence that no longer fits the current wave assignment.

