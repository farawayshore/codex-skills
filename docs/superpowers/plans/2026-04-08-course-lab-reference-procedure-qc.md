# Course Lab Reference Procedure QC Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a discovery-manifest-driven reference-procedure comparison gate that keeps `course-lab-finalize-qc` detector-only while surfacing precise parent reroutes.

**Architecture:** Extend `course-lab-discovery` so it emits a stable same-experiment reference bundle with canonical decode paths and explicit selection status. Add a focused comparison helper inside `course-lab-finalize-qc` that reads only the discovery JSON, expands the effective `main.tex` content tree, compares reference procedure/result structure against report content, and emits structured reroute metadata after all earlier QC gates pass. Update skill docs and parent recovery docs last so the written contracts match the tested behavior.

**Tech Stack:** Python 3 standard library (`argparse`, `dataclasses`, `json`, `pathlib`, `re`, `tempfile`, `unittest`), Markdown skill docs, YAML agent prompts, git Lore commits.

---

## File Structure

- Create: `/root/.codex/skills/course-lab-discovery/tests/test_skill_package.py`
- Modify: `/root/.codex/skills/course-lab-discovery/SKILL.md`
- Modify: `/root/.codex/skills/course-lab-discovery/agents/openai.yaml`
- Modify: `/root/.codex/skills/course-lab-discovery/scripts/discover_sources.py`
- Modify: `/root/.codex/skills/course-lab-discovery/tests/test_discovery_ranking.py`
- Create: `/root/.codex/skills/course-lab-finalize-qc/scripts/reference_procedure_compare.py`
- Modify: `/root/.codex/skills/course-lab-finalize-qc/SKILL.md`
- Modify: `/root/.codex/skills/course-lab-finalize-qc/agents/openai.yaml`
- Modify: `/root/.codex/skills/course-lab-finalize-qc/scripts/finalize_qc.py`
- Modify: `/root/.codex/skills/course-lab-finalize-qc/tests/test_finalize_qc.py`
- Create: `/root/.codex/skills/course-lab-finalize-qc/tests/test_reference_procedure_compare.py`
- Modify: `/root/.codex/skills/course-lab-finalize-qc/tests/test_skill_package.py`
- Modify: `/root/.codex/skills/course-lab-report/SKILL.md`
- Modify: `/root/.codex/skills/course-lab-report/references/recovery_matrix.md`
- Modify: `/root/.codex/skills/course-lab-report/references/leaf_responsibility_matrix.md`
- Modify: `/root/.codex/skills/course-lab-report/tests/test_recovery_matrix.py`
- Reference: `/root/.codex/skills/docs/superpowers/specs/2026-04-08-course-lab-reference-procedure-qc-design.md`

## Task 1: RED Discovery Contract Tests

**Files:**
- Create: `/root/.codex/skills/course-lab-discovery/tests/test_skill_package.py`
- Modify: `/root/.codex/skills/course-lab-discovery/tests/test_discovery_ranking.py`

- [ ] **Step 1: Write failing discovery package-contract test**

Create `tests/test_skill_package.py`:

```python
from __future__ import annotations

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class CourseLabDiscoveryPackageTests(unittest.TestCase):
    def test_skill_and_agent_describe_same_experiment_reference_bundle(self) -> None:
        skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        agent_text = (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")

        for text in (skill_text, agent_text):
            self.assertIn("same-experiment", text.lower())
            self.assertIn("reference", text.lower())
            self.assertIn("multiple", text.lower())
            self.assertIn("selected_reference_reports", text)
            self.assertIn("reference_selection_status", text)
            self.assertIn("does not decode", text.lower())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Add failing multi-reference ranking tests**

Append to `tests/test_discovery_ranking.py`:

```python
    def test_selected_reference_reports_include_all_strong_same_experiment_matches(self) -> None:
        temp_root = Path(tempfile.mkdtemp())
        course_root = temp_root / "Modern Physics Experiments"
        course_root.mkdir(parents=True)
        for name in (
            "279964_sysut_23355030 A 电光调制.pdf",
            "300001_sysut_23355030 B 电光调制.pdf",
            "23355030贾儒恺_光泵磁共振.pdf",
        ):
            (course_root / name).write_text("% pdf\n", encoding="utf-8")

        self.addCleanup(lambda: __import__("shutil").rmtree(temp_root))

        with mock.patch("discover_sources.REFERENCE_LIBRARY_ROOT", temp_root):
            payload = reference_selection_payload("Modern Physics Experiments Electro-Optic Modulation")

        self.assertEqual(payload["reference_selection_status"], "selected")
        selected = payload["selected_reference_reports"]
        self.assertEqual(len(selected), 2)
        self.assertTrue(all(item["pdf_path"].endswith(".pdf") for item in selected))
        self.assertTrue(all("电光调制" in Path(item["pdf_path"]).name for item in selected))

    def test_reference_selection_status_distinguishes_ambiguous_from_none_found(self) -> None:
        temp_root = Path(tempfile.mkdtemp())
        course_root = temp_root / "Modern Physics Experiments"
        course_root.mkdir(parents=True)
        (course_root / "vague optics note.pdf").write_text("% pdf\n", encoding="utf-8")

        self.addCleanup(lambda: __import__("shutil").rmtree(temp_root))

        with mock.patch("discover_sources.REFERENCE_LIBRARY_ROOT", temp_root):
            payload = reference_selection_payload("Electro-Optic Modulation")

        self.assertIn(payload["reference_selection_status"], {"ambiguous", "none_found"})
        self.assertEqual(payload["selected_reference_reports"], [])

    def test_selected_reference_reports_expose_expected_decode_paths(self) -> None:
        temp_root = Path(tempfile.mkdtemp())
        course_root = temp_root / "Modern Physics Experiments"
        course_root.mkdir(parents=True)
        pdf_path = course_root / "279964_sysut_23355030 A 电光调制.pdf"
        pdf_path.write_text("% pdf\n", encoding="utf-8")

        self.addCleanup(lambda: __import__("shutil").rmtree(temp_root))

        with mock.patch("discover_sources.REFERENCE_LIBRARY_ROOT", temp_root):
            payload = reference_selection_payload("Modern Physics Experiments Electro-Optic Modulation")

        item = payload["selected_reference_reports"][0]
        self.assertTrue(item["expected_decoded_markdown_path"].endswith(".md"))
        self.assertTrue(item["expected_decoded_json_path"].endswith(".json"))
        self.assertIn("pdf_markdown", item["expected_decoded_markdown_path"])
        self.assertIn("pdf_decoded", item["expected_decoded_json_path"])

    def test_selected_reference_reports_are_not_truncated_by_max_results(self) -> None:
        temp_root = Path(tempfile.mkdtemp())
        course_root = temp_root / "Modern Physics Experiments"
        course_root.mkdir(parents=True)
        for name in (
            "279964_sysut_23355030 A 电光调制.pdf",
            "300001_sysut_23355030 B 电光调制.pdf",
            "300002_sysut_23355030 C 电光调制.pdf",
        ):
            (course_root / name).write_text("% pdf\n", encoding="utf-8")

        self.addCleanup(lambda: __import__("shutil").rmtree(temp_root))

        with mock.patch("discover_sources.REFERENCE_LIBRARY_ROOT", temp_root):
            ranked = top_or_all(
                score_paths(
                    "Modern Physics Experiments Electro-Optic Modulation",
                    list(course_root.glob("*.pdf")),
                    library_root=temp_root,
                ),
                1,
            )
            payload = reference_selection_payload("Modern Physics Experiments Electro-Optic Modulation")

        self.assertEqual(len(ranked), 1)
        self.assertEqual(payload["reference_selection_status"], "selected")
        self.assertEqual(len(payload["selected_reference_reports"]), 3)

    def test_selected_reference_reports_exclude_weak_unrelated_candidates(self) -> None:
        temp_root = Path(tempfile.mkdtemp())
        course_root = temp_root / "Modern Physics Experiments"
        course_root.mkdir(parents=True)
        for name in (
            "279964_sysut_23355030 A 电光调制.pdf",
            "300001_sysut_23355030 B 电光调制.pdf",
            "optics modulation note 光学调制综述.pdf",
        ):
            (course_root / name).write_text("% pdf\n", encoding="utf-8")

        self.addCleanup(lambda: __import__("shutil").rmtree(temp_root))

        with mock.patch("discover_sources.REFERENCE_LIBRARY_ROOT", temp_root):
            payload = reference_selection_payload("Modern Physics Experiments Electro-Optic Modulation")

        selected_names = {Path(item["pdf_path"]).name for item in payload["selected_reference_reports"]}
        self.assertEqual(payload["reference_selection_status"], "selected")
        self.assertIn("279964_sysut_23355030 A 电光调制.pdf", selected_names)
        self.assertIn("300001_sysut_23355030 B 电光调制.pdf", selected_names)
        self.assertNotIn("optics modulation note 光学调制综述.pdf", selected_names)
```

- [ ] **Step 3: Run discovery tests to verify RED**

Run:

```bash
python3 -m unittest \
  /root/.codex/skills/course-lab-discovery/tests/test_skill_package.py \
  /root/.codex/skills/course-lab-discovery/tests/test_discovery_ranking.py
```

Expected: FAIL because `selected_reference_reports`, `reference_selection_status`, and `reference_selection_payload()` do not exist yet and the docs do not mention the new contract.

- [ ] **Step 4: Commit the RED test additions**

Run:

```bash
git -C /root/.codex/skills add \
  course-lab-discovery/tests/test_skill_package.py \
  course-lab-discovery/tests/test_discovery_ranking.py
git -C /root/.codex/skills commit -F - <<'EOF'
Lock the new discovery reference-selection contract with failing tests

These tests capture the required same-experiment multi-reference
selection behavior before any production code changes so discovery
cannot quietly keep a shortlist-only contract.

Constraint: Final QC must consume a discovery-produced reference bundle rather than scanning the library
Rejected: Start by changing discovery logic first | would violate test-first changes for this behavior
Confidence: high
Scope-risk: narrow
Reversibility: clean
Directive: Keep selection status explicit; empty bundles must not hide ambiguity
Tested: Discovery unit tests fail for the missing contract
Not-tested: Production implementation
EOF
```

## Task 2: GREEN Discovery Selection Implementation

**Files:**
- Modify: `/root/.codex/skills/course-lab-discovery/scripts/discover_sources.py`
- Modify: `/root/.codex/skills/course-lab-discovery/SKILL.md`
- Modify: `/root/.codex/skills/course-lab-discovery/agents/openai.yaml`
- Modify: `/root/.codex/skills/course-lab-discovery/tests/test_discovery_ranking.py`
- Modify: `/root/.codex/skills/course-lab-discovery/tests/test_skill_package.py`

- [ ] **Step 1: Implement reference-selection helpers**

Add to `scripts/discover_sources.py`:

```python
REFERENCE_PROCEDURE_SECTION_CANDIDATES = [
    "Experiment Steps",
    "Experimental Procedure",
    "Experiment Procedure",
    "Procedure",
    "Experiment Results",
    "实验步骤",
    "实验过程",
    "实验方法",
    "实验结果",
]


def expected_reference_markdown_path(pdf_path: Path) -> Path:
    return pdf_path.parent / "pdf_markdown" / pdf_path.stem / f"{pdf_path.stem}.md"


def expected_reference_json_path(pdf_path: Path) -> Path:
    return pdf_path.parent / "pdf_decoded" / pdf_path.stem / f"{pdf_path.stem}.json"


def is_substantive_reference_match(item: ScoredPath) -> bool:
    detail_set = set(item.details)
    return (
        "exact-match" in detail_set
        or "contains-query" in detail_set
        or any(detail.startswith("token-overlap:") for detail in detail_set)
    )


def same_reference_cluster(scored: list[ScoredPath]) -> list[ScoredPath]:
    strong = [item for item in scored if is_substantive_reference_match(item)]
    if not strong:
        return []
    best = strong[0]
    best_tokens = set(match_tokens(best.label))
    clustered: list[ScoredPath] = []
    for item in strong:
        item_tokens = set(match_tokens(item.label))
        shared_tokens = best_tokens & item_tokens
        if shared_tokens or normalize_for_match(best.label) in normalize_for_match(item.label):
            clustered.append(item)
    return clustered


def reference_selection_payload(query: str) -> dict[str, object]:
    references = list(iter_files(REFERENCE_LIBRARY_ROOT, suffixes=PDF_SUFFIXES, exclude_parts={"pdf_decoded", "pdf_markdown"}))
    scored = score_paths(query, references, library_root=REFERENCE_LIBRARY_ROOT)
    strong = same_reference_cluster(scored)
    if strong:
        return {
            "reference_selection_status": "selected",
            "selected_reference_reports": [
                {
                    "pdf_path": item.path,
                    "experiment_match_label": item.label,
                    "match_score": round(item.score, 3),
                    "selection_reason": item.details,
                    "expected_decoded_markdown_path": str(expected_reference_markdown_path(Path(item.path))),
                    "expected_decoded_json_path": str(expected_reference_json_path(Path(item.path))),
                    "current_decoded_markdown_exists": expected_reference_markdown_path(Path(item.path)).exists(),
                    "current_decoded_json_exists": expected_reference_json_path(Path(item.path)).exists(),
                    "procedure_section_candidates": REFERENCE_PROCEDURE_SECTION_CANDIDATES,
                }
                for item in strong
            ],
        }
    if any(item.score > 0 for item in scored):
        return {"reference_selection_status": "ambiguous", "selected_reference_reports": []}
    return {"reference_selection_status": "none_found", "selected_reference_reports": []}
```

- [ ] **Step 2: Thread the new selection payload into CLI output**

In `main()` replace the reference-only payload portion with:

```python
    reference_selection = reference_selection_payload(query_text)
    payload = {
        "course": args.course,
        "experiment_query": args.experiment,
        "normalized_query": normalize_for_match(args.experiment),
        "reference_reports": top_or_all(
            score_paths(query_text, references, library_root=REFERENCE_LIBRARY_ROOT),
            args.max_results,
        ),
        **reference_selection,
        "reference_decoded_json": decoded_candidates(REFERENCE_LIBRARY_ROOT, query_text, args.max_results),
        "warnings": warnings,
    }
```

- [ ] **Step 3: Update skill docs and agent prompt minimally**

Add to `course-lab-discovery/SKILL.md` and `agents/openai.yaml`:

```text
- Surface all strong same-experiment reference reports through `selected_reference_reports`.
- Emit `reference_selection_status` as `selected`, `ambiguous`, or `none_found`.
- Predict canonical `pdf_markdown` and `pdf_decoded` paths for selected references.
- Discovery confirms and emits source paths only; it does not decode the reference PDFs itself.
```

- [ ] **Step 4: Run discovery tests to verify GREEN**

Run:

```bash
python3 -m unittest \
  /root/.codex/skills/course-lab-discovery/tests/test_skill_package.py \
  /root/.codex/skills/course-lab-discovery/tests/test_discovery_ranking.py
```

Expected: PASS

- [ ] **Step 5: Commit the discovery implementation**

Run:

```bash
git -C /root/.codex/skills add \
  course-lab-discovery/SKILL.md \
  course-lab-discovery/agents/openai.yaml \
  course-lab-discovery/scripts/discover_sources.py \
  course-lab-discovery/tests/test_discovery_ranking.py \
  course-lab-discovery/tests/test_skill_package.py
git -C /root/.codex/skills commit -F - <<'EOF'
Preserve all same-experiment reference reports in discovery

Discovery now emits a detector-facing reference bundle with explicit
selection status and canonical decode paths so downstream QC no longer
has to rediscover or guess which references matter.

Constraint: Same-experiment references may have multiple substantive matches
Rejected: Reuse the ranked shortlist as the QC contract | `max-results` truncation would hide references
Confidence: high
Scope-risk: moderate
Reversibility: clean
Directive: Keep decode ownership out of discovery; emit paths only
Tested: Discovery package and ranking tests
Not-tested: End-to-end parent orchestration
EOF
```

## Task 3: RED Finalize-QC Comparison Tests

**Files:**
- Create: `/root/.codex/skills/course-lab-finalize-qc/tests/test_reference_procedure_compare.py`
- Modify: `/root/.codex/skills/course-lab-finalize-qc/tests/test_finalize_qc.py`
- Modify: `/root/.codex/skills/course-lab-finalize-qc/tests/test_skill_package.py`

- [ ] **Step 1: Write failing comparison-helper tests**

Create `tests/test_reference_procedure_compare.py`:

```python
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


from reference_procedure_compare import compare_reference_procedure_coverage


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class ReferenceProcedureCompareTests(unittest.TestCase):
    def test_experiment_results_heading_alias_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            markdown = root / "reference.md"
            markdown.write_text(
                "# 电光调制\n\n## 实验结果\n\n### 观察倍频失真并测量线性工作区\n\n记录倍频失真与线性工作区。\n",
                encoding="utf-8",
            )
            main_tex = root / "main.tex"
            main_tex.write_text(r\"\"\"\\section{实验结果}\n\\subsection{观察倍频失真并测量线性工作区}\n记录倍频失真与线性工作区。\n\"\"\", encoding="utf-8")
            discovery = root / "discovery.json"
            write_json(discovery, {
                "reference_selection_status": "selected",
                "selected_reference_reports": [{
                    "pdf_path": str(root / "reference.pdf"),
                    "expected_decoded_markdown_path": str(markdown),
                }],
            })

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertTrue(summary["pass"])
            self.assertEqual(summary["missing_content_items"], [])

    def test_numbered_heading_alias_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            markdown = root / "reference.md"
            markdown.write_text(
                "# 电光调制\n\n## 5. 实验步骤\n\n### 5.2.3 观察倍频失真并测量线性工作区\n\n记录倍频失真与线性工作区。\n",
                encoding="utf-8",
            )
            main_tex = root / "main.tex"
            main_tex.write_text(
                r"\section{实验步骤}" "\n"
                r"\subsection{观察倍频失真并测量线性工作区}" "\n"
                r"记录倍频失真与线性工作区。" "\n",
                encoding="utf-8",
            )
            discovery = root / "discovery.json"
            write_json(discovery, {
                "reference_selection_status": "selected",
                "selected_reference_reports": [{
                    "pdf_path": str(root / "reference.pdf"),
                    "expected_decoded_markdown_path": str(markdown),
                }],
            })

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertTrue(summary["pass"])
            self.assertEqual(summary["missing_structure_items"], [])

    def test_body_anchor_only_extraction_matches_report_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            markdown = root / "reference.md"
            markdown.write_text(
                "# 电光调制\n\n## 实验步骤\n\n- 调节滑轨激光器远近点使其与导轨水平。\n",
                encoding="utf-8",
            )
            main_tex = root / "main.tex"
            main_tex.write_text(
                r"\section{实验步骤}" "\n"
                r"我们调节滑轨激光器远近点，使其与导轨保持水平。" "\n",
                encoding="utf-8",
            )
            discovery = root / "discovery.json"
            write_json(discovery, {
                "reference_selection_status": "selected",
                "selected_reference_reports": [{
                    "pdf_path": str(root / "reference.pdf"),
                    "expected_decoded_markdown_path": str(markdown),
                }],
            })

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertTrue(summary["pass"])
            self.assertEqual(summary["missing_content_items"], [])

    def test_missing_markdown_is_blocking_reroute(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main_tex = root / "main.tex"
            main_tex.write_text(r"\section{实验步骤}" "\nAlready present.\n", encoding="utf-8")
            discovery = root / "discovery.json"
            write_json(discovery, {
                "reference_selection_status": "selected",
                "selected_reference_reports": [{
                    "pdf_path": str(root / "reference.pdf"),
                    "expected_decoded_markdown_path": str(root / "missing-reference.md"),
                }],
            })

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertFalse(summary["pass"])
            self.assertTrue(summary["blocked"])
            self.assertEqual(summary["blocked_reference_decode_items"][0]["target_skill"], "course-lab-handout-normalization")

    def test_malformed_discovery_contract_blocks_with_discovery_reroute(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main_tex = root / "main.tex"
            main_tex.write_text(r"\section{实验步骤}" "\n", encoding="utf-8")
            discovery = root / "discovery.json"
            write_json(discovery, {"selected_reference_reports": []})

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertFalse(summary["pass"])
            self.assertTrue(summary["blocked"])
            self.assertEqual(summary["recommended_reroutes"][0]["target_skill"], "course-lab-discovery")

    def test_missing_heading_lane_reroutes_to_body_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            markdown = root / "reference.md"
            markdown.write_text(
                "# 电光调制\n\n## 实验步骤\n\n### 调节黑十字图样水平\n\n通过旋转偏振片调节黑十字图样水平。\n",
                encoding="utf-8",
            )
            main_tex = root / "main.tex"
            main_tex.write_text(r"\section{实验步骤}" "\n只保留了总标题，没有对应子节。\n", encoding="utf-8")
            discovery = root / "discovery.json"
            write_json(discovery, {
                "reference_selection_status": "selected",
                "selected_reference_reports": [{
                    "pdf_path": str(root / "reference.pdf"),
                    "expected_decoded_markdown_path": str(markdown),
                }],
            })

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertFalse(summary["pass"])
            self.assertEqual(summary["missing_structure_items"][0]["target_skill"], "course-lab-body-scaffold")

    def test_present_heading_but_thin_lane_reroutes_to_final_staging(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            markdown = root / "reference.md"
            markdown.write_text(
                "# 电光调制\n\n## 实验结果\n\n### 观察倍频失真并测量线性工作区\n\n记录倍频失真与线性工作区。\n",
                encoding="utf-8",
            )
            main_tex = root / "main.tex"
            main_tex.write_text(
                r"\section{实验结果}" "\n"
                r"\subsection{观察倍频失真并测量线性工作区}" "\n"
                r"只写了一个非常短的占位句子。" "\n",
                encoding="utf-8",
            )
            discovery = root / "discovery.json"
            write_json(discovery, {
                "reference_selection_status": "selected",
                "selected_reference_reports": [{
                    "pdf_path": str(root / "reference.pdf"),
                    "expected_decoded_markdown_path": str(markdown),
                }],
            })

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertFalse(summary["pass"])
            self.assertEqual(summary["missing_content_items"][0]["target_skill"], "course-lab-final-staging")

    def test_local_input_files_are_expanded_before_matching(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            markdown = root / "reference.md"
            markdown.write_text(
                "# 电光调制\n\n## 实验步骤\n\n### 调节偏振片正交并观测黑十字干涉条纹\n\n记录黑十字干涉条纹。\n",
                encoding="utf-8",
            )
            included = root / "sections" / "procedure.tex"
            included.parent.mkdir(parents=True, exist_ok=True)
            included.write_text(
                r"\subsection{调节偏振片正交并观测黑十字干涉条纹}" "\n记录黑十字干涉条纹。\n",
                encoding="utf-8",
            )
            main_tex = root / "main.tex"
            main_tex.write_text(r"\section{实验步骤}" "\n" r"\input{sections/procedure}" "\n", encoding="utf-8")
            discovery = root / "discovery.json"
            write_json(discovery, {
                "reference_selection_status": "selected",
                "selected_reference_reports": [{
                    "pdf_path": str(root / "reference.pdf"),
                    "expected_decoded_markdown_path": str(markdown),
                }],
            })

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertTrue(summary["pass"])
            self.assertEqual(summary["missing_structure_items"], [])

    def test_needsinput_marker_can_be_declared_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            markdown = root / "reference.md"
            markdown.write_text(
                "# 电光调制\n\n## 实验结果\n\n### 观察倍频失真并测量线性工作区\n\n记录倍频失真与线性工作区。\n",
                encoding="utf-8",
            )
            main_tex = root / "main.tex"
            main_tex.write_text(
                r"\section{实验结果}" "\n"
                r"\subsection{观察倍频失真并测量线性工作区}" "\n"
                r"\NeedsInput{This lane is still blocked because the required waveform data is missing.}" "\n",
                encoding="utf-8",
            )
            discovery = root / "discovery.json"
            write_json(discovery, {
                "reference_selection_status": "selected",
                "selected_reference_reports": [{
                    "pdf_path": str(root / "reference.pdf"),
                    "expected_decoded_markdown_path": str(markdown),
                }],
            })

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertFalse(summary["pass"])
            self.assertEqual(summary["missing_content_items"], [])
            self.assertEqual(len(summary["declared_unresolved_items"]), 1)
            self.assertEqual(summary["declared_unresolved_items"][0]["target_skill"], "course-lab-final-staging")

    def test_comparison_gap_reroutes_to_results_interpretation_when_lane_exists_but_has_no_theory_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            markdown = root / "reference.md"
            markdown.write_text(
                "# 电光调制\n\n## 实验结果\n\n### 计算电光系数并与理论值做比较\n\n根据测得的半波电压计算电光系数，并与理论值做比较。\n",
                encoding="utf-8",
            )
            main_tex = root / "main.tex"
            main_tex.write_text(
                r"\section{实验结果}" "\n"
                r"\subsection{计算电光系数并与理论值做比较}" "\n"
                r"我们根据测得的半波电压计算了电光系数。" "\n",
                encoding="utf-8",
            )
            discovery = root / "discovery.json"
            write_json(discovery, {
                "reference_selection_status": "selected",
                "selected_reference_reports": [{
                    "pdf_path": str(root / "reference.pdf"),
                    "expected_decoded_markdown_path": str(markdown),
                }],
            })

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertFalse(summary["pass"])
            self.assertEqual(summary["missing_content_items"][0]["target_skill"], "course-lab-results-interpretation")

    def test_unmarked_data_gap_is_classified_as_data_lack_suspected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            markdown = root / "reference.md"
            markdown.write_text(
                "# 电光调制\n\n## 实验结果\n\n### 观察倍频失真并测量线性工作区\n\n记录倍频失真与线性工作区。\n",
                encoding="utf-8",
            )
            main_tex = root / "main.tex"
            main_tex.write_text(
                r"\section{实验结果}" "\n"
                r"\subsection{观察倍频失真并测量线性工作区}" "\n"
                r"由于本次实验没有保存可用的波形数据，这一部分尚不能完成。"
                "\n",
                encoding="utf-8",
            )
            discovery = root / "discovery.json"
            write_json(discovery, {
                "reference_selection_status": "selected",
                "selected_reference_reports": [{
                    "pdf_path": str(root / "reference.pdf"),
                    "expected_decoded_markdown_path": str(markdown),
                }],
            })

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertFalse(summary["pass"])
            self.assertEqual(summary["missing_content_items"], [])
            self.assertEqual(len(summary["data_lack_suspected_items"]), 1)

    def test_ambiguous_selection_reroutes_back_to_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main_tex = root / "main.tex"
            main_tex.write_text(r"\section{实验结果}" "\n", encoding="utf-8")
            discovery = root / "discovery.json"
            write_json(discovery, {
                "reference_selection_status": "ambiguous",
                "selected_reference_reports": [],
            })

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertFalse(summary["pass"])
            self.assertTrue(summary["blocked"])
            self.assertEqual(summary["recommended_reroutes"][0]["target_skill"], "course-lab-discovery")

    def test_unresolved_include_resolution_becomes_visible_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            markdown = root / "reference.md"
            markdown.write_text("# 电光调制\n\n## 实验步骤\n\n### 调节偏振片\n", encoding="utf-8")
            main_tex = root / "main.tex"
            main_tex.write_text(r"\section{实验步骤}" "\n" r"\input{sections/missing-procedure}" "\n", encoding="utf-8")
            discovery = root / "discovery.json"
            write_json(discovery, {
                "reference_selection_status": "selected",
                "selected_reference_reports": [{
                    "pdf_path": str(root / "reference.pdf"),
                    "expected_decoded_markdown_path": str(markdown),
                }],
            })

            summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery)

            self.assertFalse(summary["pass"])
            self.assertTrue(summary["blocked"])
            self.assertEqual(summary["recommended_reroutes"][0]["target_skill"], "course-lab-final-staging")
```

- [ ] **Step 2: Add failing finalize-qc integration tests**

Append to `tests/test_finalize_qc.py`:

```python
    def test_reference_comparison_runs_only_after_earlier_qc_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace = root / "report"
            workspace.mkdir()
            asset = root / "build_asset.sh"
            main_tex = workspace / "main.tex"
            procedures = workspace / "procedures.md"
            discovery = workspace / "discovery.json"
            summary_json = workspace / "final_qc_summary.json"
            summary_md = workspace / "final_qc_summary.md"
            unresolved = workspace / "final_qc_unresolved.md"

            write_build_asset(asset, fail=True)
            write_passing_tex(main_tex)
            write_procedures(procedures)
            write_json(discovery, {"reference_selection_status": "selected", "selected_reference_reports": []})

            summary = run_finalize_qc(
                main_tex=main_tex,
                procedures=procedures,
                discovery_json=discovery,
                output_summary_json=summary_json,
                output_summary_markdown=summary_md,
                output_unresolved=unresolved,
                build_asset=asset,
            )

            self.assertFalse(summary["build_pass"])
            self.assertFalse(summary["reference_procedure_comparison"].get("enabled"))

    def test_reference_comparison_failure_is_reported_in_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace = root / "report"
            workspace.mkdir()
            asset = root / "build_asset.sh"
            main_tex = workspace / "main.tex"
            procedures = workspace / "procedures.md"
            discovery = workspace / "discovery.json"
            reference_md = workspace / "reference.md"
            summary_json = workspace / "final_qc_summary.json"
            summary_md = workspace / "final_qc_summary.md"
            unresolved = workspace / "final_qc_unresolved.md"

            write_build_asset(asset, page_count=24)
            write_passing_tex(main_tex)
            write_procedures(procedures)
            reference_md.write_text("# 电光调制\n\n## 实验步骤\n\n### 观察倍频失真并测量线性工作区\n", encoding="utf-8")
            write_json(discovery, {
                "reference_selection_status": "selected",
                "selected_reference_reports": [{
                    "pdf_path": str(workspace / "reference.pdf"),
                    "expected_decoded_markdown_path": str(reference_md),
                }],
            })

            summary = run_finalize_qc(
                main_tex=main_tex,
                procedures=procedures,
                discovery_json=discovery,
                output_summary_json=summary_json,
                output_summary_markdown=summary_md,
                output_unresolved=unresolved,
                build_asset=asset,
            )

            self.assertFalse(summary["overall_pass"])
            self.assertFalse(summary["reference_procedure_comparison_pass"])
            self.assertIn("recommended_reroutes", summary)
            self.assertIn("reference procedure", unresolved.read_text(encoding="utf-8").lower())

    def test_none_found_reference_selection_records_neutral_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace = root / "report"
            workspace.mkdir()
            asset = root / "build_asset.sh"
            main_tex = workspace / "main.tex"
            procedures = workspace / "procedures.md"
            discovery = workspace / "discovery.json"
            summary_json = workspace / "final_qc_summary.json"
            summary_md = workspace / "final_qc_summary.md"
            unresolved = workspace / "final_qc_unresolved.md"

            write_build_asset(asset, page_count=24)
            write_passing_tex(main_tex)
            write_procedures(procedures)
            write_json(discovery, {"reference_selection_status": "none_found", "selected_reference_reports": []})

            summary = run_finalize_qc(
                main_tex=main_tex,
                procedures=procedures,
                discovery_json=discovery,
                output_summary_json=summary_json,
                output_summary_markdown=summary_md,
                output_unresolved=unresolved,
                build_asset=asset,
            )

            self.assertTrue(summary["overall_pass"])
            self.assertFalse(summary["reference_procedure_comparison_pass"])
            self.assertFalse(summary["reference_procedure_comparison_blocked"])
            self.assertEqual(summary["reference_procedure_comparison"]["selection_status"], "none_found")

    def test_ambiguous_reference_selection_reroutes_to_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace = root / "report"
            workspace.mkdir()
            asset = root / "build_asset.sh"
            main_tex = workspace / "main.tex"
            procedures = workspace / "procedures.md"
            discovery = workspace / "discovery.json"
            summary_json = workspace / "final_qc_summary.json"
            summary_md = workspace / "final_qc_summary.md"
            unresolved = workspace / "final_qc_unresolved.md"

            write_build_asset(asset, page_count=24)
            write_passing_tex(main_tex)
            write_procedures(procedures)
            write_json(discovery, {"reference_selection_status": "ambiguous", "selected_reference_reports": []})

            summary = run_finalize_qc(
                main_tex=main_tex,
                procedures=procedures,
                discovery_json=discovery,
                output_summary_json=summary_json,
                output_summary_markdown=summary_md,
                output_unresolved=unresolved,
                build_asset=asset,
            )

            self.assertFalse(summary["overall_pass"])
            self.assertTrue(summary["reference_procedure_comparison_blocked"])
            self.assertEqual(summary["recommended_reroutes"][0]["target_skill"], "course-lab-discovery")

    def test_declared_unresolved_reference_gap_still_produces_visible_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace = root / "report"
            workspace.mkdir()
            asset = root / "build_asset.sh"
            main_tex = workspace / "main.tex"
            procedures = workspace / "procedures.md"
            discovery = workspace / "discovery.json"
            reference_md = workspace / "reference.md"
            summary_json = workspace / "final_qc_summary.json"
            summary_md = workspace / "final_qc_summary.md"
            unresolved = workspace / "final_qc_unresolved.md"

            write_build_asset(asset, page_count=24)
            write_procedures(procedures)
            main_tex.write_text(
                r"\documentclass[twocolumn]{article}" "\n"
                r"\usepackage[hidelinks]{hyperref}" "\n"
                r"\begin{document}" "\n"
                r"\begin{abstract}Short abstract.\end{abstract}" "\n"
                r"\keywords{optics}" "\n"
                r"\tableofcontents" "\n"
                r"\section{实验结果}" "\n"
                r"\subsection{观察倍频失真并测量线性工作区}" "\n"
                r"\NeedsInput{Missing waveform data prevents completion of this lane.}" "\n"
                r"\section{Experiment Discussion}" "\n"
                r"The result is partially reliable because it is consistent with theory.\cite{opticspaper}" "\n"
                r"The deviation is mainly caused by instrument uncertainty." "\n"
                r"Further improvement would come from repeated measurements." "\n"
                r"\end{document}" "\n",
                encoding="utf-8",
            )
            reference_md.write_text("# 电光调制\n\n## 实验结果\n\n### 观察倍频失真并测量线性工作区\n", encoding="utf-8")
            write_json(discovery, {
                "reference_selection_status": "selected",
                "selected_reference_reports": [{
                    "pdf_path": str(workspace / "reference.pdf"),
                    "expected_decoded_markdown_path": str(reference_md),
                }],
            })

            summary = run_finalize_qc(
                main_tex=main_tex,
                procedures=procedures,
                discovery_json=discovery,
                output_summary_json=summary_json,
                output_summary_markdown=summary_md,
                output_unresolved=unresolved,
                build_asset=asset,
            )

            self.assertEqual(len(summary["reference_procedure_comparison"]["declared_unresolved_items"]), 1)
            self.assertIn("warning", unresolved.read_text(encoding="utf-8").lower())

    def test_data_lack_suspected_gap_still_fails_final_qc(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace = root / "report"
            workspace.mkdir()
            asset = root / "build_asset.sh"
            main_tex = workspace / "main.tex"
            procedures = workspace / "procedures.md"
            discovery = workspace / "discovery.json"
            reference_md = workspace / "reference.md"
            summary_json = workspace / "final_qc_summary.json"
            summary_md = workspace / "final_qc_summary.md"
            unresolved = workspace / "final_qc_unresolved.md"

            write_build_asset(asset, page_count=24)
            write_procedures(procedures)
            main_tex.write_text(
                r"\documentclass[twocolumn]{article}" "\n"
                r"\usepackage[hidelinks]{hyperref}" "\n"
                r"\begin{document}" "\n"
                r"\begin{abstract}Short abstract.\end{abstract}" "\n"
                r"\keywords{optics}" "\n"
                r"\tableofcontents" "\n"
                r"\section{实验结果}" "\n"
                r"\subsection{观察倍频失真并测量线性工作区}" "\n"
                r"由于本次实验没有保存可用的波形数据，这一部分尚不能完成。" "\n"
                r"\section{Experiment Discussion}" "\n"
                r"The result is partially reliable because it is consistent with theory.\cite{opticspaper}" "\n"
                r"The deviation is mainly caused by instrument uncertainty." "\n"
                r"Further improvement would come from repeated measurements." "\n"
                r"\end{document}" "\n",
                encoding="utf-8",
            )
            reference_md.write_text("# 电光调制\n\n## 实验结果\n\n### 观察倍频失真并测量线性工作区\n", encoding="utf-8")
            write_json(discovery, {
                "reference_selection_status": "selected",
                "selected_reference_reports": [{
                    "pdf_path": str(workspace / "reference.pdf"),
                    "expected_decoded_markdown_path": str(reference_md),
                }],
            })

            summary = run_finalize_qc(
                main_tex=main_tex,
                procedures=procedures,
                discovery_json=discovery,
                output_summary_json=summary_json,
                output_summary_markdown=summary_md,
                output_unresolved=unresolved,
                build_asset=asset,
            )

            self.assertFalse(summary["overall_pass"])
            self.assertEqual(len(summary["reference_procedure_comparison"]["data_lack_suspected_items"]), 1)
            self.assertIn("warning", unresolved.read_text(encoding="utf-8").lower())
```

Use the existing fake-build helpers in this file so the new tests only assert summary fields, not real LaTeX compilation.

- [ ] **Step 3: Extend finalize-qc package contract test**

Add to `tests/test_skill_package.py`:

```python
        self.assertIn("--discovery-json", text)
        self.assertIn("selected_reference_reports", text)
        self.assertIn("detector", text.lower())
        self.assertIn("reroute", text.lower())
        self.assertIn("same-experiment", text.lower())
```

And add the new helper file to the required path list:

```python
            SKILL_DIR / "scripts" / "reference_procedure_compare.py",
```

- [ ] **Step 4: Run finalize-qc tests to verify RED**

Run:

```bash
python3 -m unittest \
  /root/.codex/skills/course-lab-finalize-qc/tests/test_reference_procedure_compare.py \
  /root/.codex/skills/course-lab-finalize-qc/tests/test_finalize_qc.py \
  /root/.codex/skills/course-lab-finalize-qc/tests/test_skill_package.py
```

Expected: FAIL because the helper file, CLI option, and summary fields do not exist yet.

- [ ] **Step 5: Commit the RED finalize-qc tests**

Run:

```bash
git -C /root/.codex/skills add \
  course-lab-finalize-qc/tests/test_reference_procedure_compare.py \
  course-lab-finalize-qc/tests/test_finalize_qc.py \
  course-lab-finalize-qc/tests/test_skill_package.py
git -C /root/.codex/skills commit -F - <<'EOF'
Lock the reference-procedure QC gate with failing tests

These tests define the detector-only late QC behavior before the
implementation starts, including markdown blockers, `实验结果`
aliases, TeX include expansion, and declared-unresolved handling.

Constraint: Finalize-QC must not mutate report content or rediscover references
Rejected: Add comparison logic first and backfill tests later | violates test-first changes for the new gate
Confidence: high
Scope-risk: narrow
Reversibility: clean
Directive: Keep reroute decisions machine-readable in the QC summary
Tested: Finalize-QC tests fail for the missing comparison contract
Not-tested: Production implementation
EOF
```

## Task 4: GREEN Finalize-QC Comparison Implementation

**Files:**
- Create: `/root/.codex/skills/course-lab-finalize-qc/scripts/reference_procedure_compare.py`
- Modify: `/root/.codex/skills/course-lab-finalize-qc/scripts/finalize_qc.py`
- Modify: `/root/.codex/skills/course-lab-finalize-qc/SKILL.md`
- Modify: `/root/.codex/skills/course-lab-finalize-qc/agents/openai.yaml`
- Modify: `/root/.codex/skills/course-lab-finalize-qc/tests/test_reference_procedure_compare.py`
- Modify: `/root/.codex/skills/course-lab-finalize-qc/tests/test_finalize_qc.py`
- Modify: `/root/.codex/skills/course-lab-finalize-qc/tests/test_skill_package.py`

- [ ] **Step 1: Implement the comparison helper**

Create `scripts/reference_procedure_compare.py` with a narrow API:

```python
from __future__ import annotations

import json
import re
from pathlib import Path


PROCEDURE_HEADING_ALIASES = (
    "experiment steps",
    "experimental procedure",
    "experiment procedure",
    "procedure",
    "experiment results",
    "实验步骤",
    "实验过程",
    "实验方法",
    "实验结果",
)


def expand_tex_tree(main_tex: Path) -> str:
    include_re = re.compile(r"\\\\(?:input|include)\\{([^}]+)\\}")
    seen: set[Path] = set()

    def read_with_includes(path: Path) -> str:
        resolved = path.resolve()
        if resolved in seen:
            return ""
        seen.add(resolved)
        text = path.read_text(encoding="utf-8", errors="replace")

        def replace(match: re.Match[str]) -> str:
            rel = match.group(1)
            candidate = (path.parent / rel).with_suffix(".tex") if not rel.endswith(".tex") else (path.parent / rel)
            if not candidate.exists():
                raise FileNotFoundError(f"Missing included TeX file: {candidate}")
            return read_with_includes(candidate)

        return include_re.sub(replace, text)

    return read_with_includes(main_tex)


def compare_reference_procedure_coverage(*, main_tex: Path, discovery_json: Path) -> dict[str, object]:
    discovery = json.loads(discovery_json.read_text(encoding="utf-8"))
    if "reference_selection_status" not in discovery or "selected_reference_reports" not in discovery:
        return {
            "enabled": True,
            "selection_status": "malformed",
            "pass": False,
            "blocked": True,
            "blocked_reference_decode_items": [],
            "missing_structure_items": [],
            "missing_content_items": [],
            "declared_unresolved_items": [],
            "data_lack_suspected_items": [],
            "recommended_reroutes": [
                {"target_skill": "course-lab-discovery", "reason_code": "malformed-discovery-contract"}
            ],
        }
    selection_status = discovery["reference_selection_status"]
    if selection_status == "ambiguous":
        return {
            "enabled": True,
            "selection_status": "ambiguous",
            "pass": False,
            "blocked": True,
            "blocked_reference_decode_items": [],
            "missing_structure_items": [],
            "missing_content_items": [],
            "declared_unresolved_items": [],
            "data_lack_suspected_items": [],
            "recommended_reroutes": [
                {"target_skill": "course-lab-discovery", "reason_code": "ambiguous-reference-selection"}
            ],
        }
    if selection_status == "none_found":
        return {
            "enabled": True,
            "selection_status": "none_found",
            "pass": False,
            "blocked": False,
            "blocked_reference_decode_items": [],
            "missing_structure_items": [],
            "missing_content_items": [],
            "declared_unresolved_items": [],
            "data_lack_suspected_items": [],
            "recommended_reroutes": [],
        }
    selected = discovery.get("selected_reference_reports", [])
    tex_text = expand_tex_tree(main_tex)
    return build_reference_procedure_summary(tex_text=tex_text, selected_reference_reports=selected)
```

Keep the helper internal and deterministic:

- resolve only local workspace `\input{}` and `\include{}` files
- treat missing markdown as a blocker
- route `reference_selection_status = ambiguous` to `course-lab-discovery`
- block and reroute to `course-lab-discovery` when required discovery-contract fields such as `reference_selection_status` or `selected_reference_reports` are missing
- treat unresolved local include expansion as a visible blocker instead of silently reading partial TeX
- accept numbered heading forms such as `5. 实验步骤` and `5.2.3 ...`
- extract numbered or bulleted operation labels when no child heading exists
- fall back to short body-anchor extraction when a reference block has prose but no child heading
- route missing heading lanes to `course-lab-body-scaffold`
- route present heading but thin/missing content to `course-lab-final-staging`
- route weak interpretation or evidence support to `course-lab-results-interpretation`
  - minimal rule for this pass: if the report already has the matching heading lane and non-placeholder prose, but the reference heading or anchor contains comparison/evidence keywords such as `理论`, `文献`, `compare`, `comparison`, `理论值`, `一致`, `误差`, and the local report body lacks those keywords, classify it as an interpretation/evidence gap rather than a staging gap
- populate `data_lack_suspected_items` when the matching lane exists but the report body contains missing-data language such as `缺少数据`, `没有保存`, `未测得`, `data missing`, `insufficient data`, or `无法测量`, and the lane is not yet explicitly marked with `TBD` or `\NeedsInput{...}`
- downgrade visible `TBD` or `\NeedsInput{...}` matches to declared-unresolved when the missing lane is explicitly acknowledged

- [ ] **Step 2: Wire the helper into `finalize_qc.py`**

Modify `run_finalize_qc()` and CLI parsing:

```python
from reference_procedure_compare import compare_reference_procedure_coverage

def run_finalize_qc(
    *,
    main_tex: Path,
    procedures: Path,
    output_summary_json: Path,
    output_summary_markdown: Path,
    output_unresolved: Path,
    evidence_plan: Path | None = None,
    discussion_candidates: Path | None = None,
    discovery_json: Path | None = None,
    build_asset: Path = DEFAULT_BUILD_ASSET,
):
    comparison_summary: dict[str, object] = {
        "enabled": False,
        "selection_status": "not_requested",
        "pass": False,
        "blocked": False,
        "blocked_reference_decode_items": [],
        "missing_structure_items": [],
        "missing_content_items": [],
        "declared_unresolved_items": [],
        "data_lack_suspected_items": [],
        "recommended_reroutes": [],
    }
    if discovery_json and build_result.returncode == 0 and pdf_exists and qc_pass and pdf_size_ok and not build_layout_issues:
        comparison_summary = compare_reference_procedure_coverage(main_tex=main_tex, discovery_json=discovery_json)
        if (
            comparison_summary["blocked"]
            or comparison_summary["missing_structure_items"]
            or comparison_summary["missing_content_items"]
            or comparison_summary["data_lack_suspected_items"]
        ):
            overall_pass = False
        if comparison_summary["data_lack_suspected_items"]:
            unresolved_items.append("Reference procedure comparison found unresolved data-lack lanes that still require visible warning review.")
        if comparison_summary["declared_unresolved_items"]:
            unresolved_items.append("Reference procedure comparison left declared unresolved lanes in place; keep the visible TBD or NeedsInput warning in the final handoff.")
        if not comparison_summary["pass"]:
            unresolved_items.append("Reference procedure comparison produced parent-facing reroutes that must be handled before completion.")
    summary["reference_procedure_comparison_pass"] = comparison_summary["pass"]
    summary["reference_procedure_comparison_blocked"] = comparison_summary["blocked"]
    summary["reference_procedure_comparison"] = comparison_summary
    summary["recommended_reroutes"] = comparison_summary["recommended_reroutes"]
```

Also add:

```python
parser.add_argument("--discovery-json")
discovery_json=Path(args.discovery_json) if args.discovery_json else None,
```

- [ ] **Step 3: Update finalize-qc docs and prompt**

Add to `SKILL.md` and `agents/openai.yaml`:

```text
- Accept `--discovery-json` when same-experiment reference selection already exists.
- Run the reference-procedure comparison only after compile, local QC, layout, and PDF-size gates pass.
- Read only discovery-produced reference selections; do not rediscover or decode references here.
- Emit precise reroute instructions for the parent instead of repairing report content.
```

- [ ] **Step 4: Run finalize-qc tests to verify GREEN**

Run:

```bash
python3 -m unittest \
  /root/.codex/skills/course-lab-finalize-qc/tests/test_reference_procedure_compare.py \
  /root/.codex/skills/course-lab-finalize-qc/tests/test_finalize_qc.py \
  /root/.codex/skills/course-lab-finalize-qc/tests/test_skill_package.py
```

Expected: PASS

- [ ] **Step 5: Commit the finalize-qc implementation**

Run:

```bash
git -C /root/.codex/skills add \
  course-lab-finalize-qc/SKILL.md \
  course-lab-finalize-qc/agents/openai.yaml \
  course-lab-finalize-qc/scripts/finalize_qc.py \
  course-lab-finalize-qc/scripts/reference_procedure_compare.py \
  course-lab-finalize-qc/tests/test_finalize_qc.py \
  course-lab-finalize-qc/tests/test_reference_procedure_compare.py \
  course-lab-finalize-qc/tests/test_skill_package.py
git -C /root/.codex/skills commit -F - <<'EOF'
Turn final QC into a reference-driven detector gate

Final QC now consumes the discovery reference bundle, expands the
effective TeX content tree, compares procedure/result lanes against
decoded reference markdown, and emits parent-facing reroutes without
repairing report content itself.

Constraint: The comparison must run only after earlier compile and QC gates pass
Constraint: Missing reference markdown must block and reroute instead of silently skipping
Rejected: Reuse report_qc.py for all comparison logic | a dedicated helper keeps the new gate isolated
Confidence: high
Scope-risk: moderate
Reversibility: clean
Directive: Keep the comparison helper deterministic and local-workspace-only for `\\input` resolution
Tested: Finalize-QC comparison, integration, and package tests
Not-tested: Full report-family rerun loop
EOF
```

## Task 5: RED/GREEN Parent Recovery Documentation

**Files:**
- Modify: `/root/.codex/skills/course-lab-report/tests/test_recovery_matrix.py`
- Modify: `/root/.codex/skills/course-lab-report/SKILL.md`
- Modify: `/root/.codex/skills/course-lab-report/references/recovery_matrix.md`
- Modify: `/root/.codex/skills/course-lab-report/references/leaf_responsibility_matrix.md`

- [ ] **Step 1: Add failing recovery-doc assertions**

Extend `tests/test_recovery_matrix.py` with new snippets:

```python
            "reference-procedure comparison",
            "course-lab-discovery",
            "course-lab-handout-normalization",
            "selected_reference_reports",
            "same-experiment reference selection",
            "course-lab-results-interpretation",
            "declared-unresolved",
            "data-lack",
```

Add them to the relevant `expected_snippets` lists for `SKILL.md`, `recovery_matrix.md`, and `leaf_responsibility_matrix.md`.

- [ ] **Step 2: Run recovery tests to verify RED**

Run:

```bash
python3 -m unittest /root/.codex/skills/course-lab-report/tests/test_recovery_matrix.py
```

Expected: FAIL because the parent docs do not yet mention the new reroute lane.

- [ ] **Step 3: Update the parent contracts**

Edit the docs so they say, in plain terms:

```text
- Finalize-QC remains diagnostic-only for reference-procedure comparison failures.
- Ambiguous same-experiment reference selection reroutes to `course-lab-discovery`.
- Missing selected reference markdown reroutes to `course-lab-handout-normalization`.
- Missing procedure structure reroutes to `course-lab-body-scaffold`.
- Missing substantive late-stage presentation reroutes to `course-lab-final-staging`.
- Weak interpretation or evidence support reroutes to `course-lab-results-interpretation`.
- Data-lack cases may remain as visible `TBD` or `\NeedsInput{...}` markers with warnings.
```

- [ ] **Step 4: Run recovery tests to verify GREEN**

Run:

```bash
python3 -m unittest /root/.codex/skills/course-lab-report/tests/test_recovery_matrix.py
```

Expected: PASS

- [ ] **Step 5: Commit the parent recovery docs**

Run:

```bash
git -C /root/.codex/skills add \
  course-lab-report/SKILL.md \
  course-lab-report/references/recovery_matrix.md \
  course-lab-report/references/leaf_responsibility_matrix.md \
  course-lab-report/tests/test_recovery_matrix.py
git -C /root/.codex/skills commit -F - <<'EOF'
Document how parent recovery should route reference-procedure failures

The parent now explicitly owns the reroute chain for discovery-backed
reference comparison failures so finalize-QC can stay a detector leaf
and unresolved data-lack cases remain visible.

Constraint: Recovery loops belong to the parent orchestrator, not the QC leaf
Rejected: Let finalize-qc rerun upstream leaves on its own | breaks the installed ownership model
Confidence: high
Scope-risk: narrow
Reversibility: clean
Directive: Keep data-lack lanes visible as warnings instead of silently dropping them
Tested: Parent recovery doc tests
Not-tested: Live multi-reroute session
EOF
```

## Task 6: Full Verification And Final Integration Commit

**Files:**
- Modify: all files changed in Tasks 1-5

- [ ] **Step 1: Run the full targeted verification suite**

Run:

```bash
python3 -m unittest \
  /root/.codex/skills/course-lab-discovery/tests/test_skill_package.py \
  /root/.codex/skills/course-lab-discovery/tests/test_discovery_ranking.py \
  /root/.codex/skills/course-lab-finalize-qc/tests/test_reference_procedure_compare.py \
  /root/.codex/skills/course-lab-finalize-qc/tests/test_finalize_qc.py \
  /root/.codex/skills/course-lab-finalize-qc/tests/test_skill_package.py \
  /root/.codex/skills/course-lab-report/tests/test_recovery_matrix.py
```

Expected: PASS

- [ ] **Step 2: Sanity-check the working tree**

Run:

```bash
git -C /root/.codex/skills status --short
```

Expected: Only the planned discovery, finalize-qc, and course-lab-report files are staged or modified. Do not revert unrelated user changes outside this scope.

- [ ] **Step 3: Make the final integration commit**

Run:

```bash
git -C /root/.codex/skills add \
  course-lab-discovery/SKILL.md \
  course-lab-discovery/agents/openai.yaml \
  course-lab-discovery/scripts/discover_sources.py \
  course-lab-discovery/tests/test_discovery_ranking.py \
  course-lab-discovery/tests/test_skill_package.py \
  course-lab-finalize-qc/SKILL.md \
  course-lab-finalize-qc/agents/openai.yaml \
  course-lab-finalize-qc/scripts/finalize_qc.py \
  course-lab-finalize-qc/scripts/reference_procedure_compare.py \
  course-lab-finalize-qc/tests/test_finalize_qc.py \
  course-lab-finalize-qc/tests/test_reference_procedure_compare.py \
  course-lab-finalize-qc/tests/test_skill_package.py \
  course-lab-report/SKILL.md \
  course-lab-report/references/recovery_matrix.md \
  course-lab-report/references/leaf_responsibility_matrix.md \
  course-lab-report/tests/test_recovery_matrix.py
git -C /root/.codex/skills commit -F - <<'EOF'
Prevent late-stage reports from missing reference procedure coverage

Discovery now emits a same-experiment reference bundle, final QC
compares the effective report content tree against decoded reference
procedure/result structure, and the parent docs define how to reroute
decode, scaffold, staging, and data-lack outcomes.

Constraint: Final QC must consume only discovery-produced reference selections
Constraint: Missing reference markdown must route through existing MinerU normalization
Rejected: Self-contained finalize-qc repair loop | duplicates discovery logic and violates parent recovery ownership
Confidence: high
Scope-risk: moderate
Reversibility: clean
Directive: Treat `reference_selection_status` as authoritative; do not collapse ambiguity into an empty bundle
Tested: Discovery, finalize-qc, and parent recovery unit tests
Not-tested: End-to-end run against a live multi-reference lab report workspace
EOF
```

- [ ] **Step 4: Record the implementation handoff**

Capture in the final report:

- changed files
- the new discovery manifest contract
- the new finalize-qc summary fields
- the parent reroute additions
- any remaining risks, especially real-world markdown heterogeneity and live end-to-end validation gaps
