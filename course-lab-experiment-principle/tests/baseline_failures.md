# Course Lab Experiment Principle Baseline Failures

Date: `2026-04-04`

## RED Baseline

Before the combined-report follow-up is implemented, the current package still fails in four concrete ways:

1. The writer only understands top-level `Introduction`, `Background`, and `Experiment Principle` sections, so it cannot target one parent report part like `LX1: One-Dimensional Standing Waves` without risking cross-part mutation.
2. The writer reads normalized sections from JSON only. It does not prefer normalized Markdown first, and it cannot fall back to JSON only when Markdown is absent.
3. If normalized Markdown exists but is malformed or lacks the needed `Normalized key` metadata, the current writer has no contract for surfacing that problem instead of silently choosing some other source.
4. The figure-staging tool hard-codes LaTeX include paths as `principle-images/<filename>`, so it cannot represent part-specific figure paths like `principle-images/lx1/<filename>` for combined reports.

## Expected GREEN Direction

The new package should provide:

- a standalone local skill folder with copied runtime tools
- direct writing into introduction, nearby background, and experiment-principle sections
- local staging and insertion of matching handout-derived theory images
- visible unresolved-state handling instead of silent guessing
- part-scoped combined-report writing that updates only the targeted report part
- Markdown-first normalized-input resolution with JSON fallback only when Markdown is missing
- part-aware figure paths that preserve directories such as `principle-images/lx1/`
