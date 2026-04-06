# Quality Gate

Use this checklist before handoff.

## Source And Setup Integrity

- The course name was confirmed before discovery or front-matter drafting.
- The experiment was confirmed with the user.
- The chosen template was confirmed with the user for the current run.
- The template choices were drawn from `AI_works/resources/latex_templet/` with `dont use` paths excluded by default.
- The report workspace uses `AI_works/results/<experiment-safe-name>/`.
- The canonical report file is correct.
- The author profile was loaded or created at `AI_works/resources/report_author_profile.json`.
- The author profile was treated as shared cross-course person metadata rather than as a store for course identity.
- Student and collaborator metadata from the current run was written back into the author profile when it changed.
- Handout-backed sections come from the handout before any senior report is consulted.

## Narrative And Tone Hygiene

- The report reads like a normal lab report written from the experimenter's point of view.
- The TeX source and compiled report do not mention AI, Codex, ChatGPT, OpenAI, MinerU, automatic generation, decoded JSON, or similar drafting provenance.
- The report does not contain workflow narration, tool perspective, or status-log phrasing such as "this report was generated", "the following content was extracted", or similar meta narration.
- The abstract was finalized from the completed report content after the main writing was done.
- The abstract does not mention official handouts, notebook pages, transferred-data status, missing confirmations, or report-generation workflow.
- Table titles and figure captions describe experiment content rather than where the content was extracted, decoded, or transcribed from.
- The TeX source does not contain redundant empty lines between adjacent commands or already-distinct formatted blocks.

## Principle Figures And Result Pictures

- Experiments that require picture-result analysis were checked for matching files under `AI_works/resources/experiment_pic_results/`.
- Required picture-result analysis was based on actual local visual inspection rather than invented description.
- When the handout demanded interpretation of picture results, the analysis combined local vision findings with cited internet research of the relevant material or figure type.
- Any unresolved conflict between internet interpretation and local picture reading was surfaced to the user.
- When the handout required photographed or recorded observation pictures, those actual picture results were inserted into the relevant report subsection instead of being left as text-only discussion.
- Picture-result files that share the same observation-method base name and differ only by serial number are grouped together as one ordered process figure rather than scattered as unrelated images.
- The grouped process figure preserves the original serial order so the reader can follow rotation or step-by-step changes.
- When a grouped picture sequence records a process such as quartz-wedge insertion, the prose explains the evolution across the sequence clearly rather than only showing the images.
- Principle images from the decoded handout were checked and staged into the report workspace.
- Principle figures appear in the Experiment Principle section with descriptive captions from the handout image titles.
- Related `(a)`, `(b)`, `(c)` images are grouped as subfigures under one parent figure when that grouping is supported by the decoded captions or filenames.
- When grouped subfigures were needed and the template did not already support them, `subcaption` or the template-equivalent package was added before compiling.
- Those captions do not duplicate figure serial numbers when the template already numbers figures automatically.
- Each principle figure appears in the correct matching subsection, not as a detached image gallery.
- Each principle figure is referenced in nearby body text, ideally through `Fig.~\ref{...}` or the template's equivalent.
- Figures that act as schematic diagrams in the handout are explicitly introduced as schematic diagrams in the surrounding prose.
- Ambiguous picture-grouping cases were surfaced to the user instead of being guessed.
- Figure environments are not padded with gratuitous empty lines before or after the block.

## Data And Result Integrity

- Handwritten Chinese phenomenon notes in the raw data were preserved during transfer and accompanied by English translations in the transferred markdown.
- Uncertain translations of handwritten observation notes were surfaced to the user instead of silently normalized away.
- After the user confirmed the transferred data, important measured or inferred results were compared against sourced normal results, literature values, or theoretical expectations from the internet.
- Anomalous confirmed results were marked explicitly instead of being silently normalized away.
- When a result was anomalous, the report kept the user's measured value visible, attached the sourced reference value with citation, and analyzed likely reasons in the Experimental Process / Results section.
- Every recorded result is mentioned somewhere in the report, including minor qualitative observations, trivial phenomena, and method-specific result pictures.
- When one sample has results from several methods, each method-specific result is mentioned separately instead of allowing one clearer method to hide the others.
- Indirect results are not reported as bare conclusions; the report shows how they were obtained from the underlying observations or calculations.
- When the experiment uses inference logic such as complementary-color reasoning, the relevant intermediate observations and reasoning steps are written explicitly.
- Procedure IDs exist in the procedures markdown and are mirrored in TeX comments.

## Parallel Orchestration Integrity

- `Parallel Analysis Mode` was used only after the experiment was confirmed, the canonical TeX file was known, transferred data was user-validated, picture staging was complete, and `picture_evidence_plan.json` existed.
- `AI_works/results/<experiment-safe-name>/parallel-run/` existed when parallel mode was used.
- Stale `parallel-run/` artifacts were refreshed or cleared before the current run started.
- Owned region markers existed before write-capable workers were dispatched.
- Workers edited only owned regions unless the controller explicitly reassigned scope.
- `% evidence:<group_id>` coverage stayed near the owned subsection analysis and nearby figure block after checkpoint merges.
- `Further Discussion` claims remained candidate-backed after Wave B reconciliation instead of drifting into free speculation.
- Low-confidence candidates were not rewritten with overly strong certainty during or after parallel drafting.
- Preamble edits, section reordering, and other global-structure changes were escalated to the controller instead of being made opportunistically by workers.
- When subsection boundaries or ownership became ambiguous, the affected slice was downgraded to sequential fallback instead of forcing overlapping parallel edits.

## Layout, Tables, And Catalogue

- A catalogue or table of contents exists between the keywords block and the first body section, or after the front matter when no keywords block exists.
- The catalogue links to sections and subsections.
- Ordinary tables fit the two-column template instead of overflowing the column boundary.
- Wide tables were first handled with wrapped columns, shorter headers, sensible rounding, or local font reduction before any full-width fallback was used.
- Tables that were still too wide or too tall were split into logical continuation tables instead of being left unreadable.
- `longtable` is not used in the two-column report template.
- Any `table*` usage was deliberate, limited, and justified by real both-column content rather than used as the default fix.

## Placeholders, Appendix, And References

- Missing data and missing figures are marked as `TBD` instead of fabricated.
- Every unresolved placeholder is rendered in light red through `\NeedsInput{...}` or an equivalent light-red `\textcolor{...}` wrapper.
- Sidebar-only messages such as `Items Needed To Replace The Draft Placeholders` and `Suggested Raw-Data Tables` were not inserted into the TeX.
- The discussion is not just a short generic paragraph; it uses local reference reports plus cited external literature, especially experiment-teaching or education papers when available, to set expectations for what the experiment should discuss.
- The discussion makes an explicit judgment of the result as reliable, partially reliable, or unreliable.
- The discussion compares the user's results with theory or literature expectations.
- The discussion identifies concrete error sources or limitations.
- The discussion includes specific improvement suggestions or further physical interpretation when the experiment supports them.
- The report body does not mention `reference report`, `senior report`, `学长`, or similar phrases.
- The appendix contains only `Code` and `Signature Pages`, with placeholders if either is still missing.
- When signatory pages exist, they appear in `Signature Pages` as grouped full-width appendix figure blocks rather than oversized page-by-page inserts.
- The signatory-page layout uses two pages per row and about 4 to 8 pages per figure block or appendix page when the page count allows it.
- The signatory-page group uses subfigure serial markers `(a)`, `(b)`, `(c)` across the grouped layout.
- The `Assigned Thinking Questions` subsection lists each question before its answer.
- Sourced thinking-question answers use real external citations.
- Non-senior external references are listed in the references section.

## PDF Size And Final Verification

- Staged raster-image assets were audited early enough to estimate whether they threatened the final PDF size.
- Oversized PNG result assets were compressed with the `compress-png` skill when needed instead of waiting until the end.
- PNG compression was handled conservatively: audit first, copies first, representative visual check before replacement.
- The report was compiled with `build.sh`.
- `scripts/report_qc.py` has been run on the current TeX and procedures files.
- The compiled PDF was reviewed, ideally after MinerU decoding.
- The final PDF size is no larger than `20 MB`.
- The final handoff explicitly lists any remaining missing data, missing figures, failed procedures, or unresolved interpretation conflicts.
