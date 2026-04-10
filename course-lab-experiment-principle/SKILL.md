---
name: course-lab-experiment-principle
description: Use when a course lab-report run already has normalized handout Markdown or JSON, a canonical report file, and a body scaffold, and now needs direct theory-facing writing for either a normal report or one targeted part of a combined report plus matching handout-derived theory images.
---

# Course Lab Experiment Principle

## Overview

Write the early theory-facing report sections directly into the canonical report without drifting into results, discussion, or late evidence placement.

This skill is standalone with copied local tools. It owns direct writing for `Introduction`, nearby `Background`, and `Experiment Principle`, plus insertion of matching handout-derived figures inside those owned sections.

For combined reports, use `part-scoped` runs: run the skill once per matching report part. Do not merge multiple handouts into one theory-writing pass.

## Standalone Tool Contract

### Use Independently When

- A caller already has normalized handout sections and wants theory-facing report text inserted into a known TeX target.
- A report scaffold already contains `Introduction`, nearby `Background`, or `Experiment Principle` targets that can be safely mutated.
- Handout-derived theory figures need local staging before the later experiment-picture stage.
- A combined report needs one explicit handout-to-parent-section pass at a time.
- Normalized sections already came from `course-lab-handout-normalization`, the canonical report exists from `course-lab-workspace-template`, and owned targets exist from `course-lab-body-scaffold`.

### Minimum Inputs

- A canonical report TeX path supplied through `--report-tex`.
- Either normalized handout Markdown through `--sections-markdown` or normalized handout JSON through `--sections-json`; use Markdown first when both exist.
- A scaffolded section map in the TeX target showing the owned theory-facing sections, plus `--parent-section` when the run is part-scoped.
- Output paths for `--output-json` and `--output-unresolved`.
- When theory images are required, decoded handout JSON plus output paths for `principle_figures.json`, `principle_figures.tex`, and the staged image directory.

### Optional Workflow Inputs

- Body-scaffold or run-plan notes that clarify section names and part labels.
- Discovery notes about which decoded handout belongs to the current report part.
- Existing user-written TeX that should be preserved unless it is clearly placeholder text.

### Procedure

- Use only local scripts in `/root/.codex/skills/course-lab-experiment-principle/scripts/`.
- Resolve normalized section input as Markdown first and JSON fallback second; do not silently ignore malformed Markdown when it is present.
- Stage handout-derived theory figures before writing if a decoded handout JSON is provided.
- Mutate TeX only inside `Introduction`, `Background`, and `Experiment Principle`, and only inside the selected parent section for combined reports.
- Surface unsupported theory claims, unsafe existing prose, or uncertain figure grouping in unresolved outputs instead of inventing text.

### Outputs

- Mutated canonical TeX containing only owned theory-facing changes.
- `principle_ownership.json` describing written sections and inserted handout-derived figures.
- `principle_unresolved.md` with missing support, unsafe overwrite, or mapping issues.
- Optional `principle_figures.json`, `principle_figures.tex`, and staged image files when theory figures are processed.

### Validation

- The ownership manifest names only the expected theory-facing sections and, for combined reports, the requested parent section.
- The unresolved file exists and explicitly records any weak handout support, uncertain figure mapping, or skipped overwrite.
- The canonical report still leaves results, discussion, late evidence figures, and final-QC material untouched.
- Local package tests for principle-image staging and direct writing still pass.

### Failure / Reroute Signals

- Missing or malformed normalized sections: stop in standalone mode and request a fresh handout-normalization artifact; in full-report mode, return a reroute hint to handout normalization.
- Missing canonical TeX or absent scaffold targets: stop and request workspace-template/body-scaffold inputs; in full-report mode, reroute to the relevant setup tool.
- Ambiguous combined-report part: require an explicit `--parent-section` rather than writing across multiple parts.
- Substantive non-placeholder user prose in an owned section: leave it unchanged and record the conflict in `principle_unresolved.md`.

### Non-Ownership

- This tool does not choose the experiment, decode handouts, create the workspace, transfer data, compute results, write discussion, place experiment-result photos, or run final QC.
- This tool does not discover missing inputs by scanning unrelated workspaces or parent-skill folders.
- This tool does not broaden a part-scoped run into a whole combined-report theory pass.

## Optional Workflow Metadata

- Suggested future role label: `writer`.
- Typical upstream tools: `course-lab-handout-normalization`, `course-lab-workspace-template`, `course-lab-body-scaffold`.
- Typical downstream tools: `course-lab-final-staging`, `course-lab-figure-evidence`.

## Workflow Notes

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
