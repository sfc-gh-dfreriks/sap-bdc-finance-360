# Architecture — SAP BDC Finance 360

Finance 360 is built on a **medallion architecture** that sits entirely inside
Snowflake and reads SAP data via **SAP Business Data Cloud (BDC) zero-copy
shares**. No ETL pipelines, no data extraction, full SAP business context
preserved.

```
 SAP S/4HANA                SAP Business Data Cloud
 (source of record)   ─────  Standard Data Products  ─────►  Snowflake
                                (governed, zero-copy)
                                                                │
 ┌──────────────────────────────────────────────────────────────────────────┐
 │  L0  BRONZE  — SAP BDC Standard Data Products (read-only shares)           │
 │      SAP_BDC_DEMO_*.BDCCONNECT.{OPERATIONALACCTGDOCITEM, JOURNALENTRY,      │
 │      SUPPLIERINVOICE, GENERALLEDGERACCOUNT, COSTCENTER, PROFITCENTER}       │
 └──────────────────────────────────────────────────────────────────────────┘
                                                                │  (views)
 ┌──────────────────────────────────────────────────────────────────────────┐
 │  L1  SILVER  — SAP_FINANCE_360.SAP_BDC_L1 (curated 1:1 views + comments)   │
 │      COSTCENTER · GENERALLEDGERACCOUNT · JOURNALENTRY ·                     │
 │      OPERATIONALACCTGDOCITEM · PROFITCENTER · SUPPLIERINVOICE              │
 └──────────────────────────────────────────────────────────────────────────┘
                                                                │  (dynamic tables)
 ┌──────────────────────────────────────────────────────────────────────────┐
 │  L2  GOLD  — SAP_FINANCE_360.ANALYTICS (joined / enriched / aggregated)    │
 │      DT_JOURNAL_ENTRY_360   (fully-enriched GL line items)                 │
 │      DT_GL_BALANCE          (GL balances by account/period)               │
 │      DT_PNL_SUMMARY         (revenue / expenses / net income by period)   │
 │      DT_EXPENSE_BY_COSTCENTER · DT_REVENUE_BY_PROFITCENTER                 │
 │      DT_AP_AGING            (payables aging buckets)                       │
 │      DT_AR_AGING            (receivables aging, DSO, days-past-due)        │
 └──────────────────────────────────────────────────────────────────────────┘
                                                                │
 ┌──────────────────────────────────────────────────────────────────────────┐
 │  SEMANTIC — SAP_FINANCE_360 semantic view                                  │
 │      facts / dimensions / metrics over the L2 gold tables                  │
 └──────────────────────────────────────────────────────────────────────────┘
              │                                        │
              ▼                                        ▼
   SAP_FINANCE_360_AGENT                    Native App "Ask Cortex"
   (Snowflake Intelligence)                 (AI_COMPLETE in-app)
                                                        │
                                            React + Express on SPCS
                                            (self-contained Native App)
```

## Layer detail

### L0 — Bronze (SAP BDC Standard Data Products)
Governed data products shared from SAP BDC into Snowflake with **zero copy**.
Treated as immutable. See [`sql/01_l0_sources.md`](../sql/01_l0_sources.md).

### L1 — Silver (`SAP_BDC_L1`)
Six 1:1 curated views over L0 that add business-friendly column comments and a
stable interface, decoupling downstream logic from the raw share names.
DDL: [`sql/02_l1_curated_views.sql`](../sql/02_l1_curated_views.sql).

### L2 — Gold (`ANALYTICS`)
Analytics-ready **dynamic tables** that join and aggregate L1 into the shapes the
dashboard and semantic model need. `TARGET_LAG='DOWNSTREAM'` so they refresh
automatically as L1 changes. Key transforms:

| L2 object | Grain | Logic |
|-----------|-------|-------|
| `DT_JOURNAL_ENTRY_360` | GL line item | Joins line items → header → GL account → cost center → profit center |
| `DT_PNL_SUMMARY` | company / year / period | Revenue (GL `4%`, credit) − Expenses (GL `5%`/`6%`, debit) = Net income |
| `DT_GL_BALANCE` | company / GL / period / DR-CR | Summed amounts per account/period |
| `DT_EXPENSE_BY_COSTCENTER` | company / cost center / GL / period | Debit `5%`/`6%` expenses by cost center |
| `DT_REVENUE_BY_PROFITCENTER` | company / profit center / GL / period | Credit `4%` revenue by profit center |
| `DT_AP_AGING` | supplier invoice | Days outstanding + aging bucket |
| `DT_AR_AGING` | AR invoice | DSO, days past due, aging bucket (generated) |

DDL: [`sql/03_l2_analytics_dynamic_tables.sql`](../sql/03_l2_analytics_dynamic_tables.sql).

> `DT_AR_AGING` is a generated table — accounts receivable is not part of the
> standard AP-focused data products, so a representative AR dataset is produced
> for the demo. All other L2 objects derive purely from L0/L1.

### Semantic + Agent
- **`SAP_FINANCE_360`** semantic view — facts, dimensions and metrics
  (revenue, expenses, DSO, aging) over the L2 gold tables.
  DDL: [`sql/04_semantic_view.sql`](../sql/04_semantic_view.sql).
- **`SAP_FINANCE_360_AGENT`** — account-level Cortex Agent for Snowflake
  Intelligence. DDL: [`sql/05_cortex_agent.sql`](../sql/05_cortex_agent.sql).

## Native App packaging

For distribution, the app is packaged as a **self-contained Snowflake Native
App**: the 8 tables the UI needs are **bundled** into the application package's
`SHARED_DATA` schema (no consumer references), and an in-app copy of the
`SAP_FINANCE_360` semantic view backs the server's `/api/analyst` route (no app
page since the nav change; in-app questions go through Ask Cortex). The React client
+ Express server run on **Snowpark Container Services**. See
[`app/`](../app) and [`INSTALL.md`](INSTALL.md).
