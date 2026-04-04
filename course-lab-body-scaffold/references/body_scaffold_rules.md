# Body Scaffold Rules

This file localizes the body-scaffold contract so the skill can remain independent from the parent `course-lab-report` folder.

## Required Order

Insert or preserve the report body in this order:

1. Introduction
2. Objectives
3. Experiment Equipment
4. Experiment Principle
5. Experimental Process / Experimental Phenomenon
6. Experiment Discussion
7. Appendix
8. References

## Procedure Coverage Rules

- Use normalized handout sections before any reference-report wording.
- Extract procedure steps into `<experiment-safe-name>_procedures.md`.
- Prefix every extracted step with `P01`, `P02`, and so on.
- Structure the `Experimental Process / Experimental Phenomenon` section strictly against those procedure steps.
- Every procedure step must appear in the TeX either as completed content or as an explicit placeholder with a matching `% procedure:Pxx` comment.

## Section Notes

- Use the handout introduction as source material for the Introduction and as seed notes for the later abstract.
- Use the handout objective or aim section for the Objectives section.
- Build the equipment section from handout mentions and decoded tables.
- Keep thinking questions visible under the discussion scaffold instead of answering them too early.
- Keep Appendix limited to reusable structural placeholders such as `Code` and `Signature Pages` unless the current run clearly needs more.

## Missing-Content Rule

When a required section or detail is incomplete, keep a visible `\NeedsInput{...}` placeholder instead of inventing missing content.
