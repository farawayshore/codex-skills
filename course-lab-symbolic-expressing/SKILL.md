---
name: course-lab-symbolic-expressing
description: Use when a course lab-report run has explicit handout, calculation-code, and processed-result artifacts and a selected result needs temporary TeX mathematical procedure support before another skill consumes the returned path.
---

# Course Lab Symbolic Expressing

## Overview

Use this optional standalone helper to explain how a selected processed result follows from the handout and calculation code. It writes temporary TeX-like formula/procedure artifacts and returns the path to the requesting skill.

## When to Use

- A caller already knows the handout path, calculation-code path, processed-result path, and target result key.
- A result needs undergraduate-readable mathematical procedure support.
- Another skill, such as later final-staging work, will consume a returned temp TeX path.
- Workspace-local temporary output is preferred, or the caller explicitly provides a `/tmp` output directory.

Do not use this skill to recompute official results, mutate `main.tex`, interpret physics, compare theory, place figures, compile, or run QC.

## Output Contract

- Use local `scripts/render_symbolic_explanation.py`.
- Require explicit `--handout`, `--calculation-code`, `--processed-result`, `--result-key`, `--output-dir`, and `--output-response-json`.
- Return the generated `tex_path` through response JSON.
- Keep unresolved handout/code/result mismatches visible instead of inventing derivations.
- Default callers should use workspace-local temp output such as `analysis/symbolic_expressing/tmp/`; callers may override to `/tmp/...` for one-shot use.
- This skill does not mutate `main.tex` or discover files by scanning the workspace.

## Primary Command

```bash
python3 /root/.codex/skills/course-lab-symbolic-expressing/scripts/render_symbolic_explanation.py \
  --handout "/path/to/decoded_handout.md" \
  --calculation-code "/path/to/analysis/process_data.py" \
  --processed-result "/path/to/analysis/derived_uncertainty.json" \
  --result-key "wave_speed" \
  --output-dir "/path/to/results/<experiment>/analysis/symbolic_expressing/tmp" \
  --output-response-json "/path/to/results/<experiment>/analysis/symbolic_expressing/tmp/wave_speed_symbolic_response.json"
```

## Workflow

1. Read the handout first for official formulas, symbols, units, and result meaning.
2. Read the calculation code for the actual expression chain used for the selected result.
3. Read the processed result artifact for stored expressions, values, units, and uncertainty support.
4. Write a compact temporary TeX artifact with the formula chain and calculation route.
5. Write response JSON with `tex_path`, source trace, and `unresolved` notes.
6. Return the response path or printed TeX path to the caller.

## Common Mistakes

- Mutating `main.tex` directly instead of returning a path.
- Treating this helper as a required stage between data processing and final staging.
- Recomputing results instead of explaining the existing calculation route.
- Hiding handout/code mismatches or missing formula evidence.
- Scanning for source files instead of requiring explicit caller-owned paths.
