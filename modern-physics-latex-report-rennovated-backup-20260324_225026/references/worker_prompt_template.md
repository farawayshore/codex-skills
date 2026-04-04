# Worker Prompt Template

Use these templates when dispatching write-capable workers during `Parallel Analysis Mode`.

## Shared Instructions

Every worker prompt should include:

- the owned region name;
- the exact `group_id` or `candidate_id` values it owns;
- the allowed files;
- the blocked files or blocked adjacent regions;
- the rule that edits must stay inside owned regions;
- the rule that preamble or global-structure edits must be escalated.

## Subsection Worker Template

```text
You are drafting one owned results region in a Modern Physics lab report.

Owned region:
- % region:results:<slug>:begin ... % region:results:<slug>:end

Owned evidence:
- <group_id_1>
- <group_id_2>

Allowed files:
- <main.tex or split tex path>
- <local asset files if any>

Do not touch:
- front matter
- preamble
- any other region
- global discussion

Your job:
- draft local analysis paragraphs
- place grouped figure blocks near the analysis
- add % evidence:<group_id> markers near prose and nearby figure blocks
- keep edits inside the owned region only

If you need to edit outside your region, stop and return an escalation note instead.
```

## Further Discussion Worker Template

```text
You are drafting one owned Further Discussion region in a Modern Physics lab report.

Owned region:
- % region:further-discussion:<slug>:begin ... % region:further-discussion:<slug>:end

Owned candidates:
- <candidate_id_1>
- <candidate_id_2>

Allowed files:
- <main.tex or split tex path>

Do not touch:
- results regions
- front matter
- preamble
- unowned discussion regions

Your job:
- draft evidence-backed interpretation only from the owned candidates
- keep observed facts, supported interpretation, and tentative hypothesis distinct
- keep wording strength aligned with candidate confidence
- return any unresolved conflict instead of smoothing it away
```

## QC Or Repair Worker Template

```text
You are checking one narrow part of the parallel drafting workflow.

Focus:
- <evidence placement | wording strength | placeholder hygiene | local repair>

Allowed scope:
- <owned region or owned verification surface>

Do not touch:
- unrelated regions
- global structure
- preamble

Your job:
- inspect the assigned surface only
- report scope violations or candidate-backing problems clearly
- make edits only when the controller has explicitly assigned repair authority
```

