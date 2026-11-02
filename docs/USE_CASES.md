# Use Cases — SAP BDC Finance 360

> Record-to-report and order-to-cash visibility over SAP general ledger, cost/profit center and receivables data products.

- **App:** finance_dashboard_react (React, server 3002 / client 5175); legacy Streamlit finance_dashboard (8505)
- **Semantic view:** `SAP_FINANCE_360.ANALYTICS.SAP_FINANCE_360`
- **Analytics tables:** DT_JOURNAL_ENTRY_360, DT_EXPENSE_BY_COSTCENTER, DT_REVENUE_BY_PROFITCENTER, DT_AR_AGING
- **Catalog audited:** 2026-09-28. Each use case maps to an existing app page and to fields in the semantic view or API.

| # | Use case | Persona | App page |
|---|---|---|---|
| 1 | Company P&L snapshot | CFO / Controller | Overview; Period Analysis |
| 2 | Cost center spend control | Cost center owner / FP&A | Cost Centers |
| 3 | Profit center performance | Business unit leader | Profit Centers |
| 4 | Receivables aging and collections | Credit & collections manager | Accounts Receivable |
| 5 | Payables review | AP manager | Accounts Payable |
| 6 | Journal and close audit trail | Accounting / internal audit | General Ledger |
| 7 | Ask finance in plain English | Any finance user | Analyst (Cortex Agent) |

## 1. Company P&L snapshot

- **Persona:** CFO / Controller
- **Business question:** How are revenue and expenses tracking by company code this fiscal year?
- **Where in the app:** Overview; Period Analysis
- **Data used:** REVENUE_AMOUNT, EXPENSE_AMOUNT, COMPANYCODE, FISCALYEAR, FISCALPERIOD
- **Ask the agent:**
  - "What is total revenue versus expenses by company code?"
  - "Show the monthly revenue trend."
- **Value:** Replaces spreadsheet roll-ups with one governed view; faster month-end conversations.

## 2. Cost center spend control

- **Persona:** Cost center owner / FP&A
- **Business question:** Which cost centers and departments are driving expense?
- **Where in the app:** Cost Centers
- **Data used:** EXPENSE_AMOUNT, COSTCENTER, COSTCENTER_DEPARTMENT, DEPARTMENT
- **Ask the agent:**
  - "Which cost centers have the highest expenses?"
- **Value:** Targets budget conversations at the few cost centers that matter.

## 3. Profit center performance

- **Persona:** Business unit leader
- **Business question:** Which profit centers and segments generate the most revenue?
- **Where in the app:** Profit Centers
- **Data used:** REVENUE_AMOUNT, PROFITCENTER, SEGMENT
- **Ask the agent:**
  - "Which profit centers generate the most revenue?"
- **Value:** Shows where to invest and where margin is thin.

## 4. Receivables aging and collections

- **Persona:** Credit & collections manager
- **Business question:** How much is overdue, and which customers pay slowest?
- **Where in the app:** Accounts Receivable
- **Data used:** OPENAMOUNT, AGING_BUCKET, DAYS_TO_PAY, CUSTOMERNAME, CLEARINGSTATUS
- **Ask the agent:**
  - "What is the open AR amount by aging bucket?"
  - "What is the average DSO and which customers are the slowest to pay?"
- **Value:** Prioritizes collection calls; lowers DSO and working capital.

## 5. Payables review

- **Persona:** AP manager
- **Business question:** What is open in payables and how is it trending?
- **Where in the app:** Accounts Payable
- **Data used:** Journal entries by DEBITCREDITCODE and ACCOUNTINGDOCUMENTTYPE
- **Ask the agent:**
  - "What are total payables postings by period?"
- **Value:** Supports cash planning and payment-run decisions.

## 6. Journal and close audit trail

- **Persona:** Accounting / internal audit
- **Business question:** What was posted, by whom and when, across GL accounts?
- **Where in the app:** General Ledger
- **Data used:** GLACCOUNT, ACCOUNTINGDOCUMENTTYPE, POSTINGDATE, AMOUNTINTRANSACTIONCURRENCY
- **Ask the agent:**
  - "How many journal documents were posted this fiscal year?"
- **Value:** Speeds close review and audit sampling without SAP GUI access.

## 7. Ask finance in plain English

- **Persona:** Any finance user
- **Business question:** Answer ad-hoc finance questions without writing SQL.
- **Where in the app:** Analyst (Cortex Agent)
- **Data used:** Semantic view SAP_FINANCE_360 via Cortex Analyst
- **Ask the agent:**
  - "Which company code had the largest expense increase last period?"
- **Value:** Self-service answers from the same governed definitions the dashboards use.

---
Example agent questions are suggested prompts; validate answers in the app before customer demos.
