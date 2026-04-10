---
name: course-lab-data-transfer
description: Use when a course lab-report run already has identified raw-data sources and now needs page-level transcription from CSV, TSV, text, spreadsheet, PDF, or image inputs, preservation of handwritten Chinese observation notes with nearby English translations, or a user proofread checkpoint before calculations, uncertainty work, or interpretation.
---

# Course Lab Data Transfer

## Overview

Turn confirmed raw-data sources into reviewable transfer artifacts without drifting into calculations, anomaly judgments, or report prose.

This skill is vision-first for PDF and image sources. Read the rendered pages first, compare that reading against the corresponding MinerU Markdown second, and only use PDF-to-text as the third tie-breaker when the first two disagree or confidence stays low.

When discovery or staged picture evidence shows subordinate experiment picture results, this skill also requires a second vision pass on those pictures before any transferred phenomenon description becomes final.

## Standalone Tool Contract

### Use Independently When
- Confirmed raw-data sources need page-level or file-level transcription into reviewable Markdown before calculations, uncertainty analysis, or interpretation.
- Handwritten Chinese observation notes must be preserved with nearby English translations.
- A visible user proofread gate is required before analysis continues.

### Minimum Inputs
- Raw data source path(s): CSV, TSV, TXT, XLS/XLSX, PDF, image, or picture-result folder.
- Output destination for the transferred Markdown and any bundle manifest.
- Experiment/source identity and any source-coverage expectations from handout, discovery, or run-plan artifacts.

### Optional Workflow Inputs
- Discovery JSON with `data_groups`, `other_files`, result directories, or picture-result candidates.
- `picture_results_manifest.json` for visual corroboration of phenomena.
- Normalized handout or scaffold procedure anchors for source-coverage mapping.

### Procedure
- Read text/spreadsheet sources directly when possible; for PDFs, use `prepare_data_transfer_bundle.py` to create page images, local PDF-to-text, and bundle manifest support.
- Use vision/MinerU/PDF-text cross-checking for page-based sources and keep disagreement notes visible.
- Preserve Chinese handwritten notes and nearby English translations; keep weakly supported phenomenon descriptions provisional.
- Stop at the transferred Markdown and explicitly require user proofread before calculations or report prose continue.

### Outputs
- Reviewable transferred Markdown draft.
- Bundle manifest JSON and local page/PDF-text artifacts for page-based sources when applicable.
- Source-coverage notes, unresolved/mismatch notes, provisional phenomenon flags, and proofread request.

### Validation
- Every expected data source is covered or named in a visible source-coverage gap.
- Page/image/PDF readings are traceable to page images, MinerU/PDF text, or direct file content as applicable.
- The run stops before downstream analysis until the user proofreads or explicitly validates the transferred data.

### Failure / Reroute Signals
- Missing raw-data path: in standalone mode, stop and request the source; in full-workflow mode, reroute to discovery/source selection.
- Unsupported spreadsheet/PDF dependency: report the dependency gap and any usable fallback artifact.
- Picture evidence mismatch: mark the phenomenon description provisional and request clarification rather than finalizing it.
- No user proofread: block calculations, uncertainty analysis, interpretation, and report drafting.

### Non-Ownership
- Does not compute derived quantities, perform uncertainty propagation, judge anomalies, write final report prose, or promote provisional observations into confirmed results.
- Does not hide missing source pages or unsupported picture-result claims.

## Optional Workflow Metadata
- Suggested future role label: `preparer`.
- Typical upstream tools: `course-lab-discovery`, `course-lab-run-plan`, picture-result manifesting.
- Typical downstream tools: `course-lab-data-processing`, `course-lab-uncertainty-analysis`, `course-lab-results-interpretation`.

## Primary Commands

Prepare a review bundle for one source:

```bash
python3 /root/.codex/skills/course-lab-data-transfer/scripts/prepare_data_transfer_bundle.py \
  --source "/path/to/data.pdf" \
  --output-dir "/path/to/data_transfer_review/data" \
  --discovery-json "/tmp/course-lab-discovery-crystal-optics-en.json" \
  --picture-results-manifest "/path/to/results/<experiment>/picture_results_manifest.json"
```

Build the first transfer draft from that bundle:

```bash
python3 /root/.codex/skills/course-lab-data-transfer/scripts/build_transfer_draft.py \
  --bundle-json "/path/to/data_transfer_review/data/transfer_bundle.json" \
  --experiment-safe-name "crystal_optics" \
  --output-markdown "/path/to/data_transferred/crystal_optics_data.md"
```

## Workflow

1. Confirm that the experiment and the intended data source files are already known.
2. For CSV, TSV, TXT, XLS, and XLSX inputs, read the source directly when possible and keep the transfer artifact page-free unless the source itself is page-based.
3. For PDF inputs, run `prepare_data_transfer_bundle.py` first so the run has rendered page images, a local PDF-to-text artifact, and the best matching MinerU Markdown path if one already exists.
4. Read the rendered PDF pages or source images first. Do not let MinerU Markdown or OCR become the first reading.
5. If the corresponding MinerU Markdown is missing for a PDF source, invoke `$mineru-pdf-markdown` on the PDF folder, then continue with the comparison.
6. Compare the vision-first reading against the MinerU Markdown. If they agree well enough, draft the transfer from the vision-first reading and use MinerU as a confidence check rather than as the authoritative source.
7. If the vision-first reading and MinerU Markdown disagree, or if either one still looks weak, compare both against the local PDF-to-text artifact and then choose the final transferred wording or values from the best-supported reading.
8. If discovery JSON or `picture_results_manifest.json` shows subordinate picture results for the same experiment, inspect the relevant picture results with vision before final judgment. Use them to confirm that the transferred phenomenon description is really visible in the picture evidence.
9. If the picture evidence does not clearly support the transferred phenomenon wording, keep that wording provisional, add an uncertainty or mismatch note, and ask the user before treating it as settled.
10. Run `build_transfer_draft.py` to scaffold the final Markdown file, then replace the placeholders with the actual page-by-page or source-by-source transfer.
11. Preserve handwritten Chinese observation notes in the final Markdown, then add English translations immediately after them.
12. Keep visible uncertainty notes for partially legible text, conflicting readings, or digits whose units are not secure.
13. Show the finished transferred Markdown to the user and explicitly ask them to proofread it before later analysis continues.

## Quick Reference

### Contract Notes

- Use local `scripts/prepare_data_transfer_bundle.py` to create a standalone review bundle for each source.
- Use local `scripts/build_transfer_draft.py` to create the first Markdown transfer draft from that bundle.
- Save the final transferred Markdown as `<data-parent>/data_transferred/<experiment-safe-name>_data.md`.
- For PDF sources, the review bundle should include:
  - rendered page images for vision-first reading
  - a located MinerU Markdown path when it exists
  - a local PDF-to-text artifact for tie-breaking
  - a bundle manifest JSON
- When discovery or figure-evidence staging already found matching picture results, the review bundle should also include picture-result evidence paths and any rendered review images needed for vision inspection.
- Keep Chinese notes in the original language first, then add the English translation immediately below or beside the original note.
- Keep uncertainty local. If a digit, unit, symbol, or handwritten phrase is weak, mark that weakness in the transferred Markdown instead of silently choosing one interpretation.
- If a transferred phenomenon description is not visibly supported by the matched picture-result evidence, keep it provisional or surface a question instead of treating it as final.
- Stop after the transferred Markdown draft and explicitly ask the user to proofread it before calculations, uncertainty analysis, anomaly judgments, or report drafting continue.
- When the selected data group contains both spreadsheets and companion PDF or scan sources, do not treat spreadsheet transfer alone as complete.
- When discovery exposes companion scan sources such as data.pdf, record-book scans, or source images inside the selected data group, data transfer is incomplete until those sources are transferred or explicitly marked unresolved.

| Situation | Action |
|---|---|
| CSV or TSV source | Read directly and use the local preview artifact as the transcription aid |
| XLSX source with `openpyxl` available | Generate a sheet-by-sheet preview and transfer directly |
| XLS or XLSX source without spreadsheet support installed | Surface the dependency gap instead of pretending the workbook was read |
| PDF source with matching MinerU Markdown already present | Still read the rendered pages first, then compare with MinerU |
| PDF source without matching MinerU Markdown | Render pages first, then invoke `$mineru-pdf-markdown`, then compare |
| Vision and MinerU clearly disagree | Bring in the local PDF-to-text artifact before deciding the final reading |
| Discovery or staged evidence shows subordinate picture results | Inspect the relevant pictures with vision before finalizing any phenomenon description |
| Handwritten Chinese note is partly legible | Keep the visible Chinese text, add a best-effort English translation, and mark the uncertainty |
| User has not proofread the transfer yet | Stop before uncertainty work, interpretation, or report drafting |

## Boundary Rules

- This skill starts only after the data source set is already identified.
- This skill owns transcription, comparison, and ambiguity surfacing. It does not own calculations or interpretation.
- For PDFs and images, vision-first is mandatory. MinerU Markdown is the second reader, not the first.
- PDF-to-text is the third comparison source. Use it when the first two readings conflict or confidence stays low.
- When matched picture-result evidence exists, do not finalize a transferred phenomenon description until that description has been checked against the relevant picture with vision.
- Either transfer companion PDF/scan sources in the same stage or leave an explicit unresolved note that later stages can see.
- Do not silently replace handwritten Chinese notes with English-only summaries.
- Do not convert uncertain transfer artifacts into confident result statements.
- Keep parent-skill path dependencies out of the toolchain. Use the local copied scripts in this folder for bundle prep and draft generation.

## Common Mistakes

- Starting from MinerU Markdown and only looking at the page images later.
- Treating OCR or MinerU output as more trustworthy than a clear visual reading.
- Skipping the PDF-to-text comparison even though the first two readings conflict.
- Finalizing a phenomenon description even though the matched picture-result evidence does not visibly support it.
- Translating a Chinese note without keeping the original wording nearby.
- Cleaning up weak readings so aggressively that the uncertainty disappears.
- Continuing straight into calculations or discussion without asking the user to proofread the transferred Markdown.

## Resources

- `scripts/prepare_data_transfer_bundle.py`: local review-bundle builder for PDFs, images, and direct-read sources
- `scripts/build_transfer_draft.py`: local transfer-draft scaffold generator
- `scripts/common.py`: local helper module used by the standalone toolchain
- `tests/test_prepare_data_transfer_bundle.py`: local regression tests for bundle preparation
- `tests/test_build_transfer_draft.py`: local regression tests for draft generation
