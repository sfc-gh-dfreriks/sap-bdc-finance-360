#!/usr/bin/env python3
"""
Bundle the 9 Finance 360 tables into an application package's SHARED_DATA
schema so the Native App is fully self-contained (no consumer references).

Two modes:
  * Same-account  — CTAS directly from the local SAP_FINANCE_360 / SAP_BDC_DEMO_*
                    objects into FINANCE_360_PKG.SHARED_DATA.
  * Cross-account — extract rows from a SOURCE account and load them into a
                    TARGET account (used to seed EMEA / APAC packages).

Auth uses key-pair connections defined in ~/.snowflake/connections.toml.
NO secrets are stored in this file — pass connection names only.

Usage:
  # same-account bundle (US)
  python migrate_data.py --target dfreriksdemo --mode local

  # cross-account bundle (extract from US, load into EU)
  python migrate_data.py --source dfreriksdemo --target dfreriks_eu_demo \
      --mode remote --warehouse COMPUTE_WH
"""
import argparse
import snowflake.connector
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# target_table -> source fully-qualified object (L1/analytics + raw BDC products)
SOURCES = {
    "JOURNALENTRY":               "SAP_BDC_DEMO_JOURNAL_ENTRY_HEADER.BDCCONNECT.JOURNALENTRY",
    "OPERATIONALACCTGDOCITEM":    "SAP_BDC_DEMO_ENTRY_VIEW_JOURNAL_ENTRY.BDCCONNECT.OPERATIONALACCTGDOCITEM",
    "SUPPLIERINVOICE":            "SAP_BDC_DEMO_SUPPLIER_INVOICE.BDCCONNECT.SUPPLIERINVOICE",
    "DT_AP_AGING":                "SAP_FINANCE_360.ANALYTICS.DT_AP_AGING",
    "DT_AR_AGING":                "SAP_FINANCE_360.ANALYTICS.DT_AR_AGING",
    "DT_EXPENSE_BY_COSTCENTER":   "SAP_FINANCE_360.ANALYTICS.DT_EXPENSE_BY_COSTCENTER",
    "DT_REVENUE_BY_PROFITCENTER": "SAP_FINANCE_360.ANALYTICS.DT_REVENUE_BY_PROFITCENTER",
    "DT_JOURNAL_ENTRY_360":       "SAP_FINANCE_360.ANALYTICS.DT_JOURNAL_ENTRY_360",
    "LINEAGE_COUNTS":             "SAP_FINANCE_360.ANALYTICS.LINEAGE_COUNTS",
}
PKG = "FINANCE_360_PKG"


def connect(conn_name: str, **kw):
    """Load the key-pair connection from connections.toml and connect."""
    import tomllib, os
    with open(os.path.expanduser("~/.snowflake/connections.toml"), "rb") as f:
        cfg = tomllib.load(f)[conn_name]
    with open(cfg["private_key_path"], "rb") as f:
        pk = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())
    der = pk.private_bytes(serialization.Encoding.DER,
                           serialization.PrivateFormat.PKCS8,
                           serialization.NoEncryption())
    return snowflake.connector.connect(
        account=cfg["account"], user=cfg["user"], private_key=der,
        role=cfg.get("role", "ACCOUNTADMIN"), paramstyle="qmark", **kw)


def ensure_package(cur):
    cur.execute(f"CREATE APPLICATION PACKAGE IF NOT EXISTS {PKG}")
    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {PKG}.SHARED_DATA")
    cur.execute(f"GRANT USAGE ON SCHEMA {PKG}.SHARED_DATA TO SHARE IN APPLICATION PACKAGE {PKG}")


def grant(cur, name):
    cur.execute(f"GRANT SELECT ON TABLE {PKG}.SHARED_DATA.{name} TO SHARE IN APPLICATION PACKAGE {PKG}")


def local_bundle(target, wh):
    conn = connect(target, warehouse=wh) if wh else connect(target)
    cur = conn.cursor()
    if wh:
        cur.execute(f"USE WAREHOUSE {wh}")
    ensure_package(cur)
    for name, src in SOURCES.items():
        cur.execute(f"CREATE OR REPLACE TABLE {PKG}.SHARED_DATA.{name} AS SELECT * FROM {src}")
        grant(cur, name)
        cur.execute(f"SELECT COUNT(*) FROM {PKG}.SHARED_DATA.{name}")
        print(f"  {target}/{name}: {cur.fetchone()[0]} rows")
    cur.close(); conn.close()


def remote_bundle(source, target, wh):
    # 1) extract from source
    s = connect(source); sc = s.cursor()
    extract = {}
    for name, src in SOURCES.items():
        sc.execute(f"DESCRIBE TABLE {src}")
        desc = sc.fetchall()
        coldefs = [(r[0], r[1]) for r in desc]
        cols = [r[0] for r in desc]
        sc.execute(f'SELECT {", ".join(chr(34)+c+chr(34) for c in cols)} FROM {src}')
        extract[name] = (coldefs, cols, sc.fetchall())
        print(f"  extracted {name}: {len(extract[name][2])} rows")
    sc.close(); s.close()
    # 2) load into target
    t = connect(target, warehouse=wh); tc = t.cursor()
    tc.execute(f"USE WAREHOUSE {wh}")
    ensure_package(tc)
    for name, (coldefs, cols, rows) in extract.items():
        col_sql = ", ".join(f'"{c}" {ty}' for c, ty in coldefs)
        tc.execute(f"CREATE OR REPLACE TABLE {PKG}.SHARED_DATA.{name} ({col_sql})")
        ph = "(" + ",".join(["?"] * len(cols)) + ")"
        collist = ", ".join('"'+c+'"' for c in cols)
        ins = f'INSERT INTO {PKG}.SHARED_DATA.{name} ({collist}) VALUES {ph}'
        for i in range(0, len(rows), 2000):
            tc.executemany(ins, rows[i:i+2000])
        grant(tc, name)
        tc.execute(f"SELECT COUNT(*) FROM {PKG}.SHARED_DATA.{name}")
        print(f"  {target}/{name}: {tc.fetchone()[0]} rows")
    tc.close(); t.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source")
    ap.add_argument("--target", required=True)
    ap.add_argument("--mode", choices=["local", "remote"], default="local")
    ap.add_argument("--warehouse", default="COMPUTE_WH")
    a = ap.parse_args()
    if a.mode == "local":
        local_bundle(a.target, a.warehouse)
    else:
        assert a.source, "--source required for remote mode"
        remote_bundle(a.source, a.target, a.warehouse)
    print("DONE")
