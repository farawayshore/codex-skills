# Course Lab Standalone Tool Catalog

This catalog maps the installed course-lab skills as independently usable tools. It is for documentation organization only; standalone tool use must not require a role, team, native agent file, or `course-lab-report` controller state.

If a caller wants a coordinated full-report team, the optional overlay in `team_roster.md` and `team_handoff_contract.md` gives the role labels below a concrete home. In standalone mode they remain advisory metadata only, not prerequisites.

| Skill | Tool category | Optional role metadata | Minimum standalone input |
|---|---|---|---|
| `course-lab-discovery` | Source discovery tool | `preparer` | Course/experiment query and search roots. |
| `course-lab-handout-normalization` | Handout decode/section extraction tool | `preparer` | Selected handout/reference PDF or decoded source path. |
| `course-lab-workspace-template` | Workspace/template setup tool | `preparer` | Experiment name, template choice, output workspace target. |
| `course-lab-metadata-frontmatter` | Metadata/frontmatter tool | `preparer` | Canonical TeX file plus metadata values/profile. |
| `course-lab-run-plan` | Run-plan generator tool | `preparer` | Normalized handout artifacts and workspace target. |
| `course-lab-body-scaffold` | Body scaffold/procedure coverage tool | `preparer` | Normalized sections plus canonical TeX target. |
| `course-lab-data-transfer` | Raw data transcription tool | `preparer` | Raw data source paths and output destination. |
| `course-lab-data-processing` | Data calculation tool | `data-analyst` | Validated transferred data plus handout requirements. |
| `course-lab-uncertainty-analysis` | Uncertainty propagation tool | `data-analyst` | Processed/direct data plus uncertainty rules. |
| `course-lab-plotting` | Plot asset generation tool | `data-analyst` | Numeric artifact or plot job specification. |
| `course-lab-results-interpretation` | Evidence interpretation tool | `data-analyst` | Processed artifacts and handout/reference support. |
| `course-lab-symbolic-expressing` | TeX math explanation helper | `data-analyst` | Explicit result key and calculation artifacts. |
| `course-lab-experiment-principle` | Theory/principle writing tool | `writer` | Normalized handout plus canonical TeX/scaffold target. |
| `course-lab-final-staging` | Late non-figure report assembly tool | `writer` | Canonical report workspace plus stable upstream artifacts. |
| `course-lab-figure-evidence` | Figure/signatory evidence placement tool | `writer` | Staged draft plus evidence grouping/asset paths. |
| `course-lab-discussion-ideas` | Discussion idea generation tool | `discussioner` | Interpretation artifacts plus optional reference reports. |
| `course-lab-discussion-synthesis` | Discussion synthesis tool | `discussioner` | Approved discussion ideas and interpretation support. |
| `course-lab-finalize-qc` | Final compile/QC/examiner tool | `examiner` | Figure-complete draft or canonical `main.tex`. |

## Standalone Rule

Each leaf tool's `SKILL.md` is the authority for standalone inputs, outputs, validation, and failure handling. `course-lab-report` may sequence these tools for a complete report, but it is not required for independent use.
