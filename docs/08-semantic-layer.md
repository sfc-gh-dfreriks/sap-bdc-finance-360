# 8. The semantic layer

Three semantic artefacts exist over the same seven L2 objects. They are not
versions of one another. This document sets out what each contains, why there are
three, and which one to edit.

---

## Three artefacts, one data layer

| Artefact | Type | Location |
|---|---|---|
`SAP_FINANCE_360` | semantic view | `SAP_FINANCE_360.ANALYTICS` |
`SAP_FINANCE_360_ANALYTICS` | semantic view | `SAP_FINANCE_360.SEMANTIC` |
`finance_360.semantic.yaml` | Cortex Analyst model | `@SAP_FINANCE_360.SEMANTIC.SEMANTIC_MODELS/` |

Two are database objects and queryable with `SEMANTIC_VIEW(...)`. The third is a
file on a stage, read by Cortex Analyst. They share no definition — there is no
generation step from one to another, so a change to any one of them leaves the
other two exactly as they were.

That is the fact to internalise before touching any of them.

---

## Semantic view coverage

| | `ANALYTICS.SAP_FINANCE_360` | `SEMANTIC.SAP_FINANCE_360_ANALYTICS` |
|---|---|---|
Logical tables | 4 | 5 |
Relationships | **0** | 12 |
Metrics | 45 | **0** |
`DESCRIBE` dimension rows | 120 | 251 |
`DESCRIBE` fact rows | 25 | 74 |

Logical table names:

| `ANALYTICS.SAP_FINANCE_360` | `SEMANTIC.SAP_FINANCE_360_ANALYTICS` |
|---|---|
`AR` | `AP_AGING` |
`EXPENSE` | `EXPENSE_BY_COSTCENTER` |
`JOURNAL` | `JOURNAL_ENTRY` |
`REVENUE` | `PNL_SUMMARY` |
| `REVENUE_BY_PROFITCENTER` |

The naming convention differs too: the `ANALYTICS` view uses short business names
(`AR`, `EXPENSE`), the `SEMANTIC` view mirrors the underlying table names
(`AP_AGING`, `EXPENSE_BY_COSTCENTER`). A question written against one will not
run against the other.

### The split is a complement, not a progression

Read the relationships and metrics rows together:

- The `ANALYTICS` view has **45 metrics and cannot join**. It can compute a
  defined measure but has no declared path between its four tables.
- The `SEMANTIC` view has **12 relationships and no metrics**. It can join across
  five tables but defines no measure to compute over the join.

Neither is a superset of the other, so "use the newer one" is not available as
advice. And a question that needs a governed metric *and* a join across two
tables — a perfectly ordinary finance question — cannot be answered by either view
alone.

`DT_GL_BALANCE` (1,793 rows) appears in neither view. Of the seven L2 objects,
`ANALYTICS` exposes four and `SEMANTIC` exposes five; the union is six.

### What to do about it

This is the least defensible part of the stack. It is not a discovery about SAP
or about Snowflake semantic views — it is where iteration stopped, and it should
be read as technical debt rather than as design.

If you are reproducing this pattern: **build one semantic view** carrying both
the relationships and the metrics, over all seven L2 objects. There is no reason
in the platform for the split.

If you are maintaining this one, the merge target is the `SEMANTIC` view — it has
the relationships, which are the harder half to reconstruct, and the wider table
coverage. Port the 45 metrics onto it and add `DT_GL_BALANCE`.

### On the dimension counts

120 and 251 dimensions look like a large modelling effort and are not one. SAP
source objects are wide — `COSTCENTER` alone carries dozens of columns — and each
retained column becomes a dimension row in `DESCRIBE SEMANTIC VIEW` output.

Treat those numbers as describe-output row counts, not as a count of curated,
documented dimensions. Nobody wrote 251 dimension descriptions, and quoting the
figure as evidence of modelling depth would be misleading.

The contrast with the Analyst model is instructive: 24 dimensions across four
tables, chosen rather than inherited. That is a model someone shaped.

---

## The Cortex Analyst model

| Property | Value |
|---|---|
Stage path | `@SAP_FINANCE_360.SEMANTIC.SEMANTIC_MODELS/finance_360.semantic.yaml` |
Model name | `sap_finance_360` |
Base tables | 4 |
Dimensions | 24 |
Measures | 9 |
Facts | 0 |
Verified queries | **0** |

Base tables: `ANALYTICS.DT_JOURNAL_ENTRY_360`,
`ANALYTICS.DT_EXPENSE_BY_COSTCENTER`,
`ANALYTICS.DT_REVENUE_BY_PROFITCENTER`, `ANALYTICS.DT_AR_AGING`.

**The React app's Cortex Analyst page reads this file.** It does not read either
semantic view.

This is stated in [concepts](01-concepts.md),
[architecture](02-architecture.md#the-cortex-analyst-model-is-a-third-separate-artefact)
and [the analyst layer](07-analyst-and-agent.md), and it is repeated here because
it is the one thing in this stack that was previously documented incorrectly. The
symptom of believing otherwise is an edit that appears to do nothing: change a
semantic view, reload the app, every answer identical.

Its coverage differs from both views again — a fourth distinct table set:

| L2 object | `ANALYTICS` view | `SEMANTIC` view | Analyst model |
|---|---|---|---|
`DT_JOURNAL_ENTRY_360` | yes | yes | yes |
`DT_AR_AGING` | yes | no | yes |
`DT_EXPENSE_BY_COSTCENTER` | yes | yes | yes |
`DT_REVENUE_BY_PROFITCENTER` | yes | yes | yes |
`DT_AP_AGING` | no | yes | no |
`DT_PNL_SUMMARY` | no | yes | no |
`DT_GL_BALANCE` | no | no | no |

Three artefacts, three different table sets, and only `DT_JOURNAL_ENTRY_360`,
`DT_EXPENSE_BY_COSTCENTER` and `DT_REVENUE_BY_PROFITCENTER` are in all three.
`DT_GL_BALANCE` is in none.

`DT_AR_AGING` appears in the `ANALYTICS` view and in the Analyst model but not in
the `SEMANTIC` view; `DT_AP_AGING` and `DT_PNL_SUMMARY` appear only in the
`SEMANTIC` view. There is no principle behind that distribution — it is three
independent editing histories.

---

## Which artefact to edit

| Wrong behaviour | Edit |
|---|---|
App Analyst page gives a bad answer | the stage YAML |
App Analyst page cannot answer at all | the stage YAML — likely a missing base table |
`SAP_FINANCE_360_AGENT` gives a bad answer | the semantic view the agent is bound to |
A `SEMANTIC_VIEW(...)` query is wrong | the view named in that query |
A metric definition is wrong | `ANALYTICS.SAP_FINANCE_360` — it holds all 45 |
A join is missing | `SEMANTIC.SAP_FINANCE_360_ANALYTICS` — it holds all 12 relationships |

Editing the stage file:

```sql
get @SAP_FINANCE_360.SEMANTIC.SEMANTIC_MODELS/finance_360.semantic.yaml
    file:///tmp/;
-- edit /tmp/finance_360.semantic.yaml
put file:///tmp/finance_360.semantic.yaml
    @SAP_FINANCE_360.SEMANTIC.SEMANTIC_MODELS/ overwrite = true auto_compress = false;
```

`auto_compress = false` is required. Cortex Analyst reads the YAML as a file; a
gzipped upload is not readable, and the failure is unhelpful.

---

## What the semantic layer must encode about this data

Whichever artefact you extend, three properties of the source have to be carried
into the model. None of them is discoverable from a column name.

### 1. Signed amounts

Amounts in `OPERATIONALACCTGDOCITEM` carry the posting's natural sign, with the
debit/credit character in `DEBITCREDITCODE`. Correct aggregation needs **`ABS`
plus a `DEBITCREDITCODE` filter**.

L2 encodes this inside `DT_JOURNAL_ENTRY_360`, so a measure defined over L2
inherits it. A measure defined over L0 does not, and any hand-written SQL against
the shares does not.

The reconciliation that proves L2 gets it right: L0 with `ABS` and the filter
gives $2,250,872,386, and `SUM(REVENUE)` over `DT_PNL_SUMMARY` gives
$2,250,872,386. Exactly equal.

This is the property most worth encoding as a verified query, because the wrong
query succeeds silently.

### 2. `Cleared` dominates AR

2,983 of 3,868 `DT_AR_AGING` rows are in the `Cleared` bucket with zero open
amount. Any AR average that does not exclude them is 77% too small.

An AR measure in a semantic model should either filter `Cleared` or be named so
that its inclusion is unmistakable.

### 3. Grains are not interchangeable

Two mismatches that a model can easily invite:

- **Documents versus line items.** `DT_PNL_SUMMARY` accounts for 5,150
  documents; `DT_JOURNAL_ENTRY_360` holds 10,300 rows — exactly 2×, because every
  document has two offsetting lines. A "transaction count" measure has to say
  which it counts.
- **AP gross versus posted revenue.** AP gross is $4,340,327,683 over 419
  invoices; three years of revenue is $2,250,872,386. Different populations at
  different grains. A model that exposes both as comparable currency measures
  invites a ratio that means nothing.

---

## Data windows are a modelling constraint

| Object | Column | From | To |
|---|---|---|---|
`DT_JOURNAL_ENTRY_360` | `POSTINGDATE` | 2023-01-01 | 2025-03-28 |
`DT_AP_AGING` | `POSTINGDATE` | 2023-01-06 | 2025-04-25 |
`DT_AR_AGING` | `INVOICEDATE` | 2024-11-14 | 2026-05-07 |

The 12 relationships in the `SEMANTIC` view make cross-object joins expressible,
and a date-aligned join between AR and the ledger will return almost nothing for
most of the AR window — the ledger ends more than a year before AR does.

That is not a defect in the relationships. It is a property of `DT_AR_AGING`
being generated rather than derived from the ledger (see
[findings](05-findings.md#dt_ar_aging-is-a-plain-table-wearing-a-dynamic-tables-prefix)),
and a model offering AR-to-revenue time series should carry a description saying
so.

---

## Recommended end state

In priority order:

| # | Change | Why |
|---|---|---|
1 | Add verified queries to the Analyst model, starting with signed-amount revenue | 0 today; the hardest idiom is untaught and fails silently |
2 | Add `DT_PNL_SUMMARY` and `DT_AP_AGING` to the Analyst model | the app has pages for both subject areas |
3 | Consolidate the two semantic views into one with metrics *and* relationships | neither is complete; the split has no rationale |
4 | Add `DT_GL_BALANCE` to the consolidated view | it is in no semantic artefact at all |
5 | Describe the `Cleared` exclusion and the document/line-item distinction on every affected measure | both produce silently wrong numbers |
6 | Note the AR window on any AR measure | prevents an empty-series comparison |

Items 1 and 2 are the ones a customer will notice. Item 3 is the one a
maintainer will.
