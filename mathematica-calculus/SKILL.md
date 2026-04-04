---
name: mathematica-calculus
description: Route calculus work through Mathematica before answering. Use when Codex needs reliable symbolic or numeric results for derivatives, integrals, limits, series, extrema, Jacobians, Hessians, differential equations, or related calculus verification and simplification tasks, especially when the user asks to compute, solve, check, or confirm a result.
---

# Mathematica Calculus

Use Mathematica as the execution engine for calculus. Translate the request into Wolfram Language, run the bundled script, and answer from the computed output.

## Required Workflow

1. Translate the user's math task into explicit Wolfram Language before answering.
2. Run the bundled script immediately, even if the result looks easy enough to do mentally.

```bash
python3 /root/.codex/skills/mathematica-calculus/scripts/run_calculus.py --expr 'D[x^3 Sin[x], x]'
```

3. Treat the script output as the source of truth.
4. Refine and rerun if Mathematica returns an unevaluated or awkward result.
   - Add assumptions with `Assuming[...]` or `FullSimplify[..., Assumptions -> ...]`.
   - Force numeric evaluation with `N[...]`.
   - Rewrite branches or special functions with `FunctionExpand`, `Refine`, or `ComplexExpand`.
5. Present the answer clearly.
   - Include the Wolfram Language you ran.
   - Restate the result in standard math notation.
   - Do not invent hidden symbolic steps that Mathematica did not expose. If the user asks for steps, say Mathematica produced the final result and then give a brief human explanation.

## Common Patterns

- Derivative: `D[f[x], x]`
- Higher derivative: `D[f[x], {x, n}]`
- Indefinite integral: `Integrate[f[x], x]`
- Definite integral: `Integrate[f[x], {x, a, b}]`
- Limit: `Limit[f[x], x -> a]`
- Series: `Series[f[x], {x, a, n}]`
- Critical points: `Solve[D[f[x], x] == 0, x]`
- Jacobian: `D[{f1[x, y], f2[x, y]}, {{x, y}}]`
- Hessian: `D[f[x, y], {{x, y}, 2}]`
- Differential equation: `DSolve[{eqn, conds}, y[x], x]`

## Script Notes

- Use `--expr` for one-line or compound Wolfram Language such as `'Assuming[x > 0, FullSimplify[Integrate[1/x, x]]]'`.
- Use `--expr-file` for longer Wolfram Language programs.
- Add `--json` when a later step needs structured output.
- The runner uses `wolframscript` by default and honors `WOLFRAMSCRIPT_BIN` when it is set.
