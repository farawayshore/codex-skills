---
name: modern-physics-latex-report-rennovated
description: Use when building or refining a Modern Physics LaTeX lab report in this repo and the run needs experiment discovery, handout or reference decoding, reusable workspace setup, picture-result analysis, PNG size control, appendix staging, and final QC without inventing missing content.
---

# Modern Physics LaTeX Report (rennovated)

Use this skill for Modern Physics lab-report work in this repository.

Run it as an interactive execution checklist. Pause at the required checkpoints instead of guessing through missing data, ambiguous pictures, or uncertain structure.

## Narrative And Tone Guardrails

- The report must read like a normal lab report written from the experimenter's point of view.
- Do not use AI tone, workflow narration, status-log language, or tool-perspective wording in the report.
- Do not write lines that sound like internal process notes, such as "this report was generated", "based on the provided materials", "the following analysis was extracted", or similar meta narration.
- Do not mention AI, Codex, ChatGPT, OpenAI, MinerU, automatic generation, decoding workflow, transcription workflow, or drafting provenance anywhere in the TeX, captions, table titles, appendix notes, or non-essential comments.
- When something is missing or uncertain, use neutral experiment-report wording or a visible `\NeedsInput{...}` placeholder instead of self-referential explanation.
- Keep source comments minimal and neutral. Retain only structurally necessary comments such as `% procedure:P01` and nearby placeholder markers.

## Quick Start

1. Discover sources and likely experiment matches:

```bash
python3 /root/.codex/skills/modern-physics-latex-report/scripts/discover_sources.py \
  --experiment "原子力显微镜"
```

2. Create or reuse the workspace after the user confirms experiment, mode, and template:

```bash
python3 /root/.codex/skills/modern-physics-latex-report/scripts/ensure_report_workspace.py \
  --experiment "原子力显微镜" \
  --mode new \
  --template "/root/grassman_projects/AI_works/resources/latex_templet/tau_templet copy.tex"
```

3. Create or refresh the reusable author profile:

```bash
python3 /root/.codex/skills/modern-physics-latex-report/scripts/manage_author_profile.py
```

4. Normalize a decoded handout into report-ready section blocks:

```bash
python3 /root/.codex/skills/modern-physics-latex-report/scripts/extract_decoded_sections.py \
  --decoded-json "/path/to/pdf_decoded/experiment/experiment.json" \
  --output-json /tmp/sections.json \
  --output-markdown /tmp/sections.md
```

5. Stage principle figures from the decoded handout:

```bash
python3 /root/.codex/skills/modern-physics-latex-report/scripts/stage_principle_images.py \
  --decoded-json "/path/to/pdf_decoded/experiment/experiment.json" \
  --sections-json /tmp/sections.json \
  --output-dir "/path/to/results/<experiment>/principle-images" \
  --output-tex "/path/to/results/<experiment>/principle_figures.tex" \
  --output-json "/path/to/results/<experiment>/principle_figures.json"
```

6. Stage experiment picture-result files when the handout requires recorded photos:

```bash
python3 /root/.codex/skills/modern-physics-latex-report/scripts/stage_picture_results.py \
  --source-root "/path/to/AI_works/resources/experiment_pic_results/<matched-folder>" \
  --output-dir "/path/to/results/<experiment>/picture-results" \
  --output-json "/path/to/results/<experiment>/picture_results_manifest.json"
```

7. Plan subsection-local picture evidence after staging:

```bash
python3 /root/.codex/skills/modern-physics-latex-report-rennovated/scripts/plan_picture_evidence.py \
  --manifest-json "/path/to/results/<experiment>/picture_results_manifest.json" \
  --output-json "/path/to/results/<experiment>/picture_evidence_plan.json" \
  --output-markdown "/path/to/results/<experiment>/picture_evidence_plan.md"
```

8. Stage signatory pages when they exist:

```bash
python3 /root/.codex/skills/modern-physics-latex-report/scripts/stage_signatory_pages.py \
  --source-root "/path/to/AI_works/resources/experiment_signatory/<matched-folder>" \
  --output-dir "/path/to/results/<experiment>/signatory-pages" \
  --output-json "/path/to/results/<experiment>/signatory_pages_manifest.json" \
  --output-tex "/path/to/results/<experiment>/signatory_pages.tex"
```

9. Compute uncertainties after the transferred data is confirmed:

```bash
python3 /root/.codex/skills/modern-physics-latex-report/scripts/compute_uncertainties.py \
  --input /path/to/data_processed/example.csv \
  --quantity voltage \
  --resolution voltage=0.01 \
  --output-markdown /tmp/uncertainty.md
```

10. Build `Further Discussion` candidates after the evidence plan is stable:

```bash
python3 /root/.codex/skills/modern-physics-latex-report-rennovated/scripts/build_discussion_candidates.py \
  --evidence-plan "/path/to/results/<experiment>/picture_evidence_plan.json" \
  --output-json "/path/to/results/<experiment>/discussion_candidates.json" \
  --output-markdown "/path/to/results/<experiment>/discussion_candidates.md"
```

11. Audit and compress oversized PNG assets early when staged result pictures are likely to bloat the PDF:

```bash
python3 /root/.codex/skills/compress-png/scripts/compress_png.py \
  AI_works/results/晶体光学性质/picture-results \
  --audit-only \
  --min-size-mb 1 \
  --top 20
```

12. Check final report coverage and cleanup:

```bash
python3 /root/.codex/skills/modern-physics-latex-report/scripts/report_qc.py \
  --tex /path/to/main.tex \
  --procedures /path/to/experiment_procedures.md \
  --evidence-plan "/path/to/results/<experiment>/picture_evidence_plan.json" \
  --discussion-candidates "/path/to/results/<experiment>/discussion_candidates.json" \
  --output-markdown /tmp/report_qc.md
```

## Workflow

Follow this execution order during a real run.

### 1. Preflight And Discovery

- Run `scripts/discover_sources.py --experiment "..."`.
- Show the best-matching handout, reference-report, data, result-folder, and template candidates.
- If discovery is weak, show the candidate list instead of pretending the match is certain.
- Confirm the experiment before mutating anything.
- Detect whether a result folder and existing `.tex` files already exist so the later workspace decision is grounded in the actual files.

### 2. Handout And Source Readiness

- Look for the handout under `AI_works/resources/experiment_handout/Modern Physics Experiments/`.
- If the handout is missing, ask whether to provide one, continue without it, or stop.
- If a handout PDF exists, use `$mineru-pdf-json` unless the decoded marker already exists under `pdf_decoded/`.
- After decoding, run `scripts/extract_decoded_sections.py` so later drafting uses normalized section blocks instead of raw MinerU output.
- Inspect the decoded handout for picture-result analysis requirements, required recorded photos, equipment details, section structure, procedure steps, data expectations, and signatory-page expectations.
- If the handout requires picture-result analysis, look for the matching files under `AI_works/resources/experiment_pic_results/`.
- If required picture-result files are missing, ask whether to provide them, continue with explicit placeholders, or stop.
- Find matching reference reports under `AI_works/resources/lab_report_reference/Modern Physics Experiments/`, decode them when needed, and use them only to learn structure and depth, not to invent claims.

### 3. Workspace, Template, And Core Report Contract

- Use `AI_works/results/<experiment-safe-name>/` as the workspace. Reuse the same experiment folder instead of creating timestamp variants.
- Run `scripts/ensure_report_workspace.py` only after the user confirms whether the report should be modified in place, rewritten from a fresh template, or left untouched.
- Treat `main.tex` as the canonical report file for new work.
- If the result folder already has multiple `.tex` files and none is `main.tex`, ask which file is canonical before running the workspace script.
- Search templates under `AI_works/resources/latex_templet/`.
- Exclude directories literally named `dont use` from default template choices unless the user asks for a wider search.
- The default active template is `tau_templet copy.tex`.
- Keep the generated procedures file in the report folder as `<experiment-safe-name>_procedures.md`.
- Mirror each procedure ID in the TeX source with comments like `% procedure:P01`. Do the same for placeholder gaps.
- Add this light-red placeholder macro near the preamble if it is missing:

```tex
\definecolor{NeedsInputRed}{RGB}{220,110,110}
\newcommand{\NeedsInput}[1]{\textcolor{NeedsInputRed}{#1}}
```

- Use `\NeedsInput{...}` for every unanswered field, missing datum, missing figure, missing code block, or missing signatory page placeholder.

### 4. Metadata And Report Configuration

- Before asking repeated identity questions, run `scripts/manage_author_profile.py`.
- Use `AI_works/resources/report_author_profile.json` as the default reusable profile unless the user explicitly overrides it.
- If the profile file is missing, create it automatically with blank fields instead of failing.
- Ask the user whether the report is English or Chinese before filling in names and metadata.
- Load stored student and collaborator names plus affiliations when they exist.
- Ask only for missing or changed profile fields, the report language, and the instructor title or name that still need confirmation.
- Do not draft the title block until the required metadata answers are present.
- After the user corrects metadata, write those updates back into the author-profile file so later experiments can reuse them.
- Read [metadata_rules.md](./references/metadata_rules.md) before editing the title block or front matter.

### 5. Build The Body Scaffold From The Handout

- Use the normalized handout sections first. Use reference reports only to calibrate structure depth, not to invent content.
- If the template is missing sections, insert them in this order:
  - Introduction
  - Objectives
  - Experiment Equipment
  - Experiment Principle
  - Experimental Process / Experimental Phenomenon
  - Experiment Discussion
  - Appendix
  - References
- Use the handout introduction as source material for the Introduction and as seed notes for the eventual abstract, but do not finalize the abstract yet.
- Use the handout objective or aim section for the Objectives section.
- Summarize keyword candidates from the handout introduction when the template has a keywords block.
- Read the handout procedure carefully and extract the steps into `<experiment-safe-name>_procedures.md` with stable IDs `P01`, `P02`, and so on.
- Structure the Experimental Process / Experimental Phenomenon section strictly against those procedure steps.
- Every procedure step must appear in the TeX either as completed content or as an explicit placeholder with a matching `% procedure:Pxx` comment.
- Build the equipment section from handout mentions and decoded tables.

### 6. Transfer Data And Pause For User Validation

- Data usually lives under `AI_works/resources/experiment_data/`.
- If no data files are found, ask whether to provide data now, continue with explicit placeholders, or stop.
- Read text, csv, tsv, xls, and xlsx sources directly when possible.
- For PDF data, inspect the pages visually first and transcribe them to markdown. If the transcription looks weak or contradictory, decode the PDF with `$mineru-pdf-json` and compare the JSON to the visual markdown before asking the user about ambiguous values.
- For image data, inspect visually and transcribe to markdown.
- During visual data transfer, preserve handwritten Chinese words or sentences that record experimental phenomena, qualitative judgments, or observational comments.
- Translate those Chinese notes into English and keep both the original note and the translation near the relevant sample or page.
- If a Chinese note is only partially legible, preserve the visible text, give a best-effort English translation with an uncertainty note, and ask the user before treating it as final.
- Save transferred markdown as `<data-parent>/data_transferred/<experiment-safe-name>_data.md`.
- Show the transferred markdown to the user and do not continue to calculations until they confirm it is correct.

### 7. Stage Images Early And Control The PDF Size Budget

- Stage principle figures into `AI_works/results/<experiment-safe-name>/principle-images/` with `scripts/stage_principle_images.py`.
- Stage experiment picture results into `AI_works/results/<experiment-safe-name>/picture-results/` when the handout requires photographed or recorded observations.
- Immediately convert `picture_results_manifest.json` into `picture_evidence_plan.json` and `picture_evidence_plan.md` with `scripts/plan_picture_evidence.py`.
- Stage signatory pages into `AI_works/results/<experiment-safe-name>/signatory-pages/` when they exist.
- When decoded captions show related `(a)`, `(b)`, `(c)` markers under the same context, place them together as subfigures under one parent figure instead of splitting them apart.
- When several picture-result files share the same observation-method base name and differ only by serial number, group them as one ordered process figure and preserve the serial order.
- If figure grouping is uncertain, pause and ask the user instead of guessing.
- Use the evidence plan as the default source of truth for which method groups belong in each `results.tex` subsection.
- Mirror each planned evidence unit with `% evidence:<group_id>` markers near the analysis paragraph and again near the local figure block so QC can verify coverage and placement.
- If grouped subfigures are emitted and the template does not already support them, add `\usepackage{subcaption}` or the template-equivalent package before compiling.
- As soon as the staged raster-image pool is available, estimate whether those assets are likely to push the final PDF past `20 MB`.
- Treat text, equations, and ordinary TeX source as minor compared with raster-image size. Manage the image pool early instead of waiting for the final compile to fail the size target.
- If staged PNG assets are too large, use the `compress-png` skill before image insertion or final layout:
  - audit first,
  - write compressed copies first,
  - prefer `256` colors first,
  - escalate only when needed,
  - replace originals only after a representative visual check.
- Keep the combined staged image assets comfortably below the final `20 MB` PDF cap because the final PDF must still leave room for non-image content.
- Do not switch PNG assets to JPEG unless the user explicitly asks.

### 8. Enter Parallel Analysis Mode

- Stay sequential through discovery, source readiness, workspace setup, metadata, transferred-data confirmation, picture staging, and evidence-plan generation.
- Do not enter `Parallel Analysis Mode` until all of the following are true:
  - the experiment is confirmed,
  - the canonical TeX file is known,
  - the transferred data is user-validated,
  - picture-result staging is complete, and
  - `picture_evidence_plan.json` exists.
- When those prerequisites are stable, treat `AI_works/results/<experiment-safe-name>/parallel-run/` as the shared coordination directory for this run.
- Refresh or clear `parallel-run/` at the start of each new run so stale assignments, merge notes, or wave summaries do not leak into the next experiment.
- Before dispatching workers, insert stable owned-region markers into `main.tex` or the relevant split TeX files, for example:

```tex
% region:results:z-cut:begin
% region:results:z-cut:group_ids=z_cut_primary,z_cut_wedge
...
% region:results:z-cut:end
```

- Use the same pattern for `Further Discussion` regions, for example `% region:further-discussion:anomalies:begin` and `% region:further-discussion:anomalies:end`.
- Keep nearby ownership metadata readable. At minimum record the owned `group_id` values, owned `candidate_id` values when relevant, and any blocked adjacent regions.
- Workers may edit only inside owned regions unless the controller explicitly expands their scope.
- If a worker discovers it needs preamble edits, global section reordering, or another worker's region, it must stop and escalate to the controller instead of making that change opportunistically.
- Keep the orchestration rules easy to find during a live run:
  - [parallel_workflow.md](./references/parallel_workflow.md)
  - [shared_draft_contract.md](./references/shared_draft_contract.md)
  - [worker_prompt_template.md](./references/worker_prompt_template.md)
  - [controller_checkpoints.md](./references/controller_checkpoints.md)

#### Wave A: Results Subsection Drafting

- Group work by independent `target_subsection` values or by another evidence-family boundary that maps cleanly to the current report structure.
- As the default sizing rule, launch `2` workers when the evidence plan yields only a couple of substantial subsection clusters, and `3` workers when there are at least three clearly isolated subsection clusters with non-overlapping ownership.
- Only keep a smaller Wave A when the evidence plan does not offer a second cleanly isolated subsection cluster.
- Prepare the entire wave before dispatching:
  - write `parallel_wave_plan.md`,
  - write one assignment file per worker under `parallel-run/parallel_assignments/`,
  - and make the allowed files plus blocked files explicit.
- Dispatch the whole wave together. Do not spawn one worker, wait, then spawn the next worker when the subsection work is independent.
- Wave A workers may draft:
  - local analysis paragraphs,
  - local grouped figure blocks,
  - `% evidence:<group_id>` markers near the analysis paragraph and near the local figure block,
  - and subsection-local labels or references inside the same owned region.
- Wave A workers may not draft front matter, global discussion text, another worker's results region, or global structure.

#### Checkpoint A

- After Wave A returns, the controller reconciles only at the checkpoint.
- Verify that each owned region was touched only by its owner.
- Verify that every owned `group_id` has nearby local evidence coverage and that the figure block stays in the same subsection as its analysis.
- If a subsection boundary is not clean enough for safe ownership, stop parallel drafting for that slice and finish it sequentially.

#### Wave B: Further Discussion And Synthesis

- After the subsection-local evidence regions stabilize, dispatch a smaller wave for high-level interpretation.
- Typical Wave B workers include:
  - one anomaly-backed discussion worker,
  - one material-specific interpretation worker,
  - and one comparison-to-common-outcomes worker when the experiment needs it.
- Wave B workers edit only owned `Further Discussion` regions and any explicitly assigned summary region.
- Keep `discussion_candidates.json` as the source of truth for what this wave is allowed to claim.

#### Checkpoint B

- After Wave B returns, verify that every `Further Discussion` claim maps back to `discussion_candidates.json`.
- Verify that every `candidate_id` points to owned `group_id` values or explicit anomaly signals.
- Verify that wording strength still matches candidate confidence and that unresolved conflicts remain visible instead of being normalized away.

#### Wave C: QC And Local Repair

- Use a final mid-run wave for targeted checks and localized repair before the ordinary compile-and-handoff loop.
- Typical Wave C workers include:
  - one evidence-placement checker,
  - one reasoning-strength and placeholder-hygiene checker,
  - and one repair worker when the controller decides the fixes are sufficiently localized.
- If ownership becomes ambiguous, or if the fix cuts across several regions, stop the wave and let the controller handle the repair sequentially.

### 9. Generate Results And Analyze Them

- After the user confirms the transferred data, search for corresponding normal results, reference ranges, theoretical expectations, or literature values for the same experiment.
- Compare the confirmed data against those sourced reference results and judge which important results are normal and which are anomalous.
- If a result looks anomalous, keep the measured value visible, attach the sourced reference value with citation, and carry the anomaly note into the Experimental Process / Results section.
- Save processed markdown as `<data-parent>/data_processed/<experiment-safe-name>_data_processed.md`.
- Use `scripts/compute_uncertainties.py` after the data markdown is confirmed.
- Default the expanded-uncertainty coverage factor to `k=2`. Ask only when the experiment explicitly requires a different value.
- Build an explicit result inventory from all available evidence: processed data, handwritten phenomenon notes, standalone result pictures, grouped process-picture sequences, and method-specific result pictures.
- Every recorded result in that inventory must be mentioned somewhere in the lab report, even if it seems minor, repetitive, or only qualitative.
- When one sample was observed under several methods, each method-specific result must be mentioned separately instead of letting one clearer method hide the others.
- Draft the Results section from subsection-local analysis blocks instead of long prose followed by pooled floats:
  - one evidence unit or one tightly related cluster,
  - the analysis paragraph,
  - the grouped figure block in the same subsection,
  - and cross-sample tables only when they truly summarize multiple units.
- Use vision on each local picture-result file to identify the visible features, labels, colors, patterns, interference figures, or material-dependent structures that the handout asks you to analyze.
- When the handout calls for interpretation of those pictures, combine the local vision readout with cited internet findings and surface any conflict to the user instead of hiding it.
- When an indirect result is reported, show how it was obtained instead of giving only the final value or conclusion. Include the needed observations, comparison logic, equations, or short tables.

### 10. Write Discussion, Appendix, And References

- Before writing the discussion, thoroughly review the matched local reference reports for the same experiment so you understand the expected level of interpretation and reliability analysis.
- Search for education papers, teaching papers, experiment-teaching notes, and other experiment-specific discussion sources that explain what the experiment is meant to show, which observations matter most, what mistakes are common, and how reliability is usually judged.
- Write a real judgment of the user's experiment result: `reliable`, `partially reliable`, or `unreliable`, and defend that judgment with concrete evidence from the report.
- Push the discussion beyond a short generic paragraph. Add deeper physical interpretation, comparison with theory, comparison with literature expectations, error-source analysis, and specific improvement suggestions when the experiment supports them.
- After the standard discussion is stable, run `scripts/build_discussion_candidates.py` to create `discussion_candidates.json` and `discussion_candidates.md`.
- Add a dedicated `Further Discussion` section after the normal discussion whenever meaningful candidates exist.
- Treat those candidates as the approved starting points for beyond-handout interpretation instead of inventing freeform speculation.
- Distinguish clearly between observed fact, supported interpretation, and tentative hypothesis.
- Use balanced confidence-aware wording: direct claims only when evidence and sources line up clearly; otherwise prefer wording such as `is consistent with`, `likely indicates`, or `may indicate`.
- Always try to discuss vague images, material-specific behavior, and anomalies when the report evidence supports it, but keep uncertainty explicit instead of hiding it.
- Use moderate targeted outside lookup for those `Further Discussion` cases instead of a broad literature sweep.
- Never rewrite anomalies into agreement just because the handout or outside sources suggest a cleaner result.
- Create a dedicated Discussion subsection named `Assigned Thinking Questions`.
- Format each assigned thinking question as the numbered question first, followed by the answer on the next line or paragraph.
- Answer sourced thinking-question claims with real external citations and keep those non-senior sources in the references section.
- Restrict the Appendix to `Code` and `Signature Pages`.
- If code is missing, leave a `\NeedsInput{...}` placeholder in the `Code` subsection.
- If signatory pages exist, insert them in `Signature Pages` as grouped full-width appendix figure blocks. If they do not exist, leave a `\NeedsInput{...}` placeholder there instead.
- Keep non-reference-report external sources in the references section using the template's existing bibliography backend when possible.

### 11. Compile, Review, And Hand Off

- Copy or refresh the workspace `build.sh` from `assets/build.sh`.
- Write or rewrite the abstract only after the body, discussion, appendix, and references are stable.
- Finalize the abstract before the catalogue is inserted or refreshed.
- After the full section tree is stable, insert or refresh the catalogue between the keywords block and the Introduction. If the template has no keywords block, place it after the front matter and before the first body section.
- Use a hyperlinked catalogue so every section and subsection entry jumps to its destination. Add `\usepackage[hidelinks]{hyperref}` if needed.
- Compile with `bash build.sh`.
- The final PDF must be no larger than `20 MB`.
- If the compiled PDF still exceeds `20 MB`, revisit the staged image pool, compress oversized PNG assets with `compress-png`, rebuild, and re-check before handoff.
- Decode the compiled PDF with `$mineru-pdf-json` when practical so the review pass can inspect the generated document, not only the source.
- Run `scripts/report_qc.py` against the current `main.tex`, procedures markdown, evidence plan, and discussion candidates.
- Re-open the TeX if QC finds missing procedure IDs, forbidden phrases, irrelevant leftover text, appendix-only violations, placeholder spillover, table-layout risks, or narrative-tone leakage.
- Re-open the TeX if QC warns that planned evidence groups never reached the draft, `% evidence:<group_id>` placement markers are incomplete, `Further Discussion` lacks candidate backing, or low-confidence reasoning is written with overly strong certainty.
- Do one final scan for AI, automation, provenance wording, status-log phrasing, or tool-perspective narration anywhere in the TeX source, including comments and captions, and remove it unless it is a neutral structural marker that the skill explicitly requires.
- End by showing the PDF and explicitly listing any remaining missing data, missing figures, failed procedures, or unresolved interpretation conflicts.

## Capability Preservation Map

Use this map to verify that the execution-first rewrite did not drop required functions.

- Source discovery and experiment confirmation: `scripts/discover_sources.py`, [workflow_checklist.md](./references/workflow_checklist.md)
- Handout decoding and normalized section extraction: `$mineru-pdf-json`, `scripts/extract_decoded_sections.py`
- Workspace reuse, canonical-file handling, template selection, and placeholder macros: `scripts/ensure_report_workspace.py`, [metadata_rules.md](./references/metadata_rules.md)
- Reusable author metadata and language gating: `scripts/manage_author_profile.py`, [metadata_rules.md](./references/metadata_rules.md)
- Procedure extraction, section order, and `% procedure:Pxx` coverage: [workflow_checklist.md](./references/workflow_checklist.md), `scripts/report_qc.py`
- Data transfer, handwritten Chinese-note preservation, translation checks, and processed-data output: [workflow_checklist.md](./references/workflow_checklist.md)
- Principle-image staging, picture-result staging, evidence planning, signatory-page staging, and grouped-figure rules: `scripts/stage_principle_images.py`, `scripts/stage_picture_results.py`, `scripts/plan_picture_evidence.py`, `scripts/stage_signatory_pages.py`
- Early PNG compression and PDF-size budgeting: `compress-png`, [workflow_checklist.md](./references/workflow_checklist.md), [quality_gate.md](./references/quality_gate.md)
- Parallel-wave orchestration, shared-draft safety, worker prompts, and checkpoint behavior: [parallel_workflow.md](./references/parallel_workflow.md), [shared_draft_contract.md](./references/shared_draft_contract.md), [worker_prompt_template.md](./references/worker_prompt_template.md), [controller_checkpoints.md](./references/controller_checkpoints.md)
- Uncertainty calculation, anomaly checks, result inventory completeness, indirect-result derivation, and further-discussion candidate shaping: `scripts/compute_uncertainties.py`, `scripts/build_discussion_candidates.py`, [quality_gate.md](./references/quality_gate.md)
- Discussion depth, appendix rules, catalogue placement, provenance bans, compile, QC, PDF review, and handoff gaps: [report_structure.md](./references/report_structure.md), [quality_gate.md](./references/quality_gate.md), `scripts/report_qc.py`

## Non-Negotiable Rules

- Never fabricate measurements, figures, model numbers, procedure outcomes, or conclusions.
- Keep unresolved values as `\NeedsInput{TBD: ...}`.
- Keep unresolved figures as empty placeholders with a nearby `\NeedsInput{...}` marker.
- Render every unresolved answer, `TBD`, or missing item in light red through `\NeedsInput{...}`.
- Do not skip the author-profile load or create step, the missing-field questions, or the missing-data questions.
- Do not let handout-backed content get overridden by a senior report.
- Do not cite or mention senior reports in the final TeX.
- Do not skip decoded handout figures when the handout uses them in the Experiment Principle section.
- Do not leave principle figures unmentioned in nearby body text.
- Do not omit required experiment picture results when the handout says they should be photographed, recorded, or presented.
- Do not guess ambiguous picture grouping.
- Do not let workers edit outside owned regions during `Parallel Analysis Mode` unless the controller explicitly reassigns scope.
- Do not let wide or tall tables overflow the two-column layout when wrapped columns, logical splits, or continuation tables would solve the problem.
- Do not leave AI tone, workflow narration, status logs, tool perspective, or provenance phrasing in the report source or compiled text.
- Do not hand off a PDF larger than `20 MB`.

## Resources

- Read [workflow_checklist.md](./references/workflow_checklist.md) for the exact run order and file naming conventions.
- Read [metadata_rules.md](./references/metadata_rules.md) before editing the title block, author block, abstract, or front matter.
- Read [report_structure.md](./references/report_structure.md) before deciding the final section layout.
- Read [quality_gate.md](./references/quality_gate.md) before the compile-and-review loop.
- Read [parallel_workflow.md](./references/parallel_workflow.md), [shared_draft_contract.md](./references/shared_draft_contract.md), [worker_prompt_template.md](./references/worker_prompt_template.md), and [controller_checkpoints.md](./references/controller_checkpoints.md) before using `Parallel Analysis Mode`.
- Use `scripts/discover_sources.py`, `scripts/ensure_report_workspace.py`, `scripts/manage_author_profile.py`, `scripts/extract_decoded_sections.py`, `scripts/stage_principle_images.py`, `scripts/stage_picture_results.py`, `scripts/plan_picture_evidence.py`, `scripts/stage_signatory_pages.py`, `scripts/compute_uncertainties.py`, `scripts/build_discussion_candidates.py`, and `scripts/report_qc.py` instead of rewriting their logic inline.
- Use the `compress-png` skill when staged PNG assets threaten the final PDF size target.
