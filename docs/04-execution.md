# 4. Execution

Running, refreshing and verifying the stack once it is built. Ordered by how
often you will need each thing.

---

## Prerequisites

| Requirement | Detail |
|---|---|
Account | `MSB89522` |
Region | `PUBLIC.AWS_US_WEST_2` |
Role | `ACCOUNTADMIN`, or a role holding the L0 share grants |
Warehouse | `LOAD_WH` for the dynamic tables, or edit the `WAREHOUSE` clause |
L0 shares | The three `SAP_BDC_DEMO_*` databases mounted and selectable |
Python | for `tools/` — `python-docx`, plus a Snowflake connection for the fact extractor |

The repository is at
`https://github.com/sfc-gh-dfreriks/sap-bdc-finance-360`.

---

## First run

Run the SQL in order, as `ACCOUNTADMIN`:

```
sql/01_l0_sources.md    -- read it; there is nothing to execute
sql/02_l1_curated_views.sql
sql/03_l2_analytics_dynamic_tables.sql
sql/04_semantic_view.sql
sql/05_cortex_agent.sql
```

Then verify before going further:

```sql
-- 4 schemas
select count(*) from SAP_FINANCE_360.INFORMATION_SCHEMA.SCHEMATA;

-- L1: 6 objects, all views
select table_type, count(*)
from SAP_FINANCE_360.INFORMATION_SCHEMA.TABLES
where table_schema = 'SAP_BDC_L1'
group by 1;

-- L2: 7 objects, 20,011 rows
select count(*) as objects, sum(row_count) as rows
from SAP_FINANCE_360.INFORMATION_SCHEMA.TABLES
where table_schema = 'ANALYTICS';

-- exactly 6 of them are dynamic
show dynamic tables in schema SAP_FINANCE_360.ANALYTICS;
```

Expected: 4 schemas; 6 rows of `VIEW` and nothing else in L1; 7 objects and
20,011 rows in L2; 6 dynamic tables.

If `SHOW DYNAMIC TABLES` returns 7, something has changed — `DT_AR_AGING` is
supposed to be a plain table.

---

## The reconciliation check

This is the one test worth running every time the data changes. It compares
revenue computed from L0 to revenue reported by L2.

```sql
-- L0/L1 side: signed amounts, so ABS plus a DEBITCREDITCODE filter,
-- and a GL account range to isolate the P&L lines.
select
  sum(case when GLACCOUNT like '4%' and DEBITCREDITCODE = 'H'
           then abs(AMOUNTINCOMPANYCODECURRENCY) else 0 end) as revenue,
  sum(case when (GLACCOUNT like '5%' or GLACCOUNT like '6%') and DEBITCREDITCODE = 'S'
           then abs(AMOUNTINCOMPANYCODECURRENCY) else 0 end) as expenses
from SAP_FINANCE_360.SAP_BDC_L1.OPERATIONALACCTGDOCITEM;

-- L2 side
select sum(REVENUE) as revenue, sum(EXPENSES) as expenses
from SAP_FINANCE_360.ANALYTICS.DT_PNL_SUMMARY;
```

Both sides must return revenue **2250872386** and expenses **1709590738**.
As verified on 2026-09-21 they do, on both measures, exactly.

The three predicates are all load-bearing, and it is worth knowing what each one
is defending against:

| Predicate | Why it is there |
|---|---|
`abs(AMOUNTINCOMPANYCODECURRENCY)` | The ledger is balanced double-entry. `sum(AMOUNTINCOMPANYCODECURRENCY)` over the whole table returns **exactly 0** — not an approximation, zero. Drop `ABS` and every P&L figure collapses. |
`DEBITCREDITCODE = 'H'` / `'S'` | `H` is the credit side, `S` the debit side, and the table holds 5,150 of each. Without the filter both sides are counted and the total doubles: credits and debits each sum to 9,094,935,724 in absolute terms. |
`GLACCOUNT like '4%'` / `'5%'`,`'6%'` | Isolates P&L accounts from balance-sheet accounts. `4` is revenue, `5` and `6` are expense. Without it you are summing the entire ledger, not a P&L. |

Do **not** reach for `ABSOLUTEAMOUNTINCOCODECRCY`, which looks like exactly the
column you want and is named as though SAP has already done the work. It is
present on the table and it is **entirely NULL** in this dataset. A query built
on it returns NULL rather than a wrong number, which is the one merciful
failure mode in this section.

A mismatch points at the `DEBITCREDITCODE` predicate before it points at the
join. Dropping `ABS` produces a number that looks plausible and is wrong, which
is precisely why this check exists as a numeric equality rather than a smoke test.

---

## Refreshing after the SAP data changes

The six dynamic tables carry `TARGET_LAG = 'DOWNSTREAM'`, so they refresh in
response to being read rather than on a schedule. Nothing needs to be triggered
in the normal case.

To force it:

```sql
alter dynamic table SAP_FINANCE_360.ANALYTICS.DT_JOURNAL_ENTRY_360 refresh;
```

Refresh the wide table first; the five aggregates are downstream of it and will
follow.

**`DT_AR_AGING` does not participate.** It is a plain table, so no refresh
command applies to it and no lag is reported for it. If AR figures need to
change, the table is rebuilt by re-running its section of
`sql/03_l2_analytics_dynamic_tables.sql`.

Because L1 is views, nothing in L1 ever needs refreshing. A change at L0 is
visible through L1 on the next query.

---

## Data windows to keep in mind

The three transactional objects do not cover the same period, and a
side-by-side comparison across them will mislead unless that is stated:

| Object | Column | From | To |
|---|---|---|---|
`DT_JOURNAL_ENTRY_360` | `POSTINGDATE` | 2023-01-01 | 2025-03-28 |
`DT_AP_AGING` | `POSTINGDATE` | 2023-01-06 | 2025-04-25 |
`DT_AR_AGING` | `INVOICEDATE` | 2024-11-14 | 2026-05-07 |

The ledger stops in March 2025. AR runs to May 2026. Any "AR vs revenue" chart
covering the full AR window is comparing a populated series to an empty one for
most of its length.

Note also that fiscal 2025 in the ledger is a partial year — 578 documents
against 2,293 and 2,279 for 2023 and 2024. A year-on-year chart that does not
label 2025 as partial shows a collapse that did not happen.

---

## Editing the semantic layer

Which artefact to edit depends entirely on which consumer is wrong. This is the
most common source of wasted time on this stack.

| Consumer is wrong | Edit |
|---|---|
The app's Cortex Analyst page | `finance_360.semantic.yaml` on `@SAP_FINANCE_360.SEMANTIC.SEMANTIC_MODELS/` |
`SAP_FINANCE_360_AGENT` in Snowflake Intelligence | whichever semantic view the agent is bound to |
A direct `SEMANTIC_VIEW(...)` query | the semantic view named in that query |

**The app reads the stage YAML.** Editing `ANALYTICS.SAP_FINANCE_360` or
`SEMANTIC.SAP_FINANCE_360_ANALYTICS` will not change a single answer on the
app's Analyst page. This was got wrong once and is worth stating twice.

To pull the current model down, inspect it and put it back:

```sql
get @SAP_FINANCE_360.SEMANTIC.SEMANTIC_MODELS/finance_360.semantic.yaml
    file:///tmp/;
-- edit /tmp/finance_360.semantic.yaml
put file:///tmp/finance_360.semantic.yaml
    @SAP_FINANCE_360.SEMANTIC.SEMANTIC_MODELS/ overwrite = true auto_compress = false;
```

`auto_compress = false` matters. Cortex Analyst reads the YAML as a file; a
gzipped upload is not readable.

---

## Deploying the application

```
scripts/build_and_push.sh        # build + push client and server images
scripts/migrate_data.py          # stage app data
scripts/deploy_native_app.py     # package + application from app/
scripts/create_org_listing.py    # org listing for multi-region distribution
```

The deployed instance is at
`erzht4-sfsenorthamerica-dfreriks-aws1-w2.snowflakecomputing.app`.

All application SQL lives in the server's `api.ts`. When adding a query, put it
there rather than in the client — the one-file rule is what keeps the data-source
inventory in [architecture](02-architecture.md#the-app-reads-two-layers)
trustworthy.

Remember that 21 of the app's `FROM` clauses hit the L0 shares directly and do
not inherit L2's sign handling. A new query written against
`OPERATIONALACCTGDOCITEM` needs its own `ABS` and `DEBITCREDITCODE` filter.

---

## Capturing screenshots

```
python tools/capture_shots.py
```

Writes nine PNGs and a `manifest.json` to `/tmp/finance_shots/`. The manifest
records which selector each page settled on, which is the useful part when a
capture hangs: seven pages settle on `canvas`, and **BDC Data Products** and
**Cortex Analyst** settle on `[class*=card]` because they contain no chart.

If a capture of one of those two pages times out, the settle selector has
regressed to a global `canvas` wait.

---

## Extracting the facts

```
python tools/finance_facts.py
```

Writes the verified figures with a provenance entry for each — the query or
metadata view the number came from. Every figure in this handbook traces back to
that output.

Regenerate it before editing documentation rather than after. Writing prose
first and then checking the numbers is how the stale-figure problem starts.

---

## Word versions of the documentation

```
python tools/build_docs_docx.py
```

Renders each of `docs/01-*.md` through `docs/08-*.md` as a branded `.docx` and
emits a combined handbook with a contents page, into `docs/docx/` — **9 files**.

The renderer is bespoke rather than pandoc because the output has to match the
existing Word and PowerPoint deliverables in this repository: same palette, same
page setup, same navy table headers. A generic converter loses all of that.

It shares `tools/sap_docx_kit.py` with the management summary and presales kit,
through the `tools/docx_kit.py` shim. Edit `sap_docx_kit.py`, never the shim.

One behaviour to preserve if you touch the markdown parser: **table rows are
accepted with or without leading and trailing pipes.** GFM does not require
them, this doc set omits them in many places, and a parser that insists on them
drops those rows silently rather than failing.

The `.docx` files are generated. Edit the markdown.

---

## Troubleshooting

| Symptom | Cause |
|---|---|
L1 view creation fails on grants | the running role cannot see the L0 shares; check the three `SAP_BDC_DEMO_*` databases |
Dynamic table creation fails | no warehouse named `LOAD_WH`; edit the `WAREHOUSE` clause |
`SHOW DYNAMIC TABLES` returns 7 | `DT_AR_AGING` has been recreated as dynamic; it is meant to be a plain table |
No refresh history for `DT_AR_AGING` | correct — it is not a dynamic table |
Revenue does not tie to $2,250,872,386 | missing `ABS`, or the wrong `DEBITCREDITCODE` side |
A total looks too small by roughly half | signed amounts summed without `ABS`, so debits cancelled credits |
Analyst answers unchanged after editing a semantic view | the app reads the stage YAML, not the views |
Analyst cannot answer an AP, GL-balance or P&L question | those three L2 tables are not in the model |
Analyst picks an odd table for a clear question | 0 verified queries — there is nothing steering it |
Screenshot capture hangs on BDC Data Products or Cortex Analyst | those pages have no `canvas`; settle on `[class*=card]` |
A markdown table row is missing from the `.docx` | a pipe-stripping regression in the table parser |
2025 looks like a collapse | fiscal 2025 is partial: 578 documents, ledger ends 2025-03-28 |
