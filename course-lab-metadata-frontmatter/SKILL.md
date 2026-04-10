---
name: course-lab-metadata-frontmatter
description: Use when a course lab-report run already has a confirmed course and chosen template context and now needs to coordinate report language with template language, resolve reusable author-profile fields, confirm student or collaborator metadata, collect instructor or course-local front-matter answers, or edit the canonical report title block and early front matter.
---

# Course Lab Metadata Frontmatter

## Overview

Resolve reusable person metadata and front-matter requirements before the report body is drafted.

This skill keeps cross-course profile fields reusable, treats chosen template language as upstream context from discovery or workspace setup, and writes only the title block and early front matter directly into the canonical report without drifting into body scaffolding or discussion writing.

## Standalone Tool Contract

### Use Independently When
- A canonical TeX report file exists and needs title-block/front-matter metadata filled or normalized.
- Course, instructor, author, date, collaborator, or language-specific front-matter fields need explicit handling before body drafting.

### Minimum Inputs
- Canonical TeX path to mutate.
- Confirmed report language and template language context.
- Metadata values or a reusable author/profile source for required fields such as title, student, instructor, course, experiment date, and collaborators.

### Optional Workflow Inputs
- Workspace manifest from `course-lab-workspace-template`.
- Existing profile notes, course-local front-matter requirements, or user-provided title wording.
- Normalized handout title for title consistency checks.

### Procedure
- Use the local metadata/front-matter helper described below when it applies; otherwise make minimal TeX edits only to the title block and early front matter.
- Preserve template language and existing macro conventions.
- Surface missing required metadata as explicit questions or unresolved notes instead of inventing values.

### Outputs
- Updated canonical TeX title block or front matter.
- Metadata handoff notes naming populated fields, unresolved required fields, and any profile values reused.
- Optional machine-readable manifest when the local command supports it.

### Validation
- The canonical TeX file still exists and contains the required metadata fields or explicit unresolved placeholders.
- Report language and template language are not mixed accidentally.
- No body sections or scientific claims were changed as part of front-matter work.

### Failure / Reroute Signals
- Missing canonical TeX: in standalone mode, stop and request the file; in full-workflow mode, reroute to `course-lab-workspace-template`.
- Missing required metadata: request the specific value or leave a declared unresolved placeholder; do not fabricate author, instructor, date, or collaborator information.
- Template-specific macro ambiguity: report the macro conflict before broader TeX mutation.

### Non-Ownership
- Does not select templates, create workspaces, scaffold body sections, compute results, or write discussion prose.
- Does not infer personal/student metadata beyond the provided profile or explicit user facts.

## Optional Workflow Metadata
- Suggested future role label: `preparer`.
- Typical upstream tools: `course-lab-workspace-template`, user/profile metadata.
- Typical downstream tools: `course-lab-body-scaffold`, `course-lab-experiment-principle`, `course-lab-final-staging`.

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

### Contract Notes

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
