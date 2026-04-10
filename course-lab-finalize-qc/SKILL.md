---
name: course-lab-finalize-qc
description: Use when a course lab-report run already has a stable figure-placed draft and now needs standalone build refresh, compile-and-QC execution, PDF-size gating, page-count verification, and final handoff reporting without reclaiming report writing.
---

# Course Lab Finalize QC

## Overview

Use this skill as the standalone final compile, QC, and handoff package for a lab report.

This package is independent and uses only local copied tools under `/root/.codex/skills/course-lab-finalize-qc/` for direct QC work. It refreshes the workspace build script, compiles the report, runs the local QC checker, inspects TeX build output for layout diagnostics such as `Overfull \hbox` or `Float too large`, measures the final PDF against the `20 MB` size cap, records the compiled PDF page count, and warns when the result falls outside the preferred `20-30` page band before handoff.

When discovery already produced a same-experiment reference bundle, this skill may also run a detector-only reference-procedure comparison through `--discovery-json`. That comparison must read only the discovery-produced `selected_reference_reports` contract, must not rediscover or decode references here, and must emit caller-facing reroute instructions instead of repairing report content.

## Standalone Tool Contract

### Use Independently When

- A figure-placed draft or canonical `main.tex` is ready for compile/QC/handoff.
- The caller needs build refresh, compile output inspection, PDF-size gating, page-count reporting, and issue-ticket style QC findings.
- Optional evidence-plan, discussion-candidate, discovery, examiner-rubric, or same-experiment reference inputs are available for additional checks.
- The tool should report patch plans and rerun hints, not silently repair report prose.
- `course-lab-final-staging` already assembled the late non-figure draft, `course-lab-figure-evidence` already placed the late figures, and the run now needs compile, QC, and handoff reporting only.

### Minimum Inputs

- `--main-tex` pointing to the canonical TeX entrypoint in a report workspace.
- `--procedures` pointing to the handout/procedure coverage artifact used by local QC.
- Output paths for `final_qc_summary.json`, `final_qc_summary.md`, and `final_qc_unresolved.md`.
- A build path that can run `bash build.sh`; the local `assets/build.sh` is used when the workspace copy is missing or stale.

### Optional Workflow Inputs

- `--evidence-plan` from figure evidence to check planned figure/evidence markers.
- `--discussion-candidates` or newer discussion-ideas handoff artifacts for Further Discussion QA.
- `--discovery-json` containing `selected_reference_reports` and `reference_selection_status` for detector-only same-experiment comparison.
- An external examiner rubric or senior advice note supplied by the caller; if absent, use local `references/quality_gate.md` and label advice as generic.

### Procedure

- Use only local scripts in `/root/.codex/skills/course-lab-finalize-qc/scripts/`.
- Refresh `build.sh`, compile, inspect layout diagnostics, run `report_qc.py`, check the hard `20 MB` PDF gate, and record page count.
- Translate QC findings into a score/rubric summary and concrete issue tickets in the human-facing handoff summary.
- Include rerun hints that name the likely upstream tool (`course-lab-final-staging`, `course-lab-figure-evidence`, `$compress-png`, or source discovery) without rewriting content here.
- Preserve declared-unresolved and data-lack findings from reference comparison as visible final handoff risks.

### Outputs

- `final_qc_summary.json` with compile/QC/PDF/reference-comparison status.
- `final_qc_summary.md` with examiner-style score/rubric summary, issue tickets, evidence, and rerun hints.
- `final_qc_unresolved.md` with hard failures, warnings, declared-unresolved items, suspected data-lack items, and oversized-PDF handoff instructions.
- A refreshed workspace `build.sh` when needed, plus the compiled PDF when the build succeeds.

### Validation

- Compile status, PDF existence, layout diagnostics, local QC result, PDF byte size, and page count are recorded.
- Any `20 MB` failure points to `$compress-png`; this skill does not compress or convert images itself.
- Same-experiment reference comparison runs only after compile, local QC, layout, and PDF-size gates pass.
- Declared unresolved/data-lack lanes remain visible in the final summary and unresolved artifacts.
- Local final-QC tests pass.

### Failure / Reroute Signals

- Missing `main.tex`, procedures, build support, or compiled PDF: stop in standalone mode with exact missing paths; in full-report mode, reroute to workspace/template, body-scaffold, final-staging, or build setup as appropriate.
- Compile, layout, local QC, PDF-size, or page-band findings: emit issue tickets and rerun hints without editing report prose.
- Missing evidence plan or discussion handoff: continue only for checks that remain meaningful, then list the missing optional checks as unresolved risks.
- Reference comparison missing structure, missing content, declared unresolved, or suspected data-lack: keep those findings visible and route repairs upstream rather than masking them.

### Non-Ownership

- This tool does not decode handouts, transfer data, compute results, execute modeling, write prose, stage figures, compress images, convert image formats, discover references, decode references, or patch final report content.
- This tool may recommend repairs but does not apply them unless a future explicit repair mode is added.
- This tool does not require a full-workflow controller, examiner agent, senior agent, or native course-lab agent file for standalone use.
- Do not use this skill to decode handouts, write or rewrite report prose, execute modeling, stage figures, or take over direct report writing.

## Optional Workflow Metadata

- Suggested future role label: `examiner`.
- Typical upstream tools: `course-lab-final-staging`, `course-lab-figure-evidence`, optional source discovery.
- Typical downstream tools: `$compress-png` for oversized image assets, or a targeted upstream rerun based on issue tickets.

## Workflow Notes

- Use local `/root/.codex/skills/course-lab-finalize-qc/scripts/finalize_qc.py` as the main entrypoint.
- Use local `/root/.codex/skills/course-lab-finalize-qc/scripts/report_qc.py` as the copied QC checker.
- Use local `/root/.codex/skills/course-lab-finalize-qc/scripts/reference_procedure_compare.py` for the detector-only same-experiment reference comparison gate.
- Keep runtime dependencies local to `/root/.codex/skills/course-lab-finalize-qc/`.
- Refresh `build.sh` into the report workspace from the local copied asset when the workspace copy is missing or stale.
- Run the compile loop through `bash build.sh`.
- Treat TeX layout diagnostics from the compile output, including overflow warnings such as `Overfull \hbox` and `Float too large`, as QC failures that must be surfaced in the handoff summary.
- Enforce a hard `20 MB` PDF-size gate.
- Record compiled PDF page count and emit a visible warning when the report falls outside the preferred `20-30` page band.
- Accept optional `--discovery-json` input when discovery already emitted `selected_reference_reports` and `reference_selection_status`.
- Run the same-experiment reference comparison only after compile, local QC, layout, and PDF-size gates already pass.
- Treat `discussion_ideas` as the canonical Further Discussion QA payload when upstream hands off pre-synthesis idea artifacts, while tolerating legacy `discussion_candidates` files for backward compatibility.
- Read only discovery-produced same-experiment reference selections. This skill is a detector and reroute surface; it does not rediscover references and does not decode them.
- Emit:
  - `final_qc_summary.json`
  - `final_qc_summary.md`
  - `final_qc_unresolved.md`
- If the PDF remains oversized, hand the run off to `$compress-png` instead of compressing or converting images inside this skill.

## Primary Command

```bash
python3 /root/.codex/skills/course-lab-finalize-qc/scripts/finalize_qc.py \
  --main-tex "/path/to/results/<experiment>/main.tex" \
  --procedures "/path/to/results/<experiment>/<experiment-safe-name>_procedures.md" \
  --discovery-json "/path/to/results/<experiment>/course-lab-discovery-<experiment>.json" \
  --evidence-plan "/path/to/results/<experiment>/picture_evidence_plan.json" \
  --discussion-candidates "/path/to/results/<experiment>/discussion_candidates.json" \
  --output-summary-json "/path/to/results/<experiment>/final_qc_summary.json" \
  --output-summary-markdown "/path/to/results/<experiment>/final_qc_summary.md" \
  --output-unresolved "/path/to/results/<experiment>/final_qc_unresolved.md"
```

## Workflow

1. Confirm that the figure-placed draft already exists and that compile/QC/handoff is the only remaining responsibility.
2. Refresh or install the workspace `build.sh` from the local copied asset.
3. Compile through `bash build.sh`.
4. Confirm that the expected `main.pdf` was produced.
5. Inspect compile output for layout diagnostics that indicate visible PDF breakage.
6. Run the local copied `report_qc.py`.
7. Check the final PDF size against the hard `20 MB` cap.
8. Record the compiled PDF page count and surface a warning when it falls outside the preferred `20-30` page band.
9. If `--discovery-json` is present and the earlier gates passed, run the detector-only same-experiment reference comparison against `selected_reference_reports`.
10. Emit the final summary, reroute, and unresolved-gap artifacts.
11. If the PDF is oversized, hand off to `$compress-png`.

## Boundary Rules

- This skill owns compile, QC, and handoff only.
- This skill does not own abstract rewriting or catalogue insertion.
- This skill does not own direct report writing.
- This skill does not own figure staging or figure placement.
- This skill does not own handout decoding, data transfer, data processing, or modeling.
- This skill does not own rediscovery of same-experiment references or MinerU decoding of those references.
- This skill should fail clearly instead of silently repairing report content.
- This skill should treat compile-time layout overflow as a QC finding, not as a harmless warning to ignore.
- Keep all direct runtime tool usage local to this standalone folder.

## Common Mistakes

- Reaching back into external or sibling skill folders instead of using the copied local tools.
- Treating page-count guidance as a hard failure instead of a visible QC warning.
- Trusting source-only heuristics while ignoring TeX overflow diagnostics that already prove the rendered PDF is broken.
- Letting this detector leaf re-own report writing, reference discovery, or reference decoding instead of emitting reroutes for the full-report orchestrator.
- Letting this skill reclaim late writing work that belongs upstream.
- Compressing or converting images inside this skill instead of handing oversized PDFs off to `$compress-png`.

## Resources

- `assets/build.sh`: local copied build asset
- `references/quality_gate.md`: local copied QC checklist
- `scripts/common.py`: local helper functions for JSON, file copying, subprocess capture, and PDF metadata
- `scripts/report_qc.py`: local copied report checker
- `scripts/reference_procedure_compare.py`: local detector-only same-experiment reference comparison helper
- `scripts/finalize_qc.py`: local final QC orchestrator
- `tests/baseline_failures.md`: baseline notes for why the standalone skill is needed
