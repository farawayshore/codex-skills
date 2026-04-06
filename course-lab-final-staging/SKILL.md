---
name: course-lab-final-staging
description: Use when a course lab-report run already has a canonical report workspace plus stable processing, interpretation, and discussion artifacts and now needs late-stage non-figure report assembly with case-by-case results, processing narration, uncertainty narration, modeling inclusion, and appendix code staging before course-lab-figure-evidence and final QC.
---

# Course Lab Final Staging

## Overview

Use this skill as the standalone late-stage non-figure writer for a lab report.

This package is independent and uses only local copied tools under `/root/.codex/skills/course-lab-final-staging/`. It should read the canonical `main.tex` plus stabilized upstream artifacts, then assemble a substantive draft that favors completeness over brevity: direct results for each case, handout-demanded indirect results, data-processing narration, uncertainty-calculation narration, modeling inclusion, synthesized discussion, calculation details appendix support, and appendix code support. The goal is a text-first draft that naturally supports a roughly `20-30` page two-column final PDF after `course-lab-figure-evidence` and final QC complete the later stages.

## When to Use

- The experiment is already confirmed.
- The canonical report workspace and `main.tex` already exist.
- Front matter is already handled by `course-lab-metadata-frontmatter`.
- Introduction, nearby Background, and Experiment Principle are already handled by `course-lab-experiment-principle`.
- Stable processed-data artifacts already exist.
- Stable results-interpretation artifacts already exist.
- Stable discussion-synthesis artifacts already exist.
- Optional modeling artifacts or appendix code files may also exist and should be staged into the report when relevant.

Do not use this skill to transfer raw data, recompute uncertainties, execute modeling, place late figures, compile the report, or take over final QC.

## Output Contract

- Use local `/root/.codex/skills/course-lab-final-staging/scripts/build_final_staging.py` as the main entrypoint.
- Keep runtime dependencies local to `/root/.codex/skills/course-lab-final-staging/`.
- Mutate `main.tex` only in safe owned section bodies.
- Resolve target headings with explicit deterministic bucket matching across both `\section{...}` and `\subsection{...}` so synonyms such as `Experimental Procedure and Observations`, `Results and Analysis`, `Local Discussion`, and `Code` can be recognized without LLM-only fuzzy matching.
- In split reports, prefer same-block subsection targets such as `Local Discussion` inside the active experiment block before falling back to later global sections such as `Discussion`.
- Allow overwrite of explicit draft-like scaffold prose when it is still short, clearly provisional, and does not already look like substantive authored report content.
- Accept `% course-lab-final-staging:allow-overwrite` as an intentional handoff marker when upstream skills or manual editors want final staging to replace a local draft block on the next run.
- Honor `body_scaffold.json` field `staging_mode: "summary_only_existing_draft"` for reruns on already-authored drafts: preserve substantive target sections instead of failing, but still update any safe placeholder-owned sections and still emit the staging summary artifacts.
- Preserve case-by-case direct results instead of flattening them into one short summary.
- When upstream artifacts expose multiple validated `comparison_cases`, preserve them as multiple report blocks instead of collapsing them into one aggregate comparison paragraph.
- When many validated `comparison_cases` are present, prefer a compact comparison matrix or similarly dense rendering over one long per-case paragraph stack so the later figure stage still has room.
- Include handout-demanded indirect results when upstream artifacts support them.
- Write report-side narration for the data-processing procedure and the corresponding uncertainty-calculation procedure from upstream artifacts.
- When upstream uncertainty artifacts expose result-specific formulas, render the explicit partial derivative propagation formula for each reported indirect result instead of only a generic definition.
- After those formulas, write the substituted key quantities and evaluated steps that lead to the reported uncertainty, including direct-summary terms such as `s`, `u_a`, `u_b`, `u_c`, and the final expanded uncertainty when those artifacts exist.
- Prefer compact tables for those middle uncertainty results when several quantities must be shown together, especially in two-column report layouts.
- Format detailed propagation equations so they can wrap cleanly inside a two-column page, using multi-line math instead of one unbroken inline expression.
- Include modeling results when modeling artifacts exist.
- Convert synthesized discussion artifacts into final report prose without hiding unresolved support limits.
- Attach explicit calculation details in the appendix when `course-lab-data-processing` provides a `--calculation-details-manifest` handoff.
- Place `Calculation Details` before `Code` in appendix rendering when both are present.
- Render that `Calculation Details` appendix as full-width appendix material when needed; it does not need to preserve the two-column body-layout math constraints used elsewhere in the report.
- Attach major code in the appendix when those files are explicitly provided.
- Attach uncited CSV data attachments in the appendix when those files are explicitly provided through `--appendix-data`, using a visually distinct data-file block instead of the code-style block.
- Require the caller to pass appendix code paths explicitly through `--appendix-code` when discovered simulation or modeling scripts should appear in the report appendix.
- Require the caller to pass appendix data-file paths explicitly through `--appendix-data` when staged CSV bundles should appear in the report appendix.
- Require the caller to pass the calculation-details manifest explicitly through `--calculation-details-manifest`; this skill does not discover calculation-detail attachments by scanning the workspace.
- Render explicitly provided appendix code as selectable report text when the downstream build path supports it, using compact styled code blocks rather than path-only placeholders.
- Skip appendix data files that are already cited by filename in the current report draft, so the appendix only catches still-unmentioned staged CSV attachments.
- Emit:
  - `final_staging_summary.json`
  - `final_staging_summary.md`
  - `final_staging_unresolved.md`
  - `appendix_code_manifest.json`
- Include normalized `comparison_cases` in `final_staging_summary.json` when case-paired observed/simulation assets were discovered, so `course-lab-figure-evidence` can place same-case experiment-vs-simulation figures instead of rediscovering those pairings.

## Primary Command

```bash
python3 /root/.codex/skills/course-lab-final-staging/scripts/build_final_staging.py \
  --main-tex "/path/to/results/<experiment>/main.tex" \
  --body-scaffold-json "/path/to/results/<experiment>/body_scaffold.json" \
  --procedures-markdown "/path/to/results/<experiment>/<experiment-safe-name>_procedures.md" \
  --processed-data-json "/path/to/results/<experiment>/analysis/processed_data.json" \
  --calculation-details-manifest "/path/to/results/<experiment>/analysis/calculation_details_manifest.json" \
  --results-interpretation-json "/path/to/results/<experiment>/results_interpretation.json" \
  --discussion-synthesis-json "/path/to/results/<experiment>/discussion_synthesis.json" \
  --modeling-result "/path/to/results/<experiment>/modeling/batch_run_result.json" \
  --appendix-data "/path/to/results/<experiment>/analysis/appendix_data/case1_measurements.csv" \
  --appendix-data "/path/to/results/<experiment>/analysis/appendix_data/case2_measurements.csv" \
  --appendix-code "/path/to/results/<experiment>/modeling/model.wl" \
  --appendix-code "/path/to/results/<experiment>/analysis/process_data.py" \
  --output-summary-json "/path/to/results/<experiment>/final_staging_summary.json" \
  --output-summary-markdown "/path/to/results/<experiment>/final_staging_summary.md" \
  --output-unresolved "/path/to/results/<experiment>/final_staging_unresolved.md" \
  --output-appendix-manifest "/path/to/results/<experiment>/appendix_code_manifest.json"
```

## Workflow

1. Confirm that `main.tex` and the required upstream artifacts already exist.
2. Read `references/shared_draft_contract.md` before mutating the draft.
3. Collect and validate the staging inputs with the local helper scripts.
4. Write report-ready narration for the data-processing procedure.
5. Write report-ready narration for the corresponding uncertainty-calculation procedure.
6. Render direct results and indirect results per case so former results remain visible instead of compressed away.
7. For each indirect result with staged uncertainty support, show the specialized partial derivative propagation formula and the substituted values that evaluate it, preferring tables for grouped middle values and line-breakable math for two-column drafts.
8. Render one comparison block per validated comparison case when paired evidence or explicit `comparison_cases` records exist, but switch to a compact matrix-style rendering when many cases would otherwise consume too much body space.
9. Insert interpretation bridges, modeling results, and synthesized discussion where the artifact evidence supports them.
10. If some comparison-case material cannot be mapped safely, keep that gap visible in unresolved outputs instead of silently shortening the report.
11. Stage explicit calculation details as appendix attachments before data files and code when the caller provides a calculation-details manifest.
12. Stage appendix data-file references and distinct colored CSV listings when `--appendix-data` files are provided and the current draft does not already cite them by filename.
13. Stage appendix code references and compact styled code listings when major code files are provided.
14. Treat calculation details, appendix data files, and appendix code as explicit caller-owned handoffs: this skill does not discover those attachments from workspace scans, discovery manifests, or result folders on its own.
15. Emit staging summaries and unresolved-gap notes.
16. Stop and hand off to `course-lab-figure-evidence`, then final QC.

## Boundary Rules

- This skill is a late-stage non-figure writer.
- This skill does not overwrite front matter or theory-facing sections already owned upstream.
- This skill does not recompute results, recompute uncertainties, or execute modeling.
- This skill does not place late figures.
- This skill owns case-by-case comparison prose; `course-lab-figure-evidence` owns later paired-image placement.
- This skill may compact comparison prose or tables to protect page budget, but it still does not own late figure layout.
- This skill does not compile the report.
- This skill does not choose or refresh the TeX compiler; final build-path ownership stays with final QC.
- This skill does not take over final QC.
- This skill does not discover calculation details files from discovery artifacts or result directories; callers must pass that manifest explicitly.
- This skill does not discover appendix data files from discovery artifacts or result directories; callers must pass those CSV paths explicitly.
- This skill does not discover appendix code files from discovery artifacts or result directories; callers must pass those paths explicitly.
- This skill should fail clearly instead of overwriting substantive user prose in an owned section unless the block is explicitly draft-like or intentionally handed over with `% course-lab-final-staging:allow-overwrite`.
- When `staging_mode: "summary_only_existing_draft"` is explicitly set in `body_scaffold.json`, preserving substantive user prose and emitting a summary-only rerun is the intended behavior rather than a failure.
- Keep all runtime tool usage local to this standalone folder.

## Common Mistakes

- Flattening several experiment cases into one short result paragraph.
- Flattening multiple validated comparison cases into one short aggregate comparison paragraph.
- Letting many comparison cases expand into a long stack of near-duplicate paragraph blocks when a compact comparison matrix would preserve more space for later evidence.
- Listing only final indirect values without showing the data-processing route or uncertainty route.
- Stopping at a generic propagation definition when the staged artifacts are rich enough to show the specific partial derivative formula and substituted values for that indirect result.
- Leaving uncertainty middle results in paragraph-long prose when a compact table would keep the two-column report readable.
- Emitting one unbroken propagation expression that overflows the column instead of using multi-line math that can wrap.
- Leaving modeling outputs detached from the report when modeling artifacts already exist.
- Hiding calculation details in body prose or hand-maintained special includes after `course-lab-data-processing` already provided appendix-ready attachments.
- Forgetting that uncited CSV bundles can belong in a separate appendix data-files lane instead of being buried in code or omitted entirely.
- Trimming appendix code support too early even though reproducibility material should remain visible.
- Reaching back into parent or sibling skill folders instead of using this local package.
- Drifting into `course-lab-figure-evidence` or final QC responsibilities.

## Resources

- `scripts/common.py`: local helper functions for JSON, TeX section ownership, and safe-overwrite rules
- `scripts/collect_staging_inputs.py`: local input collector and validator
- `scripts/render_results_sections.py`: local renderer for data-processing narration, uncertainty narration, and per-case results
- `scripts/render_appendix_materials.py`: local appendix and code-manifest renderer
- `scripts/render_catalog_and_timing.py`: local catalogue and timing summary renderer
- `scripts/build_final_staging.py`: local final-staging builder
- `references/report_structure.md`: local report-depth and structure guidance
- `references/shared_draft_contract.md`: local safe-mutation guidance for reruns and owned regions
