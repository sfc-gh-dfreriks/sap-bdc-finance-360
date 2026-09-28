# 2. Architecture

Every object in the stack, what reads what, and the two places where the wiring
is not what the diagram would lead you to expect.

---

## Data flow

```
SAP BDC Standard Data Products                     (L0, shared, not copied)
  SAP_BDC_DEMO_ENTRY_VIEW_JOURNAL_ENTRY.BDCCONNECT.OPERATIONALACCTGDOCITEM
  SAP_BDC_DEMO_JOURNAL_ENTRY_HEADER.BDCCONNECT.JOURNALENTRY
  SAP_BDC_DEMO_SUPPLIER_INVOICE.BDCCONNECT.SUPPLIERINVOICE
        |
        v
SAP_FINANCE_360.SAP_BDC_L1                         (L1, 6 passthrough VIEWS)
  COSTCENTER  GENERALLEDGERACCOUNT  JOURNALENTRY
  OPERATIONALACCTGDOCITEM  PROFITCENTER  SUPPLIERINVOICE
        |
        v
SAP_FINANCE_360.ANALYTICS                          (L2, 7 objects, 20,011 rows)
  DT_JOURNAL_ENTRY_360  DT_GL_BALANCE  DT_PNL_SUMMARY
  DT_EXPENSE_BY_COSTCENTER  DT_REVENUE_BY_PROFITCENTER
  DT_AP_AGING  DT_AR_AGING
        |
        +--> SAP_FINANCE_360.ANALYTICS.SAP_FINANCE_360           (semantic view)
        +--> SAP_FINANCE_360.SEMANTIC.SAP_FINANCE_360_ANALYTICS   (semantic view)
        +--> @SEMANTIC.SEMANTIC_MODELS/finance_360.semantic.yaml  (Analyst model)
        |
        v
React + Express app, 9 pages
```

The app arrow is drawn from L2, and that is only two thirds true. See
[the app reads two layers](#the-app-reads-two-layers) below.

---

## L1 — six views, nothing more

| Property | Value |
|---|---|
Objects | 6 |
Object type | `VIEW` |
Materialized views | 0 |
Tables | 0 |
Storage added | none |
Refresh lag | none — a view has no lag |

Each view selects from its L0 counterpart and declares a `COMMENT` on every
column. That is the whole transform. The value is not in the SQL, it is in the
fact that a downstream consumer can `DESCRIBE` a finance object and read what
`ISBLKDFORPRIMARYCOSTSPOSTING` means without opening SAP documentation.

Because they are views, the correctness question for L1 is "does it compile and
does the grant chain reach L0", not "is it fresh".

---

## L2 — seven objects, six of them dynamic

| Object | Rows | Type |
|---|---|---|
`DT_JOURNAL_ENTRY_360` | 10,300 | dynamic table |
`DT_AR_AGING` | 3,868 | **plain table** |
`DT_EXPENSE_BY_COSTCENTER` | 2,459 | dynamic table |
`DT_GL_BALANCE` | 1,793 | dynamic table |
`DT_REVENUE_BY_PROFITCENTER` | 1,091 | dynamic table |
`DT_AP_AGING` | 419 | dynamic table |
`DT_PNL_SUMMARY` | 81 | dynamic table |
**Total** | **20,011** | 7 objects, 6 dynamic |

`DT_AR_AGING` carries the `DT_` prefix and is not a dynamic table. `SHOW DYNAMIC
TABLES` returns six names and this is not one of them. The naming convention
asserts something about the object that is false, and anyone maintaining this
stack should know it before they go looking for a refresh history that does not
exist. The reason, and why it is defensible, is in
[findings](05-findings.md#ar-is-generated-not-shared).

The six real dynamic tables are declared `TARGET_LAG = 'DOWNSTREAM'`, so refresh
is driven by what consumes them rather than by a fixed schedule.

### The aggregation grain

`DT_JOURNAL_ENTRY_360` is the wide fact object — journal line items joined to
their header and to the cost centre, profit centre and GL account masters. The
remaining five dynamic tables are aggregations over it or over `SUPPLIERINVOICE`:

| Object | Grain |
|---|---|
`DT_GL_BALANCE` | GL account × period |
`DT_PNL_SUMMARY` | fiscal year × company code, revenue / expense / net |
`DT_EXPENSE_BY_COSTCENTER` | cost centre × period |
`DT_REVENUE_BY_PROFITCENTER` | profit centre × period |
`DT_AP_AGING` | supplier invoice, bucketed by days outstanding |

`DT_PNL_SUMMARY` is the smallest object at 81 rows and the one most likely to be
read by a human directly, because it is already signed correctly — the `ABS` and
`DEBITCREDITCODE` handling happens inside it.

---

## The app reads two layers

The Express server's `api.ts` issues its queries against both L0 shares and L2,
not against L2 alone:

| Source | `FROM` clauses |
|---|---|
`SAP_BDC_DEMO_ENTRY_VIEW_JOURNAL_ENTRY.BDCCONNECT.OPERATIONALACCTGDOCITEM` | 13 |
`SAP_FINANCE_360.ANALYTICS.DT_EXPENSE_BY_COSTCENTER` | 7 |
`SAP_FINANCE_360.ANALYTICS.DT_AR_AGING` | 7 |
`SAP_BDC_DEMO_SUPPLIER_INVOICE.BDCCONNECT.SUPPLIERINVOICE` | 6 |
`SAP_FINANCE_360.ANALYTICS.DT_REVENUE_BY_PROFITCENTER` | 5 |
`SAP_BDC_DEMO_JOURNAL_ENTRY_HEADER.BDCCONNECT.JOURNALENTRY` | 2 |
`SAP_FINANCE_360.ANALYTICS.DT_AP_AGING` | 1 |

That is **21 reads straight against the shares** and **20 against L2** — very
nearly an even split, and the largest single source is L0, not L2.

Two things follow. First, the app is a live demonstration of zero-copy rather
than a warehouse dashboard: a third of its queries touch the provider's storage
directly. Second, **the app does not skip L1 by accident — it skips it by
design**, because L1 adds only comments, and a query that needs no comments gains
nothing by routing through a second view.

The cost is that the signed-amount discipline has to be repeated in application
SQL for those 21 clauses, since they do not inherit L2's handling.

Note also that `DT_GL_BALANCE` and `DT_PNL_SUMMARY` appear nowhere in the table
above. The General Ledger and Period Analysis pages compute from L0 rather than
reading the matching L2 aggregate.

---

## Semantic objects

Two semantic views exist. They differ in which L2 objects they expose and
whether they declare relationships.

| | `ANALYTICS.SAP_FINANCE_360` | `SEMANTIC.SAP_FINANCE_360_ANALYTICS` |
|---|---|---|
Logical tables | `AR`, `EXPENSE`, `JOURNAL`, `REVENUE` | `AP_AGING`, `EXPENSE_BY_COSTCENTER`, `JOURNAL_ENTRY`, `PNL_SUMMARY`, `REVENUE_BY_PROFITCENTER` |
Table count | 4 | 5 |
Relationships declared | 0 | 12 |
Metrics declared | 45 | 0 |

The two are close to complements. The `ANALYTICS` view carries metrics and no
relationships; the `SEMANTIC` view carries relationships and no metrics. Neither
is a superset of the other, and `DT_GL_BALANCE` is in neither.

The dimension and fact tallies reported by `DESCRIBE SEMANTIC VIEW` are large
(120 and 251 dimensions respectively) because SAP source objects are wide and
every retained column becomes a dimension. Treat those as row counts from
`DESCRIBE` rather than as a count of curated, documented dimensions.

---

## The Cortex Analyst model is a third, separate artefact

```
@SAP_FINANCE_360.SEMANTIC.SEMANTIC_MODELS/finance_360.semantic.yaml
```

| Property | Value |
|---|---|
Model name | `sap_finance_360` |
Base tables | 4 |
Dimensions | 24 |
Measures | 9 |
Facts | 0 |
Verified queries | **0** |

Its base tables are `ANALYTICS.DT_JOURNAL_ENTRY_360`,
`ANALYTICS.DT_EXPENSE_BY_COSTCENTER`,
`ANALYTICS.DT_REVENUE_BY_PROFITCENTER` and `ANALYTICS.DT_AR_AGING`.

**The app's Cortex Analyst page reads this stage file.** It does not read
`ANALYTICS.SAP_FINANCE_360` and it does not read
`SEMANTIC.SAP_FINANCE_360_ANALYTICS`. If an Analyst answer is wrong, the file to
edit is the YAML on the stage; changing either semantic view will have no effect
on the app.

Three L2 objects are outside the Analyst model entirely — `DT_AP_AGING`,
`DT_GL_BALANCE` and `DT_PNL_SUMMARY` — so an Analyst question about accounts
payable, GL balances or the P&L summary has no table to land on. Detail in
[the semantic layer](08-semantic-layer.md).

---

## Application

A React client and an Express server, packaged as a Snowflake Native App on
Snowpark Container Services.

| Component | Detail |
|---|---|
Client | React + Vite |
Server | Express + TypeScript, `api.ts` holding all SQL |
Packaging | Native App — `manifest.yml`, `setup.sql`, `service_spec.yml` |
Pages | 9 |
Deployed URL | `erzht4-sfsenorthamerica-dfreriks-aws1-w2.snowflakecomputing.app` |

The nine pages:

| # | Page |
|---|---|
1 | Executive Overview |
2 | General Ledger |
3 | Cost Centers |
4 | Profit Centers |
5 | Accounts Payable |
6 | Accounts Receivable |
7 | Period Analysis |
8 | BDC Data Products |
9 | Cortex Analyst |

Pages 1–7 are conventional dashboards. Page 8 exists to make the zero-copy claim
visible — it shows the shares themselves. Page 9 is the natural-language surface
over the stage model.

All SQL lives in the server. The client holds no query text, which is what makes
the `FROM`-clause census in the table above a complete inventory of what the
application reads.
