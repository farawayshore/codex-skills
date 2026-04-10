# Full Workflow Routing

Use this reference only when `course-lab-report` coordinates a complete report run. Standalone leaf-tool calls should follow the leaf tool's own `## Standalone Tool Contract` instead.

## Full-Report State Boundary

- `AI_works/results/<experiment-safe-name>/course_lab_report_state.json` is required only when the optional full-workflow catalog/router is claiming full report completion.
- Controller-state requirements apply only to full-report orchestration; they do not make `course-lab-report` mandatory for standalone leaf tools.
- The full workflow must preserve stage artifact paths, `skipped_optional_leaves`, proposal confirmation states, rerun history, last mutating leaf, and reference-selection status.

## Reroute Ticket Schema

```json
{
  "ticket_id": "qc-001",
  "owning_skill": "course-lab-final-staging",
  "severity": "major",
  "evidence": "finalize_qc found missing appendix_code_manifest.json",
  "required_artifact": "appendix_code_manifest.json",
  "downstream_reruns": ["course-lab-figure-evidence", "course-lab-finalize-qc"]
}
```

## Routing Principles

- Preserve the leaf tool's precise missing-input or malformed-artifact signal.
- Route source-coverage gaps to `course-lab-data-transfer`.
- Route persistent handout decode gaps to `course-lab-handout-normalization`.
- Route weak evidence support to `course-lab-results-interpretation` before discussion or staging repairs.
- Route missing late-stage proof to `course-lab-final-staging` or `course-lab-figure-evidence`, not to a manual prose shortcut.
- Rerun downstream late-stage and final QC tools after any upstream repair.
