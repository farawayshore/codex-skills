# Reference Report Structure

This summary is distilled from decoded reference reports under `AI_works/resources/lab_report_reference/Modern Physics Experiments/pdf_decoded/`.

## Common Backbone

Most reports follow this high-level order:

1. Introduction
2. Experiment Purpose
3. Experiment Equipment
4. Experiment Principle
5. Experiment Steps or Experiment Content
6. Experimental Process / Data and Analysis / Results
7. Experiment Discussion
8. Appendix or Signature Page
9. References

## Common Strong Patterns

- The principle section is often deep and uses numbered subsections plus figures or tables inside the same section.
- Principle figures are usually explained in the exact subsection where they appear, not appended later as a gallery.
- Multi-part visuals are commonly best represented as one parent figure with `(a)`, `(b)`, `(c)` subfigures when the source handout or filenames indicate that structure.
- Some experiments, especially optics-oriented ones, require explicit analysis of picture results rather than only numerical data tables.
- When the handout explicitly asks the student to photograph or record observations, those images should appear in the Experimental Process or Results section at the matching step, not only in prose summary.
- When several recorded pictures share the same observation-method name but differ by a serial number, they usually represent one process or rotation sequence and should be shown together as one grouped figure in serial order.
- Strong reports do not silently drop smaller observations. Even trivial or qualitative results are usually mentioned briefly so the result record remains complete.
- When the same sample has picture results from different methods, stronger reports mention each method-specific result instead of collapsing them into only the clearest method.
- Strong reports also explain how indirect results were obtained, rather than listing only the inferred final values.
- Strong reports often compare confirmed data against literature or reference results during the Results section itself, especially when a measured value looks abnormal.
- Strong reports sound like experimenters reporting observations and conclusions, not like tools narrating a workflow.
- Strong reports keep AI, automation, provenance, and process-log phrasing out of the visible text.
- Discussion commonly contains a subsection for assigned thinking questions.
- Stronger reports do more than answer thinking questions: they judge whether the result is reliable, partially reliable, or unreliable, explain why, compare the observations with theory and literature expectations, and discuss error sources plus improvements.
- Signature pages appear either as a dedicated subsection or as an appendix component.
- Equipment is usually a dedicated section with a main-equipment subsection and a compact table.

## Practical Rules For This Skill

- Use the matched handout to decide the actual content and order.
- Use the full reference-report pool only to learn the common structure and level of detail.
- Prefer a discussion section with an `Assigned Thinking Questions` subsection.
- For the rest of the discussion, prefer several substantial subsections rather than one short paragraph.
- Review local reference reports for the same experiment to understand the expected level of discussion, but keep the final wording original.
- Search education papers, teaching papers, or experiment-specific discussion notes to learn what the experiment is meant to demonstrate and what a good discussion should emphasize.
- Use that literature context to judge the user's results as reliable, partially reliable, or unreliable, and then explain the main reasons.
- Compare the user's results with theory and literature expectations whenever the available data are strong enough to support that comparison.
- In the principle section, keep figure placement local to the matching subsection and reference each figure in the surrounding prose.
- When figure grouping is uncertain, ask the user instead of inventing a subfigure layout.
- When a handout asks for picture-result interpretation, combine local vision reading with cited external reference analysis instead of relying on either one alone.
- Preserve serial-number order when process pictures are grouped, so the reader can follow the evolution of the observation over time or rotation angle.
- When a grouped process picture set shows a dynamic operation such as quartz-wedge insertion, explain the visible progression in the surrounding prose rather than leaving the process implicit.
- When an experiment relies on inference rules, color-comparison logic, or multi-step calculations, include the intermediate observations and reasoning path in the Experimental Process or Results section.
- If a confirmed result appears anomalous relative to literature or normal reference behavior, mention that anomaly in the Results section, keep the measured value visible, and explain the likely cause before the later discussion section expands on it.
- Stage and size-check raster result assets early. If the staged PNG pool threatens the final PDF size target, compress those PNG assets before the final layout and compile loop.
- Keep appendix material limited to code and signature pages or placeholders for them.
