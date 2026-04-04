# Controller Checkpoints

Use this guide to manage wave preparation, merge checkpoints, and cleanup.

## Pre-Wave Checklist

Before dispatching a wave, confirm:

- sequential prerequisites are complete;
- `parallel-run/` has been refreshed for the current run;
- owned regions exist in the draft;
- ownership metadata is present near each region;
- each worker has an assignment file;
- allowed files and blocked files are explicit;
- the wave can be reconciled without shared ownership.

## Merge Checklist

At each checkpoint, review:

- which regions were edited;
- whether any worker crossed region boundaries;
- whether each owned `group_id` or `candidate_id` was covered;
- whether any worker returned an escalation instead of forcing a cross-region edit;
- whether a boundary collision requires sequential fallback.

Record the outcome in `parallel_merge_notes.md`.

## Post-Wave Verification Checklist

After each wave, verify:

- the merged draft still has sound structure;
- figure placement stays near the owned analysis block;
- `Further Discussion` claims remain candidate-backed;
- low-confidence material is not overstated;
- unresolved conflicts remain visible;
- the next wave still has clean ownership.

## Cleanup And Refresh Rule

At the start of each new report run, refresh or clear `AI_works/results/<experiment-safe-name>/parallel-run/` before writing new assignments. Do not reuse stale worker instructions, merge notes, or wave plans from a previous experiment.

## Downgrade-To-Sequential Rules

Stop parallel execution for the affected slice when:

- ownership is ambiguous;
- a fix crosses several regions;
- a worker needs preamble or global-structure edits;
- the subsection boundary is too weak for safe isolation.

When that happens, keep the remaining clean slices parallel if possible and finish the ambiguous slice sequentially.
