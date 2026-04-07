# Course Lab Reference Procedure QC Design

## Context

The installed `course-lab-report` family already separates discovery, normalization, late-stage writing, figure placement, and final QC. The current `course-lab-finalize-qc` leaf is intentionally narrow: it refreshes `build.sh`, compiles the report, runs local TeX/QC checks, enforces the PDF-size gate, records page count, and emits a handoff summary.

The next gap is cross-checking the generated final report against same-experiment reference reports written by different people. The goal is not to copy prose or let final QC become a writing orchestrator. The goal is to detect whether the final report has actually presented the procedure and procedure-adjacent result lanes that appear in the existing same-experiment references, then hand precise reroute instructions back to the parent orchestrator.

The user explicitly wants:

- comparison only against same-experiment reference reports
- support for multiple reference reports for the same experiment
- final QC to read only a discovery-produced file for reference selection
- missing reference Markdown to be handled through the existing MinerU path rather than direct decoding inside final QC
- the parent loop to continue until nothing is missing or the remaining gap is truly unsatisfied due to missing data, in which case the report should contain a visible `TBD` or `\NeedsInput{...}` marker and the final handoff should warn about it

## Goals

- Refine `course-lab-discovery` so it can surface all substantive same-experiment reference reports rather than hiding extra references behind a ranked top-N cutoff.
- Make discovery emit a stable reference-selection contract that downstream steps can trust.
- Keep `course-lab-finalize-qc` as a detector leaf rather than expanding it into a repair loop.
- Add a late comparison check that runs only after compile, layout, local report QC, and PDF-size checks already pass.
- Compare the generated `main.tex` against reference-report procedure structure using decoded Markdown as the canonical readable source.
- Treat procedure-style headings broadly enough to catch common variants, including `Experiment Steps`, `Experimental Procedure`, `实验步骤`, `实验过程`, `实验方法`, and `实验结果`.
- Emit machine-readable reroute instructions that tell the parent which upstream leaf should re-own the gap.
- Preserve visible warnings for data-lack cases instead of encouraging fabricated content.

## Non-Goals

- Do not let `course-lab-finalize-qc` scan the reference library on its own.
- Do not let `course-lab-finalize-qc` invoke MinerU or decode PDFs directly.
- Do not let `course-lab-finalize-qc` rewrite report prose, mutate `main.tex`, or drive its own multi-step rerun loop.
- Do not turn the comparison into a semantic plagiarism checker or require textual similarity to one specific reference report.
- Do not make `course-lab-discovery` own PDF decoding.
- Do not make missing reference Markdown a silent skip.

## Recommended Approach

Refine three contracts in a coordinated way:

1. `course-lab-discovery` becomes the single source of truth for same-experiment reference selection.
2. `course-lab-finalize-qc` consumes the discovery artifact and performs a structural coverage comparison only after all earlier QC gates pass.
3. `course-lab-report` keeps ownership of rerouting, rerunning downstream leaves, and deciding when a remaining gap is truly a data-lack `TBD` case.

This keeps discovery responsible for source selection, final QC responsible for diagnostic proof, and the parent responsible for recovery orchestration.

## Discovery Contract Changes

`course-lab-discovery` currently returns ranked `reference_reports`, but that is still a shortlist-oriented view shaped by `--max-results`. That is not strong enough for the new late-stage contract because multiple same-experiment references can exist and all of them matter for comparison.

Add an explicit same-experiment reference bundle to the discovery JSON, for example:

```json
{
  "reference_selection_status": "selected",
  "selected_reference_reports": [
    {
      "pdf_path": "/abs/path/to/reference.pdf",
      "experiment_match_label": "Electro-Optic Modulation",
      "match_score": 123.4,
      "selection_reason": [
        "query:electro optic modulation",
        "contains-query",
        "token-overlap:electro,modulation"
      ],
      "expected_decoded_markdown_path": "/abs/path/to/pdf_markdown/reference/reference.md",
      "expected_decoded_json_path": "/abs/path/to/pdf_decoded/reference/reference.json",
      "current_decoded_markdown_exists": false,
      "current_decoded_json_exists": true,
      "procedure_section_candidates": [
        "实验步骤",
        "实验结果"
      ]
    }
  ]
}
```

Key rules:

- `selected_reference_reports` is not just a mirror of `reference_reports`.
- It must contain every strong same-experiment reference match, not only the first `max_results` entries.
- Add an explicit `reference_selection_status` field so downstream steps can distinguish:
  - `selected`: discovery confidently identified one or more same-experiment references
  - `ambiguous`: discovery found plausible candidates but could not safely confirm the bundle
  - `none_found`: discovery confidently found no same-experiment references
- `selected_reference_reports` may be empty only for `ambiguous` or `none_found`, and the status must disambiguate those cases.
- The parent should stop earlier if discovery remains ambiguous rather than forcing final QC to guess.
- Discovery may compute canonical expected decode paths even when the files do not exist yet. Final QC can then read those paths from the discovery artifact and check current existence at runtime.
- Discovery should still keep the older ranked `reference_reports` view for human inspection, but downstream QC should trust `selected_reference_reports`.

The same-experiment selection rule should prefer:

- exact or strong token/character match to the experiment query
- same course subtree
- multiple strong matches when several reports clearly belong to the same experiment

It should avoid:

- truncating substantive same-experiment references just because `--max-results` is small
- mixing in unrelated experiments with weak fuzzy similarity

## Reference Decode Ownership

Discovery should not decode PDFs. That remains the job of the existing MinerU path through `course-lab-handout-normalization`.

The new contract is:

- discovery selects the reference PDFs and predicts the canonical decode paths
- normalization creates the Markdown and JSON when they are missing
- when multiple selected references still lack Markdown, the parent may batch them through repeated or grouped `course-lab-handout-normalization` calls, but the handoff must stay explicit and path-based rather than allowing final QC to rediscover files on its own
- final QC reads the discovery artifact and verifies whether the expected Markdown now exists

This preserves one source of truth for selection while keeping decode logic in the family leaf that already owns MinerU-backed normalization.

## Final QC Contract Changes

`course-lab-finalize-qc` should add a new optional input:

```bash
--discovery-json "/path/to/course-lab-discovery-<experiment>.json"
```

The new comparison check should run only if:

- build succeeded
- the expected PDF exists
- local report QC passed
- build-layout diagnostics are absent
- PDF-size gate passed

If any of those earlier gates fail, the reference comparison should not run. Final QC should report the earlier hard failure first.

When the earlier gates pass, final QC should:

1. read `selected_reference_reports` from the discovery JSON
2. check whether each selected reference has readable decoded Markdown at the expected path
3. extract procedure/result structure from those Markdown files
4. compare the extracted structure against `main.tex`
5. emit structured reroute instructions instead of making repairs

## Procedure Comparison Rule

Use decoded Markdown as the canonical readable source for late comparison.

Accepted reference heading aliases should include bilingual procedure and procedure-adjacent result headings such as:

- `Experiment Steps`
- `Experimental Procedure`
- `Experiment Procedure`
- `Procedure`
- `Experiment Results`
- `实验步骤`
- `实验过程`
- `实验方法`
- `实验结果`
- numbered forms such as `5. 实验步骤`

The extractor should collect the subtree under those headings and keep:

- subsection titles
- subsubsection titles
- title-adjacent numbered or bulleted operation labels
- short body anchors when no child heading exists but one clear operation block is present

Coverage in `main.tex` should be structural and evidence-based, not prose-copy based. A reference item counts as covered when one of the following is true:

- the normalized title matches a report heading or subsection heading
- the normalized title appears in nearby procedure or result body text
- a short anchor phrase from the reference item appears in the report procedure/results discussion lane
- the item is intentionally present as a visible unresolved marker such as `\NeedsInput{...}` or `TBD` because the parent already proved the data is unavailable

The comparison should inspect the effective TeX content tree rooted at `main.tex`, not only the raw top-level file text. If the report uses local `\input{...}` or `\include{...}` files inside the workspace, final QC should resolve those local includes before matching; if resolution fails, it should surface that as a visible comparison blocker rather than quietly under-reading the report.

The comparison should distinguish at least:

- `missing_structure_items`
- `missing_content_items`
- `blocked_reference_decode_items`
- `declared_unresolved_items`
- `data_lack_suspected_items`

## Reroute Output Contract

Extend `final_qc_summary.json` with a machine-readable comparison block, for example:

```json
{
  "reference_procedure_comparison_pass": false,
  "reference_procedure_comparison_blocked": false,
  "reference_procedure_comparison": {
    "selected_reference_count": 2,
    "blocked_reference_decode_items": [],
    "missing_structure_items": [],
    "missing_content_items": [
      {
        "reference_pdf": "/abs/reference-a.pdf",
        "heading": "5.2.3 观察倍频失真并测量线性工作区",
        "anchor_text": "倍频失真 线性工作区",
        "matched_in_report": false
      }
    ],
    "declared_unresolved_items": [],
    "data_lack_suspected_items": []
  },
  "recommended_reroutes": [
    {
      "target_skill": "course-lab-final-staging",
      "reason_code": "reference-procedure-content-missing",
      "reason_summary": "A same-experiment reference contains a procedure/result lane that is not yet presented in main.tex.",
      "source_reference": "/abs/reference-a.pdf",
      "missing_items": [
        "5.2.3 观察倍频失真并测量线性工作区"
      ],
      "next_after_success": [
        "course-lab-figure-evidence",
        "course-lab-finalize-qc"
      ]
    }
  ]
}
```

State semantics:

- `reference_procedure_comparison_pass = true` only when the comparison actually ran and no missing or blocked items remain.
- `reference_procedure_comparison_blocked = true` when the comparison could not run to completion because selected references lacked required decoded Markdown or another prerequisite from the discovery contract was missing.
- If discovery reports `reference_selection_status = none_found`, final QC may skip the comparison and record a visible warning or neutral note rather than a hard failure. In that branch, `reference_procedure_comparison_pass` should stay `false`, `reference_procedure_comparison_blocked` should stay `false`, and the comparison payload should record `selection_status: "none_found"` with empty item lists so downstream consumers do not infer a hidden pass.
- If discovery reports `reference_selection_status = ambiguous`, final QC should fail with a discovery-facing reroute rather than pretending no references exist.

Recommended routing rules:

- Missing expected reference Markdown: `course-lab-handout-normalization`
- Ambiguous same-experiment reference selection: `course-lab-discovery`
- Missing procedure subsection scaffold or missing owned heading lane: `course-lab-body-scaffold`
- Missing substantive content under an existing lane: `course-lab-final-staging`
- Missing interpretation/evidence support rather than structural presentation: `course-lab-results-interpretation`

## Parent Recovery Changes

`course-lab-report` and its recovery references should add a dedicated reroute lane for this new comparison outcome.

Expected behavior:

1. Final QC reports comparison failures and recommended reroutes.
2. The parent reads those reroutes and sends work back to the owning leaf.
3. After that leaf succeeds, the parent reruns downstream late-stage leaves in order.
4. Final QC runs again.
5. The loop stops only when:
   - no missing items remain, or
   - the remaining items are explicitly marked unresolved because the required data truly does not exist

If a lane cannot be completed because data is genuinely unavailable, the upstream owning leaf should insert a visible `TBD` or `\NeedsInput{...}` marker rather than fabricate content. Final QC should then downgrade the item from hard-missing to declared-unresolved, but it must still warn in the final handoff.

## File-Level Impact

Expected spec-aligned implementation work will likely touch:

- `course-lab-discovery/SKILL.md`
- `course-lab-discovery/scripts/discover_sources.py`
- `course-lab-discovery/tests/test_discovery_ranking.py`
- `course-lab-finalize-qc/SKILL.md`
- `course-lab-finalize-qc/agents/openai.yaml`
- `course-lab-finalize-qc/scripts/finalize_qc.py`
- `course-lab-finalize-qc/scripts/report_qc.py` or a new local comparison helper if separation is cleaner
- `course-lab-finalize-qc/tests/test_finalize_qc.py`
- `course-lab-finalize-qc/tests/test_report_qc.py`
- `course-lab-report/SKILL.md`
- `course-lab-report/references/recovery_matrix.md`
- `course-lab-report/references/leaf_responsibility_matrix.md`

## Test Strategy

Follow test-first changes for both discovery and final QC.

Discovery RED tests:

1. Failing test that multiple same-experiment reference PDFs are all included in `selected_reference_reports`.
2. Failing test that `selected_reference_reports` is not truncated by `--max-results` when the omitted references are still strong same-experiment matches.
3. Failing test that each selected reference includes canonical expected Markdown/JSON decode paths.
4. Failing test that unrelated weak references do not leak into the selected bundle.

Finalize-QC RED tests:

1. Failing test that the new comparison does not run when earlier QC gates already failed.
2. Failing test that missing reference Markdown produces a blocking reroute instead of a silent skip.
3. Failing test that a missing procedure heading from a selected reference becomes a `course-lab-body-scaffold` reroute.
4. Failing test that a present heading but thin/missing content becomes a `course-lab-final-staging` reroute.
5. Failing test that `实验结果` is treated as an allowed comparison heading alias.
6. Failing test that visible `TBD` or `\NeedsInput{...}` markers can downgrade a truly data-lack case to warned-but-declared-unresolved rather than hard-missing.

Parent recovery RED tests:

1. Failing test that the recovery matrix mentions the new reference-procedure comparison reroute lane.
2. Failing test that finalize-QC remains diagnostic-only and does not claim ownership of the rerun loop.

## Open Risks

- Reference reports are heterogeneous. Some authors place execution content under `实验结果` or similarly overloaded headings, so the alias set must stay broad without becoming too fuzzy.
- If the comparison relies too heavily on title text alone, it may miss valid coverage written in compact prose. Short anchor matching is necessary but should stay conservative.
- Discovery-time `current_decoded_markdown_exists` can become stale. The discovery manifest should therefore carry canonical expected decode paths, and final QC should verify current existence when it runs.
- Some experiments may have no trustworthy reference reports. In that case, discovery should surface the uncertainty earlier rather than leaving final QC to guess.

## Recommendation

Implement the refinement as a discovery-manifest-driven late QC extension rather than a new autonomous recovery loop inside `course-lab-finalize-qc`. That yields the behavior the user wants while preserving the installed lab-skill family boundaries:

- discovery selects all same-experiment references
- normalization owns MinerU decode
- final QC proves whether procedure/result lanes are missing
- the parent reroutes to the correct upstream leaf
- unresolved data-lack gaps stay visible as `TBD` warnings rather than fabricated prose
