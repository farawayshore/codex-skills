# Course Lab Results Interpretation Baseline Failures

Date: `2026-04-04`

## RED Baseline

Before this refinement is implemented, the current skill still fails in these concrete ways:

1. The current interpretation script can run without a normalized handout even though interpretation should be handout-first.
2. The current interpretation flow treats processed-data JSON as the only required scientific input and does not fail when the handout is missing.
3. The current implementation treats simulation or modeling outputs only as inventory source hints, not as explicit comparison targets.
4. There is no `comparison_records` output structure that clearly distinguishes handout-vs-data, simulation-vs-data, and theory-vs-data lanes.
5. The current script does not fail visibly when handout Markdown exists but is malformed; it has no handout parser at all.
6. The current docs do not yet teach agents to read the normalized handout first or to compare data, simulation, and theory explicitly when the experiment requires those comparisons.

## Expected GREEN Direction

The refined package should provide:

- handout-required, handout-first interpretation
- Markdown-first handout resolution with JSON fallback only when Markdown is absent
- explicit comparison lanes recorded in `comparison_records`
- honest partial-output behavior when theory or simulation lanes are missing
- artifact-only outputs for JSON, Markdown, and unresolved gaps
- visible completeness checks before discussion generation or final staging
