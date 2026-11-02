import { Router, type Request, type Response } from "express";
import { runQuery } from "../services/snowflake.js";
import { callCortexAnalyst } from "../services/analyst.js";

const router = Router();

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Parse comma-separated values from query string. */
function parseList(raw: unknown): string[] {
  if (typeof raw !== "string" || raw.trim() === "") return [];
  return raw.split(",").map((v) => v.trim()).filter(Boolean);
}

/**
 * Build a SQL IN clause with positional bind placeholders.
 * Returns { clause: "IN (?, ?, ?)", binds: [...values] }
 */
function inClause(values: string[]): { clause: string; binds: string[] } {
  const placeholders = values.map(() => "?").join(", ");
  return { clause: `IN (${placeholders})`, binds: values };
}

/** Build WHERE fragments for company codes and fiscal years. */
function buildFilters(
  companyCodes: string[],
  fiscalYears: string[],
  ccCol = "COMPANYCODE",
  fyCol = "FISCALYEAR"
): { where: string; binds: string[] } {
  const parts: string[] = [];
  const binds: string[] = [];

  if (companyCodes.length > 0) {
    const cc = inClause(companyCodes);
    parts.push(`${ccCol} ${cc.clause}`);
    binds.push(...cc.binds);
  }
  if (fiscalYears.length > 0) {
    const fy = inClause(fiscalYears);
    parts.push(`${fyCol} ${fy.clause}`);
    binds.push(...fy.binds);
  }

  const where = parts.length > 0 ? `WHERE ${parts.join(" AND ")}` : "";
  return { where, binds };
}

// ---------------------------------------------------------------------------
// GET /api/filters
// ---------------------------------------------------------------------------
router.get("/api/filters", async (_req: Request, res: Response) => {
  try {
    const [ccRows, fyRows] = await Promise.all([
      runQuery(
        `SELECT DISTINCT COMPANYCODE
           FROM APP_DATA.JOURNALENTRY
          ORDER BY 1`
      ),
      runQuery(
        `SELECT DISTINCT FISCALYEAR
           FROM APP_DATA.JOURNALENTRY
          ORDER BY 1`
      ),
    ]);
    res.json({
      companyCodes: ccRows.map((r) => r.companycode),
      fiscalYears: fyRows.map((r) => r.fiscalyear),
    });
  } catch (err) {
    console.error("GET /api/filters error:", err);
    res.status(500).json({ error: String(err) });
  }
});

// ---------------------------------------------------------------------------
// GET /api/overview?companyCodes=...&fiscalYears=...
// ---------------------------------------------------------------------------
router.get("/api/overview", async (req: Request, res: Response) => {
  try {
    const companyCodes = parseList(req.query.companyCodes);
    const fiscalYears = parseList(req.query.fiscalYears);
    if (companyCodes.length === 0 && fiscalYears.length === 0) {
      return res.json({});
    }

    const { where, binds } = buildFilters(companyCodes, fiscalYears);

    const [kpis, revenueTrend, expenseByCategory, monthlyPL, docsByType, revenueByCC] =
      await Promise.all([
        // KPIs
        runQuery(
          `SELECT
             ABS(SUM(CASE WHEN GLACCOUNT LIKE '4%' AND DEBITCREDITCODE = 'H' THEN AMOUNTINTRANSACTIONCURRENCY ELSE 0 END)) AS total_revenue,
             ABS(SUM(CASE WHEN (GLACCOUNT LIKE '5%' OR GLACCOUNT LIKE '6%') AND DEBITCREDITCODE = 'S' THEN AMOUNTINTRANSACTIONCURRENCY ELSE 0 END)) AS total_expenses,
             COUNT(DISTINCT ACCOUNTINGDOCUMENT || COMPANYCODE || FISCALYEAR) AS total_documents,
             COUNT(DISTINCT GLACCOUNT) AS gl_accounts_used,
             COUNT(DISTINCT COSTCENTER) AS cost_centers_used
           FROM APP_DATA.OPERATIONALACCTGDOCITEM
           ${where}`,
          binds
        ),
        // Revenue Trend
        runQuery(
          `SELECT FISCALYEAR, FISCALPERIOD,
                  ABS(SUM(AMOUNTINTRANSACTIONCURRENCY)) AS revenue
             FROM APP_DATA.OPERATIONALACCTGDOCITEM
            ${where}${where ? " AND" : " WHERE"} GLACCOUNT LIKE '4%' AND DEBITCREDITCODE = 'H'
            GROUP BY FISCALYEAR, FISCALPERIOD
            ORDER BY FISCALYEAR, FISCALPERIOD`,
          binds
        ),
        // Expense by Category
        runQuery(
          `SELECT
             CASE
               WHEN GLACCOUNT LIKE '5%' THEN 'COGS'
               WHEN GLACCOUNT LIKE '600%' OR GLACCOUNT LIKE '610%' THEN 'Personnel'
               WHEN GLACCOUNT LIKE '620%' OR GLACCOUNT LIKE '630%' THEN 'Facilities'
               WHEN GLACCOUNT LIKE '640%' OR GLACCOUNT LIKE '650%' THEN 'IT & Marketing'
               WHEN GLACCOUNT LIKE '660%' OR GLACCOUNT LIKE '670%' THEN 'Travel & Prof Fees'
               WHEN GLACCOUNT LIKE '680%' OR GLACCOUNT LIKE '690%' OR GLACCOUNT LIKE '695%' THEN 'Insurance/Depr/R&D'
               ELSE 'Other'
             END AS category,
             ABS(SUM(AMOUNTINTRANSACTIONCURRENCY)) AS amount
           FROM APP_DATA.OPERATIONALACCTGDOCITEM
           ${where}${where ? " AND" : " WHERE"} (GLACCOUNT LIKE '5%' OR GLACCOUNT LIKE '6%') AND DEBITCREDITCODE = 'S'
           GROUP BY category
           ORDER BY amount DESC`,
          binds
        ),
        // Monthly P&L
        runQuery(
          `SELECT FISCALYEAR, FISCALPERIOD,
                  ABS(SUM(CASE WHEN GLACCOUNT LIKE '4%' AND DEBITCREDITCODE = 'H' THEN AMOUNTINTRANSACTIONCURRENCY ELSE 0 END)) AS revenue,
                  ABS(SUM(CASE WHEN (GLACCOUNT LIKE '5%' OR GLACCOUNT LIKE '6%') AND DEBITCREDITCODE = 'S' THEN AMOUNTINTRANSACTIONCURRENCY ELSE 0 END)) AS expenses
             FROM APP_DATA.OPERATIONALACCTGDOCITEM
           ${where}
           GROUP BY FISCALYEAR, FISCALPERIOD
           ORDER BY FISCALYEAR, FISCALPERIOD`,
          binds
        ),
        // Documents by Type
        runQuery(
          `SELECT ACCOUNTINGDOCUMENTTYPE,
                  COUNT(DISTINCT ACCOUNTINGDOCUMENT || COMPANYCODE || FISCALYEAR) AS doc_count
             FROM APP_DATA.OPERATIONALACCTGDOCITEM
           ${where}
           GROUP BY ACCOUNTINGDOCUMENTTYPE
           ORDER BY doc_count DESC`,
          binds
        ),
        // Revenue by Company Code
        runQuery(
          `SELECT COMPANYCODE,
                  ABS(SUM(AMOUNTINTRANSACTIONCURRENCY)) AS revenue
             FROM APP_DATA.OPERATIONALACCTGDOCITEM
           ${where}${where ? " AND" : " WHERE"} GLACCOUNT LIKE '4%' AND DEBITCREDITCODE = 'H'
           GROUP BY COMPANYCODE
           ORDER BY revenue DESC`,
          binds
        ),
      ]);

    res.json({
      kpis: kpis[0] ?? {},
      revenueTrend,
      expenseByCategory,
      monthlyPL,
      docsByType,
      revenueByCC,
    });
  } catch (err) {
    console.error("GET /api/overview error:", err);
    res.status(500).json({ error: String(err) });
  }
});

// ---------------------------------------------------------------------------
// GET /api/general-ledger?companyCodes=...&fiscalYears=...
// ---------------------------------------------------------------------------
router.get("/api/general-ledger", async (req: Request, res: Response) => {
  try {
    const companyCodes = parseList(req.query.companyCodes);
    const fiscalYears = parseList(req.query.fiscalYears);
    if (companyCodes.length === 0 && fiscalYears.length === 0) {
      return res.json({});
    }

    const { where, binds } = buildFilters(companyCodes, fiscalYears);

    const [trialBalance, plSummary, balanceSheet, glActivity] =
      await Promise.all([
        // Trial Balance
        runQuery(
          `SELECT GLACCOUNT,
                  SUM(CASE WHEN DEBITCREDITCODE = 'S' THEN AMOUNTINTRANSACTIONCURRENCY ELSE 0 END) AS debit,
                  ABS(SUM(CASE WHEN DEBITCREDITCODE = 'H' THEN AMOUNTINTRANSACTIONCURRENCY ELSE 0 END)) AS credit,
                  SUM(AMOUNTINTRANSACTIONCURRENCY) AS balance
             FROM APP_DATA.OPERATIONALACCTGDOCITEM
           ${where}
           GROUP BY GLACCOUNT
           ORDER BY GLACCOUNT`,
          binds
        ),
        // P&L Summary
        runQuery(
          `SELECT
             CASE
               WHEN GLACCOUNT LIKE '4%' THEN 'Revenue'
               WHEN GLACCOUNT LIKE '5%' THEN 'COGS'
               WHEN GLACCOUNT LIKE '6%' THEN 'Operating Expenses'
               WHEN GLACCOUNT LIKE '7%' THEN 'Other Income/Expense'
               WHEN GLACCOUNT LIKE '8%' THEN 'Tax'
               ELSE 'Other'
             END AS category,
             ABS(SUM(AMOUNTINTRANSACTIONCURRENCY)) AS amount
           FROM APP_DATA.OPERATIONALACCTGDOCITEM
           ${where}${where ? " AND" : " WHERE"} GLACCOUNT >= '400000'
           GROUP BY category
           ORDER BY category`,
          binds
        ),
        // Balance Sheet
        runQuery(
          `SELECT
             CASE
               WHEN GLACCOUNT < '200000' THEN 'Assets'
               WHEN GLACCOUNT < '300000' THEN 'Liabilities'
               ELSE 'Equity'
             END AS category,
             SUM(AMOUNTINTRANSACTIONCURRENCY) AS amount
           FROM APP_DATA.OPERATIONALACCTGDOCITEM
           ${where}${where ? " AND" : " WHERE"} GLACCOUNT < '400000'
           GROUP BY category
           ORDER BY category`,
          binds
        ),
        // GL Activity by Period
        runQuery(
          `SELECT FISCALYEAR, FISCALPERIOD,
                  COUNT(*) AS postings,
                  SUM(ABS(AMOUNTINTRANSACTIONCURRENCY)) AS total_amount
             FROM APP_DATA.OPERATIONALACCTGDOCITEM
           ${where}
           GROUP BY FISCALYEAR, FISCALPERIOD
           ORDER BY FISCALYEAR, FISCALPERIOD`,
          binds
        ),
      ]);

    res.json({ trialBalance, plSummary, balanceSheet, glActivity });
  } catch (err) {
    console.error("GET /api/general-ledger error:", err);
    res.status(500).json({ error: String(err) });
  }
});

// ---------------------------------------------------------------------------
// GET /api/cost-centers?companyCodes=...&fiscalYears=...
// ---------------------------------------------------------------------------
router.get("/api/cost-centers", async (req: Request, res: Response) => {
  try {
    const companyCodes = parseList(req.query.companyCodes);
    const fiscalYears = parseList(req.query.fiscalYears);
    if (companyCodes.length === 0 && fiscalYears.length === 0) {
      return res.json({});
    }

    const { where, binds } = buildFilters(
      companyCodes,
      fiscalYears,
      "COMPANYCODE",
      "FISCALYEAR"
    );

    const [kpis, topCostCenters, byDepartment, monthlyTrend, detail] =
      await Promise.all([
        // KPIs
        runQuery(
          `SELECT
             COUNT(DISTINCT COSTCENTER) AS cost_center_count,
             SUM(EXPENSE_AMOUNT) AS total_expense,
             AVG(EXPENSE_AMOUNT) AS avg_expense
           FROM APP_DATA.DT_EXPENSE_BY_COSTCENTER
           ${where}`,
          binds
        ),
        // Top cost centers
        runQuery(
          `SELECT COSTCENTER,
                  SUM(EXPENSE_AMOUNT) AS total
             FROM APP_DATA.DT_EXPENSE_BY_COSTCENTER
           ${where}
           GROUP BY COSTCENTER
           ORDER BY total DESC
           LIMIT 15`,
          binds
        ),
        // By department
        runQuery(
          `SELECT DEPARTMENT,
                  SUM(EXPENSE_AMOUNT) AS total
             FROM APP_DATA.DT_EXPENSE_BY_COSTCENTER
           ${where}${where ? " AND" : " WHERE"} DEPARTMENT IS NOT NULL AND DEPARTMENT != ''
           GROUP BY DEPARTMENT
           ORDER BY total DESC`,
          binds
        ),
        // Monthly trend
        runQuery(
          `SELECT FISCALYEAR || '-' || FISCALPERIOD AS period,
                  COSTCENTER,
                  SUM(EXPENSE_AMOUNT) AS amount
             FROM APP_DATA.DT_EXPENSE_BY_COSTCENTER
           ${where}
           GROUP BY period, COSTCENTER
           ORDER BY period`,
          binds
        ),
        // Detail
        runQuery(
          `SELECT COSTCENTER, FISCALYEAR,
                  SUM(EXPENSE_AMOUNT) AS total
             FROM APP_DATA.DT_EXPENSE_BY_COSTCENTER
           ${where}
           GROUP BY COSTCENTER, FISCALYEAR
           ORDER BY COSTCENTER, FISCALYEAR`,
          binds
        ),
      ]);

    res.json({
      kpis: kpis[0] ?? {},
      topCostCenters,
      byDepartment,
      monthlyTrend,
      detail,
    });
  } catch (err) {
    console.error("GET /api/cost-centers error:", err);
    res.status(500).json({ error: String(err) });
  }
});

// ---------------------------------------------------------------------------
// GET /api/profit-centers?companyCodes=...&fiscalYears=...
// ---------------------------------------------------------------------------
router.get("/api/profit-centers", async (req: Request, res: Response) => {
  try {
    const companyCodes = parseList(req.query.companyCodes);
    const fiscalYears = parseList(req.query.fiscalYears);
    if (companyCodes.length === 0 && fiscalYears.length === 0) {
      return res.json({});
    }

    const { where, binds } = buildFilters(companyCodes, fiscalYears);

    const [revenueKpis, expenseTotal, revenueByPC, revenueBySegment, monthlyRevenueTrend, comparison] =
      await Promise.all([
        // Revenue KPIs
        runQuery(
          `SELECT
             COUNT(DISTINCT PROFITCENTER) AS profit_center_count,
             SUM(REVENUE_AMOUNT) AS total_revenue,
             AVG(REVENUE_AMOUNT) AS avg_revenue
           FROM APP_DATA.DT_REVENUE_BY_PROFITCENTER
           ${where}`,
          binds
        ),
        // Expense total
        runQuery(
          `SELECT SUM(EXPENSE_AMOUNT) AS total_expense
             FROM APP_DATA.DT_EXPENSE_BY_COSTCENTER
           ${where}`,
          binds
        ),
        // Revenue by profit center
        runQuery(
          `SELECT PROFITCENTER,
                  SUM(REVENUE_AMOUNT) AS revenue
             FROM APP_DATA.DT_REVENUE_BY_PROFITCENTER
           ${where}
           GROUP BY PROFITCENTER
           ORDER BY revenue DESC`,
          binds
        ),
        // Revenue by segment
        runQuery(
          `SELECT COALESCE(SEGMENT, 'Unassigned') AS segment,
                  SUM(REVENUE_AMOUNT) AS revenue
             FROM APP_DATA.DT_REVENUE_BY_PROFITCENTER
           ${where}
           GROUP BY segment
           ORDER BY revenue DESC`,
          binds
        ),
        // Monthly revenue trend by profit center
        runQuery(
          `SELECT FISCALYEAR || '-' || FISCALPERIOD AS period,
                  PROFITCENTER,
                  SUM(REVENUE_AMOUNT) AS revenue
             FROM APP_DATA.DT_REVENUE_BY_PROFITCENTER
           ${where}
           GROUP BY period, PROFITCENTER
           ORDER BY period`,
          binds
        ),
        // Comparison: revenue vs expense by profit center
        runQuery(
          `SELECT r.PROFITCENTER,
                  SUM(r.REVENUE_AMOUNT) AS revenue,
                  COALESCE(e.total_expense, 0) AS expense
             FROM APP_DATA.DT_REVENUE_BY_PROFITCENTER r
             LEFT JOIN (
               SELECT PROFITCENTER, SUM(EXPENSE_AMOUNT) AS total_expense
                 FROM APP_DATA.DT_EXPENSE_BY_COSTCENTER
               ${where}
               GROUP BY PROFITCENTER
             ) e ON r.PROFITCENTER = e.PROFITCENTER
           ${where}
           GROUP BY r.PROFITCENTER, e.total_expense
           ORDER BY revenue DESC`,
          [...binds, ...binds]
        ),
      ]);

    res.json({
      kpis: {
        ...(revenueKpis[0] ?? {}),
        total_expense: (expenseTotal[0] as Record<string, unknown>)?.total_expense ?? 0,
      },
      revenueByPC,
      revenueBySegment,
      monthlyRevenueTrend,
      comparison,
    });
  } catch (err) {
    console.error("GET /api/profit-centers error:", err);
    res.status(500).json({ error: String(err) });
  }
});

// ---------------------------------------------------------------------------
// GET /api/accounts-payable?companyCodes=...&fiscalYears=...
// ---------------------------------------------------------------------------
router.get("/api/accounts-payable", async (req: Request, res: Response) => {
  try {
    const companyCodes = parseList(req.query.companyCodes);
    const fiscalYears = parseList(req.query.fiscalYears);
    if (companyCodes.length === 0 && fiscalYears.length === 0) {
      return res.json({});
    }

    const { where, binds } = buildFilters(companyCodes, fiscalYears);

    const [kpis, aging, invoiceStatus, topVendors, currencyDist, monthlyVolume] =
      await Promise.all([
        // KPIs
        runQuery(
          `SELECT
             COUNT(*) AS invoice_count,
             SUM(INVOICEGROSSAMOUNT) AS total_amount,
             AVG(INVOICEGROSSAMOUNT) AS avg_amount,
             COUNT(DISTINCT INVOICINGPARTY) AS vendor_count
           FROM APP_DATA.SUPPLIERINVOICE
           ${where}`,
          binds
        ),
        // Aging
        runQuery(
          `SELECT AGING_BUCKET, SUM(INVOICEGROSSAMOUNT) AS amount, COUNT(*) AS count
             FROM APP_DATA.DT_AP_AGING
           ${where}
           GROUP BY AGING_BUCKET
           ORDER BY AGING_BUCKET`,
          binds
        ),
        // Invoice status
        runQuery(
          `SELECT SUPPLIERINVOICESTATUS AS status,
                  COUNT(*) AS count
             FROM APP_DATA.SUPPLIERINVOICE
           ${where}
           GROUP BY SUPPLIERINVOICESTATUS
           ORDER BY count DESC`,
          binds
        ),
        // Top vendors
        runQuery(
          `SELECT INVOICINGPARTY AS vendor,
                  SUM(INVOICEGROSSAMOUNT) AS total,
                  COUNT(*) AS invoice_count
             FROM APP_DATA.SUPPLIERINVOICE
           ${where}
           GROUP BY INVOICINGPARTY
           ORDER BY total DESC
           LIMIT 10`,
          binds
        ),
        // Currency distribution
        runQuery(
          `SELECT DOCUMENTCURRENCY AS currency,
                  COUNT(*) AS count,
                  SUM(INVOICEGROSSAMOUNT) AS total
             FROM APP_DATA.SUPPLIERINVOICE
           ${where}
           GROUP BY DOCUMENTCURRENCY
           ORDER BY total DESC`,
          binds
        ),
        // Monthly volume
        runQuery(
          `SELECT FISCALYEAR || '-' || LPAD(MONTH(POSTINGDATE), 3, '0') AS period,
                  COUNT(*) AS count,
                  SUM(INVOICEGROSSAMOUNT) AS total
             FROM APP_DATA.SUPPLIERINVOICE
           ${where}
           GROUP BY period
           ORDER BY period`,
          binds
        ),
      ]);

    res.json({
      kpis: kpis[0] ?? {},
      aging,
      invoiceStatus,
      topVendors,
      currencyDist,
      monthlyVolume,
    });
  } catch (err) {
    console.error("GET /api/accounts-payable error:", err);
    res.status(500).json({ error: String(err) });
  }
});

// ---------------------------------------------------------------------------
// GET /api/accounts-payable/largest?companyCodes=...&fiscalYears=...
// ---------------------------------------------------------------------------
router.get("/api/accounts-payable/largest", async (req: Request, res: Response) => {
  try {
    const companyCodes = parseList(req.query.companyCodes);
    const fiscalYears = parseList(req.query.fiscalYears);
    if (companyCodes.length === 0 && fiscalYears.length === 0) {
      return res.json([]);
    }

    const { where, binds } = buildFilters(companyCodes, fiscalYears);

    const rows = await runQuery(
      `SELECT SUPPLIERINVOICE, INVOICINGPARTY, COMPANYCODE, DOCUMENTCURRENCY,
              INVOICEGROSSAMOUNT, DOCUMENTDATE, POSTINGDATE, SUPPLIERINVOICESTATUS, DOCUMENTHEADERTEXT
         FROM APP_DATA.SUPPLIERINVOICE
       ${where}
       ORDER BY INVOICEGROSSAMOUNT DESC
       LIMIT 50`,
      binds
    );

    res.json(rows);
  } catch (err) {
    console.error("GET /api/accounts-payable/largest error:", err);
    res.status(500).json({ error: String(err) });
  }
});

// ---------------------------------------------------------------------------
// GET /api/accounts-receivable?companyCodes=...&fiscalYears=...
// ---------------------------------------------------------------------------
router.get("/api/accounts-receivable", async (req: Request, res: Response) => {
  try {
    const companyCodes = parseList(req.query.companyCodes);
    const fiscalYears = parseList(req.query.fiscalYears);
    if (companyCodes.length === 0 && fiscalYears.length === 0) {
      return res.json({});
    }

    const { where, binds } = buildFilters(companyCodes, fiscalYears);

    const [kpis, agingBuckets, dsoTrend, topCustomers, paymentPerf, monthlyCollections] =
      await Promise.all([
        // KPIs
        runQuery(
          `SELECT
             SUM(OPENAMOUNT) AS total_open,
             ROUND(AVG(CASE WHEN CLEARINGSTATUS = 'Cleared' THEN DAYS_TO_PAY END), 1) AS avg_dso,
             SUM(CASE WHEN IS_OVERDUE THEN OPENAMOUNT ELSE 0 END) AS overdue_amount,
             ROUND(100.0 * COUNT(CASE WHEN CLEARINGSTATUS = 'Cleared' AND DAYS_TO_PAY <=
               CASE PAYMENTTERMS WHEN 'NET30' THEN 30 WHEN 'NET45' THEN 45
                    WHEN 'NET60' THEN 60 WHEN 'NET90' THEN 90 ELSE 30 END THEN 1 END) /
               NULLIF(COUNT(CASE WHEN CLEARINGSTATUS = 'Cleared' THEN 1 END), 0), 1) AS on_time_pct
           FROM APP_DATA.DT_AR_AGING
           ${where}`,
          binds
        ),
        // Aging Buckets
        runQuery(
          `SELECT AGING_BUCKET, SUM(OPENAMOUNT) AS amount, COUNT(*) AS count
             FROM APP_DATA.DT_AR_AGING
           ${where}${where ? " AND" : " WHERE"} CLEARINGSTATUS != 'Cleared'
           GROUP BY AGING_BUCKET
           ORDER BY AGING_BUCKET`,
          binds
        ),
        // DSO Trend
        runQuery(
          `SELECT TO_CHAR(INVOICEDATE, 'YYYY-MM') AS period,
                  ROUND(AVG(DAYS_TO_PAY), 1) AS avg_dso
             FROM APP_DATA.DT_AR_AGING
           ${where}${where ? " AND" : " WHERE"} CLEARINGSTATUS = 'Cleared'
           GROUP BY TO_CHAR(INVOICEDATE, 'YYYY-MM')
           ORDER BY period`,
          binds
        ),
        // Top Customers
        runQuery(
          `SELECT CUSTOMERNAME,
                  SUM(OPENAMOUNT) AS open_amount,
                  COUNT(*) AS invoice_count
             FROM APP_DATA.DT_AR_AGING
           ${where}${where ? " AND" : " WHERE"} CLEARINGSTATUS != 'Cleared'
           GROUP BY CUSTOMERNAME
           ORDER BY open_amount DESC
           LIMIT 10`,
          binds
        ),
        // Payment Performance
        runQuery(
          `SELECT
             CASE
               WHEN CLEARINGSTATUS = 'Cleared' AND DAYS_TO_PAY <= 30 THEN 'On Time'
               WHEN CLEARINGSTATUS = 'Cleared' AND DAYS_TO_PAY > 30 THEN 'Late'
               WHEN IS_OVERDUE = FALSE AND CLEARINGSTATUS != 'Cleared' THEN 'Not Yet Due'
               ELSE 'Overdue'
             END AS status,
             COUNT(*) AS count,
             SUM(COALESCE(OPENAMOUNT, NETAMOUNT)) AS amount
           FROM APP_DATA.DT_AR_AGING
           ${where}
           GROUP BY status`,
          binds
        ),
        // Monthly Collections
        runQuery(
          `SELECT TO_CHAR(INVOICEDATE, 'YYYY-MM') AS period,
                  COUNT(*) AS count,
                  SUM(NETAMOUNT) AS net_amount,
                  SUM(PAIDAMOUNT) AS paid_amount
             FROM APP_DATA.DT_AR_AGING
           ${where}${where ? " AND" : " WHERE"} CLEARINGSTATUS = 'Cleared'
           GROUP BY TO_CHAR(INVOICEDATE, 'YYYY-MM')
           ORDER BY period`,
          binds
        ),
      ]);

    res.json({
      kpis: kpis[0] ?? {},
      agingBuckets,
      dsoTrend,
      topCustomers,
      paymentPerf,
      monthlyCollections,
    });
  } catch (err) {
    console.error("GET /api/accounts-receivable error:", err);
    res.status(500).json({ error: String(err) });
  }
});

// ---------------------------------------------------------------------------
// GET /api/accounts-receivable/overdue?companyCodes=...&fiscalYears=...
// ---------------------------------------------------------------------------
router.get("/api/accounts-receivable/overdue", async (req: Request, res: Response) => {
  try {
    const companyCodes = parseList(req.query.companyCodes);
    const fiscalYears = parseList(req.query.fiscalYears);
    if (companyCodes.length === 0 && fiscalYears.length === 0) {
      return res.json([]);
    }

    const { where, binds } = buildFilters(companyCodes, fiscalYears);

    const rows = await runQuery(
      `SELECT INVOICEID, CUSTOMERNAME, COMPANYCODE, DOCUMENTCURRENCY,
              INVOICEDATE, DUEDATE, OPENAMOUNT, DAYS_PAST_DUE, AGING_BUCKET, PAYMENTTERMS
         FROM APP_DATA.DT_AR_AGING
       ${where}${where ? " AND" : " WHERE"} IS_OVERDUE = TRUE
       ORDER BY DAYS_PAST_DUE DESC
       LIMIT 50`,
      binds
    );

    res.json(rows);
  } catch (err) {
    console.error("GET /api/accounts-receivable/overdue error:", err);
    res.status(500).json({ error: String(err) });
  }
});

// ---------------------------------------------------------------------------
// GET /api/period-analysis?companyCodes=...&fiscalYears=...
// ---------------------------------------------------------------------------
router.get("/api/period-analysis", async (req: Request, res: Response) => {
  try {
    const companyCodes = parseList(req.query.companyCodes);
    const fiscalYears = parseList(req.query.fiscalYears);
    if (companyCodes.length === 0 && fiscalYears.length === 0) {
      return res.json({});
    }

    const { where, binds } = buildFilters(companyCodes, fiscalYears);

    const [monthlySummary, yoyRevenue, heatmap] = await Promise.all([
      // Monthly Summary
      runQuery(
        `SELECT FISCALYEAR, FISCALPERIOD,
                ABS(SUM(CASE WHEN GLACCOUNT LIKE '4%' AND DEBITCREDITCODE = 'H' THEN AMOUNTINTRANSACTIONCURRENCY ELSE 0 END)) AS revenue,
                ABS(SUM(CASE WHEN (GLACCOUNT LIKE '5%' OR GLACCOUNT LIKE '6%') AND DEBITCREDITCODE = 'S' THEN AMOUNTINTRANSACTIONCURRENCY ELSE 0 END)) AS expenses,
                COUNT(DISTINCT ACCOUNTINGDOCUMENT || COMPANYCODE || FISCALYEAR) AS doc_count
           FROM APP_DATA.OPERATIONALACCTGDOCITEM
         ${where}
         GROUP BY FISCALYEAR, FISCALPERIOD
         ORDER BY FISCALYEAR, FISCALPERIOD`,
        binds
      ),
      // YoY Revenue
      runQuery(
        `SELECT FISCALYEAR, FISCALPERIOD,
                ABS(SUM(AMOUNTINTRANSACTIONCURRENCY)) AS revenue
           FROM APP_DATA.OPERATIONALACCTGDOCITEM
         ${where}${where ? " AND" : " WHERE"} GLACCOUNT LIKE '4%' AND DEBITCREDITCODE = 'H'
         GROUP BY FISCALYEAR, FISCALPERIOD
         ORDER BY FISCALYEAR, FISCALPERIOD`,
        binds
      ),
      // Heatmap: revenue by FISCALYEAR x FISCALPERIOD
      runQuery(
        `SELECT FISCALYEAR, FISCALPERIOD,
                ABS(SUM(AMOUNTINTRANSACTIONCURRENCY)) AS revenue
           FROM APP_DATA.OPERATIONALACCTGDOCITEM
         ${where}${where ? " AND" : " WHERE"} GLACCOUNT LIKE '4%' AND DEBITCREDITCODE = 'H'
         GROUP BY FISCALYEAR, FISCALPERIOD
         ORDER BY FISCALYEAR, FISCALPERIOD`,
        binds
      ),
    ]);

    res.json({ monthlySummary, yoyRevenue, heatmap });
  } catch (err) {
    console.error("GET /api/period-analysis error:", err);
    res.status(500).json({ error: String(err) });
  }
});

// ---------------------------------------------------------------------------
// POST /api/analyst
// ---------------------------------------------------------------------------
router.post("/api/analyst", async (req: Request, res: Response) => {
  try {
    const { messages } = req.body;
    if (!Array.isArray(messages)) {
      return res.status(400).json({ error: "messages array is required" });
    }
    const result = await callCortexAnalyst(messages);
    res.json(result);
  } catch (err) {
    console.error("POST /api/analyst error:", err);
    res.status(500).json({ error: String(err) });
  }
});

// ---------------------------------------------------------------------------
// POST /api/analyst/run-sql — Execute a SQL query from Cortex Analyst
// ---------------------------------------------------------------------------
router.post("/api/analyst/run-sql", async (req: Request, res: Response) => {
  try {
    const { sql } = req.body;
    if (!sql || typeof sql !== "string") {
      return res.status(400).json({ error: "sql string is required" });
    }
    // Safety: only allow SELECT statements
    const trimmed = sql.trim().toUpperCase();
    if (!trimmed.startsWith("SELECT") && !trimmed.startsWith("WITH")) {
      return res.status(400).json({ error: "Only SELECT/WITH queries are allowed" });
    }
    const rows = await runQuery(sql);
    res.json({ rows, columns: rows.length > 0 ? Object.keys(rows[0]) : [] });
  } catch (err) {
    console.error("POST /api/analyst/run-sql error:", err);
    res.status(500).json({ error: String(err) });
  }
});

// ---------------------------------------------------------------------------
// GET /api/lineage — BDC sources & medallion lineage for this app
// ---------------------------------------------------------------------------
function buildLineage(c: any) {
  const p = (sapSystem: string, dataProduct: string, l0Object: string, l1Object: string, rows: unknown, usage: string) =>
    ({ sapSystem, dataProduct, l0Object, l1Object: `SAP_BDC_L1.${l1Object}`, rows, usage });
  return {
    app: "SAP BDC Finance 360",
    database: "SAP_FINANCE_360",
    sourceSystems: ["SAP S/4HANA Finance — Financial Accounting (FI-GL / FI-AP)", "SAP S/4HANA Controlling (CO-CCA / CO-PCA)"],
    summary:
      "Journal entries, supplier invoices and cost / profit center / GL account master data flow from SAP S/4HANA into " +
      "Snowflake as SAP BDC zero-copy data products (L0), exposed as passthrough views (L1), and curated into journal, " +
      "GL balance, P&L, cost center, profit center and AP aging dynamic tables plus a semantic view (L2) that serve this " +
      "app and the SAP Finance 360 Analyst. Accounts receivable aging is a generated demo table.",
    products: [
      p("S/4HANA Finance", "Journal Entry Header", "SAP_BDC_DEMO_JOURNAL_ENTRY_HEADER.BDCCONNECT.JOURNALENTRY", "JOURNALENTRY", c.je, "Document headers, types & posting dates"),
      p("S/4HANA Finance", "Entry View Journal Entry — Operational Acctg Doc Item", "SAP_BDC_DEMO_ENTRY_VIEW_JOURNAL_ENTRY.BDCCONNECT.OPERATIONALACCTGDOCITEM", "OPERATIONALACCTGDOCITEM", c.acctg, "GL line items: revenue, expenses, P&L, GL balances"),
      p("S/4HANA Finance", "Supplier Invoice", "SAP_BDC_DEMO_SUPPLIER_INVOICE.BDCCONNECT.SUPPLIERINVOICE", "SUPPLIERINVOICE", c.supinv, "Accounts payable & AP aging"),
      p("S/4HANA Controlling", "Cost Center", "SAP_BDC_DEMO_COST_CENTER.BDCCONNECT.COSTCENTER", "COSTCENTER", c.costctr, "Cost center / department master"),
      p("S/4HANA Controlling", "Profit Center", "SAP_BDC_DEMO_PROFIT_CENTER.BDCCONNECT.PROFITCENTER", "PROFITCENTER", c.profitctr, "Profit center / segment master"),
      p("S/4HANA Finance", "General Ledger Account", "SAP_BDC_DEMO_GENERAL_LEDGER_ACCOUNT.BDCCONNECT.GENERALLEDGERACCOUNT", "GENERALLEDGERACCOUNT", c.glacct, "GL account master"),
    ],
    curated: [
      { object: "ANALYTICS.DT_JOURNAL_ENTRY_360", rows: c.dt_je },
      { object: "ANALYTICS.DT_AP_AGING", rows: c.dt_ap },
      { object: "ANALYTICS.DT_AR_AGING", rows: c.dt_ar },
    ],
    layers: [
      { name: "SAP Source Systems", tone: "sap", objects: ["SAP S/4HANA Finance (FI-GL / FI-AP)", "SAP S/4HANA Controlling (CO-CCA / CO-PCA)"] },
      { name: "L0 — Bronze (BDC Zero-Copy)", tone: "bronze", objects: ["SAP_BDC_DEMO_JOURNAL_ENTRY_HEADER", "SAP_BDC_DEMO_ENTRY_VIEW_JOURNAL_ENTRY", "SAP_BDC_DEMO_SUPPLIER_INVOICE", "SAP_BDC_DEMO_COST_CENTER", "SAP_BDC_DEMO_PROFIT_CENTER", "SAP_BDC_DEMO_GENERAL_LEDGER_ACCOUNT"] },
      { name: "L1 — Silver (Passthrough Views)", tone: "silver", objects: ["SAP_BDC_L1.JOURNALENTRY", "SAP_BDC_L1.OPERATIONALACCTGDOCITEM", "SAP_BDC_L1.SUPPLIERINVOICE", "SAP_BDC_L1.COSTCENTER", "SAP_BDC_L1.PROFITCENTER", "SAP_BDC_L1.GENERALLEDGERACCOUNT"] },
      { name: "L2 — Gold (Dynamic Tables + Semantic View)", tone: "gold", objects: ["ANALYTICS.DT_JOURNAL_ENTRY_360", "ANALYTICS.DT_GL_BALANCE", "ANALYTICS.DT_PNL_SUMMARY", "ANALYTICS.DT_EXPENSE_BY_COSTCENTER", "ANALYTICS.DT_REVENUE_BY_PROFITCENTER", "ANALYTICS.DT_AP_AGING", "ANALYTICS.DT_AR_AGING", "ANALYTICS.SAP_FINANCE_360 (Semantic View)"] },
      { name: "AI + Application", tone: "ai", objects: ["ANALYTICS.SAP_FINANCE_360_AGENT (Cortex Agent)", "SAP BDC Finance 360 (React)"] },
    ],
    note:
      "Journal, GL, P&L, cost center, profit center and AP figures derive from the BDC data products above; " +
      "AR aging (DT_AR_AGING — customers, invoices, payments) is generated demo data not present in the standard products.",
  };
}

router.get("/api/lineage", async (_req: Request, res: Response) => {
  try {
    const c = (await runQuery(
      `SELECT JE AS je, ACCTG AS acctg, SUPINV AS supinv, COSTCTR AS costctr, PROFITCTR AS profitctr, GLACCT AS glacct, DT_JE AS dt_je, DT_AP AS dt_ap, DT_AR AS dt_ar FROM APP_DATA.LINEAGE_COUNTS`))[0] as any;
    res.json(buildLineage(c));
  } catch (err) {
    console.error("GET /api/lineage error:", err);
    res.status(500).json({ error: String(err) });
  }
});

export default router;
