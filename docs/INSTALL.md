# Install & Deploy — SAP BDC Finance 360

Two ways to stand this up:

- **A. Build the data platform** (L0 → L1 → L2 → semantic → agent) in a Snowflake
  account. This gives you the medallion architecture + the `SAP_FINANCE_360_AGENT`
  for Snowflake Intelligence.
- **B. Deploy the self-contained Native App** (React dashboard + Ask Cortex)
  and publish it as an organization listing — optionally across multiple regions.

You can do A only, B only, or both. B bundles its own data, so it does **not**
require A to already exist in the consumer account.

---

## Prerequisites

- Snowflake account with `ACCOUNTADMIN` (or equivalent) role
- The SAP BDC **Standard Data Products** mounted as `SAP_BDC_DEMO_*` databases
  (see [`sql/01_l0_sources.md`](../sql/01_l0_sources.md))
- For the Native App: Docker + `snow` CLI (Snowflake CLI) + a Snowflake
  **image repository** (e.g. `SC360_APP_PROVIDER.IMAGES.REPO`)
- Python 3.11+ with `snowflake-connector-python` and `cryptography`
- Key-pair connections in `~/.snowflake/connections.toml` (one per target account)

---

## A. Build the data platform

Run the SQL scripts in order as `ACCOUNTADMIN`:

```sql
-- 1. (reference) confirm the L0 SAP BDC products are mounted — see 01_l0_sources.md
-- 2. L1 curated views
!source sql/02_l1_curated_views.sql
-- 3. L2 analytics dynamic tables (needs a warehouse named LOAD_WH, or edit the DDL)
!source sql/03_l2_analytics_dynamic_tables.sql
-- 4. semantic view
!source sql/04_semantic_view.sql
-- 5. Cortex agent  (grant SNOWFLAKE.CORTEX_USER to your role first)
!source sql/05_cortex_agent.sql
```

Or paste each file into a Snowsight worksheet. Verify:

```sql
SELECT * FROM SEMANTIC_VIEW(
  SAP_FINANCE_360.ANALYTICS.SAP_FINANCE_360
  METRICS JOURNAL.REVENUE, JOURNAL.EXPENSES
  DIMENSIONS JOURNAL.COMPANYCODE
);
```

Then open **Snowflake Intelligence** and chat with `SAP_FINANCE_360_AGENT`.

---

## B. Deploy the Native App

Each step is one command per target account. The example uses three connections:
`dfreriksdemo` (US), `dfreriks_eu_demo` (EMEA), `dfreriks_apac_demo` (APAC).

### 1. Build & push the container image (once per region)

```bash
scripts/build_and_push.sh dfreriksdemo \
  sfsenorthamerica-dfreriks-aws1-w2.registry.snowflakecomputing.com
scripts/build_and_push.sh dfreriks_eu_demo \
  sfseeurope-dfreriks-eu-demo.registry.snowflakecomputing.com
scripts/build_and_push.sh dfreriks_apac_demo \
  sfseapac-sap-data-product-demo.registry.snowflakecomputing.com
```

### 2. Bundle the data into the application package (once per account)

```bash
# same-account (source data is local)
python scripts/migrate_data.py --target dfreriksdemo --mode local
# cross-account (extract from US, load into EMEA / APAC)
python scripts/migrate_data.py --source dfreriksdemo --target dfreriks_eu_demo   --mode remote
python scripts/migrate_data.py --source dfreriksdemo --target dfreriks_apac_demo --mode remote
```

Bundles 8 tables (~34K rows) into `FINANCE_360_PKG.SHARED_DATA`.

### 3. Deploy the app (once per account)

```bash
python scripts/deploy_native_app.py --target dfreriksdemo
python scripts/deploy_native_app.py --target dfreriks_eu_demo
python scripts/deploy_native_app.py --target dfreriks_apac_demo
```

This stages the artifacts, registers version `v1` on the DEFAULT release
channel, creates `FINANCE_360_APP`, grants privileges, runs `version_init()`,
and prints the service status + app URL.

### 4. Publish the organization listing (once per account)

```bash
LISTING_CONTACT=you@snowflake.com python scripts/create_org_listing.py \
  --target dfreriksdemo       --region PUBLIC.AWS_US_WEST_2
LISTING_CONTACT=you@snowflake.com python scripts/create_org_listing.py \
  --target dfreriks_eu_demo   --region PUBLIC.AWS_EU_CENTRAL_1
LISTING_CONTACT=you@snowflake.com python scripts/create_org_listing.py \
  --target dfreriks_apac_demo --region PUBLIC.AWS_AP_SOUTHEAST_2
```

The listing is scoped to a single region to avoid cross-region
auto-fulfillment — each region hosts its own governed install. Locator:
`ORGDATACLOUD$INTERNAL$FINANCE_360_ORG`.

---

## Native App internals

| Artifact | Purpose |
|----------|---------|
| `app/manifest.yml` | Native App manifest v2 (image, endpoint, privileges, version_initializer) |
| `app/setup.sql` | Creates app roles, `APP_DATA` views over bundled `SHARED_DATA`, in-app `SAP_FINANCE_360` semantic view, the SPCS service + lifecycle procs |
| `app/service_spec.yml` | SPCS container/endpoint spec (`finance360`, port 8080) |
| `app/snowflake.yml` | Snowflake CLI project (package `FINANCE_360_PKG`, app `FINANCE_360_APP`) |
| `service/app/` | React (Vite) client + Express server + multi-stage Dockerfile |

## Cortex access

Ask Cortex calls `AI_COMPLETE` from inside the container. Grant
the app the Cortex role (done automatically by `deploy_native_app.py`):

```sql
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO APPLICATION FINANCE_360_APP;
```

The same grant lets the **Ask Cortex** page and the per-page "Ask Cortex about
<page>" buttons call `AI_COMPLETE` (model `claude-sonnet-4-5`; set `CORTEX_MODEL`
in the service spec to override, and check the model is available in the region).
Check it with `CALL FINANCE_360_APP.CORE.CORTEX_SELFTEST();`. If Cortex is not
reachable the UI reports "Ask Cortex is not available in this installation" with
the fix, rather than failing.

## Teardown

```sql
DROP APPLICATION FINANCE_360_APP CASCADE;
DROP APPLICATION PACKAGE FINANCE_360_PKG;
-- listing:
DROP LISTING FINANCE_360_ORG;
```
