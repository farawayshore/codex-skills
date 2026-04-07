# Course Lab Symbolic Expressing Design

## Context

The installed `course-lab-report` family already has `course-lab-data-processing` for handout-aligned direct and derived calculations, including optional appendix-ready calculation details, and `course-lab-final-staging` for late-stage non-figure report assembly. Recent reports still lack enough mathematical procedure for a physics undergraduate reader to understand how selected reported results came from the handout and calculation code.

`course-lab-symbolic-expressing` will fill that gap as a standalone optional helper leaf. It is not a required stage between processing and staging. It behaves more like optional modeling support: another skill can call it when a result needs a compact symbolic explanation artifact, then consume the returned path.

## Goals

- Explain how a given processed result was obtained from handout formulas and calculation code.
- Produce undergraduate-readable TeX-like temporary artifacts with formula chain, variable definitions, substitution route, and a short calculation-route paragraph.
- Return the generated artifact path to the requesting skill through a small JSON response.
- Default to workspace-local temporary output for reproducibility, with caller override support for true `/tmp` one-shot output.
- Keep uncertainty and calculation gaps visible instead of inventing missing derivations.
- Stay independent of `course-lab-final-staging` so staging can be modified later to call this helper more eagerly.

## Non-Goals

- Do not mutate `main.tex`.
- Do not recompute official results or replace `course-lab-data-processing`.
- Do not perform physics interpretation, theory comparison, discussion synthesis, figure placement, compilation, or QC.
- Do not decide which results are scientifically important.
- Do not silently normalize handout/code disagreements.
- Do not scan a workspace to discover inputs. Callers must pass explicit handout, code, result, and output paths.

## Recommended Approach

Create a standalone skill package:

```text
/root/.codex/skills/course-lab-symbolic-expressing/
  SKILL.md
  agents/openai.yaml
  scripts/render_symbolic_explanation.py
  tests/baseline_failures.md
  tests/test_render_symbolic_explanation.py
  tests/test_skill_package.py
```

The primary command should be script-backed and path-returning:

```bash
python3 /root/.codex/skills/course-lab-symbolic-expressing/scripts/render_symbolic_explanation.py \
  --handout "/path/to/decoded_handout.md" \
  --calculation-code "/path/to/analysis/process_data.py" \
  --processed-result "/path/to/analysis/derived_uncertainty.json" \
  --result-key "wave_speed" \
  --output-dir "/path/to/results/<experiment>/analysis/symbolic_expressing/tmp" \
  --output-response-json "/path/to/results/<experiment>/analysis/symbolic_expressing/tmp/wave_speed_symbolic_response.json"
```

The command returns by writing JSON such as:

```json
{
  "result_key": "wave_speed",
  "tex_path": "/path/to/results/experiment/analysis/symbolic_expressing/tmp/wave_speed_symbolic_explanation.tex",
  "sources": {
    "handout": "/path/to/decoded_handout.md",
    "calculation_code": ["/path/to/analysis/process_data.py"],
    "processed_result": "/path/to/analysis/derived_uncertainty.json"
  },
  "unresolved": []
}
```

## Data Flow

1. The caller identifies a result that needs mathematical procedure support and passes explicit source paths.
2. The helper reads the handout first to identify the official formula, symbols, units, and result meaning.
3. The helper reads the calculation code and extracts the relevant assignment or expression chain for the target result.
4. The helper reads the processed result artifact and matches the target result key against stored formulas, values, units, and uncertainties when present.
5. The helper writes a short temporary TeX artifact to the requested output directory.
6. The helper writes a response JSON containing the TeX path, source trace, and unresolved notes.
7. The caller decides whether and how to include the returned TeX path in the report.

## TeX Artifact Shape

The generated file should be compact and report-ready, for example:

```tex
\paragraph{Calculation route for wave speed}
The handout defines the string linear density and wave speed as
\[
\rho = \frac{m}{L}, \qquad v = \sqrt{\frac{T}{\rho}}.
\]
The calculation code first evaluates \(\rho\) from the measured mass and length, then substitutes the measured tension into \(v=\sqrt{T/\rho}\). This is why the reported wave speed depends on \(m\), \(L\), and \(T\).
```

The artifact should prefer symbolic route and key substitutions over raw numeric dumps. If uncertainty propagation is present in the processed result, it may include a compact partial-derivative route, but it should not duplicate a full appendix table unless the caller explicitly asks for that level later.

## Error Handling

- If the handout formula cannot be found, write a visible `\NeedsInput{...}` note in TeX and an `unresolved` JSON entry.
- If the result key cannot be traced in code or processed results, write a visible unresolved note instead of fabricating a derivation.
- If code and handout formulas conflict, preserve both evidence lanes and flag the disagreement.
- If a value exists but no formula exists, explain only the evidence-backed value source and mark the missing formula route unresolved.
- Missing output directories may be created by the script, but missing input files should fail clearly.

## Integration With The Skill Family

The parent `course-lab-report` skill should list `course-lab-symbolic-expressing` as an optional helper leaf near late-stage result assembly and modeling support. The parent should describe the handoff as explicit and caller-owned: callers provide the handout, calculation code, processed result, target result key, and output directory; the helper returns a temp TeX path and unresolved notes.

`course-lab-final-staging` does not need to change in the first implementation pass. A later staging update can call this helper more eagerly and include the returned TeX artifacts when result narration lacks mathematical procedure.

## Test Strategy

Follow skill-TDD:

1. Record baseline failures showing no standalone package exists and no path-returning symbolic helper is available.
2. Add a failing package test for required files and skill boundary language.
3. Add a failing behavior test for JSON response creation and TeX path output.
4. Add a failing behavior test that a handout formula plus calculation-code expression produces a formula-chain TeX artifact.
5. Add a failing behavior test that missing or mismatched formula evidence appears in `unresolved`.
6. Add a failing behavior test that the default workspace-local temp output can be overridden by an explicit output directory.
7. Implement minimally until tests pass.

## Open Risks

- Static code expression extraction can be brittle for complex analysis scripts. The first version should handle straightforward Python assignment chains and fall back to unresolved notes for harder cases.
- If processed result artifacts vary widely, the first version should support the current `course-lab-data-processing` JSON shape first and treat other shapes conservatively.
- The generated explanation may need later tuning after final-staging begins consuming it in real reports.
