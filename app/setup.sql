-- =====================================================================
-- SAP Finance 360 Native App — SELF-CONTAINED setup script
-- Data is bundled in the package (SHARED_DATA). No consumer references.
-- Powers the SAP_FINANCE_360 Cortex Analyst semantic view (the same
-- model behind the account-level SAP_FINANCE_360_AGENT).
-- =====================================================================

CREATE APPLICATION ROLE IF NOT EXISTS app_public;

-- ---------------------------------------------------------------------
-- config schema: settings consumed by the container (e.g. semantic view)
-- ---------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS config;
GRANT USAGE ON SCHEMA config TO APPLICATION ROLE app_public;
CREATE TABLE IF NOT EXISTS config.settings(key STRING, value STRING);

-- ---------------------------------------------------------------------
-- app_data schema: views over the bundled data + Cortex Analyst semantic view
-- ---------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS app_data;
GRANT USAGE ON SCHEMA app_data TO APPLICATION ROLE app_public;

CREATE OR REPLACE VIEW app_data.JOURNALENTRY AS SELECT * FROM shared_data.JOURNALENTRY;
GRANT SELECT ON VIEW app_data.JOURNALENTRY TO APPLICATION ROLE app_public;
CREATE OR REPLACE VIEW app_data.OPERATIONALACCTGDOCITEM AS SELECT * FROM shared_data.OPERATIONALACCTGDOCITEM;
GRANT SELECT ON VIEW app_data.OPERATIONALACCTGDOCITEM TO APPLICATION ROLE app_public;
CREATE OR REPLACE VIEW app_data.SUPPLIERINVOICE AS SELECT * FROM shared_data.SUPPLIERINVOICE;
GRANT SELECT ON VIEW app_data.SUPPLIERINVOICE TO APPLICATION ROLE app_public;
CREATE OR REPLACE VIEW app_data.DT_AP_AGING AS SELECT * FROM shared_data.DT_AP_AGING;
GRANT SELECT ON VIEW app_data.DT_AP_AGING TO APPLICATION ROLE app_public;
CREATE OR REPLACE VIEW app_data.DT_AR_AGING AS SELECT * FROM shared_data.DT_AR_AGING;
GRANT SELECT ON VIEW app_data.DT_AR_AGING TO APPLICATION ROLE app_public;
CREATE OR REPLACE VIEW app_data.DT_EXPENSE_BY_COSTCENTER AS SELECT * FROM shared_data.DT_EXPENSE_BY_COSTCENTER;
GRANT SELECT ON VIEW app_data.DT_EXPENSE_BY_COSTCENTER TO APPLICATION ROLE app_public;
CREATE OR REPLACE VIEW app_data.DT_REVENUE_BY_PROFITCENTER AS SELECT * FROM shared_data.DT_REVENUE_BY_PROFITCENTER;
GRANT SELECT ON VIEW app_data.DT_REVENUE_BY_PROFITCENTER TO APPLICATION ROLE app_public;
CREATE OR REPLACE VIEW app_data.DT_JOURNAL_ENTRY_360 AS SELECT * FROM shared_data.DT_JOURNAL_ENTRY_360;
GRANT SELECT ON VIEW app_data.DT_JOURNAL_ENTRY_360 TO APPLICATION ROLE app_public;
CREATE OR REPLACE VIEW app_data.LINEAGE_COUNTS AS SELECT * FROM shared_data.LINEAGE_COUNTS;
GRANT SELECT ON VIEW app_data.LINEAGE_COUNTS TO APPLICATION ROLE app_public;

-- Semantic view for Cortex Analyst, built over the bundled APP_DATA views.
-- Mirrors SAP_FINANCE_360.ANALYTICS.SAP_FINANCE_360 (SAP_FINANCE_360_AGENT).
CREATE OR REPLACE SEMANTIC VIEW app_data.SAP_FINANCE_360
  tables (
    JOURNAL as APP_DATA.DT_JOURNAL_ENTRY_360 comment='Journal entry line items with full SAP dimensions',
    EXPENSE as APP_DATA.DT_EXPENSE_BY_COSTCENTER comment='Expenses by cost center and department',
    REVENUE as APP_DATA.DT_REVENUE_BY_PROFITCENTER comment='Revenue by profit center and segment',
    AR as APP_DATA.DT_AR_AGING comment='Accounts receivable aging with DSO and payment performance'
  )
  facts (
    JOURNAL.AMOUNTINTRANSACTIONCURRENCY as AMOUNTINTRANSACTIONCURRENCY comment='Transaction amount in currency',
    EXPENSE.EXPENSE_AMOUNT as EXPENSE_AMOUNT comment='Expense amount',
    REVENUE.REVENUE_AMOUNT as REVENUE_AMOUNT comment='Revenue amount',
    AR.OPENAMOUNT as OPENAMOUNT comment='Open outstanding amount',
    AR.DAYS_TO_PAY as DAYS_TO_PAY comment='Days to pay'
  )
  dimensions (
    JOURNAL.COMPANYCODE as COMPANYCODE comment='SAP company code (1000=US, 2100=DE, 5000=JP)',
    JOURNAL.FISCALYEAR as FISCALYEAR comment='Fiscal year',
    JOURNAL.FISCALPERIOD as FISCALPERIOD comment='Fiscal period within the year',
    JOURNAL.GLACCOUNT as GLACCOUNT comment='General ledger account number',
    JOURNAL.COSTCENTER as COSTCENTER comment='Cost center code',
    JOURNAL.PROFITCENTER as PROFITCENTER comment='Profit center code',
    JOURNAL.SEGMENT as SEGMENT comment='Business segment',
    JOURNAL.ACCOUNTINGDOCUMENTTYPE as ACCOUNTINGDOCUMENTTYPE comment='Document type (DR=Customer Invoice, KR=Vendor Invoice, SA=GL Posting)',
    JOURNAL.DEBITCREDITCODE as DEBITCREDITCODE comment='S=Debit, H=Credit',
    JOURNAL.POSTINGDATE as POSTINGDATE comment='Posting date',
    JOURNAL.COSTCENTER_DEPARTMENT as COSTCENTER_DEPARTMENT comment='Department mapped from cost center',
    EXPENSE.EXP_COSTCENTER as COSTCENTER comment='Cost center code',
    EXPENSE.EXP_COMPANYCODE as COMPANYCODE comment='Company code',
    EXPENSE.EXP_FISCALYEAR as FISCALYEAR comment='Fiscal year',
    EXPENSE.DEPARTMENT as DEPARTMENT comment='Department name',
    REVENUE.REV_PROFITCENTER as PROFITCENTER comment='Profit center code',
    REVENUE.REV_COMPANYCODE as COMPANYCODE comment='Company code',
    REVENUE.REV_FISCALYEAR as FISCALYEAR comment='Fiscal year',
    REVENUE.REV_SEGMENT as SEGMENT comment='Business segment',
    AR.CUSTOMERNAME as CUSTOMERNAME comment='Customer name',
    AR.AR_COMPANYCODE as COMPANYCODE comment='Company code',
    AR.AR_FISCALYEAR as FISCALYEAR comment='Fiscal year',
    AR.AGING_BUCKET as AGING_BUCKET comment='Aging classification (Current, 1-30 Days, 31-60 Days, etc.)',
    AR.CLEARINGSTATUS as CLEARINGSTATUS comment='Payment status (Cleared, Current, Overdue)'
  )
  metrics (
    JOURNAL.TOTAL_AMOUNT as SUM(JOURNAL.AMOUNTINTRANSACTIONCURRENCY) comment='Sum of transaction amounts',
    JOURNAL.REVENUE as SUM(CASE WHEN JOURNAL.GLACCOUNT LIKE '4%' AND JOURNAL.DEBITCREDITCODE = 'H' THEN ABS(JOURNAL.AMOUNTINTRANSACTIONCURRENCY) ELSE 0 END) comment='Total revenue (GL accounts starting with 4)',
    JOURNAL.EXPENSES as SUM(CASE WHEN (JOURNAL.GLACCOUNT LIKE '5%' OR JOURNAL.GLACCOUNT LIKE '6%') AND JOURNAL.DEBITCREDITCODE = 'S' THEN JOURNAL.AMOUNTINTRANSACTIONCURRENCY ELSE 0 END) comment='Total expenses (GL accounts starting with 5 or 6)',
    JOURNAL.DOCUMENT_COUNT as COUNT(DISTINCT JOURNAL.ACCOUNTINGDOCUMENT || JOURNAL.COMPANYCODE || JOURNAL.FISCALYEAR) comment='Number of unique documents',
    EXPENSE.TOTAL_EXPENSE as SUM(EXPENSE.EXPENSE_AMOUNT) comment='Total expense amount',
    REVENUE.TOTAL_REVENUE as SUM(REVENUE.REVENUE_AMOUNT) comment='Total revenue amount',
    AR.TOTAL_OPEN as SUM(AR.OPENAMOUNT) comment='Total open/outstanding amount',
    AR.AVG_DSO as AVG(AR.DAYS_TO_PAY) comment='Average days sales outstanding',
    AR.INVOICE_COUNT as COUNT(AR.OPENAMOUNT) comment='Number of AR invoices'
  )
  comment='SAP BDC Finance 360 semantic model covering journal entries, cost centers, profit centers, and accounts receivable aging (bundled with the Native App).';
GRANT SELECT ON SEMANTIC VIEW app_data.SAP_FINANCE_360 TO APPLICATION ROLE app_public;

-- Record the semantic view FQN for the container's Analyst page.
DELETE FROM config.settings WHERE key = 'semantic_view';
INSERT INTO config.settings(key, value)
  SELECT 'semantic_view', CURRENT_DATABASE() || '.APP_DATA.SAP_FINANCE_360';

-- ---------------------------------------------------------------------
-- services schema (non-versioned): holds the SPCS service
-- ---------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS services;
GRANT USAGE ON SCHEMA services TO APPLICATION ROLE app_public;

-- ---------------------------------------------------------------------
-- core schema (versioned): lifecycle + service management
-- ---------------------------------------------------------------------
CREATE OR ALTER VERSIONED SCHEMA core;
GRANT USAGE ON SCHEMA core TO APPLICATION ROLE app_public;

CREATE OR REPLACE PROCEDURE core.version_init()
  RETURNS STRING
  LANGUAGE SQL
  EXECUTE AS OWNER
AS $$
DECLARE
  pool_name VARCHAR;
  wh_name VARCHAR;
  svc_count INTEGER;
BEGIN
  pool_name := (SELECT CURRENT_DATABASE()) || '_POOL';
  wh_name   := (SELECT CURRENT_DATABASE()) || '_WH';

  CREATE COMPUTE POOL IF NOT EXISTS IDENTIFIER(:pool_name)
    MIN_NODES = 1 MAX_NODES = 1 INSTANCE_FAMILY = CPU_X64_XS
    AUTO_RESUME = TRUE AUTO_SUSPEND_SECS = 300;

  CREATE WAREHOUSE IF NOT EXISTS IDENTIFIER(:wh_name)
    WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

  SHOW SERVICES LIKE 'FINANCE_360_SERVICE' IN SCHEMA services;
  svc_count := (SELECT COUNT(*) FROM TABLE(RESULT_SCAN(LAST_QUERY_ID())));

  IF (:svc_count = 0) THEN
    CREATE SERVICE services.finance_360_service
      IN COMPUTE POOL IDENTIFIER(:pool_name)
      FROM SPECIFICATION_FILE = '/service_spec.yml'
      MIN_INSTANCES = 1 MAX_INSTANCES = 1;
    GRANT USAGE ON SERVICE services.finance_360_service TO APPLICATION ROLE app_public;
    GRANT SERVICE ROLE services.finance_360_service!finance_360_role TO APPLICATION ROLE app_public;
  ELSE
    ALTER SERVICE services.finance_360_service FROM SPECIFICATION_FILE = '/service_spec.yml';
    CALL SYSTEM$WAIT_FOR_SERVICES(600, 'services.finance_360_service');
  END IF;
  RETURN 'version_init ok';
END;
$$;
GRANT USAGE ON PROCEDURE core.version_init() TO APPLICATION ROLE app_public;

CREATE OR REPLACE PROCEDURE core.suspend_service()
  RETURNS STRING LANGUAGE SQL EXECUTE AS OWNER
AS $$ BEGIN ALTER SERVICE services.finance_360_service SUSPEND; RETURN 'Service suspended'; END; $$;
GRANT USAGE ON PROCEDURE core.suspend_service() TO APPLICATION ROLE app_public;

CREATE OR REPLACE PROCEDURE core.resume_service()
  RETURNS STRING LANGUAGE SQL EXECUTE AS OWNER
AS $$ BEGIN ALTER SERVICE services.finance_360_service RESUME; RETURN 'Service resumed'; END; $$;
GRANT USAGE ON PROCEDURE core.resume_service() TO APPLICATION ROLE app_public;

CREATE OR REPLACE PROCEDURE core.get_service_status()
  RETURNS STRING LANGUAGE SQL EXECUTE AS OWNER
AS $$ DECLARE status VARCHAR;
BEGIN CALL SYSTEM$GET_SERVICE_STATUS('services.finance_360_service') INTO :status; RETURN :status; END; $$;
GRANT USAGE ON PROCEDURE core.get_service_status() TO APPLICATION ROLE app_public;

CREATE OR REPLACE PROCEDURE core.get_service_logs(instance_id STRING, container_name STRING)
  RETURNS STRING LANGUAGE SQL EXECUTE AS OWNER
AS $$ DECLARE logs VARCHAR;
BEGIN CALL SYSTEM$GET_SERVICE_LOGS('services.finance_360_service', :instance_id, :container_name, 200) INTO :logs; RETURN :logs; END; $$;
GRANT USAGE ON PROCEDURE core.get_service_logs(STRING, STRING) TO APPLICATION ROLE app_public;

CREATE OR REPLACE PROCEDURE core.app_url()
  RETURNS STRING LANGUAGE SQL EXECUTE AS OWNER
AS $$ DECLARE url VARCHAR;
BEGIN
  SHOW ENDPOINTS IN SERVICE services.finance_360_service;
  SELECT "ingress_url" INTO :url FROM TABLE(RESULT_SCAN(LAST_QUERY_ID())) WHERE "name" = 'finance360';
  RETURN :url;
END; $$;
GRANT USAGE ON PROCEDURE core.app_url() TO APPLICATION ROLE app_public;

CREATE OR REPLACE PROCEDURE core.selftest()
  RETURNS STRING LANGUAGE SQL EXECUTE AS OWNER
AS $$ DECLARE ar_rows INTEGER; je_rows INTEGER;
BEGIN
  SELECT COUNT(*) INTO :ar_rows FROM app_data.DT_AR_AGING;
  SELECT COUNT(*) INTO :je_rows FROM app_data.JOURNALENTRY;
  RETURN 'bundled data OK — DT_AR_AGING=' || :ar_rows || ' rows, JOURNALENTRY=' || :je_rows || ' rows';
END; $$;
GRANT USAGE ON PROCEDURE core.selftest() TO APPLICATION ROLE app_public;
