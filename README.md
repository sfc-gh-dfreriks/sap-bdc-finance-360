# SAP BDC Finance 360

A reference implementation showing how to turn **SAP Business Data Cloud (BDC)
Standard Data Products** into a live, AI-powered finance analytics app on
Snowflake — using a **medallion (L0/L1/L2) architecture**, a governed
**semantic view**, a **Cortex Agent**, and a self-contained **Snowflake Native
App** (React + Express on Snowpark Container Services), deployable across
multiple regions.

Zero ETL. Zero copy. Full SAP business context preserved.

---

## What's in here

```
sap-bdc-finance-360/
├── sql/                 Medallion + semantic + agent (run in order)
│   ├── 01_l0_sources.md            L0 bronze — SAP BDC Standard Data Products
│   ├── 02_l1_curated_views.sql     L1 silver — SAP_BDC_L1 curated views
│   ├── 03_l2_analytics_dynamic_tables.sql  L2 gold — ANALYTICS dynamic tables
│   ├── 04_semantic_view.sql        SAP_FINANCE_360 semantic view
│   └── 05_cortex_agent.sql         SAP_FINANCE_360_AGENT
├── app/                 Native App package (manifest, setup.sql, spec, snowflake.yml)
├── service/app/         React (Vite) client + Express server + Dockerfile
├── scripts/             build_and_push · migrate_data · deploy_native_app · create_org_listing
└── docs/                ARCHITECTURE.md · INSTALL.md · DEMO_GUIDE.md · demo deck (.pptx)
```

## Architecture at a glance

`SAP BDC Standard Data Products (L0)` → `SAP_BDC_L1 curated views (L1)` →
`ANALYTICS dynamic tables (L2)` → `SAP_FINANCE_360 semantic view` →
`SAP_FINANCE_360_AGENT` (Snowflake Intelligence) + Native App "Ask Cortex".

Full detail (with diagram and per-table transform logic):
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Quick start

- **Build the data platform + agent:** run `sql/02` → `sql/05` as
  `ACCOUNTADMIN`, then chat with `SAP_FINANCE_360_AGENT` in Snowflake
  Intelligence.
- **Deploy the Native App:** `build_and_push.sh` → `migrate_data.py` →
  `deploy_native_app.py` → `create_org_listing.py`.

Step-by-step runbook: [`docs/INSTALL.md`](docs/INSTALL.md).

## The app

A React dashboard with **Ask Cortex** (first in the sidebar) plus an "Ask Cortex about <page>" button
under each data page header with two suggested questions: the server gathers live
facts for that page from the app's own tables and asks Snowflake Cortex
(`AI_COMPLETE`, default model `claude-sonnet-4-5`, override with `CORTEX_MODEL`) for a
markdown analysis (background job, `POST/GET /api/ask-cortex`, 2 s polling).

Sidebar order: **Ask Cortex, Executive Dashboard** (the app opens here)**, General
Ledger, Cost Centers, Profit Centers, Accounts Payable, Accounts Receivable, Period
Analysis, BDC Sources & Lineage**. The `SAP_FINANCE_360_AGENT` Cortex Agent is used
from Snowflake Intelligence and has no in-app page. Company codes: **1000 = US, 2100 = DE,
5000 = JP**.

## Demo

See [`docs/DEMO_GUIDE.md`](docs/DEMO_GUIDE.md) and the slide deck
[`docs/SAP_Finance_360_Demo_Guide.pptx`](docs/SAP_Finance_360_Demo_Guide.pptx)
(15 slides + presenter notes).

## Security notes

- No credentials are committed. Scripts read key-pair connections from
  `~/.snowflake/connections.toml` by connection name; `.gitignore` excludes
  `*.p8`, `.env`, and `connections.toml`.
- L0 SAP BDC products are read-only zero-copy shares; the medallion only reads
  from them.

## Sibling projects

Same pattern, other SAP domains:
`sap-bdc-supply-chain-360` · `sap-bdc-people-360` · `sap-bdc-sales-360`
