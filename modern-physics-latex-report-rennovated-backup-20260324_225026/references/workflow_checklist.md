# Workflow Checklist

Use this file as the run-order contract.

## Phase 1: Preflight And Discovery

1. Confirm the experiment from discovered candidates before mutating files.
2. If discovery is weak, show the candidate list instead of pretending the match is certain.
3. Detect the existing result folder and existing `.tex` files before proposing modify, rewrite, or stop.
4. If multiple report `.tex` files exist and none is `main.tex`, ask which file is canonical before running the workspace script.
5. Ask whether to modify in place, rewrite from a fresh template, or stop before the workspace is touched.

## Phase 2: Handout And Source Readiness

6. Find the handout.
7. If the handout is missing, ask whether to provide one, continue without it, or stop.
8. Decode the handout with `$mineru-pdf-json` when no decoded marker exists.
9. Normalize the decoded handout with `scripts/extract_decoded_sections.py`.
10. Check from the handout whether the experiment requires picture-result analysis.
11. Check from the handout whether recorded result pictures or signatory pages will be required later.
12. Find reference reports and decode them when needed.
13. Review the heading structure across the reference-report pool to learn the common report backbone before drafting.
14. If the handout needs picture-result analysis, find the corresponding files under `AI_works/resources/experiment_pic_results/`.
15. If required picture-result files are missing, ask whether to provide them, continue with placeholders, or stop.

## Phase 3: Workspace, Template, And Core Report Contract

16. Ensure `AI_works/results/<experiment-safe-name>/`.
17. Confirm the chosen template before copying it into the workspace.
18. Discover template candidates under `AI_works/resources/latex_templet/`.
19. Exclude templates under directories named `dont use` by default.
20. Use `tau_templet copy.tex` as the default template candidate unless the user chooses otherwise.
21. Keep the procedures markdown file as `AI_works/results/<experiment-safe-name>/<experiment-safe-name>_procedures.md`.
22. Add a `\NeedsInput{...}` macro in the preamble if the template does not already define one.
23. Render every unanswered field and every `TBD` item in light red with that macro.
24. Mirror each procedure ID in TeX comments such as `% procedure:P01`.
25. Mirror each placeholder gap with its own nearby comment.

## Phase 4: Metadata And Front-Matter Setup

26. Create or load `AI_works/resources/report_author_profile.json`.
27. If the profile file is missing, create it automatically and then ask only for the missing values.
28. Ask for the report language before drafting the title block.
29. Ask only for missing or changed student, collaborator, affiliation, and instructor fields.
30. Do not draft the title block until the metadata answers are present.
31. Write corrected student and collaborator metadata back into the author profile for reuse.

## Phase 5: Handout-Driven Body Scaffold

32. Use normalized handout sections before any reference report wording.
33. Insert missing sections in this order: Introduction, Objectives, Experiment Equipment, Experiment Principle, Experimental Process / Experimental Phenomenon, Experiment Discussion, Appendix, References.
34. Use the handout introduction as source material for the Introduction and as seed notes for the later abstract.
35. Use the handout objective or aim section for the Objectives section.
36. Summarize keyword candidates from the handout introduction when the template has a keywords block.
37. Extract procedure steps into `<experiment-safe-name>_procedures.md`.
38. Prefix every extracted step with `P01`, `P02`, and so on.
39. Structure the Experimental Process / Experimental Phenomenon section strictly against those procedure steps.
40. Every procedure step must appear in the TeX either as completed content or as an explicit placeholder with a matching `% procedure:Pxx` comment.
41. Build the equipment section from handout mentions and decoded tables.
42. If equipment models or counts are missing and no data files supply them, ask whether to provide more data, continue with `TBD`, or stop.

## Phase 6: Data Transfer And User Validation

43. If experiment data is missing, ask whether to provide data now, continue with `TBD`, or stop.
44. Read text, csv, tsv, xls, and xlsx sources directly when possible.
45. For PDF data, inspect the pages visually first and decode only when the transcription is weak or contradictory.
46. For image data, inspect visually and transcribe to markdown.
47. Preserve handwritten Chinese phenomenon notes and add English translations in the transferred markdown.
48. Keep those translated observation notes near the relevant sample or page instead of moving them into a detached miscellaneous section.
49. If any translated phenomenon note is uncertain, show that uncertainty to the user before using it as a final observation.
50. Save transferred markdown as `<data-parent>/data_transferred/<experiment-safe-name>_data.md`.
51. Stop for user confirmation before calculations, uncertainty work, anomaly judgments, or results drafting.

## Phase 7: Image Staging And Early PDF-Size Control

52. Stage principle figures from the decoded handout into `AI_works/results/<experiment-safe-name>/principle-images/`.
53. Insert those principle figures into the matching principle subsection instead of collecting them as a gallery at the section end.
54. Mention each principle figure in nearby prose with a label-based reference, and call it a schematic diagram when that matches the handout's role.
55. Group related `(a)`, `(b)`, `(c)` principle images into one parent figure with subfigures when the decoded captions or filenames clearly support that grouping.
56. If picture grouping is uncertain, pause and ask the user which pictures belong together before generating that figure block.
57. If grouped subfigures are emitted and the template does not already support them, add `\usepackage{subcaption}` or the template-equivalent package before compiling.
58. Stage experiment picture-result files into `AI_works/results/<experiment-safe-name>/picture-results/` when the handout requires photographed or recorded observations.
59. Stage signatory pages into `AI_works/results/<experiment-safe-name>/signatory-pages/` when they exist.
60. When several picture-result files share the same base observation name and differ only by serial number, group them as one ordered process figure rather than scattering them as unrelated images.
61. Preserve the original serial order in grouped process figures so the reader can follow the change across the sequence.
62. As soon as the staged raster-image pool is available, estimate whether those assets are likely to push the final PDF past `20 MB`.
63. Treat image assets as the main PDF-size driver because pure text and ordinary TeX take much less space.
64. If the staged image pool is too large, compress oversized PNG assets early with the `compress-png` skill instead of waiting for the final PDF to fail the size gate.
65. Start PNG compression conservatively: audit first, write compressed copies first, prefer `256` colors first, and escalate only when needed.
66. Replace original PNG files only after checking representative compressed outputs.
67. Do not switch those PNG assets to JPEG unless the user explicitly asks.

## Phase 8: Parallel Analysis Mode

68. Stay sequential through discovery, source readiness, workspace setup, metadata, transferred-data confirmation, picture staging, and evidence-plan generation.
69. Enter parallel mode only when the experiment is confirmed, the canonical TeX file is known, transferred data is user-validated, picture-result staging is complete, and `picture_evidence_plan.json` exists.
70. Refresh or clear `AI_works/results/<experiment-safe-name>/parallel-run/` before writing new assignments for the current run.
71. Insert stable region markers into the active draft before dispatching any write-capable workers.
72. Record nearby ownership metadata for each region, including owned `group_id` values, owned `candidate_id` values when relevant, and blocked adjacent regions.
73. Write `parallel_wave_plan.md` plus one assignment file per worker under `parallel-run/parallel_assignments/`.
74. Dispatch all workers for the current wave before waiting on the checkpoint when the work is independent.
75. Use Wave A for subsection-local results drafting with clean ownership by `target_subsection` or another evidence-family boundary.
76. At Checkpoint A, verify owned-region boundaries, nearby `% evidence:<group_id>` coverage, and subsection-local figure placement before moving on.
77. Use Wave B for owned `Further Discussion` regions that synthesize anomaly-backed, material-specific, or comparison-backed interpretation from `discussion_candidates.json`.
78. At Checkpoint B, verify candidate-backed claims, confidence-aware wording, and visible unresolved conflicts.
79. Use Wave C for targeted QC and localized repair only when the fix still fits clear ownership boundaries.
80. If subsection boundaries, ownership, or required edits stop being cleanly isolatable, downgrade the affected slice to sequential work instead of forcing parallel edits.

## Phase 9: Results Generation And Analysis

81. After the user confirms the transferred data, search for corresponding normal results, reference ranges, theoretical expectations, or literature values on the internet.
82. Compare the confirmed data against those sourced reference results and judge which important results are normal and which are anomalous.
83. If a result is anomalous, keep the measured value visible, attach the sourced reference result with citation, and prepare an anomaly note for the Experimental Process / Results section.
84. Save processed markdown as `<data-parent>/data_processed/<experiment-safe-name>_data_processed.md`.
85. Use `scripts/compute_uncertainties.py` after the markdown is confirmed.
86. Default the expanded-uncertainty coverage factor to `k=2` unless the experiment explicitly requires a different value.
87. Build an explicit result inventory from all available evidence: processed data, handwritten notes, standalone result pictures, grouped process sequences, and method-specific result pictures.
88. Make sure every item in that inventory is mentioned in the report text or marked with a local placeholder if the evidence is still missing or unclear.
89. When one sample has pictures from different methods, mention each method separately instead of letting one clearer method hide the others.
90. When a grouped picture sequence records a process such as rotation or quartz-wedge insertion, describe the evolution across the sequence clearly in prose.
91. When an indirect result is reported, write its derivation path in the report instead of only the final inferred value.
92. Include the intermediate observations, comparison logic, and equations or calculation steps that lead to that indirect result.
93. If the handout demands interpretation of picture results, combine local visual inspection with cited external reference analysis and surface any conflict to the user.

## Phase 10: Discussion, Appendix, And References

94. Before writing the discussion, thoroughly review the matched local reference reports for the same experiment.
95. Search for education papers, teaching papers, and experiment-specific discussion sources that explain what the experiment is meant to demonstrate and what a strong report should discuss.
96. Use those sources to judge the user's result as reliable, partially reliable, or unreliable, and write the reasons explicitly.
97. Compare the report's observations and results against theory, literature expectations, and common error patterns from those sources.
98. Expand the discussion with error sources, limitations, physical interpretation, and improvement suggestions instead of stopping at a short generic paragraph.
99. Create a dedicated subsection named `Assigned Thinking Questions`.
100. Format each assigned thinking question as the numbered question first, followed by its answer.
101. Answer sourced thinking-question claims with real external citations and include those non-senior sources in the references section.
102. Restrict the Appendix to `Code` and `Signature Pages`.
103. If code is still missing, leave a `\NeedsInput{...}` placeholder inside the `Code` subsection.
104. If signatory pages are missing, leave a `\NeedsInput{...}` placeholder inside the `Signature Pages` subsection.
105. When signatory pages exist, insert them as grouped full-width appendix figure blocks with two pages per row and about 4 to 8 pages per figure block when practical.

## Phase 11: Compile, QC, And Handoff

106. Write or rewrite the abstract from the finished report content, not from the drafting workflow.
107. Keep process notes, missing confirmations, and provenance notes out of the abstract.
108. After the full section tree is written, insert or refresh the catalogue between keywords and the first body section.
109. Ensure the catalogue hyperlinks sections and subsections.
110. Keep AI, automation, provenance wording, status-log phrasing, and tool-perspective narration out of the report source as well as the visible PDF.
111. Make sure the report reads like the experimenter is describing the work, not like a tool is describing its own process.
112. Compact the TeX source by removing redundant empty lines between adjacent commands or already-distinct formatted blocks.
113. Review every table against the two-column template and keep ordinary tables within `\columnwidth`.
114. Prefer wrapped columns, shorter headers, sensible rounding, and local font reduction before using a spanning table.
115. If a table is still too wide or too tall, split it into logical continuation tables instead of leaving it unreadable.
116. Avoid `longtable`, and use `table*` only when a true two-column comparison is necessary.
117. Copy or refresh `build.sh` from the skill assets when the workspace copy is missing or stale.
118. Compile with `bash build.sh`.
119. Run `scripts/report_qc.py`.
120. Decode the compiled PDF when practical and review it.
121. Verify that the final PDF size is no larger than `20 MB`.
122. If the PDF is still too large, revisit the staged PNG assets, compress them further with the `compress-png` skill, rebuild, and re-check before handoff.
123. Show the PDF and list unresolved gaps, including missing data, missing figures, failed procedures, or unresolved interpretation conflicts.

## Naming Conventions

- Transferred data markdown: `<data-parent>/data_transferred/<experiment-safe-name>_data.md`
- Processed data markdown: `<data-parent>/data_processed/<experiment-safe-name>_data_processed.md`
- Procedure markdown: `AI_works/results/<experiment-safe-name>/<experiment-safe-name>_procedures.md`
- Generated figures: `AI_works/results/<experiment-safe-name>/pictures-generated/`
- Principle figures copied from decoded handouts: `AI_works/results/<experiment-safe-name>/principle-images/`
- Staged experiment picture results: `AI_works/results/<experiment-safe-name>/picture-results/`
- Staged signatory pages: `AI_works/results/<experiment-safe-name>/signatory-pages/`

## Sidebar-Only Messages

- Tell the user about `Items Needed To Replace The Draft Placeholders` in the sidebar, not in the TeX.
- Tell the user about `Suggested Raw-Data Tables` in the sidebar, not in the TeX.
- Ask missing-data questions in the sidebar before drafting around the gap.
