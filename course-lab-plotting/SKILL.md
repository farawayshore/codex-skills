---
name: course-lab-plotting
description: Use when a course lab-report run already has validated or processed numeric artifacts plus a handout-grounded plotting requirement and now needs standalone plot generation, special-point annotation, or permanent plot assets before figure staging or interpretation.
---

# Course Lab Plotting

## Overview

Turn already-available numeric lab artifacts into permanent plot images without drifting into data processing, model execution, figure staging, or report prose.

This skill is standalone with local copied tools. It should use the local scripts in this folder and keep unresolved plotting gaps visible instead of guessing through them.

The renderer uses a vendored local `matplotlib` copy under this skill folder so the package stays self-contained while producing stronger scientific plots than a hand-drawn fallback.

## When to Use

- The experiment is already confirmed.
- The run already has validated transferred data or processed numeric artifacts.
- The handout or run plan already identifies one or more required plots.
- The workflow needs permanent plot assets under the matched `plottings/` folder before later figure staging or interpretation.
- The plots should mark honest special point features such as a highest point, lowest point, or zero point when those can be derived directly from the numeric artifacts.

Do not use this skill to transcribe raw data, compute new derived quantities, run modeling jobs, stage figures into report order, or write interpretation prose.

## Output Contract

- Use local `/root/.codex/skills/course-lab-plotting/scripts/build_plot_job.py` to normalize one plotting request into `plot_job.json`.
- Use local `/root/.codex/skills/course-lab-plotting/scripts/detect_special_points.py` to detect honest annotation candidates from numeric series.
- Use local vendored `matplotlib` from `/root/.codex/skills/course-lab-plotting/vendor/` through `/root/.codex/skills/course-lab-plotting/scripts/render_plot.py` to render the final PNG output with controlled color styling and special point markers.
- Use local `/root/.codex/skills/course-lab-plotting/scripts/write_plot_manifest.py` to emit `plot_manifest.json` and `plot_unresolved.md`.
- Keep permanent outputs under `AI_works/resources/experiment_pic_results/<matched-experiment-path>/plottings/`.
- Prefer serial identity for filenames such as `plot-01.png`. Use compact parameter identity only when a stable serial case is missing.
- If the plotting requirement is underspecified, or required columns are missing, emit a visible unresolved note instead of inventing data or axis meaning.

## Primary Commands

Build one plot job:

```bash
python3 /root/.codex/skills/course-lab-plotting/scripts/build_plot_job.py \
  --source "/path/to/validated_series.csv" \
  --x-field "x" \
  --y-field "y" \
  --output-root "/root/grassman_projects/AI_works/resources/experiment_pic_results/<matched-experiment-path>/plottings" \
  --plot-id "plot-01"
```

Inspect special point detection:

```bash
python3 /root/.codex/skills/course-lab-plotting/scripts/detect_special_points.py \
  --x 0 --x 1 --x 2 \
  --y -1 --y 0 --y 3
```

Render the plot:

```bash
python3 /root/.codex/skills/course-lab-plotting/scripts/render_plot.py \
  --job-json "/path/to/plot_job.json"
```

Rewrite the manifest if needed:

```bash
python3 /root/.codex/skills/course-lab-plotting/scripts/write_plot_manifest.py \
  --job-json "/path/to/plot_job.json" \
  --status ok
```

## Workflow

1. Read the handout-derived plotting requirement before plotting.
2. Confirm the numeric source is already validated or already processed.
3. Use `build_plot_job.py` to create one local `plot_job.json`.
4. Use `render_plot.py` to generate the permanent plot image.
5. Let the renderer add honest special point annotations for supported cases such as max, min, and zero.
6. Let the vendored `matplotlib` renderer handle axes, gridlines, labels, and legends so the output keeps a clean scientific look.
7. Keep color choices controlled and readable so the plot looks intentional and stays scientifically usable.
8. If a required plot cannot be produced honestly, preserve that state in `plot_unresolved.md` rather than fabricating a result.

## Quick Reference

| Situation | Action |
|---|---|
| Stable serial plot case already exists | Use that serial identity for the filename |
| No serial case exists but only a few parameter sets exist | Use compact parameter identity as fallback |
| A highest point or lowest point is obvious from the numeric series | Mark it as a special point |
| A zero point is present or a zero crossing is unambiguous | Mark the zero point honestly |
| Required columns are missing | Emit `plot_unresolved.md` instead of guessing |
| The plot needs better readability | Use controlled color variation, labels, and markers rather than decorative styling |

## Boundary Rules

- This skill starts only after numeric artifacts are already available.
- This skill owns plot rendering, honest annotation, and manifest output.
- This skill does not own new scientific computation, modeling execution, figure staging, or interpretation.
- Keep all tool usage local to this standalone folder.
- Do not invent special point annotations that are not supported directly by the numeric artifact.
- Do not use color variation as decoration alone. Use it to improve clarity and beauty without leaving scientific style.

## Common Mistakes

- Reaching back into older report-skill folders instead of using the local copied scripts.
- Quietly guessing through missing axis meaning or missing columns.
- Treating plot beautification as permission to make infographic-style figures.
- Marking a special point that the current numeric artifact does not actually support.
- Folding derived-quantity work into plotting instead of handing it off to the upstream processing skill.

## Resources

- `scripts/common.py`: local helper functions for JSON, CSV, paths, and naming
- `scripts/build_plot_job.py`: local plot-job builder
- `scripts/detect_special_points.py`: local special point detector
- `scripts/write_plot_manifest.py`: local manifest and unresolved-note writer
- `scripts/render_plot.py`: local scientific plot renderer
- `vendor/matplotlib`: vendored plotting library kept inside the standalone skill package
- `tests/test_skill_package.py`: local standalone packaging checks
- `tests/test_build_plot_job.py`: local job-contract regression tests
- `tests/test_detect_special_points.py`: local annotation regression tests
- `tests/test_render_plot.py`: local renderer and manifest regression tests
