#!/usr/bin/env python3
"""Extract every figure the Finance 360 deliverables quote, with its provenance.

Nothing in the kit, deck or docs is transcribed by hand. Each figure is pulled
live from the account here and stamped with the query that produced it, so a
document cannot drift from what the platform actually contains — and a reader can
re-run the stated source to check any number.

Writes /tmp/finance_facts.json (the handoff the docx and pptx builders read).

Usage:
    python3 tools/finance_facts.py                # extract and write
    python3 tools/finance_facts.py --print        # extract and show the table
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
import tomllib

import snowflake.connector

CONN = "dfreriksdemo"
DB = "SAP_FINANCE_360"
APP_DB = "FINANCE_360_APP"
OUT = pathlib.Path("/tmp/finance_facts.json")
REPO = "https://github.com/sfc-gh-dfreriks/sap-bdc-finance-360"
SIDEBAR = (pathlib.Path.home() / "Documents" / "SAP" / "SAP Skills"
           / "finance_dashboard_react" / "client" / "src" / "components" / "Sidebar.tsx")
API_ROUTES = (pathlib.Path.home() / "Documents" / "SAP" / "SAP Skills"
              / "finance_dashboard_react" / "server" / "src" / "routes" / "api.ts")
ANALYST_STAGE = "SAP_FINANCE_360.SEMANTIC.SEMANTIC_MODELS"
ANALYST_MODEL = "finance_360.semantic.yaml"


def conn_params(name: str) -> dict:
    path = pathlib.Path.home() / ".snowflake" / "connections.toml"
    cfg = tomllib.loads(path.read_text())
    if name not in cfg:
        sys.exit(f"connection {name!r} not in {path}")
    c = dict(cfg[name])
    if "private_key_path" in c:
        c["private_key_file"] = str(pathlib.Path(c.pop("private_key_path")).expanduser())
    c.pop("database", None)
    c.pop("schema", None)
    return c


class Facts:
    """Collects values together with the source that produced each one."""

    def __init__(self, cur):
        self.cur = cur
        self.data: dict = {}
        self.provenance: dict = {}

    def sql_one(self, key: str, sql: str, source: str):
        self.cur.execute(sql)
        row = self.cur.fetchone()
        val = row[0] if row and len(row) == 1 else (list(row) if row else None)
        self.data[key] = self._clean(val)
        self.provenance[key] = source
        return self.data[key]

    def sql_rows(self, key: str, sql: str, source: str):
        self.cur.execute(sql)
        cols = [d[0] for d in self.cur.description]
        self.data[key] = [{c: self._clean(v) for c, v in zip(cols, r)}
                          for r in self.cur.fetchall()]
        self.provenance[key] = source
        return self.data[key]

    def put(self, key, value, source):
        self.data[key] = self._clean(value)
        self.provenance[key] = source
        return value

    @staticmethod
    def _clean(v):
        if isinstance(v, (dt.date, dt.datetime)):
            return v.isoformat()[:10]
        if isinstance(v, list):
            return [Facts._clean(x) for x in v]
        if hasattr(v, "normalize"):  # Decimal
            return float(v)
        return v


def collect(cur) -> Facts:
    f = Facts(cur)
    IS = f"{DB}.INFORMATION_SCHEMA"

    # ---- platform shape -----------------------------------------------------
    f.sql_one("schemas", f"""
        SELECT COUNT(*) FROM {IS}.SCHEMATA
        WHERE SCHEMA_NAME NOT IN ('INFORMATION_SCHEMA','PUBLIC')""",
        "INFORMATION_SCHEMA.SCHEMATA")
    f.sql_one("l1_views", f"""
        SELECT COUNT(*) FROM {IS}.TABLES
        WHERE TABLE_SCHEMA='SAP_BDC_L1' AND TABLE_TYPE='VIEW'""",
        "INFORMATION_SCHEMA.TABLES, SAP_BDC_L1")
    f.sql_rows("l1_objects", f"""
        SELECT TABLE_NAME FROM {IS}.TABLES
        WHERE TABLE_SCHEMA='SAP_BDC_L1' ORDER BY 1""",
        "INFORMATION_SCHEMA.TABLES, SAP_BDC_L1")
    f.sql_rows("analytics_objects", f"""
        SELECT TABLE_NAME, ROW_COUNT FROM {IS}.TABLES
        WHERE TABLE_SCHEMA='ANALYTICS' ORDER BY ROW_COUNT DESC""",
        "INFORMATION_SCHEMA.TABLES, ANALYTICS")
    f.put("analytics_rows", sum(o["ROW_COUNT"] or 0 for o in f.data["analytics_objects"]),
          "sum of ROW_COUNT over ANALYTICS")

    # A DT_ prefix is not proof of a dynamic table: DT_AR_AGING is a plain table.
    cur.execute(f"SHOW DYNAMIC TABLES IN DATABASE {DB}")
    dts = sorted(r[1] for r in cur.fetchall())
    f.put("dynamic_tables", dts, "SHOW DYNAMIC TABLES")
    f.put("dynamic_table_count", len(dts), "SHOW DYNAMIC TABLES")
    f.put("dt_prefixed_not_dynamic",
          sorted({o["TABLE_NAME"] for o in f.data["analytics_objects"]
                  if o["TABLE_NAME"].startswith("DT_")} - set(dts)),
          "ANALYTICS DT_* names minus SHOW DYNAMIC TABLES")

    # ---- semantic views -----------------------------------------------------
    svs = []
    cur.execute(f"SHOW SEMANTIC VIEWS IN DATABASE {DB}")
    cols = [d[0] for d in cur.description]
    for r in cur.fetchall():
        d = dict(zip(cols, r))
        svs.append(f"{DB}.{d['schema_name']}.{d['name']}")
    f.put("semantic_views", svs, "SHOW SEMANTIC VIEWS")

    detail = {}
    for sv in svs:
        cur.execute(f"DESCRIBE SEMANTIC VIEW {sv}")
        c2 = [d[0] for d in cur.description]
        rows = cur.fetchall()
        kinds: dict = {}
        for r in rows:
            k = str(r[c2.index("object_kind")])
            kinds[k] = kinds.get(k, 0) + 1
        detail[sv] = {
            "tables": kinds.get("TABLE", 0),
            "dimensions": kinds.get("DIMENSION", 0),
            "facts": kinds.get("FACT", 0),
            "metrics": kinds.get("METRIC", 0),
            "relationships": kinds.get("RELATIONSHIP", 0),
            "table_names": sorted({r[c2.index("object_name")] for r in rows
                                   if r[c2.index("object_kind")] == "TABLE"}),
        }
    f.put("semantic_view_detail", detail, "DESCRIBE SEMANTIC VIEW")

    # ---- data window --------------------------------------------------------
    # Deliberately per-table: the three fact tables do NOT share a window, and a
    # single "data window" sentence would be wrong.
    windows = {}
    for tbl, col in (("DT_JOURNAL_ENTRY_360", "POSTINGDATE"),
                     ("DT_AP_AGING", "POSTINGDATE"),
                     ("DT_AR_AGING", "INVOICEDATE")):
        cur.execute(f"SELECT MIN({col}), MAX({col}), COUNT(*) FROM {DB}.ANALYTICS.{tbl}")
        lo, hi, n = cur.fetchone()
        windows[tbl] = {"column": col, "min": Facts._clean(lo),
                        "max": Facts._clean(hi), "rows": n}
    f.put("data_windows", windows, f"MIN/MAX over {DB}.ANALYTICS fact tables")

    # ---- business figures ---------------------------------------------------
    f.sql_one("company_codes",
              f"SELECT COUNT(DISTINCT COMPANYCODE) FROM {DB}.ANALYTICS.DT_JOURNAL_ENTRY_360",
              "COUNT DISTINCT COMPANYCODE, DT_JOURNAL_ENTRY_360")
    f.sql_rows("pnl_by_year", f"""
        SELECT FISCALYEAR,
               SUM(REVENUE) AS REVENUE, SUM(EXPENSES) AS EXPENSES,
               SUM(NET_INCOME) AS NET_INCOME, SUM(DOCUMENT_COUNT) AS DOCS
        FROM {DB}.ANALYTICS.DT_PNL_SUMMARY GROUP BY 1 ORDER BY 1""",
        "SUM over DT_PNL_SUMMARY (pre-aggregated, already signed)")
    f.sql_rows("ap_aging", f"""
        SELECT AGING_BUCKET, COUNT(*) AS INVOICES, SUM(INVOICEGROSSAMOUNT) AS GROSS
        FROM {DB}.ANALYTICS.DT_AP_AGING GROUP BY 1 ORDER BY 2 DESC""",
        "GROUP BY AGING_BUCKET, DT_AP_AGING")
    f.sql_rows("ar_aging", f"""
        SELECT AGING_BUCKET, COUNT(*) AS INVOICES,
               SUM(OPENAMOUNT) AS OPEN_AMOUNT, SUM(IS_OVERDUE::INT) AS OVERDUE
        FROM {DB}.ANALYTICS.DT_AR_AGING GROUP BY 1 ORDER BY 3 DESC NULLS LAST""",
        "GROUP BY AGING_BUCKET, DT_AR_AGING")
    f.sql_one("ar_open_total",
              f"SELECT SUM(OPENAMOUNT) FROM {DB}.ANALYTICS.DT_AR_AGING",
              "SUM(OPENAMOUNT), DT_AR_AGING")
    f.sql_one("ar_overdue_count",
              f"SELECT COUNT(*) FROM {DB}.ANALYTICS.DT_AR_AGING WHERE IS_OVERDUE",
              "COUNT WHERE IS_OVERDUE, DT_AR_AGING")

    # ---- what Cortex Analyst actually reads ---------------------------------
    # Not either semantic view. The app points Analyst at a semantic MODEL FILE on
    # a stage, which covers a narrower set of tables than the semantic view does —
    # so quoting the view's fact count as "what the agent can answer" is wrong.
    import gzip
    import tempfile

    import yaml

    model = {"stage_file": ANALYST_MODEL, "tables": [], "dimensions": 0,
             "facts": 0, "measures": 0, "verified_queries": 0}
    try:
        tmp = tempfile.mkdtemp()
        cur.execute(f"GET @{ANALYST_STAGE}/{ANALYST_MODEL} file://{tmp}")
        p = pathlib.Path(tmp) / ANALYST_MODEL
        if p.exists():
            text = p.read_text()
        else:
            gz = list(pathlib.Path(tmp).glob("*.gz"))
            text = gzip.decompress(gz[0].read_bytes()).decode() if gz else ""
        y = yaml.safe_load(text) or {}
        tabs = y.get("tables") or []
        model.update(
            name=y.get("name"),
            tables=[t.get("name") for t in tabs],
            base_tables=[f"{(t.get('base_table') or {}).get('schema')}."
                         f"{(t.get('base_table') or {}).get('table')}" for t in tabs],
            dimensions=sum(len(t.get("dimensions") or []) for t in tabs),
            facts=sum(len(t.get("facts") or []) for t in tabs),
            measures=sum(len(t.get("measures") or []) for t in tabs),
            verified_queries=len(y.get("verified_queries") or []),
        )
    except Exception as e:  # noqa: BLE001
        model["error"] = str(e)[:120]
    f.put("analyst_model", model, f"GET @{ANALYST_STAGE} + parse YAML")

    # Which domains the agent can and cannot answer on, derived from the model.
    covered = {t.replace("DT_", "").replace("_", " ").title() for t in model["tables"]}
    f.put("analyst_covered", sorted(covered), "tables present in the Analyst model")
    f.put("analyst_not_covered",
          sorted({o["TABLE_NAME"] for o in f.data["analytics_objects"]}
                 - set(model["tables"])),
          "ANALYTICS tables absent from the Analyst model")

    # ---- what the application reads ----------------------------------------
    # The app is a hybrid: some pages read the raw BDC share, others read the L2
    # dynamic tables. It does not read either semantic view.
    sources: dict = {}
    if API_ROUTES.exists():
        import re
        for m in re.finditer(r"FROM\s+([A-Z_0-9]+)\.([A-Za-z_0-9]+)\.([A-Za-z_0-9]+)",
                             API_ROUTES.read_text()):
            key = ".".join(m.groups())
            sources[key] = sources.get(key, 0) + 1
    f.put("app_data_sources", dict(sorted(sources.items(), key=lambda kv: -kv[1])),
          f"{API_ROUTES.name} FROM clauses")
    f.put("app_reads_share_directly",
          sum(n for k, n in sources.items() if k.startswith("SAP_BDC_DEMO_")),
          f"{API_ROUTES.name} FROM clauses on SAP_BDC_DEMO_*")
    f.put("app_reads_l2",
          sum(n for k, n in sources.items() if k.startswith("SAP_FINANCE_360.ANALYTICS")),
          f"{API_ROUTES.name} FROM clauses on ANALYTICS")

    # ---- cross-validation ---------------------------------------------------
    # The app computes revenue off the raw share with ABS + DEBITCREDITCODE; the L2
    # summary pre-aggregates it. They agree exactly, which is the evidence that the
    # medallion layer is faithful to the share.
    cur.execute(f"""
        SELECT ABS(SUM(CASE WHEN GLACCOUNT LIKE '4%' AND DEBITCREDITCODE='H'
                            THEN AMOUNTINTRANSACTIONCURRENCY ELSE 0 END))
        FROM SAP_BDC_DEMO_ENTRY_VIEW_JOURNAL_ENTRY.BDCCONNECT.OPERATIONALACCTGDOCITEM""")
    raw_rev = float(cur.fetchone()[0] or 0)
    pnl_rev = sum(r["REVENUE"] or 0 for r in f.data["pnl_by_year"])
    f.put("revenue_raw_share", raw_rev, "ABS/SUM over OPERATIONALACCTGDOCITEM (L0)")
    f.put("revenue_l2_summary", pnl_rev, "SUM(REVENUE) over DT_PNL_SUMMARY (L2)")
    f.put("revenue_reconciles", abs(raw_rev - pnl_rev) < 1,
          "L0 vs L2 revenue comparison")

    # ---- app surface --------------------------------------------------------
    # The sidebar declares nav items as `{ id: 'overview', label: 'Executive
    # Overview', icon: ... }` with SINGLE quotes. Matching only double-quoted
    # `label:` silently returns the filter labels instead, which is how this
    # first reported 4 pages instead of 9 — so match the id/label pair.
    pages = []
    if SIDEBAR.exists():
        import re
        pages = [m.group(2) for m in re.finditer(
            r"""id:\s*['"]([\w-]+)['"]\s*,\s*label:\s*['"]([^'"]+)['"]""",
            SIDEBAR.read_text())]
    f.put("app_pages", pages, f"{SIDEBAR.name} nav array (id/label pairs)")
    f.put("app_page_count", len(pages), f"{SIDEBAR.name} nav array")

    try:
        cur.execute(f"CALL {APP_DB}.CORE.APP_URL()")
        f.put("app_url", cur.fetchone()[0], f"CALL {APP_DB}.CORE.APP_URL()")
    except Exception as e:  # noqa: BLE001
        f.put("app_url", None, f"unavailable: {str(e)[:60]}")

    cur.execute("SELECT CURRENT_ACCOUNT(), CURRENT_REGION()")
    acct, region = cur.fetchone()
    f.put("account", acct, "CURRENT_ACCOUNT()")
    f.put("region", region, "CURRENT_REGION()")
    f.put("repo", REPO, "constant")
    f.put("verified_on", dt.date.today().isoformat(), "extraction date")
    return f


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", action="store_true", dest="show")
    args = ap.parse_args()

    cn = snowflake.connector.connect(**conn_params(CONN))
    try:
        f = collect(cn.cursor())
    finally:
        cn.close()

    OUT.write_text(json.dumps({"facts": f.data, "provenance": f.provenance}, indent=2))
    print(f"wrote {OUT}  ({len(f.data)} facts)")

    if args.show:
        print(f"\n{'figure':34s} {'value':<44s} source")
        print("-" * 118)
        for k, v in f.data.items():
            s = json.dumps(v) if not isinstance(v, (str, int, float, type(None))) else str(v)
            if len(s) > 42:
                s = s[:39] + "..."
            print(f"{k:34s} {s:<44s} {f.provenance[k][:40]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
