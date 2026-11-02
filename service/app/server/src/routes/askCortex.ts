import crypto from "node:crypto";
import { Router, type Request, type Response } from "express";
import { runQuery } from "../services/snowflake.js";

// ================================================================ Ask Cortex
// Each topic is a set of SQL "facts" the model must treat as authoritative.
// Facts span all company codes and fiscal years (the sidebar filters are not applied).
const router = Router();
const MODEL = process.env.CORTEX_MODEL ?? "claude-sonnet-4-5";
const JE = "APP_DATA.OPERATIONALACCTGDOCITEM";
const SI = "APP_DATA.SUPPLIERINVOICE";
const A = "APP_DATA";
const REV = `ABS(SUM(CASE WHEN GLACCOUNT LIKE '4%' AND DEBITCREDITCODE = 'H' THEN AMOUNTINTRANSACTIONCURRENCY ELSE 0 END))`;
const EXP = `ABS(SUM(CASE WHEN (GLACCOUNT LIKE '5%' OR GLACCOUNT LIKE '6%') AND DEBITCREDITCODE = 'S' THEN AMOUNTINTRANSACTIONCURRENCY ELSE 0 END))`;

type Facts = (args: Record<string, string>) => Promise<Record<string, unknown>>;
const T = (sql: string, binds: string[] = []) => runQuery(sql, binds);

const pl = {
  kpis: async () => (await T(`SELECT ${REV} total_revenue, ${EXP} total_expenses, COUNT(DISTINCT ACCOUNTINGDOCUMENT || COMPANYCODE || FISCALYEAR) documents, COUNT(DISTINCT COMPANYCODE) company_codes FROM ${JE}`))[0],
  byYear: () => T(`SELECT FISCALYEAR, ${REV} revenue, ${EXP} expenses FROM ${JE} GROUP BY 1 ORDER BY 1`),
  byCompany: () => T(`SELECT COMPANYCODE, ${REV} revenue, ${EXP} expenses FROM ${JE} GROUP BY 1 ORDER BY 2 DESC`),
};
const ap = {
  kpis: async () => (await T(`SELECT COUNT(*) invoice_count, SUM(INVOICEGROSSAMOUNT) total_amount, COUNT(DISTINCT INVOICINGPARTY) vendor_count FROM ${SI}`))[0],
  aging: () => T(`SELECT AGING_BUCKET, COUNT(*) invoices, SUM(INVOICEGROSSAMOUNT) amount FROM ${A}.DT_AP_AGING GROUP BY 1 ORDER BY 1`),
};
const ar = {
  kpis: async () => (await T(`SELECT SUM(CASE WHEN CLEARINGSTATUS <> 'Cleared' THEN OPENAMOUNT ELSE 0 END) open_amount, SUM(CASE WHEN IS_OVERDUE THEN OPENAMOUNT ELSE 0 END) overdue_amount, ROUND(AVG(CASE WHEN CLEARINGSTATUS = 'Cleared' THEN DAYS_TO_PAY END),1) avg_dso FROM ${A}.DT_AR_AGING`))[0],
  aging: () => T(`SELECT AGING_BUCKET, COUNT(*) invoices, SUM(OPENAMOUNT) amount FROM ${A}.DT_AR_AGING WHERE CLEARINGSTATUS <> 'Cleared' GROUP BY 1 ORDER BY 1`),
};

const TOPICS: Record<string, { title: string; facts: Facts }> = {
  general: { title: "cross-functional finance summary (P&L, cost/profit centers, AP, AR)", facts: async () => ({
    pl_kpis: await pl.kpis(),
    pl_by_year: await pl.byYear(),
    pl_by_company_code: await pl.byCompany(),
    top_cost_centers: await T(`SELECT COSTCENTER, DEPARTMENT, SUM(EXPENSE_AMOUNT) expense FROM ${A}.DT_EXPENSE_BY_COSTCENTER GROUP BY 1,2 ORDER BY 3 DESC LIMIT 5`),
    top_profit_centers: await T(`SELECT PROFITCENTER, COALESCE(SEGMENT,'Unassigned') segment, SUM(REVENUE_AMOUNT) revenue FROM ${A}.DT_REVENUE_BY_PROFITCENTER GROUP BY 1,2 ORDER BY 3 DESC LIMIT 5`),
    ap_kpis: await ap.kpis(), ap_aging: await ap.aging(),
    ar_kpis: await ar.kpis(), ar_aging: await ar.aging(),
  }) },
  overview: { title: "executive finance overview", facts: async () => ({
    kpis: await pl.kpis(),
    by_year: await pl.byYear(),
    by_company_code: await pl.byCompany(),
    expense_by_category: await T(`SELECT CASE WHEN GLACCOUNT LIKE '5%' THEN 'COGS' WHEN GLACCOUNT LIKE '600%' OR GLACCOUNT LIKE '610%' THEN 'Personnel' WHEN GLACCOUNT LIKE '620%' OR GLACCOUNT LIKE '630%' THEN 'Facilities' WHEN GLACCOUNT LIKE '640%' OR GLACCOUNT LIKE '650%' THEN 'IT & Marketing' WHEN GLACCOUNT LIKE '660%' OR GLACCOUNT LIKE '670%' THEN 'Travel & Prof Fees' WHEN GLACCOUNT LIKE '68%' OR GLACCOUNT LIKE '69%' THEN 'Insurance/Depr/R&D' ELSE 'Other' END category, ABS(SUM(AMOUNTINTRANSACTIONCURRENCY)) amount FROM ${JE} WHERE (GLACCOUNT LIKE '5%' OR GLACCOUNT LIKE '6%') AND DEBITCREDITCODE = 'S' GROUP BY 1 ORDER BY 2 DESC`),
    docs_by_type: await T(`SELECT ACCOUNTINGDOCUMENTTYPE, COUNT(DISTINCT ACCOUNTINGDOCUMENT || COMPANYCODE || FISCALYEAR) docs FROM ${JE} GROUP BY 1 ORDER BY 2 DESC LIMIT 10`),
  }) },
  "general-ledger": { title: "general ledger, P&L and balance sheet", facts: async () => ({
    pl_summary: await T(`SELECT CASE WHEN GLACCOUNT LIKE '4%' THEN 'Revenue' WHEN GLACCOUNT LIKE '5%' THEN 'COGS' WHEN GLACCOUNT LIKE '6%' THEN 'Operating Expenses' WHEN GLACCOUNT LIKE '7%' THEN 'Other Income/Expense' WHEN GLACCOUNT LIKE '8%' THEN 'Tax' ELSE 'Other' END category, ABS(SUM(AMOUNTINTRANSACTIONCURRENCY)) amount FROM ${JE} WHERE GLACCOUNT >= '400000' GROUP BY 1 ORDER BY 1`),
    balance_sheet: await T(`SELECT CASE WHEN GLACCOUNT < '200000' THEN 'Assets' WHEN GLACCOUNT < '300000' THEN 'Liabilities' ELSE 'Equity' END category, SUM(AMOUNTINTRANSACTIONCURRENCY) amount FROM ${JE} WHERE GLACCOUNT < '400000' GROUP BY 1 ORDER BY 1`),
    largest_gl_balances: await T(`SELECT GLACCOUNT, SUM(CASE WHEN DEBITCREDITCODE='S' THEN AMOUNTINTRANSACTIONCURRENCY ELSE 0 END) debit, ABS(SUM(CASE WHEN DEBITCREDITCODE='H' THEN AMOUNTINTRANSACTIONCURRENCY ELSE 0 END)) credit, SUM(AMOUNTINTRANSACTIONCURRENCY) balance FROM ${JE} GROUP BY 1 ORDER BY ABS(balance) DESC LIMIT 15`),
    trial_balance_check: (await T(`SELECT SUM(AMOUNTINTRANSACTIONCURRENCY) net_of_all_postings, COUNT(*) postings FROM ${JE}`))[0],
  }) },
  "cost-centers": { title: "cost center expense", facts: async () => ({
    kpis: (await T(`SELECT COUNT(DISTINCT COSTCENTER) cost_centers, SUM(EXPENSE_AMOUNT) total_expense FROM ${A}.DT_EXPENSE_BY_COSTCENTER`))[0],
    top_cost_centers: await T(`SELECT COSTCENTER, SUM(EXPENSE_AMOUNT) expense FROM ${A}.DT_EXPENSE_BY_COSTCENTER GROUP BY 1 ORDER BY 2 DESC LIMIT 15`),
    by_department: await T(`SELECT DEPARTMENT, SUM(EXPENSE_AMOUNT) expense FROM ${A}.DT_EXPENSE_BY_COSTCENTER WHERE DEPARTMENT IS NOT NULL AND DEPARTMENT <> '' GROUP BY 1 ORDER BY 2 DESC`),
    by_department_year: await T(`SELECT DEPARTMENT, FISCALYEAR, SUM(EXPENSE_AMOUNT) expense FROM ${A}.DT_EXPENSE_BY_COSTCENTER GROUP BY 1,2 ORDER BY 1,2 LIMIT 120`),
  }) },
  "profit-centers": { title: "profit center revenue and margin", facts: async () => ({
    by_profit_center: await T(`SELECT r.PROFITCENTER, r.revenue, COALESCE(e.expense,0) expense, r.revenue - COALESCE(e.expense,0) margin FROM (SELECT PROFITCENTER, SUM(REVENUE_AMOUNT) revenue FROM ${A}.DT_REVENUE_BY_PROFITCENTER GROUP BY 1) r LEFT JOIN (SELECT PROFITCENTER, SUM(EXPENSE_AMOUNT) expense FROM ${A}.DT_EXPENSE_BY_COSTCENTER GROUP BY 1) e ON r.PROFITCENTER = e.PROFITCENTER ORDER BY r.revenue DESC LIMIT 25`),
    by_segment: await T(`SELECT COALESCE(SEGMENT,'Unassigned') segment, SUM(REVENUE_AMOUNT) revenue FROM ${A}.DT_REVENUE_BY_PROFITCENTER GROUP BY 1 ORDER BY 2 DESC`),
    by_year: await T(`SELECT FISCALYEAR, SUM(REVENUE_AMOUNT) revenue FROM ${A}.DT_REVENUE_BY_PROFITCENTER GROUP BY 1 ORDER BY 1`),
  }) },
  "accounts-payable": { title: "accounts payable, supplier invoices and aging", facts: async () => ({
    kpis: await ap.kpis(),
    aging: await ap.aging(),
    status: await T(`SELECT SUPPLIERINVOICESTATUS status, COUNT(*) invoices FROM ${SI} GROUP BY 1 ORDER BY 2 DESC`),
    top_vendors: await T(`SELECT INVOICINGPARTY vendor, COUNT(*) invoices, SUM(INVOICEGROSSAMOUNT) total FROM ${SI} GROUP BY 1 ORDER BY 3 DESC LIMIT 10`),
    by_currency: await T(`SELECT DOCUMENTCURRENCY currency, COUNT(*) invoices, SUM(INVOICEGROSSAMOUNT) total FROM ${SI} GROUP BY 1 ORDER BY 3 DESC`),
  }) },
  "accounts-receivable": { title: "accounts receivable, DSO and overdue customers", facts: async () => ({
    kpis: await ar.kpis(),
    aging: await ar.aging(),
    top_open_customers: await T(`SELECT CUSTOMERNAME, COUNT(*) invoices, SUM(OPENAMOUNT) open_amount, MAX(DAYS_PAST_DUE) max_days_past_due FROM ${A}.DT_AR_AGING WHERE CLEARINGSTATUS <> 'Cleared' GROUP BY 1 ORDER BY 3 DESC LIMIT 10`),
    dso_by_month: await T(`SELECT TO_CHAR(INVOICEDATE,'YYYY-MM') period, ROUND(AVG(DAYS_TO_PAY),1) avg_dso FROM ${A}.DT_AR_AGING WHERE CLEARINGSTATUS = 'Cleared' GROUP BY 1 ORDER BY 1 LIMIT 60`),
    by_payment_terms: await T(`SELECT PAYMENTTERMS, COUNT(*) invoices, ROUND(AVG(CASE WHEN CLEARINGSTATUS='Cleared' THEN DAYS_TO_PAY END),1) avg_days_to_pay FROM ${A}.DT_AR_AGING GROUP BY 1 ORDER BY 2 DESC`),
  }) },
  "period-analysis": { title: "period-over-period revenue and expense trends", facts: async () => ({
    monthly: await T(`SELECT FISCALYEAR, FISCALPERIOD, ${REV} revenue, ${EXP} expenses FROM ${JE} GROUP BY 1,2 ORDER BY 1,2 LIMIT 120`),
    by_year: await pl.byYear(),
  }) },
};

const SYSTEM = `Before answering, check that every number and characterisation in your summary (profit vs loss, up vs down, ages, counts, totals) matches the facts and any table you include; never state a figure the facts do not support.
You are Snowflake Cortex, an SAP finance analyst (FP&A / controller) for a multi-company-code
enterprise. Data comes from SAP Business Data Cloud finance data products (journal entry items, supplier
invoices) and Snowflake dynamic tables derived from them (cost center expense, profit center revenue,
AP and AR aging). The SAP BDC sources in this environment are demo data products (SAP_BDC_DEMO_*), so
figures are illustrative, not a real company's books; mention this briefly when stating conclusions.

Rules:
- The JSON facts below are authoritative. Cite specific company codes, GL accounts, cost and profit centers,
  vendors, customers, periods, percentages and amounts from them. Never invent numbers.
- Amounts are in transaction currency and may mix currencies; do not convert, and say so if it matters.
- Lead with the direct answer in one or two sentences, then evidence (a small markdown table when comparing),
  then 2-4 concrete recommended actions.
- If the facts do not contain what is needed to answer, say so plainly and name what data would be needed.
- Keep it under 300 words.`;

// Inside a Native App, AI_COMPLETE needs Cortex access granted by the consumer
// (GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO APPLICATION <app>). Report that
// plainly instead of surfacing a raw SQL error.
function friendlyError(err: unknown): string {
  const m = String(err);
  if (/AI_COMPLETE|CORTEX|unknown function|not authorized|insufficient privileges|model/i.test(m))
    return "Ask Cortex is not available in this installation: the app cannot call Snowflake Cortex (AI_COMPLETE). " +
      "An account admin can enable it with GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO APPLICATION <app name>; " +
      "the model must also be available in this region (set CORTEX_MODEL to override). Details: " + m.slice(0, 300);
  return m;
}

interface Job { status: "running" | "done" | "error"; answer?: string; error?: string; started: number }
const jobs = new Map<string, Job>();

async function runAsk(topic: string, args: Record<string, string>, question: string): Promise<string> {
  const t = TOPICS[topic];
  const facts = await t.facts(args);
  const q = question?.trim() || `Analyse this ${t.title}: what stands out, why, and what should we do?`;
  const prompt = `${SYSTEM}\n\nTopic: ${t.title}\nContext: ${JSON.stringify(args)}\n\nFACTS (JSON):\n${JSON.stringify(facts).slice(0, 60000)}\n\nQuestion: ${q}`;
  const rows = await runQuery(`SELECT AI_COMPLETE(?, ?) AS answer`, [MODEL, prompt]);
  return String(rows[0]?.answer ?? "No answer returned.");
}

router.get("/api/ask-cortex/topics", (_req, res) => {
  res.json(Object.fromEntries(Object.entries(TOPICS).map(([k, v]) => [k, v.title])));
});

router.post("/api/ask-cortex", (req: Request, res: Response) => {
  const { topic, args = {}, question = "" } = req.body ?? {};
  if (typeof topic !== "string" || !TOPICS[topic]) return res.status(400).json({ error: "unknown topic" });
  const clean: Record<string, string> = {};
  for (const [k, v] of Object.entries(args ?? {})) if (typeof v === "string" && v.length < 80) clean[k] = v;
  const id = crypto.randomUUID();
  jobs.set(id, { status: "running", started: Date.now() });
  runAsk(topic, clean, String(question).slice(0, 1000))
    .then((answer) => jobs.set(id, { status: "done", answer, started: Date.now() }))
    .catch((err) => jobs.set(id, { status: "error", error: friendlyError(err), started: Date.now() }));
  for (const [k, j] of jobs) if (Date.now() - j.started > 3_600_000) jobs.delete(k);
  res.json({ id });
});

router.get("/api/ask-cortex/:id", (req: Request, res: Response) => {
  const j = jobs.get(String(req.params.id));
  if (!j) return res.status(404).json({ error: "job not found" });
  res.json(j);
});

export default router;
