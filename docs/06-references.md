# 6. References

Where the pieces came from, what each contributed, and the boundary between this
asset and its neighbours.

---

## This repository

### [`sfc-gh-dfreriks/sap-bdc-finance-360`](https://github.com/sfc-gh-dfreriks/sap-bdc-finance-360)

The asset this handbook documents.

| | |
|---|---|
Account verified against | `MSB89522` |
Region | `PUBLIC.AWS_US_WEST_2` |
Deployed app | `erzht4-sfsenorthamerica-dfreriks-aws1-w2.snowflakecomputing.app` |
Verified on | 2026-09-21 |

Layout:

| Path | Contents |
|---|---|
`sql/01_l0_sources.md` | L0 documentation — markdown, because there is nothing to create |
`sql/02_l1_curated_views.sql` | 6 L1 passthrough views with column comments |
`sql/03_l2_analytics_dynamic_tables.sql` | 7 L2 objects — 6 dynamic tables plus `DT_AR_AGING` |
`sql/04_semantic_view.sql` | the two semantic views |
`sql/05_cortex_agent.sql` | `SAP_FINANCE_360_AGENT` |
`app/` | Native App package — `manifest.yml`, `setup.sql`, `service_spec.yml`, `snowflake.yml` |
`service/app/` | React client, Express server, Dockerfile |
`scripts/` | `build_and_push.sh`, `migrate_data.py`, `deploy_native_app.py`, `create_org_listing.py` |
`tools/` | fact extraction, screenshot capture, Word and PowerPoint builders |
`docs/` | this handbook, plus `ARCHITECTURE.md`, `INSTALL.md`, `DEMO_GUIDE.md` and the demo deck |

---

## Upstream data

### SAP Business Data Cloud Standard Data Products

The L0 layer. Shared into the account as `SAP_BDC_DEMO_*` databases and read in
place — nothing is copied at that boundary.

Three shared databases are actually read:

| Shared database | Object |
|---|---|
`SAP_BDC_DEMO_ENTRY_VIEW_JOURNAL_ENTRY` | `BDCCONNECT.OPERATIONALACCTGDOCITEM` |
`SAP_BDC_DEMO_JOURNAL_ENTRY_HEADER` | `BDCCONNECT.JOURNALENTRY` |
`SAP_BDC_DEMO_SUPPLIER_INVOICE` | `BDCCONNECT.SUPPLIERINVOICE` |

What the products give you is the SAP semantics — company code, fiscal year,
cost centre, profit centre, debit/credit indicator — preserved rather than
flattened into warehouse-native names.

What they do not give you is a receivables object. That absence is the whole
reason `DT_AR_AGING` is generated, and it is the one place where this asset
departs from real SAP data. See
[findings](05-findings.md#dt_ar_aging-is-a-plain-table-wearing-a-dynamic-tables-prefix).

They also do not give you a customer master, a cash or bank ledger, or period-end
close status, so questions requiring any of those are out of scope by
construction.

---

## Snowflake platform features used

| Feature | Where | Why |
|---|---|---|
Secure data sharing | L0 → L1 | zero-copy; no extract to go stale |
Views | L1, 6 objects | naming and comments without storage or lag |
Dynamic tables | L2, 6 objects, `TARGET_LAG = 'DOWNSTREAM'` | refresh driven by consumption, not a schedule |
Semantic views | 2 objects | governed metric and relationship definitions |
Cortex Analyst | stage YAML | natural language over the L2 objects |
Cortex Agent | `SAP_FINANCE_360_AGENT` | Snowflake Intelligence surface |
Snowpark Container Services | the app | React + Express served from the account |
Native App framework | `app/` | packaged, installable, distributable |
Org listings | `create_org_listing.py` | multi-region distribution |

`TARGET_LAG = 'DOWNSTREAM'` is the choice worth calling out. It makes refresh a
function of what reads the tables, which suits a demo asset that is idle between
sessions — but it also means `DT_GL_BALANCE` and `DT_PNL_SUMMARY`, which no page
reads, are refreshed only by whatever queries them directly.

---

## Companion assets

### Supply chain ontology

The sibling asset in this family models **metadata about SAP data products** —
which entities exist, how they are annotated, how they associate. Finance 360
models **transactional finance data**. The two do not overlap and neither
subsumes the other.

Its documentation set is the structural template this handbook follows: the same
eight-part arc, the same Word builder, the same shared `sap_docx_kit.py`. Where
this handbook reads differently, it is because the findings differ, not because
the format does.

Two conventions were taken from it directly and are worth keeping:

- **Documentation is written from an extracted fact file**, not from memory, so
  every figure traces to the query that produced it.
- **Gaps are stated as findings.** Zero verified queries is reported in this
  handbook as a gap with a severity, not omitted.

### Toolchain shared across the family

| Module | Owner | Role |
|---|---|---|
`tools/sap_docx_kit.py` | **this repository** | the real Word implementation — palette, page setup, tables |
`tools/docx_kit.py` | every repository | shim re-exporting the above |
`tools/sap_pptx_kit.py` | this repository | PowerPoint equivalent |

The kit used to be copied byte-for-byte into each repository, so a branding fix
in one silently missed the others. It now lives once, here, and the sibling repos
carry only the shim. The shim resolves an absolute path and raises `ImportError`
if this repository is not checked out alongside — a loud failure rather than a
silent divergence.

**Edit `sap_docx_kit.py`. Never edit the shim.**

---

## Generated artefacts

Regenerated, never hand-edited:

| Artefact | Producer | Output |
|---|---|---|
Fact extract | `tools/finance_facts.py` | verified figures with per-fact provenance |
Screenshots | `tools/capture_shots.py` | 9 PNGs + `manifest.json` in `/tmp/finance_shots/` |
Word handbook | `tools/build_docs_docx.py` | 9 `.docx` in `docs/docx/` |
Management summary | `tools/build_management_summary.py` | Word |
Presales kit | `tools/build_presales_kit.py` | Word / PowerPoint |
Demo deck | | `docs/SAP_Finance_360_Demo_Guide.pptx` |

The Word builder is bespoke rather than pandoc for one reason: the output has to
match the management summary and the presales kit so the set reads as one family
of documents. Palette, page setup, navy table headers and `keep_with_next`
behaviour all come from the shared kit, and none survive a generic converter.

Its markdown table parser accepts rows **with or without** leading and trailing
pipes. GFM does not require them and this doc set omits them in many places; a
parser that insists on them drops those rows without erroring. Preserve that
behaviour.

---

## Boundaries in one table

| Question | Answerable here? | Why |
|---|---|---|
Revenue, expense, net income by fiscal year | yes | `DT_PNL_SUMMARY`, reconciled to L0 |
Expense by cost centre | yes | `DT_EXPENSE_BY_COSTCENTER` |
Revenue by profit centre | yes | `DT_REVENUE_BY_PROFITCENTER` |
GL balance by account and period | yes | `DT_GL_BALANCE` — but no app page reads it |
AP aging | yes, with caveats | `DT_AP_AGING`; gross not comparable to P&L revenue |
AR aging | yes, with caveats | `DT_AR_AGING` is generated, not shared |
Anything by customer | no | no customer master among the six L1 objects |
Cash or bank position | no | no cash ledger in the products in scope |
Period-end close status | no | not published |
Anything after 2025-03-28 in the ledger | no | last posting date |
AR vs revenue over the full AR window | no | windows do not overlap; AR runs to 2026-05-07 |
AP questions via Cortex Analyst | no | `DT_AP_AGING` is outside the Analyst model |
GL-balance or P&L questions via Cortex Analyst | no | both tables outside the Analyst model |
Which SAP data products exist and how they relate | no | that is the ontology asset, not this one |
Posting, reversing or closing anything | no | every object here is read-only |
