# 7. The analyst and agent layer

The natural-language surfaces over this data: what each one reads, what each can
answer, and where the coverage stops. This is the part of the stack with the
largest gap between what it looks like it can do and what it can do.

---

## Three consumers, three different bindings

There are three ways to ask this data a question in natural language, and they do
not share a model.

| Consumer | Reads | Surface |
|---|---|---|
App page 9, "Cortex Analyst" | the **stage YAML** | the deployed React app |
`SAP_FINANCE_360_AGENT` | a semantic view | Snowflake Intelligence |
Hand-written `SEMANTIC_VIEW(...)` | the named semantic view | worksheet or client |

**The app reads the stage model.** Not `ANALYTICS.SAP_FINANCE_360`, not
`SEMANTIC.SAP_FINANCE_360_ANALYTICS`. This was got wrong once during the build
and it wasted real time, because the symptom of getting it wrong is
indistinguishable from an edit having no effect: you change a semantic view,
reload the app, and every answer is identical.

If an answer on the app's Analyst page is wrong, the artefact to change is:

```
@SAP_FINANCE_360.SEMANTIC.SEMANTIC_MODELS/finance_360.semantic.yaml
```

Verifying the agent in Snowflake Intelligence does not verify the app, and the
reverse is also true. Both have to be tested separately.

---

## The stage model

| Property | Value |
|---|---|
Stage path | `@SAP_FINANCE_360.SEMANTIC.SEMANTIC_MODELS/finance_360.semantic.yaml` |
Model name | `sap_finance_360` |
Base tables | 4 |
Dimensions | 24 |
Measures | 9 |
Facts | 0 |
Verified queries | **0** |

The four base tables, all from L2:

| Base table | Logical name in model | Rows |
|---|---|---|
`ANALYTICS.DT_JOURNAL_ENTRY_360` | Journal Entry 360 | 10,300 |
`ANALYTICS.DT_AR_AGING` | Ar Aging | 3,868 |
`ANALYTICS.DT_EXPENSE_BY_COSTCENTER` | Expense By Costcenter | 2,459 |
`ANALYTICS.DT_REVENUE_BY_PROFITCENTER` | Revenue By Profitcenter | 1,091 |

24 dimensions and 9 measures across four tables is a modest, deliberately small
model — roughly six dimensions and two measures per table. That is a reasonable
shape for Analyst, which degrades when given hundreds of undescribed columns.
Contrast the semantic views, whose `DESCRIBE` output runs to 120 and 251
dimensions because every retained SAP column becomes one.

`facts: 0` is expected here: in this model the numeric columns are declared as
measures rather than as facts.

---

## What the model covers, and what it does not

Three of the seven L2 objects are absent:

| L2 object | Rows | In Analyst model | Has an app page |
|---|---|---|---|
`DT_JOURNAL_ENTRY_360` | 10,300 | yes | General Ledger, Period Analysis |
`DT_AR_AGING` | 3,868 | yes | Accounts Receivable |
`DT_EXPENSE_BY_COSTCENTER` | 2,459 | yes | Cost Centers |
`DT_REVENUE_BY_PROFITCENTER` | 1,091 | yes | Profit Centers |
`DT_AP_AGING` | 419 | **no** | Accounts Payable |
`DT_GL_BALANCE` | 1,793 | **no** | — |
`DT_PNL_SUMMARY` | 81 | **no** | Period Analysis |

The problem is not the count, it is the overlap with the navigation. The app
presents a dedicated **Accounts Payable** page, a **General Ledger** page and a
**Period Analysis** page. A user reads those nine sidebar entries as a statement
of scope, then asks the Analyst page about payables — and the model has no table
to land on.

Nothing in the interface signals the boundary. There is no "this model covers
four of seven subject areas" notice, so the failure looks like the AI being poor
rather than the model being partial.

Two ways to close it, in order of preference:

1. **Extend the model.** `DT_PNL_SUMMARY` is the obvious first addition — 81
   rows, pre-aggregated, already correctly signed, and it is the object this
   handbook's control total comes from. `DT_AP_AGING` is second, because a page
   exists for it. `DT_GL_BALANCE` is third and least urgent, since no page reads
   it either.
2. **Disclose the boundary in the UI.** Cheaper, and honest. Name the four
   covered areas on the page.

Doing neither is the current state.

---

## The verified query gap

**Zero verified queries.** This is the most significant gap in the stack and it
should be said plainly rather than buried in a capability list.

A verified query pairs a natural-language question with the SQL that correctly
answers it. Cortex Analyst uses them as worked examples: they teach the model the
question shapes the data is meant to serve, and the idioms the data requires.

With none, every question is answered from table and column metadata alone. For
most datasets that is merely suboptimal. For this one it is worse than that,
because the single hardest thing about this data is not discoverable from
metadata:

> SAP amounts are signed. Correct aggregation requires `ABS` on the amount
> together with a `DEBITCREDITCODE` filter.

No column name states that. No description the model has seen demonstrates it.
The model is therefore free to emit a bare `SUM` — which succeeds, returns a
plausible magnitude, and is wrong. And because every document in this dataset has
exactly two offsetting line items (see
[findings](05-findings.md#documents-and-line-items-differ-by-exactly-2)), a bare
`SUM` over the journal table approximates the residual of 5,150 near-cancellations
rather than measuring money.

The failure mode is a confidently wrong number, not a refusal. In front of a
customer architect that is the worst available outcome.

### The queries to add first

In priority order, each targeting a known idiom or a known trap:

| # | Question shape | What it teaches |
|---|---|---|
1 | Total revenue for a fiscal year | `ABS` + `DEBITCREDITCODE`; ties to $2,250,872,386 across all years |
2 | Revenue, expense and net income by fiscal year | the signed pattern on both sides at once |
3 | Expense by cost centre for a period | grain, and joining to the cost centre master |
4 | Revenue by profit centre for a period | the profit-centre counterpart |
5 | Open AR by aging bucket | that `Cleared` (2,983 of 3,868 rows) must be excluded |
6 | Count of overdue AR invoices | the overdue flag, not a date arithmetic guess; answer 483 |
7 | Document count vs line-item count | that the two differ by exactly 2× and are not interchangeable |
8 | Anything spanning AR and the ledger by date | that the windows do not overlap |

Query 1 is the one to write first, because it has an exact expected answer to
assert against. Queries 5 and 7 encode traps that produce wrong answers rather
than errors, which makes them worth more than their apparent simplicity.

---

## Three traps a verified query should encode

These are the mistakes this data invites. Each produces a plausible number.

**Summing signed amounts.** Covered above. Produces a residual, not a total.

**Counting AR without excluding `Cleared`.** 2,983 of 3,868 AR rows are cleared
and carry zero open amount. An average open amount over all rows is divided by a
denominator four times too large, and the answer is quietly 77% too small.

**Comparing AP gross to revenue.** AP gross totals $4,340,327,683 across 419
invoices; three years of revenue is $2,250,872,386. The ratio is an artefact of
the two coming from different populations at different grains —
`SUPPLIERINVOICE` document amounts versus posted line items — not a finding about
liquidity. A model with no verified query on this topic will happily divide one
by the other.

---

## The agent

`SAP_FINANCE_360_AGENT`, created by `sql/05_cortex_agent.sql`, is the Snowflake
Intelligence surface. It is bound to a semantic view rather than to the stage
model.

That means the agent inherits the semantic-view split described in
[the semantic layer](08-semantic-layer.md): depending on which view it is bound
to, it has either the metrics or the relationships, but not both.

Practical consequence: the agent and the app can give different answers to the
same question, and both can be defensible given what each was handed. When
demonstrating both in one session, ask the same question of each deliberately and
be ready to explain the difference — it is a modelling artefact, not a bug, and
an architect in the room will notice.

---

## The Cortex Analyst page in the app

Page 9 of 9. Its screenshot is `/tmp/finance_shots/08_analyst.png`.

One implementation detail from the capture work that reveals something about the
page: it is the only page besides BDC Data Products whose screenshot settles on
`[class*=card]` rather than `canvas`. Both are card layouts with no chart. The
Analyst page renders results as text and tables, not as visualisations, so a
capture script waiting for a canvas on it waits forever.

---

## Honest summary for a customer conversation

What to claim:

- Natural language over governed L2 objects, with no data copied out of SAP.
- Four subject areas covered: journal entries, AR aging, expense by cost centre,
  revenue by profit centre.
- The underlying numbers reconcile to the source exactly — $2,250,872,386 L0 to
  L2, to the dollar.

What to state rather than let be discovered:

- Zero verified queries. The model has no worked examples and has not been
  taught the signed-amount idiom.
- Accounts payable, GL balances and the P&L summary are outside the model, while
  the app has pages for them.
- AR is generated data, not SAP-shared, because the products in scope publish no
  receivables object.
- The app's Analyst page and the Intelligence agent read different artefacts and
  may differ.

Declaring the gaps first costs a minute. Being caught by a payables question that
the sidebar advertises and the model cannot answer costs the meeting.
