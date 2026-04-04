# Run Contract

The primary interface is one batch-oriented `run_config.json`.

Required blocks:

- `run_id`
- `experiment`
- `engine_policy`
- `inputs`
- `workflow`
- `outputs`
- `artifacts_requested`

Optional blocks:

- `discovery`
- `handout_cases`
- `batch_policy`
- `retry_policy`
- `sanity_checks`
- `handout_expectations`

Batch defaults:

- `discovery.enabled` defaults to `false`
- `batch_policy.strict_required_cases` defaults to `true`
- `batch_policy.include_picture_result_cases` defaults to `true`
- `batch_policy.include_handout_only_cases` defaults to `true`
- `retry_policy.mathematica_attempts` defaults to `3`
- `retry_policy.python_attempts` defaults to `3`

Batch expansion rules:

- When discovery is enabled, the skill parses the matching picture-result folder and discovers required cases from experiment-specific filenames such as LX2 `f=...kHz,m=...,n=...`.
- The required batch is the union of discovered picture-result cases plus any extra `handout_cases`.
- Cases are deduplicated by physical identity rather than filename alone.

Acceptance rules:

- Mathematica is the preferred engine.
- Python fallback is allowed only after Mathematica retries are exhausted and `engine_policy.allow_python_fallback` is `true`.
- Explicit `handout_expectations` override nothing; they are additional gates that must pass.
- When no explicit expectations exist, the skill applies default physics-informed sanity checks such as geometry bounds, monotonic radii, mode-topology consistency, positive derived values, and optional cross-case consistency.
