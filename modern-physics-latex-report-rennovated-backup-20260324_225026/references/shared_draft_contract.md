# Shared Draft Contract

Use this contract whenever write-capable workers edit the shared report draft.

## Core Rule

Workers may edit only inside owned regions unless the controller explicitly expands their scope.

The controller owns:

- global structure;
- preamble changes;
- boundary reconciliation; and
- any edit that cuts across several regions.

## Region Marker Syntax

Use stable begin/end markers that are easy to search:

```tex
% region:results:z-cut:begin
% region:results:z-cut:group_ids=z_cut_primary,z_cut_wedge
% region:results:z-cut:blocked=results:x-cut,further-discussion:anomalies
...
% region:results:z-cut:end
```

For `Further Discussion`:

```tex
% region:further-discussion:anomalies:begin
% region:further-discussion:anomalies:candidate_ids=z_cut_anomaly
...
% region:further-discussion:anomalies:end
```

## Ownership Metadata

Keep nearby metadata comments readable. Record at least:

- owned `group_id` values;
- owned `candidate_id` values when relevant;
- blocked adjacent regions; and
- any local asset path the worker is allowed to touch.

## Allowed Edits Inside An Owned Region

Allowed:

- analysis paragraphs;
- local grouped figure blocks;
- `% evidence:<group_id>` markers;
- subsection-local figure labels and references;
- short local transitions that do not escape the owned region.

Forbidden unless reassigned:

- front matter;
- preamble edits;
- section reordering;
- another worker's region;
- global discussion text;
- global formatting sweeps across several regions.

## Conflict Example

Conflict:

- Worker A owns `% region:results:z-cut:*`.
- Worker B owns `% region:results:x-cut:*`.
- Worker A edits the shared subsection heading that sits outside both owned regions.

This is a controller escalation, not a valid worker change.

## Acceptable Same-Region Example

Acceptable:

- A worker adds one analysis paragraph,
- inserts one local grouped figure block,
- and adds `% evidence:z_cut_primary`

all inside `% region:results:z-cut:*`.

## Merge Rule

The controller reconciles changes only at checkpoints. If a worker discovers a needed change outside owned scope, it should return that as an escalation note instead of making the edit directly.

