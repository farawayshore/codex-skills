# Team Handoff Contract

This contract applies only to the optional team overlay described in `team_roster.md`. It must not change standalone tool truth: leaf `SKILL.md` contracts still own standalone inputs, outputs, validation, and failure signals.

## Leader / Controller Scope

The leader/controller is orchestration-only.

- Owns: ticket normalization, controller-state updates, proposal confirmation, reroute sequencing, and final stop/go decisions.
- Does not own: prose writing, numerical computation, or direct QC scoring.
- Must preserve leaf-skill truth even when a team overlay is active.

## Artifact Producers

| Role | Emits | Downstream handoff |
|---|---|---|
| Preparer | selected source bundle, persistent decoded handout artifacts, canonical workspace, run-plan artifacts, scaffold, validated transfer artifacts | hands stable setup artifacts to Writer and Data Analyst |
| Writer | `principle_ownership.json`, related principle artifacts, late-stage draft outputs, figure/signatory placement outputs | hands a draft-ready report to Senior and Examiner |
| Data Analyst | processed artifacts, uncertainty outputs, plots/models, interpretation outputs, `agent_proposed_key_results` when needed | hands stable evidence to Discussioner and Writer |
| Discussioner | discussion-idea artifacts and discussion-synthesis artifacts | hands discussion inputs to Writer before `course-lab-final-staging` |
| Senior | ranked advice with `senior-source`, `reference-report`, `generic`, or `style-only` labels | hands advisory suggestions to the leader/controller for optional ticket conversion |
| Examiner | score/rubric summary, evidence-backed issue list, owner-tagged reroute tickets, downstream rerun requirements | hands fix tickets to the leader/controller |

## Ticket Openers

- Any owned leaf may emit its precise reroute or malformed-artifact signal.
- Examiner may open score/reroute tickets after `course-lab-finalize-qc`.
- Leader/controller may normalize those signals into explicit reroute tickets and assign them to the owning role.
- Senior does not open direct reroute tickets; Senior suggestions stay advisory until the leader/controller accepts them and converts them into an owner-specific ticket.

## Role Routing Map

Use `owning_skill` as the source of truth, then map to `owning_role` for the overlay:

| owning_skill | owning_role |
|---|---|
| `course-lab-discovery`, `course-lab-handout-normalization`, `course-lab-workspace-template`, `course-lab-metadata-frontmatter`, `course-lab-run-plan`, `course-lab-body-scaffold`, `course-lab-data-transfer` | `preparer` |
| `course-lab-data-processing`, `course-lab-uncertainty-analysis`, `course-lab-plotting`, `course-lab-results-interpretation`, `course-lab-symbolic-expressing`, optional `physics-lab-mathematica-modeling` | `data-analyst` |
| `course-lab-experiment-principle`, `course-lab-final-staging`, `course-lab-figure-evidence` | `writer` |
| `course-lab-discussion-ideas`, `course-lab-discussion-synthesis` | `discussioner` |
| `course-lab-finalize-qc` | `examiner` |

Suggested ticket shape:

```json
{
  "ticket_id": "qc-001",
  "owning_skill": "course-lab-final-staging",
  "owning_role": "writer",
  "severity": "major",
  "evidence": "finalize_qc found missing appendix_code_manifest.json",
  "downstream_reruns": ["course-lab-figure-evidence", "course-lab-finalize-qc"]
}
```

## Proposal Confirmation

- `agent_proposed_key_results` remain pending until leader/user confirmation.
- Valid confirmation states remain `pending_user`, `approved`, `rejected`, and `needs_revision`.
- Data Analyst may propose scope-changing results, but Data Analyst cannot silently promote them.
- Only the leader/controller may move approved proposals back through rerun planning and downstream recomputation.

## Overlay Guardrails

- Preparer cannot pass setup readiness without persistent decoded handout artifacts and validated transfer outputs.
- Discussioner stays upstream of `course-lab-final-staging` and must not mutate final TeX.
- Writer is the only late-stage `.tex` mutator.
- Examiner emits scores and tickets, not direct edits.
- Senior advice remains advisory, anti-invention-safe, and source-labeled.
- `reference_selection_status: none_found` still maps to `skipped_optional_leaves`.
- When signatory sources exist, the Writer-owned `course-lab-figure-evidence` lane must still emit `signatory_pages_manifest.json` and `signatory_pages.tex`.
- Thinking-question ownership remains future work until an explicit artifact contract lands.
