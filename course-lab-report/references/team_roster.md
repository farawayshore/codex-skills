# Team Overlay Roster

This roster applies only when a caller intentionally runs a coordinated full-report team on top of the installed standalone course-lab skills. The overlay is optional: standalone leaf-tool usage remains first-class, and no role label, native agent file, or leader/controller state becomes mandatory unless `course-lab-report` is coordinating a full report.

## Leader / Controller

Use a lightweight leader/controller lane for orchestration only.

- Owns: stage routing, controller-state updates, reroute tickets, proposal confirmation, and final stop/go decisions.
- Does not own: normal report prose, numerical computation, or direct QC scoring.
- Full-report-only state: `AI_works/results/<experiment-safe-name>/course_lab_report_state.json`.

## Specialist Roles

| Role | Primary standalone tools / references | Main outputs | Must not own |
|---|---|---|---|
| Preparer | `course-lab-discovery`, `course-lab-handout-normalization`, `course-lab-workspace-template`, `course-lab-metadata-frontmatter`, `course-lab-run-plan`, `course-lab-body-scaffold`, `course-lab-data-transfer` | selected source bundle, persistent decoded handout artifacts, canonical workspace, run-plan artifacts, scaffold, validated transfer artifacts | late-stage prose, interpretation, final QC |
| Data Analyst | `course-lab-data-processing`, `course-lab-uncertainty-analysis`, `course-lab-plotting`, `course-lab-results-interpretation`, `course-lab-symbolic-expressing`, optional `physics-lab-mathematica-modeling` | processed evidence, uncertainty outputs, plots/models, interpretation artifacts, proposal candidates | final report prose, silent scope expansion |
| Writer | `course-lab-experiment-principle`, `course-lab-final-staging`, `course-lab-figure-evidence` | theory/principle sections, late-stage draft, figure/signatory insertions | unsupported numerical claims, QC scoring |
| Discussioner | `course-lab-discussion-ideas`, `course-lab-discussion-synthesis` | discussion ideas, synthesis snippets, evidence-tagged discussion handoffs | direct final TeX mutation |
| Examiner | `course-lab-finalize-qc`, `references/examiner_rubric.md` | scorecards, evidence-backed review notes, owner-tagged reroute tickets | direct report repair |
| Senior | `references/senior_advice_contract.md`, approved senior/reference artifacts | ranked refinement suggestions with source labels and confidence | invented preferences, direct report replacement |

## Overlay Stage Order

1. Leader/controller initializes the full-report run and shared controller state.
2. Preparer completes discovery, persistent handout decode, workspace setup, run-plan setup, scaffold setup, and validated transfer readiness.
3. Writer performs the earlier `course-lab-experiment-principle` pass once handout normalization and scaffold gates are satisfied.
4. Data Analyst turns stable inputs into processed evidence, uncertainty outputs, plots, models, and interpretation artifacts.
5. Discussioner produces discussion ideas and `course-lab-discussion-synthesis` outputs once interpretation is stable.
6. Writer performs `course-lab-final-staging` and `course-lab-figure-evidence` only after the discussion artifacts needed by final staging exist.
7. Senior reviews the current late-stage draft plus evidence and returns advisory, source-labeled refinement suggestions.
8. Examiner performs the grading/QC pass and emits scores plus reroute tickets.
9. Leader/controller routes accepted tickets back to the owning role, preserves unresolved states, and reruns downstream checks.

This overlay stage order keeps Discussioner upstream of `course-lab-final-staging`, and Writer remains the only late-stage `.tex` mutator.

## Boundary Reminders

- Preparer cannot pass normalization without persistent decoded handout artifacts at `AI_works/resources/experiment_handout/Modern Physics Experiments/pdf_decoded/<experiment-name>/<experiment-name>.md` and `.json`.
- Data Analyst cannot silently promote `agent_proposed_key_results`; proposals pause for leader/user confirmation.
- Discussioner owns idea/synthesis artifacts, not final report authority.
- Writer is the only lane that should own late-stage `.tex` mutation after setup.
- Examiner is score/ticket-only.
- Senior advice remains anti-invention-safe and source-labeled (`senior-source`, `reference-report`, `generic`, or `style-only`).
- Thinking-question ownership remains a documented future gap until a dedicated artifact contract is added.
