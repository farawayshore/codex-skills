---
name: lab-report-skill-family-auditor
description: Use when a lab-report family summary or planning note may have drifted from the installed skills, when planned subskills may be missing, or when family boundaries, overlap, or coherency need a minimum-change audit.
---

# Lab Report Skill Family Auditor

## Overview

Audit the lab-report skill family against the newest relevant family plan without turning the audit into a blanket rewrite pass.

This skill is audit-only. It prepares support artifacts, inspects whole skill folders, classifies findings as `aligned`, `needs refinement`, `missing`, or `boundary/coherency risk`, and writes one main report under `AI_construction/`.

## When To Use

- A newer `*family-summary*.md` or `*planning*.md` may have changed family responsibilities.
- You want to check the thin parent skill plus the current leaf skills against the latest family plan.
- You need missing planned skills reported separately from refinement-needed existing skills.
- You need family overlap or coherency risks surfaced without redundant rewrite prompts.

Do not use this skill to edit skills automatically, patch `SKILL.md` files directly, or perform a generic repo-wide code review.

## Primary Command

Run the local preparation script first:

```bash
python3 /root/.codex/skills/lab-report-skill-family-auditor/scripts/prepare_family_audit.py \
  --plan /root/grassman_projects/AI_envolving/lab_report_skills/2026-03-27-lab-report-skill-family-summary.md \
  --skills-root /root/.codex/skills \
  --output-dir /root/grassman_projects/AI_construction
```

This writes support artifacts under:

- `AI_construction/audit_support/<plan-stem>/family_manifest.json`
- `AI_construction/audit_support/<plan-stem>/current_family_snapshot.json`

The final report target is:

- `AI_construction/lab_report_skill_family_audit_<plan-stem>.md`

## Workflow

1. Resolve the newest family summary or planning note, unless the user gives an explicit path override.
2. Run `/root/.codex/skills/lab-report-skill-family-auditor/scripts/prepare_family_audit.py`.
3. Read the selected plan, `family_manifest.json`, and `current_family_snapshot.json`.
4. Inspect the cited source files before judging any mismatch.
5. Classify each planned member as exactly one of:
   - `aligned`
   - `needs refinement`
   - `missing`
   - `boundary/coherency risk`
6. Keep family-level overlap findings separate from single-skill findings.
7. Write one main audit report to `AI_construction/` and print a concise terminal summary.

## Minimum-Change Rules

- Prefer `aligned` unless the mismatch is material.
- Only call for refinement when there is contract drift, ownership overlap, stale output or dependency language, a missing required checkpoint, or supporting-file behavior that contradicts the documented boundary.
- Give a short `no action needed` reason for every `aligned` skill.
- Keep `missing` separate from `needs refinement`.
- Do not edit skills automatically.
- Do not generate redundant rewrite prompts for wording-only differences that preserve the same contract.

## Whole-Folder Review Rules

- Do not judge from `SKILL.md` alone.
- Inspect `SKILL.md`, `scripts/`, `references/`, `agents/`, and other local support files that affect ownership or artifact contracts.
- Read `SKILL.md` frontmatter `name:` to resolve canonical skill identity.
- Record legacy folder aliases when a folder name and the canonical skill name differ.

## Report Contract

The report must include:

- chosen plan file and selection reason
- brief family snapshot
- `aligned` skills with short evidence-backed justification
- `needs refinement` skills with concrete mismatch bullets and a detailed refinement prompt
- `missing` planned skills with a detailed creation prompt
- `boundary/coherency risk` findings for overlaps, gaps, or blurred handoffs
- a final minimum-change recommendation section

## Boundaries

- Do not edit skills automatically.
- Do not silently rewrite skills.
- Do not collapse family-level overlap into one local file complaint.
- Do not treat formatting or phrasing differences as defects when the responsibility contract still matches.
