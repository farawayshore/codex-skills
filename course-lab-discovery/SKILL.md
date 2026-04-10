---
name: course-lab-discovery
description: Use when a course lab-report run needs course-aware matching of an experiment to local handouts, reference reports, multi-file data bundles, simulation assets, picture-result folders, result directories, or LaTeX templates, especially when the correct source is uncertain or one experiment may have multiple raw files and scanned data pages.
---

# Course Lab Discovery

## Overview

Find the right local inputs before PDF decoding, workspace mutation, or report drafting begins, and surface uncertainty instead of pretending the match is obvious.

Use the model to derive bilingual search topics at run time. The Python script should stay a one-query scorer, not a hardcoded translation table.

## Standalone Tool Contract

### Use Independently When
- You need a course-aware inventory of candidate handouts, reference reports, raw-data bundles, picture-result folders, result directories, simulations, or LaTeX templates before any report workspace exists.
- The experiment name, course, language, or source location is ambiguous and must be resolved into ranked candidates plus unresolved gaps.

### Minimum Inputs
- A course or lab context when known, such as the course folder, syllabus label, or handout collection root.
- An experiment query or candidate experiment name, including language variants when relevant.
- Search roots for local handouts, data bundles, reference reports, result folders, simulations, and templates; if a root is unavailable, declare it as an unresolved search gap.

### Optional Workflow Inputs
- Desired report/template language (`english` or `chinese`) and any known experiment date or instructor metadata for tie-breaking only.
- Existing discovery cache manifests from the same experiment-specific query.
- A downstream workspace target that can receive an experiment-specific discovery manifest later.

### Procedure
- Use the local `scripts/discover_sources.py` command described below once per meaningful query variant.
- Save manifests with experiment-specific filenames such as `/tmp/course-lab-discovery-<experiment-safe-name>-<variant>.json`; never reuse one generic manifest across experiments.
- Preserve ranked alternatives and unresolved source categories instead of forcing a single match when the evidence is weak.

### Outputs
- A ranked source inventory covering the relevant handout, reference report, raw data, picture-result, result-directory, simulation, and template categories.
- Optional experiment-specific discovery JSON manifest with candidate paths and unresolved categories.
- A concise handoff note naming the selected source candidates and any roots that were unavailable or ambiguous.

### Validation
- The result states which roots were searched and which source categories were found, missing, or ambiguous.
- Any saved manifest uses an experiment-specific name and can be read by later workspace/template tooling.
- Ambiguous matches remain visible as alternatives instead of being silently collapsed.

### Failure / Reroute Signals
- Missing search root: in standalone mode, report the missing root and continue with available roots only if the remaining evidence is useful; in full-workflow mode, reroute to source-location clarification.
- Multiple plausible experiments: return ranked candidates and request a selection before downstream mutation.
- No credible handout or template candidate: stop before workspace creation and surface a discovery gap.

### Non-Ownership
- Does not decode PDFs, transcribe data, create report workspaces, mutate TeX, or choose final scientific scope.
- Does not promote discovery guesses into confirmed inputs without user or downstream confirmation.

## Optional Workflow Metadata
- Suggested future role label: `preparer`.
- Typical upstream tools: user/course query, filesystem search context.
- Typical downstream tools: `course-lab-handout-normalization`, `course-lab-workspace-template`, `course-lab-data-transfer`.

## Primary Command

```bash
python3 /root/.codex/skills/course-lab-discovery/scripts/discover_sources.py \
  --course "Modern Physics Experiments" \
  --experiment "晶体光学性质" \
  --max-results 8
```

When later steps need a manifest, use an experiment-specific filename such as `--output-json /tmp/course-lab-discovery-<experiment-safe-name>-<variant>.json` so parallel report runs do not collide. Use short variant suffixes like `en` and `zh` when you run bilingual discovery.

If the report language is already known, pass `--template-language english` or `--template-language chinese` so the JSON only returns that template group.

## Workflow

1. Ask for the course name if unknown.
2. Use the model to derive one English and one Chinese search topic for the experiment. If the user already gave both, keep both.
3. Run `scripts/discover_sources.py` once per query variant with the same `--course`. If the report language is already chosen, also pass `--template-language english|chinese`. If you save manifests, name them after the experiment, for example `/tmp/course-lab-discovery-<experiment-safe-name>-en.json` and `/tmp/course-lab-discovery-<experiment-safe-name>-zh.json`.
4. Compare the result sets. Prefer candidates that are strong in both runs, and surface disagreements instead of forcing a silent choice.
5. Review `handouts`, `reference_reports`, `data_files`, `data_groups`, `simulation_dirs`, `simulation_files`, `picture_result_dirs`, `picture_result_files`, `signatory_files`, `result_dirs`, `templates`, `excluded_templates`, and `warnings`.
6. If `template_language_requested` is `null`, show both `templates.english` and `templates.chinese` instead of flattening them into one list.
7. If `template_language_requested` is `english` or `chinese`, only show that language group and keep the other out of the JSON.
8. For bundle templates, use the bundle label and `template_root` plus `template_entry`; do not present a bare `main.tex` choice.
9. Surface result-folder state: whether a likely result directory exists, which `.tex` files it has, and whether `main.tex` is present.
10. Present valid template candidates outside `dont use`, then confirm the experiment target before invoking `course-lab-handout-normalization` or `course-lab-workspace-template`.
11. If a human or parent workflow manually promotes selected references, preserve the full dict entry; manual promotion must not collapse `selected_reference_reports` to plain strings.

## Quick Reference

### Contract Notes

- Use local `scripts/discover_sources.py` as the canonical discovery contract.
- Produce a ranked view of handouts, decoded JSON, references, complete data-file discovery, data groups, simulation directories, simulation files, picture-result directories, picture-result files, signatory files, result directories, language-grouped templates, excluded templates, and warnings.
- Surface all strong same-experiment reference reports through `selected_reference_reports` instead of hiding them behind the ranked shortlist.
- Emit `reference_selection_status` as `selected`, `ambiguous`, or `none_found` so downstream steps can distinguish a confident same-experiment bundle from discovery uncertainty.
- Each `selected_reference_reports` entry must preserve the full dict contract:
  - `pdf_path`
  - `expected_decoded_markdown_path`
  - `expected_decoded_json_path`
- Predict canonical sibling decode paths for each selected reference report and store them under `expected_decoded_markdown_path` plus `expected_decoded_json_path`.
- Translate the experiment topic into English and Chinese with the model, run discovery for each query independently, then compare the result sets.
- Confirm the experiment target and show template options before any later skill mutates files.
- If the top matches are weak, tied, or zero-score, keep that uncertainty visible and ask the user instead of choosing silently.
- Template candidates now carry `template_language`, `template_kind`, `template_root`, `template_entry`, and a human-friendly `label`.
- For mechanics-style or other multi-dataset experiments, discovery must surface all matched tabular data files such as `.csv`, `.tsv`, `.xls`, and `.xlsx`, not only the first few ranked files.
- When data files cluster under one matched experiment subtree, expose that subtree through `data_groups` and keep companion scan sources such as `data.pdf`, record-book scans, or source images visible alongside the tables.

| Need | Look at |
|---|---|
| Best handout or reference PDF | `handouts`, `reference_reports` |
| Already-decoded PDF candidates | `handout_decoded_json`, `reference_decoded_json` |
| Raw or transferred data location | `data_files`, `data_groups` |
| Complete CSV or spreadsheet bundle | `data_groups[*].csv_files` |
| Scanned record-book pages or data PDFs | `data_groups[*].scan_files` |
| Other experiment-local data artifacts such as notes or README files | `data_groups[*].other_files` |
| Simulation folders or source files | `simulation_dirs`, `simulation_files` |
| Picture-result folders and files | `picture_result_dirs`, `picture_result_files` |
| Signatory inputs | `signatory_files` |
| Existing draft state | `result_dirs[*].tex_files`, `result_dirs[*].manifest_*` |
| Template choices by language | `template_language_requested`, `templates.<language>` |
| Template metadata | `templates.<language>[*].template_kind`, `template_root`, `template_entry`, `label` |
| Excluded template pool | `excluded_templates.<language>` |
| Missing roots or other setup problems | `warnings` |

## Boundary Rules

- This skill discovers and confirms sources. It does not decode PDFs, create workspaces, edit TeX, or draft report prose.
- This skill discovers and confirms same-experiment reference report paths, but it does not decode those references itself.
- Discovery owns the selected-reference bundle shape. Downstream steps must treat plain strings as malformed and reroute instead of guessing missing decode metadata.
- Do not hardcode translation aliases inside the Python scorer. Topic translation belongs to the model-driven workflow above.
- Treat simulation discovery as query-specific. If no simulation candidate seems relevant, return `"not exist"` instead of a low-score guess.
- Do not reuse a single generic discovery manifest filename across different experiments. Saved discovery JSON should be experiment-specific.
- For data discovery, completeness beats top-N truncation once a matched experiment bundle is identified. Do not hide later CSV files just because `--max-results` is small.
- Keep grouped data discovery query-specific. Only surface full CSV and scan bundles for experiment roots that actually match the query; do not inflate weak unrelated folders into fake bundles.
- Detect template language from the first directory under `AI_works/resources/latex_templet/` and keep template results grouped by that language.
- Exclude any template path under a directory literally named `dont use`, even if the caller asks for a language-specific view.
- Do not present bundle templates as a bare `main.tex` option. Use the bundle label and metadata instead.
- Do not silently default to a template when multiple valid choices exist.
- Do not treat zero-score or near-tied matches as confirmed.
- If a result folder has multiple `.tex` files and none is `main.tex`, carry that ambiguity forward for `course-lab-workspace-template` instead of choosing a canonical file here.
- Surface missing roots, empty pools, and excluded-template warnings instead of masking them.

## Common Mistakes

- Treating a low-score match as certain because the filename looks close enough. Show the shortlist.
- Reusing one shared `/tmp/course-lab-discovery.json` file while multiple experiment runs are active.
- Flattening English and Chinese templates into one mixed list before the user has picked a report language.
- Letting a multi-file experiment collapse into one or two top-ranked data files. If a mechanics run has seven CSVs and scan pages, discovery should keep that full bundle visible.
- Returning a pile of unrelated low-score data folders as if they were equivalent bundles. Only strong or near-tied experiment roots should be grouped.
- Showing a bundle template to the user as plain `main.tex` instead of the actual bundle template name.
- Jumping into MinerU decoding during discovery. That belongs to `course-lab-handout-normalization`.
- Copying a template or editing `main.tex` during discovery. That belongs to `course-lab-workspace-template`.
- Ignoring `excluded_templates`. Paths under `dont use` stay excluded from template candidates and should remain visible only as excluded references.
- Ignoring the current result-directory state. Downstream skills need to know whether the workspace is fresh or already populated.
