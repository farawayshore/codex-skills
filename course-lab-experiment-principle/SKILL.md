---
name: course-lab-experiment-principle
description: Use when a course lab-report run already has normalized handout Markdown or JSON, a canonical report file, and a body scaffold, and now needs direct theory-facing writing for either a normal report or one targeted part of a combined report plus matching handout-derived theory images.
---

# Course Lab Experiment Principle

## Overview

Write the early theory-facing report sections directly into the canonical report without drifting into results, discussion, or late evidence placement.

This skill is standalone with copied local tools. It owns direct writing for `Introduction`, nearby `Background`, and `Experiment Principle`, plus insertion of matching handout-derived figures inside those owned sections.

For combined reports, use `part-scoped` runs: run the skill once per matching report part. Do not merge multiple handouts into one theory-writing pass.

## When to Use

- `course-lab-handout-normalization` already produced normalized section Markdown or JSON.
- `course-lab-workspace-template` already established the canonical report file.
- `course-lab-body-scaffold` already ensured the owned sections exist in the report structure.
- The run needs direct theory-facing writing before later result or discussion assembly.
- Handout-derived principle or background images should be placed inside those owned sections.
- A combined report has repeated part sections such as `LX1` and `LX2`, and each handout should fill only its matching part.

Do not use this skill to choose the experiment, normalize the handout, create the workspace, transfer raw data, compute results, write discussion prose, place experiment-result photos, or run final QC.

## Output Contract

- Use local `scripts/stage_principle_images.py` to stage handout-derived theory figures into the workspace.
- Use local `scripts/write_experiment_principle.py` to write directly into the canonical report.
- Keep runtime dependencies local to `/root/.codex/skills/course-lab-experiment-principle/`.
- Prefer normalized Markdown first. Fall back to JSON only when the Markdown artifact does not exist.
- Write only inside `Introduction`, `Background`, and `Experiment Principle`.
- In combined reports, write only inside the targeted parent part for that run.
- Insert staged handout-derived figures only inside those owned sections.
- Emit an ownership manifest for later skills.
- Keep unresolved gaps visible when handout support, section mapping, or figure mapping is weak.

## Primary Commands

Stage handout-derived theory figures:

```bash
python3 /root/.codex/skills/course-lab-experiment-principle/scripts/stage_principle_images.py \
  --decoded-json "/path/to/pdf_decoded/experiment/experiment.json" \
  --output-dir "/path/to/results/<experiment>/principle-images" \
  --output-tex "/path/to/results/<experiment>/principle_figures.tex" \
  --output-json "/path/to/results/<experiment>/principle_figures.json" \
  --sections-json "/path/to/results/<experiment>/notes/sections.json"
```

Write the owned sections directly into the canonical report:

```bash
python3 /root/.codex/skills/course-lab-experiment-principle/scripts/write_experiment_principle.py \
  --sections-markdown "/path/to/results/<experiment>/notes/sections.md" \
  --sections-json "/path/to/results/<experiment>/notes/sections.json" \
  --report-tex "/path/to/results/<experiment>/main.tex" \
  --figures-json "/path/to/results/<experiment>/principle_figures.json" \
  --output-json "/path/to/results/<experiment>/principle_ownership.json" \
  --output-unresolved "/path/to/results/<experiment>/principle_unresolved.md"
```

For combined reports, target one parent report part per run:

```bash
python3 /root/.codex/skills/course-lab-experiment-principle/scripts/write_experiment_principle.py \
  --sections-markdown "/path/to/results/mechanics_combined_english/notes/lx1_sections.md" \
  --sections-json "/path/to/results/mechanics_combined_english/notes/lx1_sections.json" \
  --parent-section "LX1: One-Dimensional Standing Waves" \
  --report-tex "/path/to/results/mechanics_combined_english/main.tex" \
  --figures-json "/path/to/results/mechanics_combined_english/principle_figures_lx1.json" \
  --output-json "/path/to/results/mechanics_combined_english/principle_ownership_lx1.json" \
  --output-unresolved "/path/to/results/mechanics_combined_english/principle_unresolved_lx1.md"
```

## Workflow

1. Confirm that normalized handout outputs, the canonical report file, and the body scaffold already exist.
2. Resolve normalized input in this order: Markdown first, JSON only if Markdown is absent.
3. Stage handout-derived theory figures with local `scripts/stage_principle_images.py`.
4. Read the normalized handout sections and identify text for `Introduction`, nearby `Background`, and `Experiment Principle`.
5. Run local `scripts/write_experiment_principle.py` to write those owned sections directly into the report.
6. For combined reports, pass one explicit parent report part per run and repeat once for each handout-part pair.
7. Insert staged theory figures only inside those owned sections.
8. Emit `principle_ownership.json` so later skills know these sections and figures are already owned.
9. Keep unresolved items visible instead of inventing unsupported theory text or forcing weak figure placement.

## Quick Reference

| Situation | Action |
|---|---|
| Handout-derived theory figures exist | Stage them with `stage_principle_images.py` before direct writing |
| Normalized Markdown exists | Use it before JSON |
| Combined report has repeated experiment parts | Run once per part with `--parent-section` |
| `Background` exists in the scaffolded report | Write the matching nearby theory context there |
| `Background` is absent but `Introduction` and `Experiment Principle` exist | Keep writing limited to the available owned sections |
| A section already contains clear user-written text | Keep that conflict visible and do not overwrite blindly |
| Handout support is incomplete | Leave `\NeedsInput{...}` or unresolved notes instead of inventing content |
| Figure grouping is uncertain | Preserve the emitted unresolved marker instead of guessing placement |

## Boundary Rules

- This skill starts only after handout normalization, workspace setup, and body scaffold preparation.
- This skill may write directly into the canonical report, but only inside `Introduction`, `Background`, and `Experiment Principle`.
- In combined reports, this skill may write only inside the one targeted parent part for that run.
- This skill owns handout-derived theory-image insertion inside those owned sections.
- This skill does not own experiment-result photo staging, grouped late evidence placement, signatory pages, results prose, discussion prose, or final QC.
- Keep parent-skill path dependencies out of the workflow. Use the copied local scripts in this folder only.
- Do not silently fall back to JSON when normalized Markdown exists but is malformed.
- Keep missing support visible instead of inventing theory text or silently overwriting user-written content.

## Common Mistakes

- Letting principle writing drift into results interpretation or discussion synthesis.
- Reaching back into `course-lab-figure-evidence` or the legacy parent skill at runtime instead of using the local copied tools.
- Treating every staged theory image as safe to insert even when grouping or mapping is uncertain.
- Reusing one run across multiple handouts instead of running once per combined-report part.
- Writing into a sibling part because headings looked similar.
- Quietly ignoring normalized Markdown and jumping straight to JSON.
- Overwriting non-placeholder user text inside the owned sections without surfacing the conflict.
- Expanding this skill into whole-report assembly instead of keeping it theory-facing and local.

## Resources

- `scripts/common.py`: local shared helper module
- `scripts/extract_decoded_sections.py`: local decoded-section helper for standalone packaging
- `scripts/stage_principle_images.py`: local theory-image staging tool
- `scripts/write_experiment_principle.py`: local direct writer for owned theory-facing sections
- `tests/test_skill_package.py`: standalone package checks
- `tests/test_stage_principle_images.py`: local theory-image staging tests
- `tests/test_write_experiment_principle.py`: local direct-writer tests
