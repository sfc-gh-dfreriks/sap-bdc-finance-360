# 1. Concepts

What Finance 360 is, what the SAP Business Data Cloud share actually provides,
and which financial questions this data can and cannot answer.

All figures in this handbook were verified against the live account on
**2026-09-21**. Account `MSB89522`, region `PUBLIC.AWS_US_WEST_2`.

---

## The problem this addresses

A finance close does not live in one place. The journal entry header sits in one
SAP table, the line items in another, the cost centre and profit centre masters
in two more, and the supplier invoice in a fifth. Answering "what did we spend
by cost centre last quarter, and which of it is still unpaid" means joining five
objects whose keys and sign conventions are SAP's, not a BI tool's.

The usual response is a nightly extract into a warehouse-native star schema.
That works, and it also means the numbers in the report are a copy whose
freshness is a property of the pipeline rather than of the source.

Finance 360 takes the other route: **the SAP objects stay where they are** and
Snowflake reads them in place through a share. There is no extract step, so
there is no extract to be stale.

---

## Zero-copy, and what that costs

The L0 sources are SAP BDC Standard Data Products, surfaced into the account as
shared databases named `SAP_BDC_DEMO_*`. Nothing is copied at that boundary — a
query against L1 is a query against the provider's storage.

That has one consequence worth stating up front, because it shapes every layer
above: **you do not control the shape of L0**. Column names, sign conventions
and the absence of any object SAP does not publish are givens. The curation work
happens in L1 and L2, not in the source.

---

## The layers

| Layer | Schema | What it is | Objects |
|---|---|---|---|
L0 | `SAP_BDC_DEMO_*` (shared) | SAP BDC Standard Data Products, read in place | 4 shared databases referenced |
L1 | `SAP_FINANCE_360.SAP_BDC_L1` | 1:1 passthrough **views** with business column comments | 6 |
L2 | `SAP_FINANCE_360.ANALYTICS` | Joined, enriched and aggregated analytics objects | 7 |
Semantic | `SAP_FINANCE_360.SEMANTIC` | Semantic view plus the Cortex Analyst stage model | 2 semantic views |

The database carries **4 schemas** in total.

L1 is deliberately thin. Each of its six objects is a view, not a table and not
a materialized view, so L1 adds naming, comments and access control and adds
nothing else — no storage, no refresh, no lag.

| L1 object | SAP concept |
|---|---|
`COSTCENTER` | Cost centre master |
`GENERALLEDGERACCOUNT` | GL account master |
`JOURNALENTRY` | Journal entry header |
`OPERATIONALACCTGDOCITEM` | Accounting document line item — the grain that carries amounts |
`PROFITCENTER` | Profit centre master |
`SUPPLIERINVOICE` | Supplier invoice |

Five of those six are masters or headers. `OPERATIONALACCTGDOCITEM` is where the
money is, and it is the object every L2 amount ultimately derives from.

---

## SAP amounts are signed

This is the single most important thing to know before writing a query against
this data, and it is the source of most wrong first answers.

In `OPERATIONALACCTGDOCITEM` an amount column carries the posting's natural
sign, and the debit/credit character of the row is carried separately in
`DEBITCREDITCODE`. A revenue credit and an expense debit can therefore sit in
the same column with opposing signs.

A bare `SUM(amount)` over that column is not revenue, not expense, and not the
difference between them — it is an artefact of the debit/credit mix that
happened to fall inside the filter. Correct aggregation requires **`ABS` on the
amount together with a `DEBITCREDITCODE` filter** that selects the side you
mean.

The L2 layer applies that pattern once so that consumers do not each have to
rediscover it. Every figure quoted in this handbook comes from either L2 or from
an L0 query written with `ABS` and a `DEBITCREDITCODE` filter — see
[findings](05-findings.md) for the reconciliation that proves the two agree.

---

## What the data covers

Three company codes appear in the journal data. The posting windows differ by
object, which matters when comparing them:

| Object | Date column | From | To | Rows |
|---|---|---|---|---|
`DT_JOURNAL_ENTRY_360` | `POSTINGDATE` | 2023-01-01 | 2025-03-28 | 10,300 |
`DT_AP_AGING` | `POSTINGDATE` | 2023-01-06 | 2025-04-25 | 419 |
`DT_AR_AGING` | `INVOICEDATE` | 2024-11-14 | 2026-05-07 | 3,868 |

AR does not share a window with the other two. It starts almost two years later
and extends past the end of the ledger. That is a property of how the AR object
was produced rather than a load error — see
[findings](05-findings.md#ar-is-generated-not-shared).

---

## What this is not

This is **transactional finance data**: postings, balances, invoices, aging.

It is **not** a metadata or catalog model. There is no object here describing
which SAP data products exist or how their entities associate; for that pattern
see the companion supply chain ontology work referenced in
[references](06-references.md).

It is also **not a general ledger of record**. Nothing here posts, reverses or
closes. Every object is read-only downstream of SAP, and the app does not write.

Questions this data cannot answer include anything requiring a customer master
(it is not among the six L1 objects), anything requiring a cash or bank ledger,
and anything requiring period-end close status.

---

## Where the AI layer sits

Two things in this system answer natural-language questions, and they are not
the same thing.

- **Semantic views** — two of them, in `ANALYTICS` and `SEMANTIC`. Governed
  Snowflake objects, queryable with `SEMANTIC_VIEW(...)`.
- **A Cortex Analyst stage model** — a YAML file at
  `@SAP_FINANCE_360.SEMANTIC.SEMANTIC_MODELS/finance_360.semantic.yaml`.

The React application's Cortex Analyst page reads **the stage model**. It does
not read either semantic view. The distinction is easy to get wrong and it
changes what you edit when an Analyst answer is bad; it is set out in full in
[the semantic layer](08-semantic-layer.md).
