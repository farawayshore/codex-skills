# Examiner Rubric

Use this rubric with `course-lab-finalize-qc` or any standalone report review pass. It produces scoring and reroute advice; it does not directly patch final report prose unless a future repair mode explicitly grants that authority.

## Scoring Dimensions

| Dimension | Checks |
|---|---|
| Scientific correctness | Claims follow handout theory, processed data, and stated assumptions. |
| Handout compliance | Required sections, procedures, and requested comparisons are present or explicitly unresolved. |
| Data and uncertainty validity | Tables, derived quantities, propagation routes, and confidence/coverage factors are internally consistent. |
| Plot/model evidence | Figures and models are traceable to plot/model manifests and not invented from prose. |
| TeX/report structure | Entry point builds, anchors/labels are stable, and report structure matches the template. |
| Figure/signatory evidence | Picture-result groups, signatory pages, and evidence plans are present when sources exist. |
| Discussion depth and thinking questions | Discussion claims are evidence-tagged and thinking-question answers are present when requested. |
| Unresolved honesty | `declared-unresolved`, `data-lack`, and missing-source states remain visible. |
| Completeness/page expectations | Page-count or completeness shortfalls become reroute tickets rather than filler prose. |

## Output Contract

Return a score/rubric summary, concrete evidence for each issue, owning skill for each reroute, downstream rerun requirements, and any declared-unresolved/data-lack items that must survive reruns.
