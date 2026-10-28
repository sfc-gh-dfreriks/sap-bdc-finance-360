# Demo Guide — SAP BDC Finance 360

A ~10-minute flow showing how the Snowflake × SAP Business Data Cloud
partnership turns locked-up SAP finance data into a live, AI-powered app.
The full slide deck (with presenter notes) is in
[`SAP_Finance_360_Demo_Guide.pptx`](SAP_Finance_360_Demo_Guide.pptx).

## The story in one line
Two platforms, one governed data foundation: SAP BDC shares governed finance
data products into Snowflake with **zero copy**; Snowflake adds AI, apps and
global reach on top — no pipelines, full SAP context preserved.

## 10-minute flow

1. **Open the app** — no setup; the data is already inside (bundled Native App).
   It opens on **Executive Dashboard** (sidebar page 2, under Ask Cortex).
2. **Executive Dashboard** — revenue, expenses and net income by company code (US/DE/JP).
3. **General Ledger** — GL postings by account; drill cost centers & profit centers.
4. **Accounts Payable** — supplier invoices and AP aging.
5. **Accounts Receivable** — AR aging buckets, DSO, slow-paying customers.
6. **Ask Cortex** — click "Ask Cortex about Accounts Receivable" (or open the
   Ask Cortex page) for a written analysis of the live figures with recommended
   actions; try "Which customers should we chase first?".
7. **Snowflake Intelligence** — type a question live into the `SAP_FINANCE_360_AGENT`
   (the agent has no in-app page):
   - "What is revenue vs expenses by company code?"
   - "Show the monthly revenue trend."
   - "Which customers are slowest to pay?"
8. **Show the generated SQL** — prove it's governed and explainable.
9. **Recap** — zero-ETL, governed, AI-ready, one-click distribution.

## Key points to land
- The data is **already inside Snowflake** — no ETL, no waiting.
- SAP **business context is preserved** (revenue, expenses, DSO, aging).
- The `SAP_FINANCE_360_AGENT` answers live, in plain English, with governed SQL.
- One definition → **three regions** (US, EMEA, APAC), each its own governed install.

## Do / Don't
- **Do** ask the agent a real question live; lead with business outcomes.
- **Don't** pre-load canned answers or drown the audience in architecture/SQL.
- **Don't** promise cross-region magic — each region is its own governed install.
