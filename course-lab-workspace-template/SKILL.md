---
name: course-lab-workspace-template
description: Use when a course lab-report run has already confirmed the experiment, template choice, and modify-or-rewrite decision and now needs to create or reuse the report workspace, select the canonical TeX file, and establish the baseline file contract before metadata or drafting begins.
---

# Course Lab Workspace Template

## Overview

Create or reuse the report workspace under `AI_works/results/<experiment-safe-name>/` and make the baseline report contract explicit before later skills touch metadata or body content.

This skill owns canonical TeX selection, template copy or refresh, local `build.sh`, procedures-markdown creation, and `\NeedsInput{...}` placeholder macro readiness.

It supports both standalone `.tex` templates and language-scoped template bundles whose root contains `main.tex` plus companion assets.

## Standalone Tool Contract

### Use Independently When
- You need to create or reuse a lab-report workspace from a selected template before metadata, scaffold, data, or drafting work begins.
- The canonical TeX entrypoint and workspace manifest must be established for later standalone tools.

### Minimum Inputs
- Experiment name or safe workspace slug.
- Template choice: standalone `.tex` file or language-scoped template bundle root with entrypoint such as `main.tex`.
- Output workspace target and modify-vs-rewrite decision.
- Report/template language when the template set is language-scoped.

### Optional Workflow Inputs
- Experiment-specific discovery JSON as cache input for candidate templates and result directories.
- Normalized handout artifacts for naming or procedure handoff only.
- Existing workspace manifest to reuse if it still matches the requested template and workspace.

### Procedure
- Use the local workspace setup command described below and keep `/tmp/course-lab-discovery-*.json` as cache input, not the canonical workspace artifact.
- Copy companion assets for bundle templates and record the selected `template_root`, `template_entry`, and `template_language`.
- Write `notes/workspace_manifest.json` and any requested secondary manifest without mutating unrelated report content.

### Outputs
- Initialized or reused report workspace.
- Canonical TeX path and build-script path when available.
- `notes/workspace_manifest.json` containing template kind, language, root, entrypoint, companion assets, discovery-cache input, procedure Markdown path, and `needs_input_*` fields.

### Validation
- The canonical TeX entrypoint exists and is inside the intended workspace.
- The workspace manifest records template provenance and any copied companion assets.
- Template placeholder support such as `\NeedsInput` is preserved or injected only by the existing setup script.

### Failure / Reroute Signals
- Missing template or output target: in standalone mode, stop and request the path; in full-workflow mode, reroute to template/source selection.
- Ambiguous template language: report the available template languages and wait for a selection before creating a workspace.
- Existing workspace conflict: surface the conflict and required reuse/overwrite decision without destructive changes.

### Non-Ownership
- Does not resolve author metadata, fill scientific body sections, decode handouts, transcribe data, or run final QC.
- Does not treat discovery cache files as permanent workspace manifests.

## Optional Workflow Metadata
- Suggested future role label: `preparer`.
- Typical upstream tools: `course-lab-discovery`, selected template source.
- Typical downstream tools: `course-lab-metadata-frontmatter`, `course-lab-run-plan`, `course-lab-body-scaffold`.

## Primary Command

```bash
python3 /root/.codex/skills/course-lab-workspace-template/scripts/ensure_report_workspace.py \
  --discovery-json /tmp/course-lab-discovery-interference-lab-en.json \
  --mode new \
  --template "/root/grassman_projects/AI_works/resources/latex_templet/english/tau_templet copy.tex" \
  --output-json /tmp/course-lab-workspace.json
```

Bundle example:

```bash
python3 /root/.codex/skills/course-lab-workspace-template/scripts/ensure_report_workspace.py \
  --experiment "晶体光学性质" \
  --mode rewrite \
  --template "/root/grassman_projects/AI_works/resources/latex_templet/chinese/Rho_Class___Research_Article_Template_CN(translated by SYSU 2024 physics department Guangwei Lang)" \
  --output-json /tmp/course-lab-workspace-crystal-optics.json
```

Use `--canonical-tex existing.tex` when `modify` or `rewrite` must target a specific existing file. Explicit `--course`, `--experiment`, `--results-root`, and source-list flags still override values from the discovery cache when both are present.

## Workflow

1. Confirm discovery is done and identify the correct experiment-specific discovery cache, such as `/tmp/course-lab-discovery-<experiment-safe-name>-en.json` or `/tmp/course-lab-discovery-<experiment-safe-name>-zh.json`.
2. Confirm the workspace mode:
   - `new` for a fresh report from a chosen template,
   - `modify` for editing an existing canonical `.tex`,
   - `rewrite` for copying the template back onto the canonical file while keeping a timestamped backup.
3. Identify whether the chosen template is a standalone `.tex` file or a bundle directory rooted at `main.tex`.
4. Run `ensure_report_workspace.py` with `--discovery-json ...` first so course, experiment, results-root, and discovered source lists come from the same cache context unless you intentionally override them.
5. Inspect the current result directory state. If multiple `.tex` files exist and none is clearly canonical, stop and carry that ambiguity back to the user with `--canonical-tex` as the follow-up.
6. When the chosen template is the stock English tau scaffold, confirm that the canonical TeX now exposes family-compatible headings such as `Objectives`, `Experimental Procedure and Observations`, `Results and Analysis`, and `Appendix`, and that the late-stage-owned sections are placeholder- or overwrite-ready instead of being left as generic boilerplate.
7. Review `canonical_tex`, `workspace`, `procedures_markdown`, `build_script`, `template_kind`, `template_language`, `template_root`, `template_entry`, `copied_companion_assets`, `discovery_cache_input`, and the `needs_input_*` manifest fields before handing off to `course-lab-metadata-frontmatter` or later drafting skills.

## Quick Reference

### Contract Notes

- Use local `scripts/ensure_report_workspace.py` as the canonical workspace tool.
- Read the chosen discovery cache first when one was saved by `course-lab-discovery`, for example `--discovery-json /tmp/course-lab-discovery-<experiment-safe-name>-<variant>.json`.
- Accept either:
  - a standalone template file such as `AI_works/resources/latex_templet/english/tau_templet copy.tex`, or
  - a bundle directory such as `AI_works/resources/latex_templet/chinese/Rho_Class___Research_Article_Template_CN(...)/` that contains `main.tex`.
- Create or reuse `AI_works/results/<experiment-safe-name>/`.
- Produce or confirm the canonical report file.
- Keep the standard subdirectories, local `build.sh`, and `<experiment-safe-name>_procedures.md` in place.
- For single-file templates, copy the chosen `.tex` into the canonical report path.
- For bundle templates, copy `main.tex` plus companion assets into the workspace while preserving bundle-relative paths.
- Ensure the canonical TeX file can render `\NeedsInput{...}` placeholders by inserting the macro block when it is missing.
- For the stock English `tau_templet copy.tex`, normalize the generic scaffold into a later-skill-friendly baseline by converting stock draft prose into `\NeedsInput{...}` placeholders, renaming stock headings to the downstream family contract, and materializing an appendix section with `% course-lab-final-staging:allow-overwrite`.
- Treat `/tmp/course-lab-discovery-*.json` as cache input, not as the canonical workspace artifact.
- Write `notes/workspace_manifest.json` and optionally a second manifest via `--output-json`.
- Record `template_language`, `template_kind`, `template_root`, `template_entry`, and `copied_companion_assets` in the workspace manifest.
- Surface ambiguity when multiple `.tex` files exist and no canonical file has been confirmed.

| Situation | Action |
|---|---|
| Discovery already saved an experiment-specific cache file | Pass `--discovery-json /tmp/course-lab-discovery-<experiment-safe-name>-<variant>.json` first |
| Fresh report from an English single-file template | `--mode new --template /root/grassman_projects/AI_works/resources/latex_templet/english/...tex` |
| Fresh or rewritten report from a Chinese bundle template | `--mode new` or `--mode rewrite --template /root/grassman_projects/AI_works/resources/latex_templet/chinese/<bundle-dir>` |
| Existing canonical file should be edited in place | `--mode modify` |
| Existing canonical file should be replaced from template | `--mode rewrite --template ...` |
| One existing `.tex` file and no `main.tex` | `modify` can reuse it automatically |
| Multiple `.tex` files and no confirmed canonical file | Stop and ask for `--canonical-tex` |
| Template lacks `\NeedsInput` support | Let the script inject the placeholder macro block |
| Template is the stock English tau scaffold | Normalize its headings and boilerplate into the course-lab family’s placeholder- and overwrite-ready baseline |

## Boundary Rules

- This skill starts after discovery, not before it.
- This skill does not choose the experiment or template silently.
- This skill does not decode handouts, normalize sections, or draft front matter.
- This skill does not interpret data, write discussion prose, or run final QC.
- `new` mode must not overwrite an existing canonical file.
- `modify` mode must not invent a canonical file when none exists.

## Common Mistakes

- Running workspace setup before the template choice is confirmed.
- Reusing one generic `/tmp/course-lab-discovery.json` name after discovery switched to experiment-specific filenames.
- Treating the `/tmp` discovery file as a permanent workspace artifact instead of a cache input.
- Treating a bundle directory like a single `.tex` file and missing its companion assets.
- Treating a folder with several `.tex` files as if `main.tex` were obvious when it is not.
- Using `rewrite` without noticing that it will replace the canonical file and create a backup.
- Assuming the template already defines `\NeedsInput{...}`.
- Leaving the stock English tau template unchanged so later skills treat generic scaffold prose as authored content and refuse to overwrite owned sections.
- Letting workspace setup drift into metadata or body drafting.

## Resources

- `scripts/ensure_report_workspace.py`: local workspace initializer
- `scripts/common.py`: local repo-root and path helpers
- `assets/build.sh`: local build-script template copied into each workspace
- `tests/test_ensure_report_workspace.py`: regression coverage for workspace creation and canonical-file reuse
