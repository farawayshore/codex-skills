---
name: course-lab-body-scaffold
description: Use when a course lab-report run already has normalized handout sections plus a current template and now needs section skeleton creation, procedure extraction, stable `% procedure:Pxx` coverage, or a handout-driven body scaffold before data transfer or later interpretation work.
---

# Course Lab Body Scaffold

## Overview

Turn normalized handout structure into a report-body scaffold without drifting into data transcription, calculations, or discussion claims.

This skill owns section ordering, procedure extraction, and placeholder coverage. It should leave a clean handoff for later data, figures, uncertainty, and interpretation skills.

## When to Use

- `course-lab-handout-normalization` has already produced normalized section artifacts.
- The current canonical template or `main.tex` is known.
- The run is ready to build the body skeleton before data transfer and later analysis.
- Procedure steps need stable IDs such as `P01`, `P02`, and matching `% procedure:P01` coverage in TeX.
- The template may be missing required report sections and the run needs a deterministic section plan first.

Do not use this skill to choose the experiment, decode PDFs, transfer data, compute uncertainties, or write final interpretation prose.

## Output Contract

- Use local `scripts/build_body_scaffold.py` as the canonical scaffold-building tool.
- Feed it workspace-local normalized section JSON from `course-lab-handout-normalization` at `/path/to/results/<experiment>/notes/sections.json`, plus the companion Markdown at `/path/to/results/<experiment>/notes/sections.md` when human review is needed, and the current template TeX.
- Produce four local artifacts:
  - scaffold JSON
  - scaffold Markdown summary
  - procedures Markdown
  - TeX scaffold with `% procedure:Pxx` placeholders
- Keep section order aligned with `references/body_scaffold_rules.md`.
- Use `references/report_structure.md` only as structure guidance and depth calibration, not as report wording to copy.
- Keep unresolved structure visible. Do not invent missing procedures, equipment details, or discussion claims.

## Primary Command

```bash
python3 /root/.codex/skills/course-lab-body-scaffold/scripts/build_body_scaffold.py \
  --sections-json "/path/to/results/<experiment>/notes/sections.json" \
  --template-tex "/path/to/results/<experiment>/main.tex" \
  --output-json "/path/to/results/<experiment>/body_scaffold.json" \
  --output-markdown "/path/to/results/<experiment>/body_scaffold.md" \
  --output-procedures "/path/to/results/<experiment>/<experiment-safe-name>_procedures.md" \
  --output-tex "/path/to/results/<experiment>/body_scaffold.tex"
```

## Workflow

1. Confirm that discovery, handout normalization, workspace setup, and front matter are already settled.
2. Read `references/body_scaffold_rules.md` before deciding section order or procedure coverage expectations.
3. Run `scripts/build_body_scaffold.py` against the normalized section JSON and the current template TeX.
4. Review `missing_template_sections`, `procedures`, `scaffold_sections`, and `tex_scaffold`.
5. Make sure every extracted procedure step has a stable `Pxx` ID and a matching `% procedure:Pxx` placeholder in the TeX scaffold.
6. If the handout includes thinking questions, keep them visible under the discussion scaffold instead of answering them early.
7. Hand off the scaffold artifacts to later skills for data transfer, figure evidence, and interpretation work.

## Quick Reference

| Situation | Action |
|---|---|
| Template already has some top-level sections | Reuse that structure input, but still generate the full scaffold contract |
| Template is missing core body sections | Keep them in `missing_template_sections` and emit them in the TeX scaffold |
| Procedure steps exist as list items | Reuse them directly and assign `P01`, `P02`, ... |
| Procedure steps exist only in paragraph text | Extract line-level steps best-effort and keep weak matches visible |
| Thinking questions exist in the normalized handout | Place them under `Assigned Thinking Questions` in the discussion scaffold |
| Equipment details are incomplete | Leave a `\NeedsInput{...}` placeholder instead of inventing details |

## Boundary Rules

- This skill starts only after normalized handout sections and the current template are known.
- This skill builds scaffold artifacts; it does not mutate discovery state or decode new PDFs.
- This skill may prepare placeholders and section order, but it does not transfer raw data or compute results.
- This skill does not convert scaffold placeholders into final polished report prose.
- Keep parent-skill path dependencies out of the workflow. Use the local copied script and local references in this folder.

## Common Mistakes

- Drafting final results prose before data transfer and validation are complete.
- Skipping procedure IDs and leaving later QC with no stable `% procedure:Pxx` markers.
- Treating reference-report structure guidance as wording to copy.
- Letting body scaffold work expand into uncertainty math, figure staging, or final discussion claims.
- Depending on the old parent-skill folder instead of this standalone local toolchain.

## Resources

- `scripts/build_body_scaffold.py`: local scaffold builder
- `scripts/common.py`: local helper module used by the scaffold builder
- `references/body_scaffold_rules.md`: local body-scaffold section-order and procedure-coverage rules
- `references/report_structure.md`: local reference-structure guidance copied for standalone use
- `tests/test_build_body_scaffold.py`: local regression test
