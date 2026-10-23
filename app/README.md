# SAP Finance 360

A self-contained Snowflake Native App that runs the **SAP BDC Finance 360**
dashboard (React + Express) on Snowpark Container Services.

## What's inside

- **Interactive dashboard** — Overview, General Ledger, Cost Centers, Profit
  Centers, Accounts Payable, Accounts Receivable, Period Analysis, and BDC Data
  Products pages.
- **Bundled data** — All finance data is packaged with the app (no external
  references or shares required). It runs immediately after install.
- **Ask Cortex** — the first sidebar page, plus an "Ask Cortex about <page>"
  button on every data page. The app gathers live facts for the page from its
  bundled tables and asks Snowflake Cortex (`AI_COMPLETE`, `claude-sonnet-4-5`)
  for a written analysis with recommended actions.
- **Ask the Agent** — A natural-language analytics page powered by Cortex
  Analyst over the bundled **`SAP_FINANCE_360`** semantic view — the same model
  behind the account-level **`SAP_FINANCE_360_AGENT`** Cortex Agent.

## Data model

The app bundles journal entries, operational accounting document items,
supplier invoices, AP/AR aging, and cost-center / profit-center analytics,
covering three company codes (1000 = US, 2100 = DE, 5000 = JP).

## Install

1. Grant the requested account privileges (CREATE COMPUTE POOL, BIND SERVICE
   ENDPOINT, CREATE WAREHOUSE).
2. Activate the app — the version initializer creates the compute pool,
   warehouse, and the `FINANCE_360_SERVICE` container service.
3. Launch the app from the default web endpoint.

## Cortex access

Grant the app the `SNOWFLAKE.CORTEX_USER` database role so the "Ask the Agent"
page can call Cortex Analyst and Ask Cortex can call `AI_COMPLETE`:

```sql
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO APPLICATION <app name>;
CALL <app name>.CORE.CORTEX_SELFTEST();   -- returns 'Ask Cortex available: ...'
```

Without it the dashboards still work; Ask Cortex shows "not available in this
installation" instead of an answer.
