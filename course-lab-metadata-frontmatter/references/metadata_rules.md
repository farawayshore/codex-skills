# Metadata Rules

Follow these rules when editing the title block or other front matter.

## Language

- Confirm the course name before drafting the title block.
- Treat the chosen template language as upstream context from discovery or workspace setup.
- If the report language is still unknown, default from the chosen template language but still require explicit confirmation before drafting.
- If the user intentionally wants a mismatch between the chosen template language and the report language, surface that mismatch explicitly instead of silently proceeding.
- Ask whether the report is English or Chinese before filling names, even when the template language suggests the default.
- English report: use the user-provided English names only unless the chosen template explicitly requires bilingual display.
- Chinese report: use bilingual names with Chinese first unless the chosen template explicitly requires a different display convention.

## Names And Affiliations

- Put the student first and the collaborator second.
- Put affiliations as footnotes attached to the names.
- Put the instructor below the names in smaller text.
- Call the instructor `Professor` or `Teacher` as specified by the user or local course convention.
- Load repeated student and collaborator metadata from `AI_works/resources/report_author_profile.json` when possible.
- If the profile file does not exist, create it automatically before asking for missing values.
- Keep the reusable author profile bilingual by storing both Chinese and English versions of the student name, collaborator name, student affiliation, and collaborator affiliation there regardless of the current report language.
- Ask only for missing or changed reusable profile fields plus the instructor name, instructor title choice, and any other course-local front-matter fields before drafting.

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

## Title Block And Front Matter

- Do not draft the title block until the course name, report language, and required metadata answers are present.
- When the canonical report file already exists, apply title-block and early-front-matter edits directly there instead of leaving them as a later staging handoff.
- If the chosen template language and confirmed report language differ, keep that mismatch explicit while drafting instead of silently pretending they align.
- Keep front matter limited to course-local identity and presentation requirements.
- Keep direct report edits limited to the title block and early front matter; later non-front-matter writing belongs to other skills.
- Keep unresolved front-matter gaps visible rather than inventing values.
- If the template requires additional course-local front-matter fields, ask for them explicitly before drafting.

## Narrative Tone

- Keep AI, automation, decoding, and workflow provenance out of the title block and front matter.
- Do not write self-referential lines such as "this report was generated" or "the following content was extracted" in front matter.
- Keep source comments minimal and neutral. Only keep comments that are structurally necessary for report maintenance.
