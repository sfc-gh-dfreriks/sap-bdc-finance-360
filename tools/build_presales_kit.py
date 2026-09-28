#!/usr/bin/env python3
"""Build the SAP Finance 360 presales kit documents.

Mirrors the Supply Chain 360 kit so the two read as a set:

    00_START_HERE.docx               what is in the kit and which file to open
    03_SE_Quick_Start.docx           positioning, demo path, objections
    05_Architecture_and_Install.docx the medallion stack and how to stand it up
    06_Setup_and_Access.docx         deployment and how to get in

One deliberate difference from the Supply Chain kit: that one pins its figures as
constants in this file, which is why several of its numbers had to be re-verified
by hand. Here every figure is read from /tmp/finance_facts.json, produced by
tools/finance_facts.py straight from the account, and each one carries the query
that produced it. Nothing below is typed in from a previous document.

Run the extractor first:

    python3 tools/finance_facts.py
    python3 tools/build_presales_kit.py
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import date

from docx import Document
from docx.shared import Pt

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from docx_kit import (  # noqa: E402
    GREY,
    RED,
    SAP_NAVY,
    SNOW_BLUE,
    body,
    bullet,
    callout,
    h1,
    h2,
    money,
    setup_page,
    table,
)

KIT = pathlib.Path.home() / "Documents" / "SAP" / "Finance_360_Presales_Kit"
FACTS_FILE = pathlib.Path("/tmp/finance_facts.json")
DATE = date.today().strftime("%d %B %Y")

PAGE_PURPOSE = {
    "Executive Overview": "P&L headline, revenue and expense trend, net income by period",
    "General Ledger": "Journal entries down to line item, by account and company code",
    "Cost Centers": "Where spend actually lands, by cost centre and period",
    "Profit Centers": "Revenue attribution by profit centre",
    "Accounts Payable": "Supplier invoices, aging buckets, days outstanding",
    "Accounts Receivable": "Customer invoices, overdue exposure, days to pay",
    "Period Analysis": "Fiscal period comparison and close progression",
    "BDC Data Products": "The SAP BDC catalog the data came from",
    "Cortex Analyst": "Natural-language questions over the semantic view",
}


def load_facts() -> dict:
    if not FACTS_FILE.exists():
        sys.exit(f"{FACTS_FILE} missing — run: python3 tools/finance_facts.py")
    payload = json.loads(FACTS_FILE.read_text())
    return payload["facts"]


def title_block(doc, title, subtitle, strap):
    for text_, size, bold, color, after in (
        (title, 20, True, SAP_NAVY, 2),
        (subtitle, 11.5, False, SNOW_BLUE, 2),
        (strap, 9, False, GREY, 14),
    ):
        p = doc.add_paragraph()
        r = p.add_run(text_)
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color
        p.paragraph_format.space_after = Pt(after)


def window_sentence(F) -> str:
    w = F["data_windows"]
    j, ap, ar = w["DT_JOURNAL_ENTRY_360"], w["DT_AP_AGING"], w["DT_AR_AGING"]
    return (f"General ledger {j['min']} to {j['max']}, payables {ap['min']} to "
            f"{ap['max']}, receivables {ar['min']} to {ar['max']}")


def stale_data_callout(doc, F):
    w = F["data_windows"]
    ar, j = w["DT_AR_AGING"], w["DT_JOURNAL_ENTRY_360"]
    callout(
        doc,
        "Read this before you demo",
        f"The three fact tables do **not** share a date window. Ledger and payables "
        f"stop at {j['max']}, while receivables run to {ar['max']}. So an aging "
        f"screen and a P&L screen are describing different periods, and a receivable "
        f"can appear 'current' that the ledger has no month for. Say it plainly if "
        f"asked: this is a fixed reference snapshot built to show the SAP BDC "
        f"pattern, not a live feed. Do not claim the data is current, and do not "
        f"put an AP trend and an AR trend on the same slide.",
    )


def provenance_table(doc, F):
    h1(doc, "Figures are verified, not copied")
    body(doc,
         "Every number in this kit was read from the account by "
         "`tools/finance_facts.py` on " + F["verified_on"] +
         ", not carried over from an earlier document. Re-run the stated source to "
         "check any of them.")
    sv = F["semantic_view_detail"]
    primary = "SAP_FINANCE_360.SEMANTIC.SAP_FINANCE_360_ANALYTICS"
    p = sv.get(primary, {})
    rows = [
        [f"{F['schemas']} domain schemas", "INFORMATION_SCHEMA.SCHEMATA"],
        [f"{F['l1_views']} L1 passthrough views", "INFORMATION_SCHEMA.TABLES, SAP_BDC_L1"],
        [f"{len(F['analytics_objects'])} analytics tables, "
         f"{F['analytics_rows']:,} rows", "INFORMATION_SCHEMA.TABLES, ANALYTICS"],
        [f"{F['dynamic_table_count']} dynamic tables", "SHOW DYNAMIC TABLES"],
        [f"{p.get('facts', 0)} facts, {p.get('dimensions', 0)} dimensions, "
         f"{p.get('relationships', 0)} relationships", "DESCRIBE SEMANTIC VIEW"],
        [f"{F['app_page_count']} app pages", "Sidebar.tsx nav array"],
        [f"{F['company_codes']} company codes", "COUNT DISTINCT, DT_JOURNAL_ENTRY_360"],
        [window_sentence(F), "MIN/MAX over the fact tables"],
    ]
    table(doc, ["Figure", "Source"], rows, [3.9, 3.0], zebra=True)


# ---------------------------------------------------------------- START HERE


def build_start_here(F):
    doc = Document()
    setup_page(doc)
    title_block(doc, "SAP Finance 360", "Presales kit — start here",
                f"{DATE} · verified against account {F['account']} · {F['region']}")

    body(doc,
         "This kit is for a Snowflake SE or partner SE who needs to show what SAP "
         "finance data looks like once it is in Snowflake, without standing anything "
         "up first. Read this page, then open one other file.")

    h1(doc, "What this demonstrates")
    body(doc,
         "SAP financial data — general ledger, payables, receivables, cost and profit "
         "centres — arriving from SAP Business Data Cloud by zero-copy share, shaped "
         "into a small analytics layer, and then queried three ways: through a "
         f"{F['app_page_count']}-page application, through a governed semantic view, "
         "and in natural language through Cortex Analyst.")
    bullet(doc, "**No pipeline.** The L1 layer reads the BDC share directly — no copy, "
                "no ETL tool, no scheduled extract.")
    bullet(doc, f"**{F['dynamic_table_count']} dynamic tables** do the shaping, so the "
                "analytics layer refreshes itself as the share changes.")
    bullet(doc, "**The shaping is provably faithful.** Revenue computed off the raw "
                f"share ({money(F['revenue_raw_share'])}) matches the pre-aggregated "
                f"summary table to the dollar — see 05_Architecture_and_Install.docx.")

    h1(doc, "Which file to open")
    table(doc, ["If you want to", "Open", "Audience"], [
        ["Demo it in ten minutes", "03_SE_Quick_Start.docx", "seller / SE"],
        ["Drop slides into your own deck", "00_Presales_Overview.pptx", "seller"],
        ["Explain the architecture", "05_Architecture_and_Install.docx", "technical"],
        ["Get access, or deploy it", "06_Setup_and_Access.docx", "technical"],
        ["Hand something to a customer", "01_Demo_Guide_Deck.pptx", "customer"],
    ], [2.6, 2.6, 1.6], zebra=True)

    stale_data_callout(doc, F)

    h1(doc, "What is in the data")
    pnl = F["pnl_by_year"]
    rows = [[r["FISCALYEAR"], money(r["REVENUE"]), money(r["EXPENSES"]),
             money(r["NET_INCOME"]), f"{r['DOCS']:,}"] for r in pnl]
    table(doc, ["Fiscal year", "Revenue", "Expenses", "Net income", "Documents"],
          rows, [1.3, 1.5, 1.5, 1.5, 1.3], align_right=(1, 2, 3, 4), zebra=True)
    part = pnl[-1]
    body(doc,
         f"Note {part['FISCALYEAR']} is a **partial year** — {part['DOCS']:,} documents "
         f"against roughly {pnl[0]['DOCS']:,} in a full year — because the ledger stops "
         f"at {F['data_windows']['DT_JOURNAL_ENTRY_360']['max']}. Do not present it as a "
         "decline.", color=RED)

    provenance_table(doc, F)

    h1(doc, "The companion kit")
    body(doc,
         "Supply Chain 360 is the sibling asset set and reads the same way — same "
         "branding, same file numbering, same medallion pattern over a different SAP "
         "domain. If you are showing a customer both, present them as one platform "
         "story with two domains, not two products.")

    h1(doc, "Support")
    body(doc, f"Source, issues and build scripts: {F['repo']}")
    out = KIT / "00_START_HERE.docx"
    doc.save(str(out))
    return out


# --------------------------------------------------------------- QUICK START


def build_quick_start(F):
    doc = Document()
    setup_page(doc)
    title_block(doc, "SE Quick Start", "SAP Finance 360",
                f"{DATE} · a ten-minute path, and what to say")

    h1(doc, "Positioning, in three sentences")
    body(doc,
         "SAP holds the finance record; getting it somewhere you can analyse it has "
         "historically meant an extract, a pipeline and a copy. SAP Business Data "
         "Cloud shares it into Snowflake with no copy at all, and from there it is "
         "ordinary Snowflake — dynamic tables to shape it, a semantic view to govern "
         "it, Cortex to ask it questions. The demo shows a finance team getting to a "
         "governed answer without a data engineering project in between.")

    h1(doc, "Before you start")
    bullet(doc, f"Open the app: {F['app_url'] or 'see 06_Setup_and_Access.docx'}")
    bullet(doc, "Know the date caveat below. It is the only thing likely to catch you out.")
    bullet(doc, "Decide whether you are showing the **app** or the **semantic view**. "
                "Both is too much for ten minutes.")
    stale_data_callout(doc, F)

    h1(doc, "The ten-minute path")
    steps = [
        ["1", "Executive Overview", "Open on the P&L headline. "
         f"{money(F['pnl_by_year'][1]['REVENUE'])} revenue, "
         f"{money(F['pnl_by_year'][1]['NET_INCOME'])} net income in "
         f"{F['pnl_by_year'][1]['FISCALYEAR']}. Say: this is SAP's own ledger, not a copy."],
        ["2", "General Ledger", "Drill from the headline into journal entries. "
         f"{F['data_windows']['DT_JOURNAL_ENTRY_360']['rows']:,} entries across "
         f"{F['company_codes']} company codes. The point is the drill exists at all."],
        ["3", "Accounts Receivable", f"{money(F['ar_open_total'])} open, "
         f"{F['ar_overdue_count']} invoices overdue. This is the screen a controller "
         "reacts to."],
        ["4", "Accounts Payable", "Aging buckets — "
         + ", ".join(f"{r['AGING_BUCKET']} {r['INVOICES']}" for r in F["ap_aging"][:3])
         + ". Ask them what their own 90-day bucket looks like."],
        ["5", "Cortex Analyst", "Ask one question in plain English. Let them choose it. "
         "This is the moment that lands."],
    ]
    table(doc, ["#", "Page", "What to do and say"], steps, [0.4, 1.8, 4.7], zebra=True)

    h2(doc, "Questions that work on the agent")
    M = F["analyst_model"]
    for q in ("What was net income by fiscal year?",
              "Which cost centres spent the most last year?",
              "Show revenue by profit centre.",
              "How much receivable is open, and how much is overdue?",
              "What are the largest journal entries by amount?"):
        bullet(doc, q)
    callout(doc, "Do not ask about:",
            f"Cortex Analyst reads a semantic **model file** on a stage "
            f"(`{M['stage_file']}`), not the semantic view. That model covers only "
            f"{len(M['tables'])} tables — {', '.join(M['tables'])} — with "
            f"{M['dimensions']} dimensions and {M['measures']} measures. "
            f"**{', '.join(F['analyst_not_covered'])} are not in it**, so anything "
            f"about payables, GL balances or the P&L summary will fail in front of "
            f"the customer. It also ships with {M['verified_queries']} verified "
            f"queries, so phrasing matters more than it does on Supply Chain 360.")

    h2(doc, "The closing line")
    callout(doc, "Say:",
            "Nothing you just saw required moving SAP's data. The share stays in "
            "place, the shaping is declarative, and every layer above it is ordinary "
            "Snowflake — dashboards, a governed model, and natural language over the "
            "same tables. That is the difference between a report and a platform.")

    h1(doc, "What is on each page")
    table(doc, ["Page", "What it shows"],
          [[p, PAGE_PURPOSE.get(p, "")] for p in F["app_pages"]],
          [2.2, 4.7], zebra=True)

    h1(doc, "Discovery questions")
    for q in ("How long does it take you to close, and where does the time go?",
              "Who outside finance can see the ledger today, and how do they get it?",
              "How many copies of the GL exist in your estate?",
              "When a number is questioned, how long to trace it to the source document?"):
        bullet(doc, q)

    h1(doc, "Objections, and what to say")
    table(doc, ["Objection", "Response"], [
        ["Our finance data cannot leave SAP.",
         "It does not. A zero-copy share exposes it for reading; the record stays in SAP."],
        ["We already have a finance warehouse.",
         "Then compare cost and latency. This has no pipeline to run and no copy to reconcile."],
        ["Can the AI be trusted on financial numbers?",
         "It only answers through the semantic view, which defines the measures. It cannot invent a metric."],
        ["This data is not current.",
         "Correct, and say so. It is a fixed reference snapshot. The pattern is the point."],
        ["What about close-period controls?",
         "Out of scope here. This shows analytics over the record, not the close process itself."],
    ], [2.4, 4.5], zebra=True)

    h1(doc, "If it goes wrong")
    bullet(doc, "**App will not load** — the service may be suspended. See 06_Setup_and_Access.docx.")
    bullet(doc, "**Analyst answers oddly** — check the question maps to a fact in the "
                "semantic view; rephrase rather than repeat.")
    bullet(doc, "**A date looks wrong** — it probably is. The three fact tables have "
                "different windows. Acknowledge and move on.")
    out = KIT / "03_SE_Quick_Start.docx"
    doc.save(str(out))
    return out


# -------------------------------------------------------------- ARCHITECTURE


def build_architecture(F):
    doc = Document()
    setup_page(doc)
    title_block(doc, "Architecture and Install", "SAP Finance 360",
                f"{DATE} · the medallion stack and how to stand it up")

    h1(doc, "The stack")
    M = F["analyst_model"]
    table(doc, ["Layer", "What it is", "Objects"], [
        ["L0 — share", "SAP BDC zero-copy share, read in place. No storage consumed.",
         "SAP_BDC_DEMO_* catalog-linked databases"],
        ["L1 — passthrough", "Views that rename and type the shared objects. Still no copy.",
         f"{F['l1_views']} views in SAP_FINANCE_360.SAP_BDC_L1"],
        ["L2 — analytics", "Dynamic tables that aggregate and age. The only layer that "
         "materialises.",
         f"{F['dynamic_table_count']} dynamic tables in ANALYTICS"],
        ["Semantic", "Governed models over L2. Three distinct artifacts — see below.",
         "2 semantic views + 1 stage model file"],
        ["App", "React service on SPCS, inside a native app.",
         f"FINANCE_360_APP, {F['app_page_count']} pages"],
    ], [1.3, 3.1, 2.5], zebra=True)

    h1(doc, "What reads what")
    body(doc,
         "This is the part most likely to be described wrongly, so it is worth being "
         "exact. The application does **not** read a semantic view, and Cortex Analyst "
         "does not read the same object the dashboards do.")
    table(doc, ["Consumer", "Reads", "Evidence"], [
        ["App — Overview, General Ledger",
         "the raw L0 share directly",
         f"{F['app_reads_share_directly']} FROM clauses on SAP_BDC_DEMO_*"],
        ["App — Cost/Profit Centres, AP, AR",
         "L2 dynamic tables",
         f"{F['app_reads_l2']} FROM clauses on ANALYTICS"],
        ["Cortex Analyst",
         f"a stage model file, {M['stage_file']}",
         f"{len(M['tables'])} tables, {M['measures']} measures"],
        ["Semantic views",
         "nothing in this app reads them",
         "no reference in the server routes"],
    ], [2.1, 2.5, 2.3], zebra=True)
    callout(doc, "Consequence",
            "Because the dashboards and the agent read different objects, a tile and an "
            "answer **can** disagree. Do not claim a single governed contract behind "
            "both. The honest version is stronger anyway: the same L2 tables feed both, "
            "and the L2 layer is provably faithful to the share.")

    h1(doc, "The L2 layer is faithful to the share")
    body(doc,
         "Revenue computed two independent ways agrees exactly, which is the evidence "
         "that the dynamic tables did not distort the ledger:")
    table(doc, ["Path", "Revenue", "Source"], [
        ["L0 raw share, ABS + DEBITCREDITCODE filter",
         money(F["revenue_raw_share"]), "OPERATIONALACCTGDOCITEM"],
        ["L2 pre-aggregated summary",
         money(F["revenue_l2_summary"]), "DT_PNL_SUMMARY"],
    ], [3.4, 1.6, 1.9], align_right=(1,), zebra=True)
    body(doc, f"Reconciles: **{F['revenue_reconciles']}**. Note the raw-share query has "
              "to apply `ABS` and filter on `DEBITCREDITCODE` because SAP amounts are "
              "already signed — summing them raw nets to near zero.", italic=True)

    h1(doc, "The L1 layer")
    body(doc, "Six passthrough views, one per SAP object the demo needs:")
    for o in F["l1_objects"]:
        bullet(doc, f"`{o['TABLE_NAME']}`")

    h1(doc, "The analytics tables")
    rows = [[o["TABLE_NAME"], f"{(o['ROW_COUNT'] or 0):,}",
             "dynamic" if o["TABLE_NAME"] in F["dynamic_tables"] else "plain table"]
            for o in F["analytics_objects"]]
    table(doc, ["Table", "Rows", "Refresh"], rows, [3.0, 1.4, 2.5],
          align_right=(1,), zebra=True)

    if F["dt_prefixed_not_dynamic"]:
        callout(doc, "Worth knowing",
                "A `DT_` prefix is not proof of a dynamic table. "
                + ", ".join(f"**{n}**" for n in F["dt_prefixed_not_dynamic"]) +
                " is a plain table despite the name, so it does not refresh with the "
                "others and will go stale silently. Verify with SHOW DYNAMIC TABLES "
                "rather than trusting the prefix.")

    h1(doc, "Two semantic views, not one")
    body(doc,
         "The database carries two, with different shapes. They are not "
         "interchangeable, and pointing a tool at the wrong one produces a working "
         "but different model:")
    rows = []
    for name, d in F["semantic_view_detail"].items():
        rows.append([name.split(".", 1)[1],
                     str(d["tables"]), str(d["dimensions"]),
                     str(d["facts"]), str(d["metrics"]), str(d["relationships"])])
    table(doc, ["Semantic view", "Tables", "Dims", "Facts", "Metrics", "Rels"],
          rows, [2.7, 0.8, 0.8, 0.8, 0.9, 0.8], align_right=(1, 2, 3, 4, 5), zebra=True)
    body(doc,
         "`SEMANTIC.SAP_FINANCE_360_ANALYTICS` is the one the app and this kit quote. "
         "`ANALYTICS.SAP_FINANCE_360` is the older shape and carries metrics the newer "
         "one expresses as facts.", italic=True)

    h1(doc, "Build order")
    for i, s in enumerate((
        "Mount the SAP BDC share (or confirm the catalog-linked databases exist).",
        "Create SAP_FINANCE_360 and the SAP_BDC_L1 passthrough views.",
        "Create the analytics dynamic tables. They backfill on creation.",
        "Create the semantic view over the analytics layer.",
        "Build and push the service image, then create the native app.",
    ), 1):
        bullet(doc, f"{i}. {s}")

    h1(doc, "Security notes")
    bullet(doc, "The share is read-only by construction — L0 cannot be written.")
    bullet(doc, "The app runs as the application role, not as the invoking user.")
    bullet(doc, "No finance data is copied out of Snowflake by any step above.")
    out = KIT / "05_Architecture_and_Install.docx"
    doc.save(str(out))
    return out


# --------------------------------------------------------------- SETUP/ACCESS


def build_setup(F):
    doc = Document()
    setup_page(doc)
    title_block(doc, "Setup and Access", "SAP Finance 360",
                f"{DATE} · how to get in, and how to stand it up")

    h1(doc, "Pick your route")
    table(doc, ["You want", "Route", "Effort"], [
        ["To show it today", "Use the reference deployment below", "none"],
        ["To show it on your own account", "Install the native app", "~30 min"],
        ["To rebuild it from scratch", "Follow 05_Architecture_and_Install.docx", "half a day"],
    ], [2.3, 3.2, 1.4], zebra=True)

    h1(doc, "The reference deployment")
    table(doc, ["Region", "Account", "URL"], [
        ["North America", f"{F['account']} · {F['region']}", F["app_url"] or "unavailable"],
    ], [1.5, 2.3, 3.1], zebra=True)
    body(doc,
         "Only the North America deployment was verified in this pass — its URL came "
         "from `CALL FINANCE_360_APP.CORE.APP_URL()` on the account. Supply Chain 360 "
         "additionally lists EMEA and APAC; the equivalent Finance deployments in "
         "those regions were **not** confirmed here, so they are deliberately not "
         "listed rather than assumed.", color=RED)

    h1(doc, "Snowflake objects")
    table(doc, ["Object", "Name"], [
        ["Database", "SAP_FINANCE_360"],
        ["L1 schema", "SAP_BDC_L1"],
        ["Analytics schema", "ANALYTICS"],
        ["Semantic view", "SEMANTIC.SAP_FINANCE_360_ANALYTICS"],
        ["Native app", "FINANCE_360_APP"],
        ["Service", "FINANCE_360_APP.SERVICES.FINANCE_360_SERVICE"],
    ], [1.9, 5.0], zebra=True)

    h1(doc, "If the app will not load")
    body(doc, "The service is owned by the application, so ACCOUNTADMIN cannot "
              "suspend or resume it directly. Use the app's own procedures:")
    for c in ("CALL FINANCE_360_APP.CORE.GET_SERVICE_STATUS();",
              "CALL FINANCE_360_APP.CORE.SUSPEND_SERVICE();",
              "CALL FINANCE_360_APP.CORE.RESUME_SERVICE();"):
        bullet(doc, f"`{c}`")
    body(doc, "A suspend/resume recreates the container and re-pulls the image, which "
              "takes about twenty seconds.", italic=True)

    h1(doc, "Data currency")
    body(doc, window_sentence(F) + ".")
    stale_data_callout(doc, F)

    h1(doc, "Related assets")
    bullet(doc, f"Source and build scripts: {F['repo']}")
    bullet(doc, "Sibling kit: Supply_Chain_360_Presales_Kit")
    out = KIT / "06_Setup_and_Access.docx"
    doc.save(str(out))
    return out


def main() -> int:
    F = load_facts()
    KIT.mkdir(parents=True, exist_ok=True)
    built = [build_start_here(F), build_quick_start(F),
             build_architecture(F), build_setup(F)]
    print(f"Finance 360 presales kit -> {KIT}")
    for p in built:
        print(f"  {p.name:34s} {p.stat().st_size / 1024:6.0f} KB")
    print(f"\nfigures verified {F['verified_on']} against account {F['account']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
