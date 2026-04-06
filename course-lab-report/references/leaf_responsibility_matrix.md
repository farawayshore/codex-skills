# Leaf Responsibility Matrix

## course-lab-discovery
- Invoke when: the run needs confirmed source candidates before any mutation.
- Required inputs: course name, experiment query, repo layout.
- Emits: confirmed experiment target, handout/reference/template/result-folder selections.
- Delegation preference: Prefer Inline / Main Agent.
- QC reroute ownership: weak discovery confirmation or wrong upstream selection.
- Does not own: decoding, workspace mutation, report drafting.

## course-lab-handout-normalization
- Invoke when: selected handout or reference material must become normalized section artifacts.
- Required inputs: confirmed handout/reference files or decoded outputs.
- Emits: normalized section JSON and Markdown.
- Delegation preference: Prefer Small Worker.
- QC reroute ownership: missing or malformed normalized handout structure.
- Does not own: workspace setup, later prose writing.

## course-lab-workspace-template
- Invoke when: the canonical report workspace and template must be established.
- Required inputs: confirmed experiment, chosen template, workspace mode.
- Emits: workspace layout, canonical TeX target, workspace manifest.
- Delegation preference: Prefer Small Worker.
- QC reroute ownership: wrong canonical workspace or template baseline.
- Does not own: discovery, data transfer, interpretation.

## course-lab-metadata-frontmatter
- Invoke when: report language and front-matter metadata must be applied.
- Required inputs: canonical workspace, reusable profile, report-language decision.
- Emits: updated front matter and reusable metadata where allowed.
- Delegation preference: Prefer Inline / Main Agent.
- QC reroute ownership: front-matter mismatch or missing identity metadata.
- Does not own: body scaffold, late-stage content writing.

## course-lab-run-plan
- Invoke when: normalized handout artifacts exist and the parent needs routing-ready planning outputs.
- Required inputs: normalized section JSON and Markdown, initialized workspace.
- Emits: run-plan JSON and Markdown artifacts.
- Delegation preference: Prefer Inline / Main Agent.
- QC reroute ownership: planning omissions that hide required later deliverables.
- Does not own: TeX mutation, downstream invocation, numerical work.

## course-lab-body-scaffold
- Invoke when: the canonical report needs handout-aligned section skeletons and procedure coverage.
- Required inputs: normalized handout artifacts, canonical workspace.
- Emits: scaffolded report sections and procedure-linked structure.
- Delegation preference: Prefer Small Worker.
- QC reroute ownership: missing required sections, missing procedure coverage, scaffold mismatch.
- Does not own: raw data transfer, final discussion, QC.

## course-lab-experiment-principle
- Invoke when: theory-facing sections must be written from handout-grounded material.
- Required inputs: normalized handout artifacts, scaffolded workspace.
- Emits: Introduction, nearby Background, Experiment Principle content and related theory figures.
- Delegation preference: Prefer Inline / Main Agent.
- QC reroute ownership: thin or missing theory-facing coverage.
- Does not own: data processing, discussion synthesis, final QC.

## course-lab-data-transfer
- Invoke when: raw data sources must be transcribed into stable report-side artifacts.
- Required inputs: matched raw data sources and canonical workspace.
- Emits: transferred data markdown and visible ambiguities for user review.
- Delegation preference: Prefer Small Worker.
- QC reroute ownership: missing raw records or transfer omissions discovered later.
- Does not own: computation, uncertainty math, interpretation prose.

## course-lab-data-processing
- Invoke when: confirmed transferred data must become processed numeric artifacts.
- Required inputs: user-validated transfer artifacts and handout requirements.
- Emits: processed-data artifacts and calculation outputs.
- Delegation preference: Prefer Inline / Main Agent.
- QC reroute ownership: data inconsistency, table inconsistency, missing processing detail.
- Does not own: raw transfer, plotting prose, final staging prose.

## course-lab-uncertainty-analysis
- Invoke when: uncertainty requirements must be computed from processed data and handout rules.
- Required inputs: processed-data artifacts and uncertainty requirements.
- Emits: uncertainty artifacts and propagated uncertainty outputs.
- Delegation preference: Prefer Inline / Main Agent.
- QC reroute ownership: weak or inconsistent uncertainty support.
- Does not own: plotting, discussion synthesis, final QC.

## course-lab-plotting
- Invoke when: processed artifacts require handout-grounded plots or figure data products.
- Required inputs: processed-data artifacts and plotting requirements.
- Emits: plot assets and plotting-side summaries.
- Delegation preference: Prefer Inline / Main Agent.
- QC reroute ownership: missing or weak plots.
- Does not own: late figure placement, prose rerouting, final QC.

## course-lab-results-interpretation
- Invoke when: processed results need evidence-grounded interpretation before discussion or final staging.
- Required inputs: processed-data artifacts, normalized handout artifacts, optional plots or modeling outputs.
- Emits: interpretation JSON, Markdown, and unresolved support gaps.
- Delegation preference: Prefer Inline / Main Agent.
- QC reroute ownership: missing, weak, contradictory, or insufficiently structured evidence support.
- Does not own: final discussion harmonization, figure placement, compile/QC.

## course-lab-discussion-ideas
- Invoke when: stable interpretation artifacts need discussion directions before synthesis.
- Required inputs: interpretation artifacts and matched reference-report paths.
- Emits: discussion-idea artifacts and synthesis-input candidates.
- Delegation preference: Explicit Stay-Local.
- QC reroute ownership: weak discussion direction coverage or missing beyond-handout ideas.
- Does not own: final harmonized discussion prose, report mutation outside its handoff artifacts.

## course-lab-discussion-synthesis
- Invoke when: approved or retained discussion directions must be harmonized before final staging.
- Required inputs: discussion-idea handoff artifacts and interpretation support.
- Emits: synthesized discussion artifacts for final staging.
- Delegation preference: Explicit Stay-Local.
- QC reroute ownership: weak harmonization or confidence-calibration across retained discussion material.
- Does not own: direct final QC, figure placement, raw idea generation.

## course-lab-final-staging
- Invoke when: stable scaffold, processing, interpretation, and discussion artifacts must become the late non-figure draft.
- Required inputs: canonical report workspace, scaffold, processed artifacts, interpretation artifacts, discussion artifacts, optional modeling or appendix inputs.
- Emits: staged late-draft TeX changes plus staging summaries and unresolved notes.
- Emits: comparison-case handoff data in the staging summary when same-case observed/simulation assets were normalized for downstream figure pairing.
- Delegation preference: Explicit Stay-Local.
- QC reroute ownership: thin staged prose, missing mathematical procedures, weak case coverage, page-count shortfall.
- Does not own: figure placement, compile loop, direct final QC.

## course-lab-figure-evidence
- Invoke when: the staged draft already exists and placement-ready evidence groups must be inserted.
- Required inputs: stable evidence-plan artifact or equivalent placement-ready grouping manifest, staged draft, explicit group-to-target mapping.
- Emits: figure placement changes and evidence-linked late draft updates.
- Emits: same-case observed-versus-simulation figure pairing when comparison-case handoff data exists.
- Delegation preference: Conditional Stronger Worker.
- QC reroute ownership: malformed late insertions or figure-placement issues.
- Does not own: scientific meaning of comparisons, compile/QC ownership.

## course-lab-finalize-qc
- Invoke when: the figure-complete draft needs compile, QC, page-count checks, and handoff reporting.
- Required inputs: canonical `main.tex`, figure-complete draft, optional evidence-plan and QC-side artifacts.
- Emits: final QC summary JSON, Markdown, unresolved report, and status outputs.
- Delegation preference: Prefer Inline / Main Agent.
- QC reroute ownership: diagnostic ownership only; it reports failures and warnings for the parent to route.
- Does not own: report prose repair, figure staging, data processing.
