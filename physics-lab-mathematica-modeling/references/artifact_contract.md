# Artifact Contract

Every batch run should emit:

- `run_config.snapshot.json`
- `batch_run_result.json`

Every required case should emit:

- `case_run_result.json`
- generated workflow source used for each attempt
- requested artifacts under the case directory

Typical per-case artifacts include:

- summary JSON
- summary text
- plots
- radial plots
- tables
- parameter snapshots

The skill is artifact-only and does not write report prose.

`batch_run_result.json` should record:

- strict batch success or failure
- required, passed, and failed case ids
- discovered-case and handout-only counts
- warnings
- per-case manifest paths

`case_run_result.json` should record:

- engine retry history
- handout expectation status
- sanity-check status
- failure reasons
- artifact paths
- source workflow paths
