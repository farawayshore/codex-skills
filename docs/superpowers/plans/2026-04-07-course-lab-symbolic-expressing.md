# Course Lab Symbolic Expressing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone optional `course-lab-symbolic-expressing` helper skill that returns temporary TeX explanation paths for selected lab-report results.

**Architecture:** Add a focused skill package under `/root/.codex/skills/course-lab-symbolic-expressing/`. The package owns one script-backed CLI that reads explicit handout, calculation-code, and processed-result paths, writes a compact TeX explanation artifact, and writes a JSON response with the returned path and unresolved notes. The parent `course-lab-report` skill only documents the optional handoff; `course-lab-final-staging` remains unchanged in this pass.

**Tech Stack:** Python 3 standard library (`argparse`, `ast`, `json`, `pathlib`, `re`, `tempfile`, `unittest`, `subprocess`), Markdown skill docs, YAML agent prompt, git Lore commits.

---

## File Structure

- Create: `/root/.codex/skills/course-lab-symbolic-expressing/SKILL.md`
- Create: `/root/.codex/skills/course-lab-symbolic-expressing/agents/openai.yaml`
- Create: `/root/.codex/skills/course-lab-symbolic-expressing/scripts/render_symbolic_explanation.py`
- Create: `/root/.codex/skills/course-lab-symbolic-expressing/tests/baseline_failures.md`
- Create: `/root/.codex/skills/course-lab-symbolic-expressing/tests/test_render_symbolic_explanation.py`
- Create: `/root/.codex/skills/course-lab-symbolic-expressing/tests/test_skill_package.py`
- Modify: `/root/.codex/skills/course-lab-report/SKILL.md`
- Reference: `/root/.codex/skills/docs/superpowers/specs/2026-04-07-course-lab-symbolic-expressing-design.md`

## Task 1: RED Package Contract Tests

**Files:**
- Create: `/root/.codex/skills/course-lab-symbolic-expressing/tests/baseline_failures.md`
- Create: `/root/.codex/skills/course-lab-symbolic-expressing/tests/test_skill_package.py`

- [ ] **Step 1: Write baseline failures**

Create `tests/baseline_failures.md` with the observed baseline:

```markdown
# Course Lab Symbolic Expressing Baseline Failures

- No standalone `course-lab-symbolic-expressing` package exists yet.
- No script-backed CLI returns a temporary TeX path for a requested result.
- The parent `course-lab-report` skill does not yet list the optional symbolic-expression helper handoff.
- Existing processing and staging skills can show formulas, but no optional helper reads handout plus calculation code for an undergraduate-readable calculation route.
```

- [ ] **Step 2: Write failing package test**

Create `tests/test_skill_package.py`:

```python
from __future__ import annotations

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
PARENT_SKILL_PATH = Path("/root/.codex/skills/course-lab-report/SKILL.md")


class CourseLabSymbolicExpressingPackageTests(unittest.TestCase):
    def test_standalone_skill_contract_files_exist(self) -> None:
        required_paths = [
            SKILL_DIR / "SKILL.md",
            SKILL_DIR / "agents" / "openai.yaml",
            SKILL_DIR / "scripts" / "render_symbolic_explanation.py",
            SKILL_DIR / "tests" / "baseline_failures.md",
        ]

        missing = [str(path.relative_to(SKILL_DIR)) for path in required_paths if not path.exists()]
        self.assertEqual(missing, [])

    def test_skill_markdown_documents_optional_path_returning_boundary(self) -> None:
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("course-lab-symbolic-expressing", text)
        self.assertIn("optional", text.lower())
        self.assertIn("standalone", text.lower())
        self.assertIn("temporary", text.lower())
        self.assertIn("tex_path", text)
        self.assertIn("handout", text.lower())
        self.assertIn("calculation code", text.lower())
        self.assertIn("processed result", text.lower())
        self.assertIn("does not mutate", text.lower())
        self.assertIn("main.tex", text)
        self.assertIn("unresolved", text.lower())
        self.assertIn("workspace-local", text.lower())
        self.assertIn("/tmp", text)

    def test_agent_prompt_requires_artifact_only_helper_behavior(self) -> None:
        text = (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("optional", text.lower())
        self.assertIn("temporary", text.lower())
        self.assertIn("tex", text.lower())
        self.assertIn("return", text.lower())
        self.assertIn("do not mutate", text.lower())

    def test_parent_skill_mentions_optional_symbolic_handoff(self) -> None:
        text = PARENT_SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("course-lab-symbolic-expressing", text)
        self.assertIn("optional", text.lower())
        self.assertIn("temp TeX", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run package test to verify RED**

Run:

```bash
python3 -m unittest /root/.codex/skills/course-lab-symbolic-expressing/tests/test_skill_package.py
```

Expected: FAIL because `SKILL.md`, `agents/openai.yaml`, and `scripts/render_symbolic_explanation.py` do not exist yet.

## Task 2: RED CLI Behavior Tests

**Files:**
- Create: `/root/.codex/skills/course-lab-symbolic-expressing/tests/test_render_symbolic_explanation.py`

- [ ] **Step 1: Write failing behavior tests**

Create `tests/test_render_symbolic_explanation.py`:

```python
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "render_symbolic_explanation.py"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class RenderSymbolicExplanationTests(unittest.TestCase):
    def build_fixture(self, root: Path) -> dict[str, Path]:
        handout = root / "decoded_handout.md"
        code = root / "analysis" / "process_data.py"
        processed = root / "analysis" / "derived_uncertainty.json"
        output_dir = root / "analysis" / "symbolic_expressing" / "tmp"
        response = output_dir / "wave_speed_symbolic_response.json"

        handout.write_text(
            "# Experiment Handout\n\n"
            "The linear density is $rho = m / L$ and the wave speed is $v = sqrt(T / rho)$.\n",
            encoding="utf-8",
        )
        code.parent.mkdir(parents=True, exist_ok=True)
        code.write_text(
            "rho = m / L\n"
            "wave_speed = sqrt(T / rho)\n",
            encoding="utf-8",
        )
        write_json(
            processed,
            {
                "coverage_k": 2.0,
                "inputs": {
                    "m": {"value": 0.01391, "unit": "kg", "symbol": "m"},
                    "L": {"value": 3.0, "unit": "m", "symbol": "L"},
                    "T": {"value": 4.9, "unit": "N", "symbol": "T"},
                },
                "derived": {
                    "rho": {"label": "linear density", "expression": "m / L", "unit": "kg/m", "value": 0.00464},
                    "wave_speed": {"label": "wave speed", "expression": "sqrt(T / rho)", "unit": "m/s", "value": 32.5},
                },
            },
        )
        return {"handout": handout, "code": code, "processed": processed, "output_dir": output_dir, "response": response}

    def run_renderer(self, fixture: dict[str, Path], result_key: str = "wave_speed") -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--handout",
                str(fixture["handout"]),
                "--calculation-code",
                str(fixture["code"]),
                "--processed-result",
                str(fixture["processed"]),
                "--result-key",
                result_key,
                "--output-dir",
                str(fixture["output_dir"]),
                "--output-response-json",
                str(fixture["response"]),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_cli_writes_response_json_with_temp_tex_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = self.build_fixture(Path(tmpdir))

            completed = self.run_renderer(fixture)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            response = json.loads(fixture["response"].read_text(encoding="utf-8"))
            self.assertEqual(response["result_key"], "wave_speed")
            self.assertEqual(response["unresolved"], [])
            tex_path = Path(response["tex_path"])
            self.assertTrue(tex_path.exists())
            self.assertTrue(str(tex_path).startswith(str(fixture["output_dir"])))

    def test_cli_renders_handout_code_and_processed_formula_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = self.build_fixture(Path(tmpdir))

            completed = self.run_renderer(fixture)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            response = json.loads(fixture["response"].read_text(encoding="utf-8"))
            tex = Path(response["tex_path"]).read_text(encoding="utf-8")
            self.assertIn(r"\paragraph{Calculation route for wave speed}", tex)
            self.assertIn("handout", tex.lower())
            self.assertIn("calculation code", tex.lower())
            self.assertIn("rho", tex)
            self.assertIn("sqrt", tex)
            self.assertIn(r"wave\_speed", tex)
            self.assertNotIn("Raw source table", tex)

    def test_cli_keeps_untraceable_result_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = self.build_fixture(Path(tmpdir))

            completed = self.run_renderer(fixture, result_key="missing_result")

            self.assertEqual(completed.returncode, 0, completed.stderr)
            response = json.loads(fixture["response"].read_text(encoding="utf-8"))
            self.assertTrue(response["unresolved"])
            tex = Path(response["tex_path"]).read_text(encoding="utf-8")
            self.assertIn(r"\NeedsInput", tex)
            self.assertIn(r"missing\_result", tex)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run behavior test to verify RED**

Run:

```bash
python3 -m unittest /root/.codex/skills/course-lab-symbolic-expressing/tests/test_render_symbolic_explanation.py
```

Expected: FAIL because `scripts/render_symbolic_explanation.py` does not exist yet.

## Task 3: GREEN Minimal Script Implementation

**Files:**
- Create: `/root/.codex/skills/course-lab-symbolic-expressing/scripts/render_symbolic_explanation.py`

- [ ] **Step 1: Implement minimal CLI**

Create `scripts/render_symbolic_explanation.py` with:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def safe_slug(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", text.strip()).strip("-")
    return slug or "symbolic-result"


def python_expr_to_text(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return "<unparsed expression>"


def extract_assignments(code_text: str) -> dict[str, str]:
    assignments: dict[str, str] = {}
    try:
        tree = ast.parse(code_text)
    except SyntaxError:
        return assignments
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        expression = python_expr_to_text(node.value)
        for target in node.targets:
            if isinstance(target, ast.Name):
                assignments[target.id] = expression
    return assignments


def result_record(processed: dict[str, object], result_key: str) -> dict[str, object] | None:
    for bucket_name in ("derived", "results", "indirect_results"):
        bucket = processed.get(bucket_name)
        if isinstance(bucket, dict):
            record = bucket.get(result_key)
            if isinstance(record, dict):
                return record
        if isinstance(bucket, list):
            for item in bucket:
                if isinstance(item, dict) and str(item.get("name") or item.get("key") or "") == result_key:
                    return item
    return None


def render_tex(result_key: str, handout_text: str, code_assignments: dict[str, str], record: dict[str, object] | None) -> tuple[str, list[str]]:
    unresolved: list[str] = []
    label = str(record.get("label") if record else result_key) if record else result_key
    expression = str(record.get("expression") or "").strip() if record else ""
    code_expression = code_assignments.get(result_key, "")

    lines = [rf"\paragraph{{Calculation route for {latex_escape(label)}}}"]
    if not record:
        unresolved.append(f"Processed result key was not found: {result_key}")
        lines.append(rf"\NeedsInput{{Processed result key was not found: {latex_escape(result_key)}.}}")
        return "\n".join(lines) + "\n", unresolved

    handout_hint = ""
    lower_handout = handout_text.casefold()
    if result_key.casefold() in lower_handout or label.casefold() in lower_handout:
        handout_hint = "The handout text mentions this result or its label."
    elif expression and any(token in lower_handout for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expression.casefold())):
        handout_hint = "The handout text contains symbols used in the processed expression."
    else:
        unresolved.append(f"Handout formula evidence was weak for result: {result_key}")
        handout_hint = "The handout formula evidence was incomplete, so this route is provisional."

    if not code_expression:
        unresolved.append(f"Calculation code assignment was not found for result: {result_key}")
        code_expression = expression or "unresolved"

    lines.append(latex_escape(handout_hint))
    if expression:
        lines.extend(["", r"\[", rf"{latex_escape(result_key)} = {latex_escape(expression)}", r"\]"])
    lines.append(
        latex_escape(
            f"The calculation code evaluates {result_key} using `{code_expression}` and the processed result artifact records"
            f" the expression `{expression or code_expression}`."
        )
    )
    return "\n".join(lines) + "\n", unresolved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--handout", required=True)
    parser.add_argument("--calculation-code", action="append", required=True)
    parser.add_argument("--processed-result", required=True)
    parser.add_argument("--result-key", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output-response-json", required=True)
    args = parser.parse_args()

    handout_path = Path(args.handout)
    processed_path = Path(args.processed_result)
    code_paths = [Path(path) for path in args.calculation_code]
    for path in [handout_path, processed_path, *code_paths]:
        if not path.exists():
            raise FileNotFoundError(path)

    handout_text = handout_path.read_text(encoding="utf-8")
    code_assignments: dict[str, str] = {}
    for path in code_paths:
        code_assignments.update(extract_assignments(path.read_text(encoding="utf-8")))
    processed = load_json(processed_path)
    record = result_record(processed, args.result_key)
    tex, unresolved = render_tex(args.result_key, handout_text, code_assignments, record)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    tex_path = output_dir / f"{safe_slug(args.result_key)}_symbolic_explanation.tex"
    tex_path.write_text(tex, encoding="utf-8")
    response_path = Path(args.output_response_json)
    response_path.parent.mkdir(parents=True, exist_ok=True)
    response = {
        "result_key": args.result_key,
        "tex_path": str(tex_path),
        "sources": {
            "handout": str(handout_path),
            "calculation_code": [str(path) for path in code_paths],
            "processed_result": str(processed_path),
        },
        "unresolved": unresolved,
    }
    response_path.write_text(json.dumps(response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(tex_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run behavior tests to verify GREEN**

Run:

```bash
python3 -m unittest /root/.codex/skills/course-lab-symbolic-expressing/tests/test_render_symbolic_explanation.py
```

Expected: PASS.

- [ ] **Step 3: Refactor only if tests stay green**

If needed, improve helper names or rendering clarity without adding extra behavior. Rerun the same behavior test after any refactor.

## Task 4: GREEN Skill Docs And Agent Prompt

**Files:**
- Create: `/root/.codex/skills/course-lab-symbolic-expressing/SKILL.md`
- Create: `/root/.codex/skills/course-lab-symbolic-expressing/agents/openai.yaml`

- [ ] **Step 1: Write `SKILL.md`**

Create the skill doc with:

```markdown
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
```

- [ ] **Step 2: Write `agents/openai.yaml`**

Create:

```yaml
name: course-lab-symbolic-expressing
description: Optional course-lab helper for temporary TeX symbolic calculation-route artifacts.
default_prompt: "Use $course-lab-symbolic-expressing only when explicit handout, calculation-code, processed-result, result-key, and output paths are provided. Write temporary TeX explanation artifacts, return the tex_path through response JSON, keep unresolved formula gaps visible, and do not mutate main.tex or recompute official results."
```

- [ ] **Step 3: Run package tests to verify docs**

Run:

```bash
python3 -m unittest /root/.codex/skills/course-lab-symbolic-expressing/tests/test_skill_package.py
```

Expected: FAIL only because parent `course-lab-report` has not been updated yet, or PASS if all docs are already present and parent text was handled early.

## Task 5: Parent Optional Handoff Documentation

**Files:**
- Modify: `/root/.codex/skills/course-lab-report/SKILL.md`

- [ ] **Step 1: Update stage/optional helper language**

Modify the parent skill without making `course-lab-symbolic-expressing` a required default stage:

```markdown
## Optional Helper Leaves

- `course-lab-symbolic-expressing`: optional result-explanation helper that reads explicit handout, calculation-code, processed-result, result-key, and output paths, then returns a temp TeX path plus unresolved notes to the caller. It is not a required stage between `course-lab-data-processing` and `course-lab-final-staging`.
```

Also add one parent-only responsibility:

```markdown
- Keep artifact handoffs explicit for optional `course-lab-symbolic-expressing` calls: callers must pass source paths and consume the returned temp TeX path; the parent must not treat this helper as proof that final-staging ran.
```

- [ ] **Step 2: Run package tests to verify GREEN**

Run:

```bash
python3 -m unittest /root/.codex/skills/course-lab-symbolic-expressing/tests/test_skill_package.py
```

Expected: PASS.

## Task 6: Full Verification And Commit

**Files:**
- All files from previous tasks.

- [ ] **Step 1: Run focused tests**

Run:

```bash
python3 -m unittest \
  /root/.codex/skills/course-lab-symbolic-expressing/tests/test_render_symbolic_explanation.py \
  /root/.codex/skills/course-lab-symbolic-expressing/tests/test_skill_package.py
```

Expected: PASS.

- [ ] **Step 2: Run adjacent regression tests**

Run:

```bash
python3 -m unittest /root/.codex/skills/course-lab-data-processing/tests/test_render_calculation_details.py
python3 -m unittest /root/.codex/skills/course-lab-final-staging/tests/test_skill_package.py
```

Expected: PASS. If failures occur, inspect before changing anything because the new helper should not alter data-processing or final-staging behavior.

- [ ] **Step 3: Inspect git diff**

Run:

```bash
git -C /root/.codex/skills status --short
git -C /root/.codex/skills diff --stat
git -C /root/.codex/skills diff -- course-lab-symbolic-expressing course-lab-report/SKILL.md
```

Expected: only the new skill package and parent documentation changed.

- [ ] **Step 4: Commit with Lore protocol**

Run:

```bash
git -C /root/.codex/skills add course-lab-symbolic-expressing course-lab-report/SKILL.md
git -C /root/.codex/skills commit -m "Enable optional symbolic calculation-route handoffs"
```

Use a Lore-format full message in the editor or via `-m` arguments:

```text
Enable optional symbolic calculation-route handoffs

The lab-report family needs a reusable helper for explaining how selected results came from handout formulas and calculation code, without forcing final-staging to own that logic yet.

Constraint: Helper is optional and must not become a required stage between processing and staging
Rejected: Mutate main.tex directly | callers should consume returned temp TeX paths
Rejected: Recompute official results | data-processing remains the calculation owner
Confidence: medium
Scope-risk: narrow
Tested: python3 -m unittest course-lab-symbolic-expressing/tests/test_render_symbolic_explanation.py course-lab-symbolic-expressing/tests/test_skill_package.py
Tested: python3 -m unittest course-lab-data-processing/tests/test_render_calculation_details.py
Tested: python3 -m unittest course-lab-final-staging/tests/test_skill_package.py
Not-tested: Real report final-staging consumption; user plans to modify staging later
```

## Completion Checklist

- [ ] Tests were written and observed failing before implementation.
- [ ] `course-lab-symbolic-expressing` exists as a standalone optional skill package.
- [ ] CLI writes response JSON with `tex_path`.
- [ ] CLI writes a temporary TeX artifact into caller-provided output dir.
- [ ] Missing or untraceable formulas remain visible as unresolved notes.
- [ ] Parent skill documents optional handoff without adding a required stage.
- [ ] `course-lab-final-staging` was not modified.
- [ ] Focused and adjacent tests pass.
- [ ] Lore-format commit created.
