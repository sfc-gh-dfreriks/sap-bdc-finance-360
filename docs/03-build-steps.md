# 3. Build steps

The order in which this was built, and what each step has to produce before the
next one can start. Scripts and file paths are in
[execution](04-execution.md); this document is the sequence and the reasoning.

---

## Step 0 — Confirm the L0 shares are readable

Nothing downstream can be built until the SAP BDC Standard Data Products are
mounted and the running role can select from them.

The three shared databases the stack actually reads are:

| Shared database | Object used |
|---|---|
`SAP_BDC_DEMO_ENTRY_VIEW_JOURNAL_ENTRY` | `BDCCONNECT.OPERATIONALACCTGDOCITEM` |
`SAP_BDC_DEMO_JOURNAL_ENTRY_HEADER` | `BDCCONNECT.JOURNALENTRY` |
`SAP_BDC_DEMO_SUPPLIER_INVOICE` | `BDCCONNECT.SUPPLIERINVOICE` |

`sql/01_l0_sources.md` documents the L0 layer. It is markdown, not SQL, because
there is nothing to create — the objects belong to the provider. That file is the
only "DDL" step in the stack that runs no DDL, and that is the point being made.

Do the sign check here, before building anything on top. Run a `SUM` over the
amount column on `OPERATIONALACCTGDOCITEM` with no `ABS` and no
`DEBITCREDITCODE` filter, then run it with both. If the two agree, the filter is
not doing what you think it is.

---

## Step 1 — L1 curated views

`sql/02_l1_curated_views.sql`, run as `ACCOUNTADMIN` or a role holding the L0
grants.

Creates `SAP_FINANCE_360.SAP_BDC_L1` and six views in it. Each view is a
projection over one L0 object with a `COMMENT` on every column.

Deliberate constraints on this step:

- **Views, not tables.** No `CREATE TABLE AS`, no `CREATE MATERIALIZED VIEW`.
  The layer must add no storage and no refresh obligation.
- **No filtering.** L1 is 1:1. A row excluded here is invisible to every
  consumer, and the exclusion would be buried in a view definition nobody reads.
- **No renaming beyond case.** Column names stay as SAP publishes them so that
  SAP documentation still applies.

Verification: six objects in the schema, all of `TABLE_TYPE = 'VIEW'`.

---

## Step 2 — L2 analytics objects

`sql/03_l2_analytics_dynamic_tables.sql`. Requires a warehouse named `LOAD_WH`,
or edit the `WAREHOUSE` clause.

Build `DT_JOURNAL_ENTRY_360` first. It is the wide join — line items to header to
the cost centre, profit centre and GL account masters — and the five aggregates
depend on it. This is also the object where the signed-amount handling is written
once: `ABS` on the amount with a `DEBITCREDITCODE` filter.

Then the aggregates:

| Order | Object | Built from |
|---|---|---|
1 | `DT_JOURNAL_ENTRY_360` | L1 line items + header + 3 masters |
2 | `DT_GL_BALANCE` | `DT_JOURNAL_ENTRY_360` |
3 | `DT_PNL_SUMMARY` | `DT_JOURNAL_ENTRY_360` |
4 | `DT_EXPENSE_BY_COSTCENTER` | `DT_JOURNAL_ENTRY_360` |
5 | `DT_REVENUE_BY_PROFITCENTER` | `DT_JOURNAL_ENTRY_360` |
6 | `DT_AP_AGING` | L1 `SUPPLIERINVOICE` |
7 | `DT_AR_AGING` | generated — see below |

All six dynamic tables are declared `TARGET_LAG = 'DOWNSTREAM'` with
`REFRESH_MODE = AUTO` and `INITIALIZE = ON_CREATE`, so they populate as they are
created and thereafter refresh according to what reads them.

`DT_AR_AGING` is the exception. The SAP BDC Standard Data Products in scope
publish no receivables object, so there is nothing to build a dynamic table on.
It is created as a plain table from generated data, which is why it carries the
`DT_` prefix while not being a dynamic table. Say this out loud when handing the
stack over; the prefix will otherwise mislead.

Verification after this step: 7 objects, **20,011 rows**, and `SHOW DYNAMIC
TABLES` returning exactly 6.

---

## Step 3 — Reconcile L2 against L0

Do not proceed to the semantic layer until the numbers tie. This is the step
that catches a sign error, and a sign error in L2 is invisible until someone
compares a total to SAP.

The check that matters: total revenue computed from L0 with `ABS` plus a
`DEBITCREDITCODE` filter, against `SUM(REVENUE)` from `DT_PNL_SUMMARY`.

| Side | Value |
|---|---|
L0 `OPERATIONALACCTGDOCITEM`, `ABS` + `DEBITCREDITCODE` filter | $2,250,872,386 |
L2 `DT_PNL_SUMMARY`, `SUM(REVENUE)` | $2,250,872,386 |
Difference | 0 |

An exact match to the dollar. That is the evidence that the L1→L2 chain neither
drops nor double-counts rows and that the sign handling is right.

If this does not tie, the fault is almost always in the `DEBITCREDITCODE`
predicate rather than in the join.

---

## Step 4 — Semantic views

`sql/04_semantic_view.sql`. Produces two semantic views over L2:

- `SAP_FINANCE_360.ANALYTICS.SAP_FINANCE_360` — 4 logical tables (`AR`,
  `EXPENSE`, `JOURNAL`, `REVENUE`), 45 metrics, 0 relationships.
- `SAP_FINANCE_360.SEMANTIC.SAP_FINANCE_360_ANALYTICS` — 5 logical tables
  (`AP_AGING`, `EXPENSE_BY_COSTCENTER`, `JOURNAL_ENTRY`, `PNL_SUMMARY`,
  `REVENUE_BY_PROFITCENTER`), 12 relationships, 0 metrics.

Building two rather than one was not planned as a design; it is where the work
landed, and the split is awkward — metrics in one, relationships in the other,
`DT_GL_BALANCE` in neither. If you are reproducing this, consider consolidating.
See [findings](05-findings.md#two-semantic-views-and-neither-is-complete).

---

## Step 5 — The Cortex Analyst stage model

Upload `finance_360.semantic.yaml` to
`@SAP_FINANCE_360.SEMANTIC.SEMANTIC_MODELS/`.

This is a **separate artefact from step 4**, not a serialisation of it. It
declares the model `sap_finance_360` over 4 base tables with 24 dimensions and
9 measures.

| Base table | In Analyst model |
|---|---|
`ANALYTICS.DT_JOURNAL_ENTRY_360` | yes |
`ANALYTICS.DT_EXPENSE_BY_COSTCENTER` | yes |
`ANALYTICS.DT_REVENUE_BY_PROFITCENTER` | yes |
`ANALYTICS.DT_AR_AGING` | yes |
`ANALYTICS.DT_AP_AGING` | no |
`ANALYTICS.DT_GL_BALANCE` | no |
`ANALYTICS.DT_PNL_SUMMARY` | no |

**Verified queries: 0.** This step is therefore incomplete as shipped. Verified
queries are the mechanism by which Cortex Analyst learns the question shapes a
model is meant to serve; with none, every question is answered from the schema
alone. Adding them is the highest-value remaining work on this stack — see
[the analyst and agent layer](07-analyst-and-agent.md#the-verified-query-gap).

---

## Step 6 — The Cortex Agent

`sql/05_cortex_agent.sql` creates `SAP_FINANCE_360_AGENT`, reachable from
Snowflake Intelligence.

The agent is a separate consumer from the app. Confirming the agent answers
correctly does not confirm the app will, because the app's Cortex Analyst page
goes to the stage model.

---

## Step 7 — The application

1. `scripts/build_and_push.sh` — build the client and server images and push to
   the image repository.
2. `scripts/migrate_data.py` — stage what the app needs.
3. `scripts/deploy_native_app.py` — create the application package and the
   application from `app/manifest.yml`, `app/setup.sql`, `app/service_spec.yml`.
4. `scripts/create_org_listing.py` — publish the org listing for multi-region
   distribution.

All SQL belongs in the server's `api.ts`. Keeping it there is what makes the
data-source census in [architecture](02-architecture.md#the-app-reads-two-layers)
possible — a `FROM`-clause grep over one file is a complete inventory. Put one
query in the client and that stops being true.

Build the nine pages in the order they appear in the sidebar. The Cortex Analyst
page goes last, because it depends on step 5 rather than on any page above it.

---

## Step 8 — Capture and document

`tools/capture_shots.py` drives the deployed app and writes one PNG per page to
`/tmp/finance_shots/` with a `manifest.json` recording, per page, the selector
the capture settled on.

Nine pages, nine screenshots:

| File | Page | Settled on |
|---|---|---|
`00_overview.png` | Executive Overview | `canvas` |
`01_general-ledger.png` | General Ledger | `canvas` |
`02_cost-centers.png` | Cost Centers | `canvas` |
`03_profit-centers.png` | Profit Centers | `canvas` |
`04_accounts-payable.png` | Accounts Payable | `canvas` |
`05_accounts-receivable.png` | Accounts Receivable | `canvas` |
`06_period-analysis.png` | Period Analysis | `canvas` |
`07_bdc-products.png` | BDC Data Products | `[class*=card]` |
`08_analyst.png` | Cortex Analyst | `[class*=card]` |

The two pages that settle on `[class*=card]` rather than `canvas` are the two
with no chart — BDC Data Products and Cortex Analyst are card layouts. A capture
script waiting for a canvas on those pages waits forever, so the settle selector
is per-page rather than global.

`tools/finance_facts.py` extracts the verified figures used throughout this
handbook, each with its provenance query recorded alongside it. Documentation is
written from that extract rather than from memory, so a number in this handbook
can always be traced to the statement that produced it.

---

## Step 9 — Word deliverables

`tools/build_docs_docx.py` renders each markdown document in `docs/` as a branded
`.docx` and also emits a combined handbook with a contents page, into
`docs/docx/`. Nine files: eight parts plus the handbook.

Run it after any documentation edit; the Word files are generated artefacts and
are never edited directly.
