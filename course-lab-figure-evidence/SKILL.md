---
name: course-lab-figure-evidence
description: Use when a course lab-report run already has a staged draft from course-lab-final-staging plus matched picture-result or signatory sources, and now needs picture-result grouping, evidence-plan artifacts, or late picture placement into the assembled draft.
---

# Course Lab Figure Evidence

## Overview

Turn matched experiment-image sources into staged figure artifacts and placement decisions for an already assembled report draft without drifting into non-figure prose, plotting, or final QC decisions.

This skill owns experiment picture-result staging, signatory-page staging, and report-facing evidence planning. It is standalone with local copied tools, so it should not reach back into the old parent report-skill folder.

When late-stage comparison artifacts exist, this skill should stage the paired simulation image assets and group them with the matching observed case evidence rather than planning only experiment-side photos.

## Standalone Tool Contract

### Use Independently When

- A staged report draft or evidence-planning target already exists and matched picture-result or signatory sources are known.
- The caller needs picture-result staging, signatory-page staging, evidence-plan artifacts, or late figure placement guidance.
- Paired observed/simulation comparison cases should be grouped from an explicit final-staging summary.
- The task is figure/evidence focused and should not rewrite non-figure prose or take over final compile/QC decisions.
- `course-lab-final-staging` already produced the staged draft, and `course-lab-experiment-principle` already owns handout-derived theory images for the early theory-facing sections.

### Minimum Inputs

- For picture-result staging: a matched `--source-root`, an `--output-dir`, and an `--output-json` manifest path.
- For evidence planning: a `--manifest-json`, an `--output-json`, and an `--output-markdown`.
- For signatory staging: a matched signatory `--source-root`, an output directory, an output manifest path, and an output TeX snippet path.
- For direct late TeX mutation, an explicitly identified staged draft or canonical TeX target plus a validated evidence plan; artifact-only staging does not require TeX mutation authority.
- When pairing observed/simulation cases, an explicit `--comparison-cases-json` such as `final_staging_summary.json`.

### Optional Workflow Inputs

- Final-staging summary fields that name safe result/discussion neighborhoods and normalized `comparison_cases`.
- Discovery notes identifying representative picture-result folders and signatory-page folders.
- Image-size measurements used to decide whether `$compress-png` should run before final QC.
- Existing placement notes or `\NeedsInput{...}` markers from earlier figure attempts.

### Procedure

- Use only local scripts in `/root/.codex/skills/course-lab-figure-evidence/scripts/`.
- Stage picture results and same-case comparison assets before planning placement.
- Build the evidence plan from the manifest, then use that plan to decide any late figure TeX insertion.
- Keep low-confidence grouping, missing captions, oversized images, and representative-subset choices visible.
- Keep captions report-facing and avoid internal provenance wording such as `source archive`, `staged evidence set`, `source label`, `metadata`, or `evidence pool`.

### Outputs

- `picture_results_manifest.json` and staged image assets under the caller-provided output directory.
- `picture_evidence_plan.json` and `picture_evidence_plan.md`.
- Optional `signatory_pages_manifest.json`, `signatory_pages.tex`, and staged signatory images.
- Optional TeX figure insertions or visible `\NeedsInput{...}` placeholders when late placement is explicitly requested and safe.
- Compression guidance when the staged image pool threatens the `15 MB` coordination target.

### Validation

- Manifests refer only to staged local assets and preserve sequence/case grouping warnings.
- Evidence-plan Markdown is suitable for report-facing placement review and does not masquerade as interpretation prose.
- Any TeX mutation is limited to figure blocks near existing final-staging content and does not rewrite non-figure sections.
- Captions avoid internal workflow/provenance language and use file-name stems or handout-grounded descriptions when formal captions are missing.
- Local figure-evidence staging, planning, and signatory tests pass.

### Failure / Reroute Signals

- Missing picture-result or signatory source roots: stop in standalone mode with the missing path; in full-report mode, return a reroute hint to source discovery.
- Ambiguous grouping or subsection mapping: emit warnings and `\NeedsInput{...}` placeholders instead of forcing a placement.
- Missing or malformed comparison-case summary: continue with observed-only staging when safe and record the pairing gap.
- PNG pool still too large after same-format compression attempts: ask for explicit user confirmation before converting to another format.

### Non-Ownership

- This tool does not choose the experiment, decode handouts, transfer raw data, compute uncertainties, write interpretation prose, synthesize discussion prose, or make final compile/QC decisions.
- This tool does not reclaim handout-derived theory images already owned by `course-lab-experiment-principle`.
- This tool does not convert PNG assets to JPEG or another format without explicit user confirmation.

## Optional Workflow Metadata

- Suggested future role label: `writer`.
- Typical upstream tools: `course-lab-final-staging`, `course-lab-discovery`, `course-lab-experiment-principle`.
- Typical downstream tools: `course-lab-finalize-qc`, `$compress-png` when same-format PNG compression is needed.

## Workflow Notes

- Use local `scripts/stage_picture_results.py` to copy experiment picture results into the report workspace and emit `picture_results_manifest.json`.
- Use local `scripts/plan_picture_evidence.py` to convert the manifest into `picture_evidence_plan.json` and `picture_evidence_plan.md`.
- Use local `scripts/stage_signatory_pages.py` to stage signed record sheets and emit both a manifest and a LaTeX snippet.
- When `course-lab-final-staging` emitted normalized `comparison_cases`, pass that artifact into `stage_picture_results.py` so simulation images are staged into the report workspace and can be paired with same-case observed images.
- Keep signatory-page layouts footer-safe: bound the staged page height so two-row appendix blocks stay inside the printable area, and use normal subfigure captions so `(a)`, `(b)`, `(c)` markers remain visible.
- Treat handout-derived theory images for `Introduction`, nearby `Background`, and `Experiment Principle` as already owned by `course-lab-experiment-principle`.
- Treat the staged draft from `course-lab-final-staging` as the main upstream report-writing input for figure placement decisions.
- Support late picture placement into that staged draft by using the staged assets, manifests, and evidence plan to decide where local figure blocks belong.
- Keep evidence planning focused on improving placement quality after final staging. It does not replace interpretation work or final QC.
- Keep grouping uncertainty visible. If figure grouping is not secure, emit a visible `\NeedsInput{...}` placeholder instead of guessing.
- Keep figure captions and nearby placement notes human-sounding. Do not use provenance or workflow wording such as `source archive`, `staged evidence set`, `source label`, `metadata`, or `evidence pool` in the report.
- When the handout does not supply a formal caption, refer to a picture by its file name stem or a handout-grounded description instead of exposing internal staging language.
- Use `15 MB` as a late-stage coordination target for image handling, and surface compression guidance early enough that `course-lab-finalize-qc` still owns the final compile-and-QC decision.
- Use `$compress-png` when staged PNG assets threaten that coordination target, but keep the figure-evidence toolchain local to this folder.
- Do not switch staged images to another format unless it is truly necessary. Prefer staying in the original format, especially PNG.
- Do not switch PNG assets to JPEG or another format without asking the user for confirmation first.

## Primary Commands

Stage experiment picture results:

```bash
python3 /root/.codex/skills/course-lab-figure-evidence/scripts/stage_picture_results.py \
  --source-root "/path/to/AI_works/resources/experiment_pic_results/<matched-folder>" \
  --comparison-cases-json "/path/to/results/<experiment>/final_staging_summary.json" \
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
5. If `course-lab-final-staging` emitted normalized `comparison_cases`, pass that summary JSON to `stage_picture_results.py` so same-case simulation images are copied into `picture-results/comparison-cases/`.
6. Convert `picture_results_manifest.json` into `picture_evidence_plan.json` and `picture_evidence_plan.md` with `plan_picture_evidence.py`.
7. If signed record sheets exist, run `stage_signatory_pages.py` and keep the emitted LaTeX snippet separate from the scientific results figures.
8. Use the staged draft as the placement surface and apply late picture placement near the already assembled figure-relevant content without rewriting non-figure prose.
9. Review grouping warnings, unmapped evidence units, and representative-subset choices before finalizing late picture placement.
10. Prefer same-case paired comparison units when both observed and simulation assets are available, placing experiment and simulation pictures together rather than in disconnected figure groups.
11. If the staged raster-image pool looks heavy against the `15 MB` coordination target, invoke `$compress-png` before handing off to `course-lab-finalize-qc`.
12. Keep compression in the same image format unless that still cannot get the asset pool under control.
13. If cross-format conversion looks necessary after same-format compression attempts, ask the user for confirmation first and wait before converting anything.

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
- Keep parent-skill path dependencies out of the workflow. Use the copied local scripts in this folder instead of the old parent report-skill folder.
- Preserve low-confidence mapping as warnings and placeholders instead of silently forcing a subsection or caption.
- Do not let captions or placement notes sound like workflow logs. Prefer neutral lab-report naming based on the file name stem or the handout description.
- Do not fold signatory pages into the scientific results discussion.
- Prefer same-format compression first. Do not switch staged images to another format unless necessary, and ask the user for confirmation first before any such conversion.

## Common Mistakes

- Reaching back into the old parent report-skill folder instead of using the copied local scripts.
- Treating the evidence plan as final interpretation prose or as a substitute for final QC instead of a late-stage placement contract.
- Reclaiming handout-derived theory images that were already owned by `course-lab-experiment-principle`.
- Guessing through ambiguous figure grouping instead of surfacing a visible question.
- Treating image-size guidance as if this skill owns the final compile-and-QC decision.
- Letting signatory-page captions drift into the footer by widening portrait scans without a height cap.
- Writing captions with provenance wording such as `source archive`, `staged evidence set`, `source label`, `metadata`, or `evidence pool`.
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
