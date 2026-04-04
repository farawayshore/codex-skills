# Baseline Failures

Date: `2026-04-04`

These RED-phase failures come from the approved design spec and the observed risk patterns discussed during brainstorming and planning.

They are recorded before the final skill wording is written so the documentation responds to real failure modes instead of hypothetical polish requests.

## Expected No-Skill Failure Modes

- Missing planned subskills are easy to overlook when the reviewer focuses only on folders that already exist.
- Existing aligned skills are easy to over-flag for cosmetic wording differences instead of material contract drift.
- The parent orchestrator can be missed because the installed folder is currently a legacy alias, `modern-physics-latex-report-rennovated`, while the canonical skill name is `course-lab-report`.
- Overlap risks tend to be reported as isolated local comments instead of one family-level coherency finding.
- A `SKILL.md` can look current while `scripts/`, `references/`, or `agents/` still imply obsolete ownership or artifact contracts.
- A generic review can collapse `missing` and `needs refinement` into one noisy bucket, which violates the minimum-change rule.

## Documentation Response Required

- Keep `missing`, `needs refinement`, `aligned`, and `boundary/coherency risk` as separate states.
- Require whole-folder inspection, not `SKILL.md` alone.
- Mention frontmatter-based canonical-name resolution and legacy folder aliases.
- Prefer minimum-change judgments and explicit `no action needed` reasons for aligned skills.
- Keep family-level overlap analysis separate from single-skill mismatch notes.
