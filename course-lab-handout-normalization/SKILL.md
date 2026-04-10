---
name: course-lab-handout-normalization
description: Use when a course lab-report run has already selected a handout or reference PDF and now needs MinerU Markdown-first inspection, MinerU JSON-second section extraction, or visible structure-gap notes before workspace setup or report drafting.
---

# Course Lab Handout Normalization

## Overview

Make a selected handout or reference structurally usable for later report work.

This skill is MinerU-only for decoding: MinerU Markdown is the required Markdown-first path for readable inspection, MinerU JSON is the required JSON-second path when structure extraction is needed, and vision is complementary only for resolving layout or figure ambiguities. Do not use `pdftotext`.

## Standalone Tool Contract

### Use Independently When
- A selected handout or reference PDF needs Markdown-first decoding, JSON section extraction, or visible structure-gap notes.
- Persistent decoded handout artifacts are missing, stale, or summary-only and must be recreated before workspace setup or report drafting.

### Minimum Inputs
- A selected handout/reference PDF path, or an existing decoded Markdown/JSON source that is visibly tied to the selected experiment.
- Experiment name or safe slug for persistent artifact naming.
- Output destination for normalized section artifacts when a workspace already exists, or an experiment-specific temporary destination when it does not.

### Optional Workflow Inputs
- Discovery manifest entries naming candidate handout/reference paths.
- Workspace notes directory, canonical report workspace path, or run-plan destination for `sections.json` and `sections.md`.
- Source role label such as `handout` or `reference` when more than one PDF is normalized in the same run.

### Procedure
- Prefer MinerU Markdown-first inspection before JSON extraction when no suitable persistent decoded artifact exists.
- Persist decoded handout artifacts under `AI_works/resources/experiment_handout/Modern Physics Experiments/pdf_decoded/<experiment-name>/` rather than leaving only `/tmp` or summary-only notes.
- Run `extract_decoded_sections.py` only after the decoded JSON is available and section artifacts are actually needed.
- Keep visible notes for missing titles, broken section order, ambiguous figures, or appendix candidates.

### Outputs
- Persistent decoded Markdown and JSON artifacts for the selected handout/reference source.
- Normalized section JSON and Markdown artifacts, typically `/path/to/results/<experiment>/notes/sections.json` and `/path/to/results/<experiment>/notes/sections.md` once a workspace exists.
- Structure-gap notes naming ambiguous or missing sections that later tools must not ignore.

### Validation
- Markdown-first decode was checked before JSON-dependent section extraction.
- Successful normalization leaves persistent decoded artifacts, not only ad hoc excerpts or summary notes.
- Normalized artifacts include title, section order, front matter, sections, appendix candidates, and unresolved structure notes when present.

### Failure / Reroute Signals
- Missing selected PDF/decoded source: in standalone mode, stop and request the source path; in full-workflow mode, reroute to `course-lab-discovery`.
- MinerU/API/decode failure: report the failed decode path and any partial artifacts; do not pretend summary notes are normalized handout artifacts.
- Structure ambiguity: emit normalized artifacts with explicit gap notes when usable, or stop before downstream drafting if the required sections are unrecoverable.

### Non-Ownership
- Does not create or refresh the report workspace, choose the template, transcribe raw data, or write report prose.
- Does not treat temporary snippets, OCR summaries, or human memory as replacements for persistent decoded handout artifacts.

## Optional Workflow Metadata
- Suggested future role label: `preparer`.
- Typical upstream tools: `course-lab-discovery`, selected PDF/reference source.
- Typical downstream tools: `course-lab-workspace-template`, `course-lab-run-plan`, `course-lab-body-scaffold`, `course-lab-experiment-principle`.

## Primary Command

```bash
python3 /root/.codex/skills/course-lab-handout-normalization/scripts/extract_decoded_sections.py \
  --decoded-json "/path/to/pdf_decoded/experiment/experiment.json" \
  --output-json /tmp/course-lab-handout-normalization-<experiment-safe-name>-handout.json \
  --output-markdown /tmp/course-lab-handout-normalization-<experiment-safe-name>-handout.md
```

When later steps need saved normalization artifacts, keep the filenames experiment-specific instead of reusing one generic `sections.json` or `sections.md` path. Once a workspace exists, route those normalized artifacts into `/path/to/results/<experiment>/notes/sections.json` and `/path/to/results/<experiment>/notes/sections.md`. Use short source suffixes like `handout` and `reference` when the run may normalize more than one PDF.

## Workflow

1. Confirm that `course-lab-discovery` already selected the experiment and the candidate handout or reference PDF.
2. Look first for persistent decoded handout artifacts under `AI_works/resources/experiment_handout/Modern Physics Experiments/pdf_decoded/<experiment-name>/`, starting with `<experiment-name>.md` and then `<experiment-name>.json`.
3. Reuse the decoded Markdown when the match is clear and the current task is source reading, section planning, or handout inspection.
4. If no suitable decoded Markdown exists, invoke `$mineru-pdf-markdown` for the selected PDF. Do not switch to `pdftotext`.
5. Use MinerU JSON-second only when downstream work needs `extract_decoded_sections.py`, stable section keys, or structured image and table blocks.
6. Reuse a clearly matching decoded JSON when it already exists; otherwise invoke `$mineru-pdf-json`.
7. If MinerU output still leaves headings, diagrams, or formula regions unclear, use vision as a complementary check. Do not replace MinerU with vision-only extraction.
8. When decoding succeeds, persist the chosen outputs as `AI_works/resources/experiment_handout/Modern Physics Experiments/pdf_decoded/<experiment-name>/<experiment-name>.md` and `AI_works/resources/experiment_handout/Modern Physics Experiments/pdf_decoded/<experiment-name>/<experiment-name>.json` instead of leaving the run with temporary-only or summary-only artifacts.
9. If the active source is a selected same-experiment reference, confirm the discovery entry still includes `expected_decoded_markdown_path` and `expected_decoded_json_path`; if not, reroute to `course-lab-discovery` before continuing.
10. Run `extract_decoded_sections.py` only after the JSON step is available and necessary. If a workspace already exists, save the normalized routing artifacts as `/path/to/results/<experiment>/notes/sections.json` and `/path/to/results/<experiment>/notes/sections.md`; otherwise keep experiment-specific temporary filenames until the workspace exists.
11. Review `title`, `section_order`, `front_matter`, `sections`, and `appendix_candidates`, then hand off either Markdown-first inspection notes or experiment-specific normalized artifacts plus unresolved structure notes.

## Quick Reference

### Contract Notes

- Use the local `scripts/extract_decoded_sections.py` as this skill's canonical normalization tool.
- Reuse an existing decoded Markdown when it clearly matches the selected handout or reference.
- MinerU Markdown-first is mandatory. Prefer `$mineru-pdf-markdown` as the first decode path when no suitable decoded artifact exists.
- Reuse an existing decoded JSON when normalized section extraction is already needed and the match is clear.
- MinerU JSON-second is mandatory. Use `$mineru-pdf-json` as the second decode path only when downstream work needs structured blocks, section extraction, or block-level image and table metadata.
- Never use `pdftotext`, plain OCR text dumps, or text-only PDF fallback methods for this skill.
- Use vision only as a complementary check when MinerU output leaves figures, formulas, page regions, or heading boundaries ambiguous.
- Successful handout normalization must leave persistent decoded handout artifacts under `AI_works/resources/experiment_handout/Modern Physics Experiments/pdf_decoded/<experiment-name>/`.
- The canonical persistent success paths are `AI_works/resources/experiment_handout/Modern Physics Experiments/pdf_decoded/<experiment-name>/<experiment-name>.md` and `AI_works/resources/experiment_handout/Modern Physics Experiments/pdf_decoded/<experiment-name>/<experiment-name>.json`.
- Run `extract_decoded_sections.py` only on the chosen decoded JSON when section artifacts are actually needed.
- When a workspace already exists, the canonical downstream normalized routing artifacts are `/path/to/results/<experiment>/notes/sections.json` and `/path/to/results/<experiment>/notes/sections.md`.
- For selected same-experiment references, preserve `expected_decoded_markdown_path` and `expected_decoded_json_path` from discovery; if those fields are missing, reroute to `course-lab-discovery` instead of guessing.
- If selected same-experiment references exist but the decoded Markdown path is still missing on disk, reroute back here and restore `expected_decoded_markdown_path` before downstream QC continues.
- When you save paired normalization artifacts, use experiment-specific filenames such as `/tmp/course-lab-handout-normalization-<experiment-safe-name>-handout.json` and `/tmp/course-lab-handout-normalization-<experiment-safe-name>-handout.md`. Use source suffixes like `handout` and `reference` when both sources may exist in the same run.
- Produce visible unresolved structure notes even when the run stops at the Markdown-first stage.
- When JSON is required, produce one normalized section JSON and one normalized section Markdown artifact.
- Summary-only notes are not successful handout normalization. The skill must not treat ad hoc extracts as equivalent to persistent decoded handout artifacts.

| Situation | Action |
|---|---|
| Confirmed PDF and matching persistent `<experiment-name>.md` already exist | Reuse the decoded Markdown first |
| Confirmed PDF exists but no persistent `<experiment-name>.md` exists | Invoke `$mineru-pdf-markdown` first |
| Only decoded Markdown exists | Use it for inspection first, then re-decode to MinerU JSON only if downstream structure is needed |
| Matching decoded JSON already exists and section extraction is needed | Reuse the decoded JSON and normalize it into an experiment-specific filename |
| No decoded JSON exists but section extraction is needed | Invoke `$mineru-pdf-json`, then normalize into an experiment-specific filename |
| MinerU output leaves figure regions or page structure ambiguous | Use vision as a complementary check, then continue with the MinerU artifacts |
| A fallback such as `pdftotext` seems tempting | Do not use it; keep the run on MinerU Markdown-first and MinerU JSON-second |
| Only `handout_extract.md`, `sections.json`, or other summary-only notes exist | Treat normalization as incomplete and continue the decode path |
| Two decoded candidates look similarly plausible | Stop and surface the shortlist instead of choosing silently |
| Normalized output is missing expected sections | Record the gap; do not invent missing content |
| Reference report is the only available source | Normalize it as structure guidance only, not as report wording to copy |

## Boundary Rules

- This skill starts only after discovery confirms the experiment and source candidates.
- This skill may decide MinerU Markdown-first versus MinerU JSON-second decoding, but it does not perform experiment discovery itself.
- This skill produces structure artifacts. It does not create or refresh the report workspace.
- This skill does not edit TeX, choose a canonical report file, or fill front matter.
- This skill does not turn missing handout content into polished report prose.
- This skill should preserve uncertainty when headings are noisy, sections are merged, or source selection is ambiguous.
- This skill must not use `pdftotext` or any equivalent text-only fallback in place of MinerU decoding.
- This skill may use vision only as a complementary read aid after MinerU, never as the primary decode path.
- Do not reuse one generic normalization filename across different experiments. Saved JSON and Markdown artifacts should be experiment-specific and source-specific when needed.
- Use reference reports to learn structure depth only. Do not treat them as copyable report content.
- `handout_extract.md`, summary-only notes, or normalization-only outputs such as `sections.json` are not enough to claim successful handout normalization by themselves.

## Common Mistakes

- Jumping straight into `main.tex` edits after decoding. That belongs to later skills.
- Jumping straight to MinerU JSON when MinerU Markdown would have been enough for the current step.
- Treating decoded Markdown as interchangeable with decoded JSON when downstream steps need structured sections.
- Using `pdftotext` because it seems faster or simpler. This skill strictly prohibits `pdftotext`.
- Treating vision as a primary decoder instead of a complementary check for ambiguous MinerU output.
- Reusing one shared `/tmp/sections.json` or `/tmp/sections.md` path while multiple experiment runs are active.
- Treating `handout_extract.md` or other summary-only fallbacks as if they were persistent decoded handout artifacts.
- Hiding weak source matches because one filename looks close enough.
- Inventing missing objectives or procedure steps instead of surfacing them as unresolved structure gaps.
- Letting normalization drift into workspace setup, front matter, or final wording.

## Resources

- `scripts/extract_decoded_sections.py`: local normalization tool for decoded MinerU JSON
- `scripts/common.py`: local helper module used by the normalization script
- `tests/test_extract_decoded_sections.py`: local regression test
- `tests/fixtures/sample_mineru.json`: local fixture for the regression test
