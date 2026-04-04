---
name: course-lab-metadata-frontmatter
description: Use when a course lab-report run already has a confirmed course and chosen template context and now needs to coordinate report language with template language, resolve reusable author-profile fields, confirm student or collaborator metadata, collect instructor or course-local front-matter answers, or edit the canonical report title block and early front matter.
---

# Course Lab Metadata Frontmatter

## Overview

Resolve reusable person metadata and front-matter requirements before the report body is drafted.

This skill keeps cross-course profile fields reusable, treats chosen template language as upstream context from discovery or workspace setup, and writes only the title block and early front matter directly into the canonical report without drifting into body scaffolding or discussion writing.

## When to Use

- `course-lab-discovery` has already confirmed the course and experiment.
- `course-lab-workspace-template` or equivalent upstream context already established the chosen template and its likely language.
- The run needs the report language to be confirmed against the chosen template language before filling names or front matter.
- Student, collaborator, affiliation, instructor, or other course-local metadata is missing or may have changed.
- The title block or early front matter is about to be edited.
- The run needs to reuse or refresh `AI_works/resources/report_author_profile.json` without storing course identity there.

Do not use this skill to choose the experiment, create the workspace, extract procedures, or draft body sections.

## Output Contract

- Use local `scripts/manage_author_profile.py` as the canonical profile-management tool.
- Reuse `AI_works/resources/report_author_profile.json` by default unless the user explicitly overrides the profile path.
- Create the profile automatically when it does not exist.
- Treat the chosen template language as upstream context from discovery or workspace setup, not as something this skill guesses in isolation.
- If the report language is still unknown, default the question from the chosen template language but still require explicit confirmation before drafting.
- If the user intentionally wants the report language to differ from the chosen template language, surface that mismatch explicitly instead of silently proceeding.
- Keep the reusable author profile bilingual regardless of the current template or report language.
- Ask only for missing or changed reusable person fields plus course-local front-matter answers.
- Keep the course name and instructor identity out of the reusable profile unless the user explicitly asks otherwise.
- Read `references/metadata_rules.md` before editing the title block or front matter.
- Apply the confirmed title-block and early-front-matter edits directly in the canonical report file once the workspace is available.
- Keep direct report edits limited to the title block and early front matter; do not spill into later body prose.
- Keep unresolved front-matter gaps visible instead of inventing values when the required metadata is incomplete.

## Primary Command

```bash
python3 /root/.codex/skills/course-lab-metadata-frontmatter/scripts/manage_author_profile.py
```

Use `--profile /custom/path/report_author_profile.json` to override the default profile path, and `--set dotted.key=value` when the run already has confirmed updates to persist.

## Workflow

1. Confirm that the course is already known from discovery or the current run context.
2. Confirm that the chosen template or workspace handoff is already known, and treat its language as upstream context for this step.
3. Run `scripts/manage_author_profile.py` before asking repeated identity questions.
4. Review the returned `missing_fields` and the stored profile values.
5. If the report language is still unknown, default from the chosen template language, then ask the user to confirm the report language explicitly before drafting.
6. If the user intentionally wants a different report language than the chosen template language, restate that mismatch explicitly and keep it visible for the title-block decision instead of silently normalizing it away.
7. Ask only for missing or changed reusable person fields plus instructor name, instructor title choice, and any other course-local front-matter fields.
8. Persist only reusable person-field updates back into the author profile.
9. Apply the title-block and front-matter rules from `references/metadata_rules.md` directly in the canonical report file, typically `main.tex`.
10. Stop after the direct title-block and early-front-matter edits are complete, or after unresolved gaps are left visible for follow-up.

## Quick Reference

| Situation | Action |
|---|---|
| No profile file exists yet | Run `manage_author_profile.py` and let it create the JSON |
| Reusable student or collaborator fields already exist | Reuse them and ask only for changes |
| The report language is still unknown but the chosen template language is known | Use the template language as the default guess, then require explicit confirmation before drafting |
| The user wants the report language to differ from the chosen template language | Surface that mismatch explicitly and confirm the intended display convention before drafting |
| Instructor or course-local title info is missing | Ask for it, but do not store it in the reusable profile by default |
| The template title block is about to be edited | Read `references/metadata_rules.md` first, then edit the canonical report file directly |
| The next task is procedure extraction or body section drafting | Hand off to a different leaf skill instead of expanding scope here |

## Boundary Rules

- This skill assumes discovery already confirmed the course and experiment context.
- This skill treats chosen template language as upstream context from discovery or workspace setup; it does not silently infer template choice on its own.
- This skill manages reusable profile data and directly edits only the title block and early front matter in the canonical report; it does not create or refresh the report workspace.
- This skill does not extract procedures, normalize handouts, transfer data, stage figures, or write discussion prose.
- This skill may write title-block content directly into the report, but it should not draft later body sections or other non-front-matter report content.
- This skill should keep missing metadata visible instead of inventing names, affiliations, or instructor details.

## Common Mistakes

- Re-asking for every name and affiliation even though the reusable profile already has them.
- Treating template language and report language as unrelated and silently proceeding when they differ.
- Storing course identity or instructor identity in the reusable profile without explicit user approval.
- Filling the title block before confirming the report language, even when the template language suggests a default.
- Stopping at metadata notes when the canonical report file is already available for direct front-matter edits.
- Letting front-matter edits spill into body scaffold work, abstract writing, or final QC tasks.
- Keeping parent-skill path dependencies instead of using the local copied tool and rules file.

## Resources

- `scripts/manage_author_profile.py`: local profile creation and update tool
- `scripts/common.py`: local helper module used by the profile tool
- `references/metadata_rules.md`: local title-block and front-matter rules
- `tests/test_manage_author_profile.py`: local regression test
