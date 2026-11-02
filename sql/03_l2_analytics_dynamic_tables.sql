-- =====================================================================
-- L2 (gold) — Analytics dynamic tables
-- Joined / enriched / aggregated analytics-ready objects built on L1.
-- Dynamic tables auto-refresh (TARGET_LAG='DOWNSTREAM'); DT_AR_AGING is a
-- generated table (synthetic AR not present in the standard products).
-- Requires a warehouse named LOAD_WH (or edit the WAREHOUSE clause).
-- =====================================================================

create or replace schema SAP_FINANCE_360.ANALYTICS COMMENT='L2: Dynamic tables - analytics-ready joined/enriched data';

create or replace dynamic table SAP_FINANCE_360.ANALYTICS.DT_AP_AGING(
	COMPANYCODE COMMENT 'SAP company code identifier',
	VENDOR COMMENT 'Vendor/supplier who issued the invoice',
	DOCUMENTCURRENCY COMMENT 'Currency of the invoice document',
	FISCALYEAR COMMENT 'Fiscal year of the invoice',
	DOCUMENTDATE COMMENT 'Date on the supplier invoice document',
	POSTINGDATE COMMENT 'Date the invoice was posted to the ledger',
	INVOICEGROSSAMOUNT COMMENT 'Gross amount of the supplier invoice',
	SUPPLIERINVOICESTATUS COMMENT 'Processing status (P=Posted, A=Approved, C=Cleared, X=Cancelled)',
	DAYS_OUTSTANDING COMMENT 'Number of days between posting date and the latest posting date in the dataset',
	AGING_BUCKET COMMENT 'Aging classification bucket (Current, 31-60 Days, 61-90 Days, 90+ Days)'
) target_lag = 'DOWNSTREAM' refresh_mode = AUTO initialize = ON_CREATE warehouse = LOAD_WH
 as
SELECT
    COMPANYCODE,
    INVOICINGPARTY AS VENDOR,
    DOCUMENTCURRENCY,
    FISCALYEAR,
    DOCUMENTDATE,
    POSTINGDATE,
    INVOICEGROSSAMOUNT,
    SUPPLIERINVOICESTATUS,
    DATEDIFF('day', POSTINGDATE, (SELECT MAX(POSTINGDATE) FROM SAP_FINANCE_360.SAP_BDC_L1.SUPPLIERINVOICE)) AS DAYS_OUTSTANDING,
    CASE
        WHEN DATEDIFF('day', POSTINGDATE, (SELECT MAX(POSTINGDATE) FROM SAP_FINANCE_360.SAP_BDC_L1.SUPPLIERINVOICE)) <= 30 THEN 'Current'
        WHEN DATEDIFF('day', POSTINGDATE, (SELECT MAX(POSTINGDATE) FROM SAP_FINANCE_360.SAP_BDC_L1.SUPPLIERINVOICE)) <= 60 THEN '31-60 Days'
        WHEN DATEDIFF('day', POSTINGDATE, (SELECT MAX(POSTINGDATE) FROM SAP_FINANCE_360.SAP_BDC_L1.SUPPLIERINVOICE)) <= 90 THEN '61-90 Days'
        ELSE '90+ Days'
    END AS AGING_BUCKET
FROM SAP_FINANCE_360.SAP_BDC_L1.SUPPLIERINVOICE
WHERE ISINVOICE = TRUE;
create or replace TABLE SAP_FINANCE_360.ANALYTICS.DT_AR_AGING (
	INVOICEID VARCHAR(16777216),
	CUSTOMER VARCHAR(7),
	CUSTOMERNAME VARCHAR(28),
	COMPANYCODE VARCHAR(4),
	DOCUMENTCURRENCY VARCHAR(3),
	FISCALYEAR VARCHAR(16777216),
	INVOICEDATE DATE,
	DUEDATE DATE,
	PAYMENTTERMS VARCHAR(5),
	NETAMOUNT NUMBER(6,0),
	PAIDAMOUNT NUMBER(6,0),
	OPENAMOUNT NUMBER(6,0),
	PAYMENTDATE DATE,
	CLEARINGSTATUS VARCHAR(7),
	DAYS_PAST_DUE NUMBER(9,0),
	AGING_BUCKET VARCHAR(11),
	IS_OVERDUE BOOLEAN,
	DAYS_TO_PAY NUMBER(9,0)
);
create or replace dynamic table SAP_FINANCE_360.ANALYTICS.DT_EXPENSE_BY_COSTCENTER(
	COMPANYCODE COMMENT 'SAP company code identifier',
	COSTCENTER COMMENT 'Cost center receiving the expense',
	DEPARTMENT COMMENT 'Department name from the cost center master data',
	PROFITCENTER COMMENT 'Associated profit center',
	GLACCOUNT COMMENT 'General ledger expense account (5xxxx or 6xxxx range)',
	FISCALYEAR COMMENT 'Fiscal year of the expense',
	FISCALPERIOD COMMENT 'Fiscal period within the fiscal year',
	EXPENSE_AMOUNT COMMENT 'Total expense amount (absolute value) in company code currency',
	LINE_COUNT COMMENT 'Number of journal entry line items in this group'
) target_lag = 'DOWNSTREAM' refresh_mode = AUTO initialize = ON_CREATE warehouse = LOAD_WH
 as
SELECT
    li.COMPANYCODE,
    li.COSTCENTER,
    cc.DEPARTMENT,
    li.PROFITCENTER,
    li.GLACCOUNT,
    li.FISCALYEAR,
    li.FISCALPERIOD,
    SUM(ABS(li.AMOUNTINCOMPANYCODECURRENCY)) AS EXPENSE_AMOUNT,
    COUNT(*) AS LINE_COUNT
FROM SAP_FINANCE_360.SAP_BDC_L1.OPERATIONALACCTGDOCITEM li
LEFT JOIN SAP_FINANCE_360.SAP_BDC_L1.COSTCENTER cc
    ON li.COSTCENTER = cc.COSTCENTER AND li.COMPANYCODE = cc.COMPANYCODE
WHERE li.DEBITCREDITCODE = 'S'
  AND (li.GLACCOUNT LIKE '5%' OR li.GLACCOUNT LIKE '6%')
  AND li.COSTCENTER != ''
GROUP BY li.COMPANYCODE, li.COSTCENTER, cc.DEPARTMENT, li.PROFITCENTER, li.GLACCOUNT, li.FISCALYEAR, li.FISCALPERIOD;
create or replace dynamic table SAP_FINANCE_360.ANALYTICS.DT_GL_BALANCE(
	COMPANYCODE COMMENT 'SAP company code identifier',
	GLACCOUNT COMMENT 'General ledger account number',
	FISCALYEAR COMMENT 'Fiscal year of the balance',
	FISCALPERIOD COMMENT 'Fiscal period within the fiscal year',
	DEBITCREDITCODE COMMENT 'Debit (S) or Credit (H) indicator',
	AMOUNT COMMENT 'Aggregated amount in company code currency',
	LINE_COUNT COMMENT 'Number of journal entry line items in this group'
) target_lag = 'DOWNSTREAM' refresh_mode = AUTO initialize = ON_CREATE warehouse = LOAD_WH
 as
SELECT
    COMPANYCODE,
    GLACCOUNT,
    FISCALYEAR,
    FISCALPERIOD,
    DEBITCREDITCODE,
    SUM(AMOUNTINCOMPANYCODECURRENCY) AS AMOUNT,
    COUNT(*) AS LINE_COUNT
FROM SAP_FINANCE_360.SAP_BDC_L1.OPERATIONALACCTGDOCITEM
GROUP BY COMPANYCODE, GLACCOUNT, FISCALYEAR, FISCALPERIOD, DEBITCREDITCODE;
create or replace dynamic table SAP_FINANCE_360.ANALYTICS.DT_JOURNAL_ENTRY_360(
	COMPANYCODE COMMENT 'SAP company code identifier',
	ACCOUNTINGDOCUMENT COMMENT 'Unique accounting document number',
	FISCALYEAR COMMENT 'Fiscal year of the journal entry',
	ACCOUNTINGDOCUMENTITEM COMMENT 'Line item number within the accounting document',
	GLACCOUNT COMMENT 'General ledger account number',
	POSTINGDATE COMMENT 'Date the entry was posted to the ledger',
	AMOUNTINCOMPANYCODECURRENCY COMMENT 'Amount in company code (local) currency',
	AMOUNTINTRANSACTIONCURRENCY COMMENT 'Amount in the original transaction currency',
	DEBITCREDITCODE COMMENT 'Debit (S) or Credit (H) indicator',
	COSTCENTER COMMENT 'Cost center for expense allocation',
	PROFITCENTER COMMENT 'Profit center for profitability reporting',
	BUSINESSAREA COMMENT 'Business area for internal reporting segmentation',
	SEGMENT COMMENT 'Segment for external segment reporting',
	FUNCTIONALAREA COMMENT 'Functional area for government reporting',
	CUSTOMER COMMENT 'Customer account number',
	SUPPLIER COMMENT 'Supplier/vendor account number',
	COMPANYCODECURRENCY COMMENT 'Local currency of the company code',
	TRANSACTIONCURRENCY COMMENT 'Currency of the original transaction',
	DOCUMENTITEMTEXT COMMENT 'Free-text description of the line item',
	ACCOUNTINGDOCUMENTTYPE COMMENT 'Type of accounting document (e.g. SA, AB, KR)',
	FISCALPERIOD COMMENT 'Fiscal period within the fiscal year',
	CONTROLLINGAREA COMMENT 'Controlling area for cost accounting',
	DOCUMENTDATE COMMENT 'Date on the original source document',
	ISREVERSAL COMMENT 'Whether this document is a reversal entry',
	ISREVERSED COMMENT 'Whether this document has been reversed',
	ISBALANCESHEETACCOUNT COMMENT 'Whether the GL account is a balance sheet account',
	ISPROFITLOSSACCOUNT COMMENT 'Whether the GL account is a profit and loss account',
	GLACCOUNTTYPE COMMENT 'GL account type code',
	GLACCOUNTGROUP COMMENT 'GL account group classification',
	COSTCENTER_DEPARTMENT COMMENT 'Department name from the cost center master data',
	PROFITCENTER_SEGMENT COMMENT 'Segment name from the profit center master data'
) target_lag = 'DOWNSTREAM' refresh_mode = AUTO initialize = ON_CREATE warehouse = LOAD_WH
 as
SELECT
    li.COMPANYCODE,
    li.ACCOUNTINGDOCUMENT,
    li.FISCALYEAR,
    li.ACCOUNTINGDOCUMENTITEM,
    li.GLACCOUNT,
    li.POSTINGDATE,
    li.AMOUNTINCOMPANYCODECURRENCY,
    li.AMOUNTINTRANSACTIONCURRENCY,
    li.DEBITCREDITCODE,
    li.COSTCENTER,
    li.PROFITCENTER,
    li.BUSINESSAREA,
    li.SEGMENT,
    li.FUNCTIONALAREA,
    li.CUSTOMER,
    li.SUPPLIER,
    li.COMPANYCODECURRENCY,
    li.TRANSACTIONCURRENCY,
    li.DOCUMENTITEMTEXT,
    li.ACCOUNTINGDOCUMENTTYPE,
    li.FISCALPERIOD,
    li.CONTROLLINGAREA,
    je.DOCUMENTDATE,
    je.ISREVERSAL,
    je.ISREVERSED,
    gl.ISBALANCESHEETACCOUNT,
    gl.ISPROFITLOSSACCOUNT,
    gl.GLACCOUNTTYPE,
    gl.GLACCOUNTGROUP,
    cc.DEPARTMENT AS COSTCENTER_DEPARTMENT,
    pc.SEGMENT AS PROFITCENTER_SEGMENT
FROM SAP_FINANCE_360.SAP_BDC_L1.OPERATIONALACCTGDOCITEM li
LEFT JOIN SAP_FINANCE_360.SAP_BDC_L1.JOURNALENTRY je
    ON li.COMPANYCODE = je.COMPANYCODE
    AND li.FISCALYEAR = je.FISCALYEAR
    AND li.ACCOUNTINGDOCUMENT = je.ACCOUNTINGDOCUMENT
LEFT JOIN SAP_FINANCE_360.SAP_BDC_L1.GENERALLEDGERACCOUNT gl
    ON li.GLACCOUNT = gl.GLACCOUNT
LEFT JOIN SAP_FINANCE_360.SAP_BDC_L1.COSTCENTER cc
    ON li.COSTCENTER = cc.COSTCENTER
    AND li.COMPANYCODE = cc.COMPANYCODE
LEFT JOIN SAP_FINANCE_360.SAP_BDC_L1.PROFITCENTER pc
    ON li.PROFITCENTER = pc.PROFITCENTER
    AND li.COMPANYCODE = pc.COMPANYCODE;
create or replace dynamic table SAP_FINANCE_360.ANALYTICS.DT_PNL_SUMMARY(
	COMPANYCODE COMMENT 'SAP company code identifier',
	FISCALYEAR COMMENT 'Fiscal year of the P&L period',
	FISCALPERIOD COMMENT 'Fiscal period within the fiscal year',
	COMPANYCODECURRENCY COMMENT 'Local currency of the company code',
	REVENUE COMMENT 'Total revenue from GL accounts starting with 4 (credit side)',
	EXPENSES COMMENT 'Total expenses from GL accounts starting with 5 or 6 (debit side)',
	NET_INCOME COMMENT 'Net income calculated as Revenue minus Expenses',
	DOCUMENT_COUNT COMMENT 'Count of distinct accounting documents in the period',
	LINE_ITEM_COUNT COMMENT 'Total number of journal entry line items in the period'
) target_lag = 'DOWNSTREAM' refresh_mode = AUTO initialize = ON_CREATE warehouse = LOAD_WH
 as
SELECT
    li.COMPANYCODE,
    li.FISCALYEAR,
    li.FISCALPERIOD,
    li.COMPANYCODECURRENCY,
    SUM(CASE WHEN li.GLACCOUNT LIKE '4%' AND li.DEBITCREDITCODE = 'H'
             THEN ABS(li.AMOUNTINCOMPANYCODECURRENCY) ELSE 0 END) AS REVENUE,
    SUM(CASE WHEN (li.GLACCOUNT LIKE '5%' OR li.GLACCOUNT LIKE '6%') AND li.DEBITCREDITCODE = 'S'
             THEN ABS(li.AMOUNTINCOMPANYCODECURRENCY) ELSE 0 END) AS EXPENSES,
    SUM(CASE WHEN li.GLACCOUNT LIKE '4%' AND li.DEBITCREDITCODE = 'H'
             THEN ABS(li.AMOUNTINCOMPANYCODECURRENCY) ELSE 0 END)
    - SUM(CASE WHEN (li.GLACCOUNT LIKE '5%' OR li.GLACCOUNT LIKE '6%') AND li.DEBITCREDITCODE = 'S'
             THEN ABS(li.AMOUNTINCOMPANYCODECURRENCY) ELSE 0 END) AS NET_INCOME,
    COUNT(DISTINCT li.ACCOUNTINGDOCUMENT) AS DOCUMENT_COUNT,
    COUNT(*) AS LINE_ITEM_COUNT
FROM SAP_FINANCE_360.SAP_BDC_L1.OPERATIONALACCTGDOCITEM li
GROUP BY li.COMPANYCODE, li.FISCALYEAR, li.FISCALPERIOD, li.COMPANYCODECURRENCY;
create or replace dynamic table SAP_FINANCE_360.ANALYTICS.DT_REVENUE_BY_PROFITCENTER(
	COMPANYCODE COMMENT 'SAP company code identifier',
	PROFITCENTER COMMENT 'Profit center generating the revenue',
	SEGMENT COMMENT 'Segment for external reporting from profit center master',
	GLACCOUNT COMMENT 'General ledger revenue account (4xxxx range)',
	FISCALYEAR COMMENT 'Fiscal year of the revenue',
	FISCALPERIOD COMMENT 'Fiscal period within the fiscal year',
	REVENUE_AMOUNT COMMENT 'Total revenue amount (absolute value) in company code currency',
	LINE_COUNT COMMENT 'Number of journal entry line items in this group'
) target_lag = 'DOWNSTREAM' refresh_mode = AUTO initialize = ON_CREATE warehouse = LOAD_WH
 as
SELECT
    li.COMPANYCODE,
    li.PROFITCENTER,
    pc.SEGMENT,
    li.GLACCOUNT,
    li.FISCALYEAR,
    li.FISCALPERIOD,
    SUM(ABS(li.AMOUNTINCOMPANYCODECURRENCY)) AS REVENUE_AMOUNT,
    COUNT(*) AS LINE_COUNT
FROM SAP_FINANCE_360.SAP_BDC_L1.OPERATIONALACCTGDOCITEM li
LEFT JOIN SAP_FINANCE_360.SAP_BDC_L1.PROFITCENTER pc
    ON li.PROFITCENTER = pc.PROFITCENTER AND li.COMPANYCODE = pc.COMPANYCODE
WHERE li.DEBITCREDITCODE = 'H'
  AND li.GLACCOUNT LIKE '4%'
GROUP BY li.COMPANYCODE, li.PROFITCENTER, pc.SEGMENT, li.GLACCOUNT, li.FISCALYEAR, li.FISCALPERIOD;

-- ------------------------------------------- lineage snapshot (for Native App,
-- which bundles L2 only and cannot see the L1 / L0 shares)
create or replace table SAP_FINANCE_360.ANALYTICS.LINEAGE_COUNTS as
select
  (select count(*) from SAP_FINANCE_360.SAP_BDC_L1.JOURNALENTRY) as JE,
  (select count(*) from SAP_FINANCE_360.SAP_BDC_L1.OPERATIONALACCTGDOCITEM) as ACCTG,
  (select count(*) from SAP_FINANCE_360.SAP_BDC_L1.SUPPLIERINVOICE) as SUPINV,
  (select count(*) from SAP_FINANCE_360.SAP_BDC_L1.COSTCENTER) as COSTCTR,
  (select count(*) from SAP_FINANCE_360.SAP_BDC_L1.PROFITCENTER) as PROFITCTR,
  (select count(*) from SAP_FINANCE_360.SAP_BDC_L1.GENERALLEDGERACCOUNT) as GLACCT,
  (select count(*) from SAP_FINANCE_360.ANALYTICS.DT_JOURNAL_ENTRY_360) as DT_JE,
  (select count(*) from SAP_FINANCE_360.ANALYTICS.DT_AP_AGING) as DT_AP,
  (select count(*) from SAP_FINANCE_360.ANALYTICS.DT_AR_AGING) as DT_AR;
