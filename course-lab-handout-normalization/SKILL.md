---
name: course-lab-handout-normalization
description: Use when a course lab-report run has already selected a handout or reference PDF and now needs to decide whether decoding is required, convert decoded content into normalized section blocks, or keep structural gaps visible before workspace setup or report drafting.
---

# Course Lab Handout Normalization

## Overview

Make a selected handout or reference structurally usable for later report work.

This skill prefers PDF-to-Markdown first for readable inspection, escalates to PDF-to-JSON second when section structure is needed, and keeps structural gaps visible for later skills.

## When to Use

- The experiment and source PDF are already confirmed by `course-lab-discovery`.
- A handout or reference PDF exists, but it is unclear whether decoded output already exists.
- MinerU output exists, but later steps need normalized sections instead of raw blocks.
- The next step needs procedure, principle, equipment, image, table, or thinking-question structure from the handout.
- The run needs a clean handoff before `course-lab-workspace-template` or `course-lab-body-scaffold`.

Do not use this skill to pick the experiment, choose a template, edit `main.tex`, or draft report wording.

## Output Contract

- Use the local `scripts/extract_decoded_sections.py` as this skill's canonical normalization tool.
- Reuse an existing decoded Markdown when it clearly matches the selected handout or reference.
- Prefer `$mineru-pdf-markdown` as the first decode path when no suitable decoded artifact exists.
- Reuse an existing decoded JSON when normalized section extraction is already needed and the match is clear.
- Use `$mineru-pdf-json` as the second decode path only when downstream work needs structured blocks, section extraction, or block-level image and table metadata.
- Run `extract_decoded_sections.py` only on the chosen decoded JSON when section artifacts are actually needed.
- When you save paired normalization artifacts, use experiment-specific filenames such as `/tmp/course-lab-handout-normalization-<experiment-safe-name>-handout.json` and `/tmp/course-lab-handout-normalization-<experiment-safe-name>-handout.md`. Use source suffixes like `handout` and `reference` when both sources may exist in the same run.
- Produce visible unresolved structure notes even when the run stops at the Markdown-first stage.
- When JSON is required, produce one normalized section JSON and one normalized section Markdown artifact.

## Primary Command

```bash
python3 /root/.codex/skills/course-lab-handout-normalization/scripts/extract_decoded_sections.py \
  --decoded-json "/path/to/pdf_decoded/experiment/experiment.json" \
  --output-json /tmp/course-lab-handout-normalization-<experiment-safe-name>-handout.json \
  --output-markdown /tmp/course-lab-handout-normalization-<experiment-safe-name>-handout.md
```

When later steps need saved normalization artifacts, keep the filenames experiment-specific instead of reusing one generic `sections.json` or `sections.md` path. Use short source suffixes like `handout` and `reference` when the run may normalize more than one PDF.

## Workflow

1. Confirm that `course-lab-discovery` already selected the experiment and the candidate handout or reference PDF.
2. Look first for a clearly matching decoded Markdown under the related `pdf_markdown/` tree, then look for decoded JSON under `pdf_decoded/` when structure extraction may be needed.
3. Reuse the decoded Markdown when the match is clear and the current task is source reading, section planning, or handout inspection.
4. If no suitable decoded Markdown exists, invoke `$mineru-pdf-markdown` for the selected PDF.
5. Escalate to `$mineru-pdf-json` only when downstream work needs `extract_decoded_sections.py`, stable section keys, or structured image and table blocks.
6. Reuse a clearly matching decoded JSON when it already exists; otherwise invoke `$mineru-pdf-json`.
7. Run `extract_decoded_sections.py` only after the JSON step is available and necessary. If you save outputs, name them after the experiment, for example `/tmp/course-lab-handout-normalization-<experiment-safe-name>-handout.json` and `/tmp/course-lab-handout-normalization-<experiment-safe-name>-handout.md`.
8. Review `title`, `section_order`, `front_matter`, `sections`, and `appendix_candidates`, then hand off either Markdown-first inspection notes or experiment-specific normalized artifacts plus unresolved structure notes.

## Quick Reference

| Situation | Action |
|---|---|
| Confirmed PDF and matching decoded Markdown already exist | Reuse the decoded Markdown first |
| Confirmed PDF exists but no decoded Markdown exists | Invoke `$mineru-pdf-markdown` first |
| Only decoded Markdown exists | Use it for inspection first, then re-decode to JSON only if downstream structure is needed |
| Matching decoded JSON already exists and section extraction is needed | Reuse the decoded JSON and normalize it into an experiment-specific filename |
| No decoded JSON exists but section extraction is needed | Invoke `$mineru-pdf-json`, then normalize into an experiment-specific filename |
| Two decoded candidates look similarly plausible | Stop and surface the shortlist instead of choosing silently |
| Normalized output is missing expected sections | Record the gap; do not invent missing content |
| Reference report is the only available source | Normalize it as structure guidance only, not as report wording to copy |

## Boundary Rules

- This skill starts only after discovery confirms the experiment and source candidates.
- This skill may decide Markdown-first versus JSON-second decoding, but it does not perform experiment discovery itself.
- This skill produces structure artifacts. It does not create or refresh the report workspace.
- This skill does not edit TeX, choose a canonical report file, or fill front matter.
- This skill does not turn missing handout content into polished report prose.
- This skill should preserve uncertainty when headings are noisy, sections are merged, or source selection is ambiguous.
- Do not reuse one generic normalization filename across different experiments. Saved JSON and Markdown artifacts should be experiment-specific and source-specific when needed.
- Use reference reports to learn structure depth only. Do not treat them as copyable report content.

## Common Mistakes

- Jumping straight into `main.tex` edits after decoding. That belongs to later skills.
- Jumping straight to JSON when Markdown would have been enough for the current step.
- Treating decoded Markdown as interchangeable with decoded JSON when downstream steps need structured sections.
- Reusing one shared `/tmp/sections.json` or `/tmp/sections.md` path while multiple experiment runs are active.
- Hiding weak source matches because one filename looks close enough.
- Inventing missing objectives or procedure steps instead of surfacing them as unresolved structure gaps.
- Letting normalization drift into workspace setup, front matter, or final wording.

## Resources

- `scripts/extract_decoded_sections.py`: local normalization tool for decoded MinerU JSON
- `scripts/common.py`: local helper module used by the normalization script
- `tests/test_extract_decoded_sections.py`: local regression test
- `tests/fixtures/sample_mineru.json`: local fixture for the regression test
