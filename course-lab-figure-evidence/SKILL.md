---
name: course-lab-figure-evidence
description: Use when a course lab-report run already has a staged draft from course-lab-final-staging plus matched picture-result or signatory sources, and now needs picture-result grouping, evidence-plan artifacts, or late picture placement into the assembled draft.
---

# Course Lab Figure Evidence

## Overview

Turn matched experiment-image sources into staged figure artifacts and placement decisions for an already assembled report draft without drifting into non-figure prose, plotting, or final QC decisions.

This skill owns experiment picture-result staging, signatory-page staging, and report-facing evidence planning. It is standalone with local copied tools, so it should not reach back into the old `course-lab-report` folder.

## When to Use

- The experiment is already confirmed.
- `course-lab-final-staging` has already produced the staged draft that will receive late figure placement.
- Matching picture-result folders or signatory-page folders are already known.
- The assembled draft needs grouped experiment figures, manifests, or an evidence plan to support late picture placement after final staging.
- The staged image pool may still need late-stage compression guidance before the final QC step.

Do not use this skill to choose the experiment, decode a new handout, transfer raw data, compute uncertainties, write interpretation prose, write discussion prose, or make final compile-and-QC decisions.

## Output Contract

- Use local `scripts/stage_picture_results.py` to copy experiment picture results into the report workspace and emit `picture_results_manifest.json`.
- Use local `scripts/plan_picture_evidence.py` to convert the manifest into `picture_evidence_plan.json` and `picture_evidence_plan.md`.
- Use local `scripts/stage_signatory_pages.py` to stage signed record sheets and emit both a manifest and a LaTeX snippet.
- Treat handout-derived theory images for `Introduction`, nearby `Background`, and `Experiment Principle` as already owned by `course-lab-experiment-principle`.
- Treat the staged draft from `course-lab-final-staging` as the main upstream report-writing input for figure placement decisions.
- Support late picture placement into that staged draft by using the staged assets, manifests, and evidence plan to decide where local figure blocks belong.
- Keep evidence planning focused on improving placement quality after final staging. It does not replace interpretation work or final QC.
- Keep grouping uncertainty visible. If figure grouping is not secure, emit a visible `\NeedsInput{...}` placeholder instead of guessing.
- Use `15 MB` as a late-stage coordination target for image handling, and surface compression guidance early enough that `course-lab-finalize-qc` still owns the final compile-and-QC decision.
- Use `$compress-png` when staged PNG assets threaten that coordination target, but keep the figure-evidence toolchain local to this folder.
- Do not switch staged images to another format unless it is truly necessary. Prefer staying in the original format, especially PNG.
- Do not switch PNG assets to JPEG or another format without asking the user for confirmation first.

## Primary Commands

Stage experiment picture results:

```bash
python3 /root/.codex/skills/course-lab-figure-evidence/scripts/stage_picture_results.py \
  --source-root "/path/to/AI_works/resources/experiment_pic_results/<matched-folder>" \
  --output-dir "/path/to/results/<experiment>/picture-results" \
  --output-json "/path/to/results/<experiment>/picture_results_manifest.json"
```

Plan report-facing picture evidence:

```bash
python3 /root/.codex/skills/course-lab-figure-evidence/scripts/plan_picture_evidence.py \
  --manifest-json "/path/to/results/<experiment>/picture_results_manifest.json" \
  --output-json "/path/to/results/<experiment>/picture_evidence_plan.json" \
  --output-markdown "/path/to/results/<experiment>/picture_evidence_plan.md"
```

Stage signatory pages:

```bash
python3 /root/.codex/skills/course-lab-figure-evidence/scripts/stage_signatory_pages.py \
  --source-root "/path/to/AI_works/resources/experiment_signatory/<matched-folder>" \
  --output-dir "/path/to/results/<experiment>/signatory-pages" \
  --output-json "/path/to/results/<experiment>/signatory_pages_manifest.json" \
  --output-tex "/path/to/results/<experiment>/signatory_pages.tex"
```

## Workflow

1. Confirm that `course-lab-final-staging` has already assembled the staged draft and that this draft is the main upstream input for figure placement.
2. Confirm that discovery already identified the picture-result directory and any signatory-page directory.
3. Assume `course-lab-experiment-principle` already handled handout-derived theory figures for the early theory-facing sections.
4. Run `stage_picture_results.py` on the matched experiment picture-result directory.
5. Convert `picture_results_manifest.json` into `picture_evidence_plan.json` and `picture_evidence_plan.md` with `plan_picture_evidence.py`.
6. If signed record sheets exist, run `stage_signatory_pages.py` and keep the emitted LaTeX snippet separate from the scientific results figures.
7. Use the staged draft as the placement surface and apply late picture placement near the already assembled figure-relevant content without rewriting non-figure prose.
8. Review grouping warnings, unmapped evidence units, and representative-subset choices before finalizing late picture placement.
9. If the staged raster-image pool looks heavy against the `15 MB` coordination target, invoke `$compress-png` before handing off to `course-lab-finalize-qc`.
10. Keep compression in the same image format unless that still cannot get the asset pool under control.
11. If cross-format conversion looks necessary after same-format compression attempts, ask the user for confirmation first and wait before converting anything.

## Quick Reference

| Situation | Action |
|---|---|
| `course-lab-final-staging` already produced the staged draft | Use that staged draft as the upstream placement surface for late picture placement |
| Handout-derived theory images were already placed by `course-lab-experiment-principle` | Leave them alone and focus on late experiment evidence |
| Matched experiment photo folder is known | Run `stage_picture_results.py` |
| Serial-numbered files show a process sequence | Preserve the ordered sequence group in the manifest and evidence plan |
| Result-picture groups must map into report subsections late in the run | Run `plan_picture_evidence.py` to improve placement quality after final staging |
| Signatory sheets exist | Run `stage_signatory_pages.py` |
| PNG assets are inflating the image pool | Invoke `$compress-png`, keep PNG output if possible, and treat `15 MB` as a coordination target for late-stage handoff |
| Same-format compression still looks insufficient | Ask the user for confirmation first before converting to another format |

## Boundary Rules

- This skill starts only after source discovery and `course-lab-final-staging` are settled.
- This skill owns staging, grouping, evidence-plan artifacts, and late picture placement.
- This skill does not own handout-derived theory images already placed by `course-lab-experiment-principle`.
- This skill does not own non-figure prose writing.
- This skill does not own final compile or QC decisions.
- This skill does not own interpretation prose or discussion synthesis.
- Keep parent-skill path dependencies out of the workflow. Use the copied local scripts in this folder instead of the old `course-lab-report` folder.
- Preserve low-confidence mapping as warnings and placeholders instead of silently forcing a subsection or caption.
- Do not fold signatory pages into the scientific results discussion.
- Prefer same-format compression first. Do not switch staged images to another format unless necessary, and ask the user for confirmation first before any such conversion.

## Common Mistakes

- Reaching back into the old parent report-skill folder instead of using the copied local scripts.
- Treating the evidence plan as final interpretation prose or as a substitute for final QC instead of a late-stage placement contract.
- Reclaiming handout-derived theory images that were already owned by `course-lab-experiment-principle`.
- Guessing through ambiguous figure grouping instead of surfacing a visible question.
- Treating image-size guidance as if this skill owns the final compile-and-QC decision.
- Converting PNG assets to JPEG immediately instead of trying same-format compression first and getting user confirmation before any format switch.

## Resources

- `scripts/common.py`: local helper module copied for standalone use
- `scripts/stage_picture_results.py`: local picture-result staging tool
- `scripts/plan_picture_evidence.py`: local evidence-plan builder
- `scripts/stage_signatory_pages.py`: local signatory-page staging tool
- `tests/test_skill_package.py`: local standalone packaging checks
- `tests/test_stage_picture_results.py`: local regression tests for picture-result staging
- `tests/test_plan_picture_evidence.py`: local regression tests for evidence planning
- `tests/test_stage_signatory_pages.py`: local regression tests for signatory-page staging
