# Metadata Rules

Follow these rules exactly when editing the title block, abstract, captions, and early sections.

## Language

- Ask for the course name at the beginning of every run before drafting the title block.
- Ask the user whether the report is English or Chinese before filling the title block.
- English report: use the user-provided English names only.
- Chinese report: use bilingual names with Chinese first.

## Names And Affiliations

- Put the student first and the collaborator second.
- Put affiliations as footnotes attached to the names.
- Put the instructor below the names in smaller text.
- Call the instructor `Professor` or `Teacher` as specified by the user or local course convention.
- Load repeated student and collaborator metadata from `AI_works/resources/report_author_profile.json` when possible.
- If the profile file does not exist, create it automatically before asking the user for the missing values.
- Store both Chinese and English versions of the student name, collaborator name, student affiliation, and collaborator affiliation in that profile.
- Ask only for the missing or changed profile fields plus the instructor name, instructor title choice, and any other course-local front-matter fields before drafting.

## Author Profile

- Default profile path: `AI_works/resources/report_author_profile.json`
- Treat this file as shared cross-course person metadata.
- Preferred stored keys:
  - `student.name_zh`
  - `student.name_en`
  - `student.affiliation_zh`
  - `student.affiliation_en`
  - `collaborator.name_zh`
  - `collaborator.name_en`
  - `collaborator.affiliation_zh`
  - `collaborator.affiliation_en`
- Do not persist the course name there by default.
- Do not persist instructor identity there by default unless the user explicitly asks for that behavior.
- When the user gives corrected reusable person metadata during a run, write those updates back into the profile so later courses reuse them automatically.

## Narrative Tone

- Write the report like the experimenter is describing the experiment, observations, calculations, and conclusions.
- Do not use AI-style tone, workflow narration, internal status logs, or tool-perspective wording.
- Do not write self-referential lines such as "this report was generated", "the following content was extracted", "I analyzed", or similar meta commentary in the report.
- Keep AI, automation, decoding, and drafting provenance out of the report source as well as the visible PDF.
- Do not mention Codex, AI, ChatGPT, OpenAI, MinerU, automatic generation, decoded JSON, extracted handout text, transferred notes, or similar workflow wording in body text, captions, table titles, appendix notes, or casual source comments.
- Keep source comments minimal and neutral. Only keep comments that are structurally necessary for report maintenance, such as procedure markers and local placeholder markers.

## Section Order

When the template is missing a required section, insert it in this order:

1. Introduction
2. Objectives
3. Experiment Equipment
4. Experiment Principle
5. Experimental Process / Experimental Phenomenon
6. Experiment Discussion
7. Appendix
8. References

## Catalogue

- After all report sections and subsections are written, insert a catalogue or table of contents between the keywords block and the first body section.
- If the template has no keywords block, place the catalogue after the front matter and before the Introduction.
- The catalogue must include hyperlinks for sections and subsections.
- If the template does not already provide hyperlink support, add `\usepackage[hidelinks]{hyperref}` or the template-equivalent package.

## Abstract

- Do not freeze the abstract at the beginning of the drafting process.
- Finalize the abstract after the main body, discussion, appendix, and references are written, and before the catalogue is inserted or refreshed.
- Keep the abstract focused on experiment content: objective, method, key observations or results, and the main conclusion.
- Do not mention handout provenance, notebook pages, transferred data status, placeholders, missing confirmations, or report-generation workflow in the abstract.
- Keep the abstract free of AI tone, status-log phrasing, and tool-perspective narration.
- Show drafting or confirmation issues to the user outside the report text instead.

## Source Spacing

- Keep the TeX source compact.
- Do not insert empty lines between adjacent commands or environments when the format change already makes the structure obvious.
- Reserve blank lines mainly for genuine paragraph separation in running text, not for every change of command or block type.
- Avoid multiple consecutive blank lines unless the template explicitly requires them.

## Equipment Section

- Prefer decoded tables and explicit model numbers from the handout or data files.
- If counts or model numbers are missing, ask whether to provide more data, continue with `TBD`, or stop.
- If the handout includes equipment explanations, place them under the equipment table as a subsection.

## Table Layout

- Assume the active template is two-column unless the local TeX clearly changes that.
- Keep ordinary report tables inside `\columnwidth` whenever possible.
- Prefer `tabularx`, wrapped `p{...}` columns, shorter headers, and sensible rounding before using a full-width float.
- Use `\small` or `\scriptsize` locally for compact numeric tables when needed, but do not shrink text until it becomes hard to read.
- Use `\resizebox{\columnwidth}{!}{...}` or `adjustbox` only as a last resort for compact numeric content, not for text-heavy tables.
- If a table is still too wide, split it into two logical tables or a continuation table instead of letting it break the two-column structure.
- If a table is too tall, split it by sample, condition, or stage so it remains readable where it appears.
- Avoid `longtable` in this template.
- Avoid `table*` by default because it often floats to the next page in two-column mode. Use it only when both-column width is genuinely necessary and the table is still short enough to read comfortably.

## Principle Images

- If the decoded handout principle section contains figures or image captions, include them inside the report's Experiment Principle section.
- Use the decoded image title as the caption text by default.
- If the template already provides `Figure n` numbering, do not embed `Fig. n` again in the caption text.
- Group related `(a)`, `(b)`, `(c)` visuals under one parent figure when the decoded captions or filenames show they belong together.
- If grouped subfigures are emitted and the template does not already support them, add `\usepackage{subcaption}` or the template-equivalent package before compiling.
- Use the individual marker text as the subcaption and the shared figure title as the parent caption.
- Place each principle figure in the subsection where the handout actually uses it.
- Mention each principle figure in the surrounding discussion with a label-based reference rather than leaving it as a floating picture with no textual mention.
- When a handout figure functions as a schematic diagram, explicitly call it a schematic diagram in that subsection.
- If grouping is uncertain, stop and ask the user before fixing the layout.
- Do not move those principle visuals to the appendix.
- Do not surround figure environments with extra blank-line padding unless the template explicitly needs it.

## Thinking Questions

- Use a subsection named `Assigned Thinking Questions`.
- Format each item as the numbered question first, followed by its answer on the next line or paragraph.

## Appendix

- Limit the appendix to `Code` and `Signature Pages`.
- If no code is available yet, leave a placeholder in `Code`.
- If signatory pages exist, insert them in `Signature Pages` as grouped full-width appendix figure blocks.
- Use two signatory pages per row.
- Prefer about 4 to 8 signatory pages per figure block or appendix page when possible, and split long sets into continued figure blocks instead of shrinking all pages into one tiny block.
- Use subfigures so the pages carry `(a)`, `(b)`, `(c)` style serial markers automatically, continuing across blocks when the grouped layout spans multiple figures.
- If the template does not already support grouped figures, add `\usepackage{subcaption}` or the template-equivalent package before compiling.
- Use the parent caption `Signatory pages`.
- Do not enlarge signatory pages to full-page size unless the user explicitly asks for that layout.
- If no signatory pages are available yet, leave a placeholder in `Signature Pages`.
- Do not put draft-management lists there.
