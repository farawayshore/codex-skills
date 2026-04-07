# Course Lab Report Orchestrator Baseline Failures

## Why The New Parent Skill Is Needed

- The current parent behavior is still anchored in `modern-physics-latex-report-rennovated`, which mixes orchestration language with execution-heavy guidance instead of acting as a compact controller.
- The legacy parent does not define a standalone controller-state artifact for recording stage outputs, late-stage ownership, and reroute history.
- Delegation policy is not captured as a clear hybrid map with inline-preferred, small-worker, stay-local, and conditional-stronger-worker cases.
- Final QC is described, but the new reroute contract is not isolated in a dedicated parent package.
- Page-count shortfall is not yet owned by a standalone orchestrator that explicitly sends the run back to `course-lab-final-staging` for richer re-staging.
- The parent contract did not explicitly forbid manual late-stage shortcuts such as a hand-written short draft or a prose-only appendix stub when `course-lab-final-staging` and `course-lab-figure-evidence` artifacts were missing.
- The parent contract did not require artifact proof such as `final_staging_summary.json`, `appendix_code_manifest.json`, `picture_evidence_plan.json`, `signatory_pages_manifest.json`, and `signatory_pages.tex` before a report could be claimed complete.
- The parent contract did not require principle-stage artifact proof such as `principle_ownership.json`, `principle_figures.json`, `principle_figures.tex`, or `principle_unresolved.md`, so a run could silently continue after hand-written theory prose without ever proving that handout-derived theory-image staging had happened.
- The parent contract did not require persistent decoded handout artifacts under `AI_works/resources/experiment_handout/Modern Physics Experiments/pdf_decoded/<experiment-name>/<experiment-name>.md` and `.json`, so a run could silently continue with only `handout_extract.md`, `notes/sections.md`, or `sections.json`.
