---
name: course-lab-finalize-qc
description: Use when a course lab-report run already has a stable figure-placed draft and now needs standalone build refresh, compile-and-QC execution, PDF-size gating, page-count verification, and final handoff reporting without reclaiming report writing.
---

# Course Lab Finalize QC

## Overview

Use this skill as the standalone final compile, QC, and handoff package for a lab report.

This package is independent and uses only local copied tools under `/root/.codex/skills/course-lab-finalize-qc/` for direct QC work. It refreshes the workspace build script, compiles the report, runs the local QC checker, inspects TeX build output for layout diagnostics such as `Overfull \hbox` or `Float too large`, measures the final PDF against the `20 MB` size cap, records the compiled PDF page count, and warns when the result falls outside the preferred `20-30` page band before handoff.

## When to Use

- The experiment is already confirmed.
- The canonical report workspace and `main.tex` already exist.
- `course-lab-final-staging` already assembled the late non-figure draft.
- `course-lab-figure-evidence` already placed the late figures.
- The run now needs compile, QC, and handoff reporting only.

Do not use this skill to decode handouts, write or rewrite report prose, execute modeling, stage figures, or take over direct report writing.

## Output Contract

- Use local `/root/.codex/skills/course-lab-finalize-qc/scripts/finalize_qc.py` as the main entrypoint.
- Use local `/root/.codex/skills/course-lab-finalize-qc/scripts/report_qc.py` as the copied QC checker.
- Keep runtime dependencies local to `/root/.codex/skills/course-lab-finalize-qc/`.
- Refresh `build.sh` into the report workspace from the local copied asset when the workspace copy is missing or stale.
- Run the compile loop through `bash build.sh`.
- Treat TeX layout diagnostics from the compile output, including overflow warnings such as `Overfull \hbox` and `Float too large`, as QC failures that must be surfaced in the handoff summary.
- Enforce a hard `20 MB` PDF-size gate.
- Record compiled PDF page count and emit a visible warning when the report falls outside the preferred `20-30` page band.
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
9. Emit the final summary and unresolved-gap artifacts.
10. If the PDF is oversized, hand off to `$compress-png`.

## Boundary Rules

- This skill owns compile, QC, and handoff only.
- This skill does not own abstract rewriting or catalogue insertion.
- This skill does not own direct report writing.
- This skill does not own figure staging or figure placement.
- This skill does not own handout decoding, data transfer, data processing, or modeling.
- This skill should fail clearly instead of silently repairing report content.
- This skill should treat compile-time layout overflow as a QC finding, not as a harmless warning to ignore.
- Keep all direct runtime tool usage local to this standalone folder.

## Common Mistakes

- Reaching back into parent or sibling skill folders instead of using the copied local tools.
- Treating page-count guidance as a hard failure instead of a visible QC warning.
- Trusting source-only heuristics while ignoring TeX overflow diagnostics that already prove the rendered PDF is broken.
- Letting this skill reclaim late writing work that belongs upstream.
- Compressing or converting images inside this skill instead of handing oversized PDFs off to `$compress-png`.

## Resources

- `assets/build.sh`: local copied build asset
- `references/quality_gate.md`: local copied QC checklist
- `scripts/common.py`: local helper functions for JSON, file copying, subprocess capture, and PDF metadata
- `scripts/report_qc.py`: local copied report checker
- `scripts/finalize_qc.py`: local final QC orchestrator
- `tests/baseline_failures.md`: baseline notes for why the standalone skill is needed
