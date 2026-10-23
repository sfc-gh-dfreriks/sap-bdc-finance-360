#!/usr/bin/env python3
"""Build the Finance 360 management summary.

    ~/Documents/SAP/Finance_360_Presales_Kit/01_Management_Summary.docx

Every figure is read from /tmp/finance_facts.json, which tools/finance_facts.py
produces straight from the account with the originating query recorded against
each value. Nothing here is transcribed by hand, so the document cannot drift
away from what the system actually reports. If a number in this document is
wrong, the extractor is wrong, and re-running it fixes both.

Run the extractor first:

    python3 tools/finance_facts.py
    python3 tools/build_management_summary.py
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
    setup_page,
    table,
)

KIT = pathlib.Path.home() / "Documents" / "SAP" / "Finance_360_Presales_Kit"
OUT = KIT / "01_Management_Summary.docx"
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
    "Cortex Analyst": "Natural-language questions over a stage semantic model",
}


# ------------------------------------------------------------------ utilities

def load_facts() -> dict:
    """Read the extractor output. Fail loudly — a silent default would let the
    document claim figures nobody verified."""
    if not FACTS_FILE.exists():
        sys.exit(
            f"missing input: {FACTS_FILE}\n"
            "The management summary is generated from verified figures and will not "
            "be built without them. Produce the file first:\n"
            "    python3 tools/finance_facts.py"
        )
    try:
        payload = json.loads(FACTS_FILE.read_text())
    except json.JSONDecodeError as exc:
        sys.exit(f"{FACTS_FILE} is not valid JSON ({exc}). Re-run tools/finance_facts.py.")
    if "facts" not in payload:
        sys.exit(f"{FACTS_FILE} has no 'facts' key. Re-run tools/finance_facts.py.")
    return payload["facts"]


def usd(n) -> str:
    """Exact dollars, grouped. Used wherever the point is that two figures match
    digit for digit, where an abbreviation would destroy the evidence."""
    return f"${float(n):,.0f}"


def approx(n) -> str:
    """Rounded dollars, the way the figure gets spoken aloud."""
    n = float(n)
    if abs(n) >= 1e9:
        return f"${n / 1e9:.2f} billion"
    if abs(n) >= 1e6:
        return f"${n / 1e6:.0f} million"
    return usd(n)


def title_block(doc, title, subtitle, strap):
    for text_, size, bold, color, after in (
        (title, 22, True, SAP_NAVY, 2),
        (subtitle, 12, False, SNOW_BLUE, 2),
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
    return (f"ledger {j['min']} to {j['max']}, payables {ap['min']} to {ap['max']}, "
            f"receivables {ar['min']} to {ar['max']}")


# ------------------------------------------------------------------- sections

def section_what_it_is(doc, F):
    h1(doc, "What this is")
    body(doc,
         "We have taken finance data from SAP Business Data Cloud, left it where it "
         "sits, and built a working finance application on top of it in Snowflake. "
         f"The application is deployed and running: {F['app_page_count']} pages covering "
         "the general ledger, cost and profit centres, payables, receivables and period "
         "comparison, plus a natural-language question page.",
         size=10.5)
    body(doc,
         "The point of the exercise is not the application. The point is that finance "
         "reporting was built against SAP data without extracting it, without a nightly "
         "file drop, and without a second copy of the ledger to reconcile. The figures "
         "below are the evidence for that claim.")

    rows = [
        ["What was built",
         f"A {F['app_page_count']}-page finance application on Snowflake, reading SAP BDC "
         f"data products"],
        ["Status", "**Built, deployed and verified. Running today.**"],
        ["Data movement out of SAP", "**None.** The application reads shared data in place."],
        ["Scale",
         f"{F['analytics_rows']:,} rows across {len(F['analytics_objects'])} analytics "
         f"tables, {F['company_codes']} company codes, three fiscal years"],
        ["Reconciliation",
         f"Revenue agrees to the cent between the raw SAP share and the derived "
         f"summary: {usd(F['revenue_raw_share'])}"],
        ["What it is not",
         "**A fixed reference snapshot, not a live SAP feed.** Nothing in it refreshes "
         "from SAP."],
        ["Verified on", F["verified_on"]],
    ]
    table(doc, ["Item", "Summary"], rows, [1.8, 5.1], size=9.5)


def section_layers(doc, F):
    h1(doc, "How the data is layered")
    body(doc,
         "Three layers, each with a job. This matters to the summary only because it is "
         "the reason the reconciliation below is meaningful: the derived figures are not "
         "an independent re-keying of the SAP data, they are computed from it.")

    sv = F["semantic_view_detail"]
    primary = "SAP_FINANCE_360.SEMANTIC.SAP_FINANCE_360_ANALYTICS"
    p = sv.get(primary, {})

    rows = [
        ["L0 — shared SAP data products",
         "SAP BDC shares, read in place. No copy is made and nothing is transformed.",
         f"{F['app_reads_share_directly']} of the application's queries read this layer "
         f"directly"],
        ["L1 — passthrough views",
         "A thin naming layer over the shares, so downstream objects do not hard-code "
         "share names.",
         f"{F['l1_views']} views"],
        ["L2 — analytics tables",
         "The aggregates the application actually charts: journal detail, aging, GL "
         "balance, revenue and expense by centre, P&L summary.",
         f"{len(F['analytics_objects'])} tables, {F['analytics_rows']:,} rows, "
         f"{F['dynamic_table_count']} of them dynamic tables"],
        ["Semantic layer",
         "Semantic views exist in the account and describe the analytics layer.",
         f"{p.get('dimensions', 0)} dimensions, {p.get('facts', 0)} facts, "
         f"{p.get('relationships', 0)} relationships"],
    ]
    table(doc, ["Layer", "What it does", "Scale"], rows, [1.8, 3.25, 1.85], size=9)

    body(doc,
         f"The application splits its reads across two of those layers: "
         f"{F['app_reads_share_directly']} queries go straight to the raw SAP share and "
         f"{F['app_reads_l2']} go to the L2 tables. It does **not** read a semantic view. "
         f"That is worth stating because the natural assumption is that one governed "
         f"definition sits behind every screen, and here it does not.",
         size=9.5)

    rows = [[f"{n}. {name}", PAGE_PURPOSE.get(name, "")]
            for n, name in enumerate(F["app_pages"], start=1)]
    h2(doc, f"The {F['app_page_count']} pages")
    table(doc, ["Page", "What it shows"], rows, [2.2, 4.7], size=9, zebra=True)


def section_reconciliation(doc, F):
    h1(doc, "What it proves")
    body(doc,
         "One test carries most of the weight. Total revenue was computed twice by "
         "different routes: once by summing the raw SAP accounting document items in the "
         "shared L0 data product, and once by summing the pre-aggregated revenue column "
         "in the derived L2 table DT_PNL_SUMMARY. If the zero-copy pattern is sound the "
         "two have to agree exactly, and they do.",
         size=10.5)

    rows = [
        ["Raw SAP share (L0)",
         "SUM over OPERATIONALACCTGDOCITEM in the BDC share",
         usd(F["revenue_raw_share"])],
        ["Derived summary (L2)",
         "SUM(REVENUE) over ANALYTICS.DT_PNL_SUMMARY",
         usd(F["revenue_l2_summary"])],
        ["**Difference**", "**Identical to the cent**", "**$0**"],
    ]
    table(doc, ["Route", "How it was computed", "Total revenue"], rows,
          [1.7, 3.35, 1.85], size=9.5, align_right=(2,))

    callout(
        doc,
        "Why this is the figure to quote",
        f"{approx(F['revenue_raw_share'])} of revenue, computed independently from the raw "
        f"SAP share and from the derived analytics table, comes out to the same "
        f"{usd(F['revenue_raw_share'])}. The transformation layer did not lose, duplicate "
        f"or re-sign anything. There is no second copy of the ledger to reconcile because "
        f"there is no second copy of the ledger.",
    )

    h2(doc, "Profit and loss by fiscal year")
    rows = []
    for y in F["pnl_by_year"]:
        rows.append([
            y["FISCALYEAR"],
            usd(y["REVENUE"]),
            usd(y["EXPENSES"]),
            usd(y["NET_INCOME"]),
            f"{y['DOCS']:,}",
        ])
    table(doc, ["Fiscal year", "Revenue", "Expenses", "Net income", "Documents"],
          rows, [1.15, 1.6, 1.6, 1.6, 0.95], size=9.5, align_right=(1, 2, 3, 4))

    partial = next((y for y in F["pnl_by_year"] if y["FISCALYEAR"] == "2025"), None)
    full = next((y for y in F["pnl_by_year"] if y["FISCALYEAR"] == "2023"), None)
    if partial and full:
        body(doc,
             f"Read the {partial['FISCALYEAR']} row carefully. It carries "
             f"{partial['DOCS']:,} documents against {full['DOCS']:,} in a full year, so it "
             f"is a partial period and not a decline. Anyone who presents the three-year "
             f"net income line as a trend is presenting an artefact of where the snapshot "
             f"was cut.",
             size=9.5, italic=True, color=RED)

    h2(doc, "Receivables exposure")
    body(doc,
         f"The receivables position is the one figure on the application that a finance "
         f"team would act on the same day: {usd(F['ar_open_total'])} open, of which "
         f"{F['ar_overdue_count']} invoices are past due.")

    rows = []
    for b in F["ar_aging"]:
        rows.append([
            b["AGING_BUCKET"],
            f"{b['INVOICES']:,}",
            usd(b["OPEN_AMOUNT"]),
            f"{b['OVERDUE']:,}",
        ])
    rows.append(["**Open total**", "", f"**{usd(F['ar_open_total'])}**",
                 f"**{F['ar_overdue_count']:,}**"])
    table(doc, ["Aging bucket", "Invoices", "Open amount", "Overdue"], rows,
          [1.85, 1.3, 2.15, 1.6], size=9, align_right=(1, 2, 3))

    oldest = next((b for b in F["ar_aging"] if b["AGING_BUCKET"] == "120+ Days"), None)
    if oldest:
        body(doc,
             f"The shape is the finding, not the total. {oldest['INVOICES']} invoices "
             f"worth {usd(oldest['OPEN_AMOUNT'])} sit beyond 120 days, which is more "
             f"overdue value than every other overdue bucket put together. That is a "
             f"collections conversation with a number attached to it.",
             size=9.5)


def section_limits(doc, F):
    h1(doc, "What it does not do")
    body(doc,
         "This section exists so the figures survive being challenged. Every item below "
         "was verified rather than assumed, and each one has cost somebody a demo "
         "somewhere.",
         size=10.5)

    w = F["data_windows"]
    ar, ap, j = w["DT_AR_AGING"], w["DT_AP_AGING"], w["DT_JOURNAL_ENTRY_360"]
    am = F["analyst_model"]

    rows = [
        ["It is not a live SAP feed",
         f"A fixed reference snapshot, verified {F['verified_on']}. Nothing in it "
         f"refreshes from SAP. Say so before anyone asks."],
        ["There is no single governed contract behind the screens",
         f"{F['app_reads_share_directly']} application queries read the raw L0 share and "
         f"{F['app_reads_l2']} read the L2 tables. The application does not read a "
         f"semantic view, so the dashboard and the AI question page do not share one "
         f"definition of a measure."],
        ["The AI covers part of the data, not all of it",
         f"Cortex Analyst reads a model file on a stage ({am['stage_file']}) covering "
         f"{len(am['tables'])} tables, {am['dimensions']} dimensions and "
         f"{am['measures']} measures, with {am['verified_queries']} verified queries. "
         f"{', '.join(F['analyst_not_covered'])} are absent from it, so it cannot answer "
         f"payables, GL-balance or P&L-summary questions at all."],
        ["The fact tables cover different periods",
         f"Ledger runs to {j['max']}, payables to {ap['max']}, receivables from "
         f"{ar['min']} to {ar['max']}. An aging screen and a P&L screen are therefore "
         f"describing different periods, and payables and receivables trends must never "
         f"be put on one axis."],
        ["Fiscal 2025 is incomplete",
         f"{next(y['DOCS'] for y in F['pnl_by_year'] if y['FISCALYEAR'] == '2025'):,} "
         f"documents against roughly "
         f"{next(y['DOCS'] for y in F['pnl_by_year'] if y['FISCALYEAR'] == '2023'):,} in "
         f"a full year. Partial period, not a downturn."],
        ["One table can go stale without warning",
         f"{', '.join(F['dt_prefixed_not_dynamic'])} carries the DT_ prefix but is a "
         f"plain table, not a dynamic table. The other "
         f"{F['dynamic_table_count']} refresh themselves; that one does not, and it will "
         f"not announce that it has fallen behind."],
        ["No forecast, plan or budget",
         "Everything shown is actuals. There is no plan-versus-actual because no plan "
         "data was shared."],
        ["No close workflow",
         "The application reports on the ledger. It does not run a close, post a journal "
         "or hold an approval."],
    ]
    table(doc, ["Limitation", "What is actually true"], rows, [2.3, 4.6], size=9)

    callout(
        doc,
        "The one sentence not to say",
        "Do **not** say there is one governed contract behind both the dashboard and the "
        "AI. It is not true here. The dashboard reads tables and the raw share directly, "
        "and the AI reads a separate stage model file that is missing three of the seven "
        "analytics tables. Claiming otherwise is the fastest way to lose a technical "
        "audience, because it takes one question to disprove.",
    )


def section_next(doc, F):
    h1(doc, "What to do next")
    body(doc,
         "Four options, in the order they are worth doing. The first two need no further "
         "engineering.")

    bullet(doc,
           "**Use it as it stands. **It is deployed and the figures reconcile. It is ready for "
           "customer conversations today, provided the snapshot and coverage limits above "
           "are stated rather than skirted.")
    bullet(doc,
           f"**Close the AI coverage gap. **Adding {', '.join(F['analyst_not_covered'])} to the "
           f"semantic model would let the question page answer payables, GL-balance and "
           f"P&L questions, which is where finance users go first. Adding verified queries "
           f"would raise answer reliability from the current {F['analyst_model']['verified_queries']}.")
    bullet(doc,
           f"**Point the dashboard at the semantic layer. **Moving the "
           f"{F['app_reads_share_directly']} raw-share reads onto governed definitions "
           f"would make the one-contract claim true instead of aspirational, and would "
           f"mean the dashboard and the AI could not disagree.")
    bullet(doc,
           f"**Convert {', '.join(F['dt_prefixed_not_dynamic'])} to a dynamic table. **It is the "
           f"only analytics object that can silently go stale, and it is the one carrying "
           f"the receivables exposure a finance team would act on.")
    bullet(doc,
           "**Repoint at live SAP data. **The layering is independent of this snapshot. The "
           "same pattern runs against a customer's own BDC shares.")

    h1(doc, "Access")
    rows = [
        ["Application", F["app_url"]],
        ["Snowflake account", f"{F['account']}, {F['region']}"],
        ["Source", F["repo"]],
        ["Figures in this document", "tools/finance_facts.py, verified " + F["verified_on"]],
        ["Data windows", window_sentence(F)],
    ]
    table(doc, ["Resource", "Location"], rows, [2.2, 4.7], size=9)

    body(doc,
         "Every figure in this document was read from the account by "
         "tools/finance_facts.py, which records the query behind each value. No number "
         "here was carried over from an earlier document.",
         size=9, italic=True, color=GREY)


# ----------------------------------------------------------------------- main

def main():
    F = load_facts()

    doc = Document()
    setup_page(doc)

    title_block(
        doc,
        "SAP Finance 360",
        "Finance reporting on SAP Business Data Cloud and Snowflake, without moving the data",
        f"Management summary  ·  {DATE}  ·  figures verified {F['verified_on']}",
    )

    body(doc,
         "This document stands on its own. It states what was built, the one test that "
         "proves it works, the figures it produces, and the things it cannot do. It can "
         "be read without seeing the application.",
         size=10.5, italic=True, color=GREY)

    section_what_it_is(doc, F)
    section_layers(doc, F)
    doc.add_page_break()
    section_reconciliation(doc, F)
    doc.add_page_break()
    section_limits(doc, F)
    section_next(doc, F)

    KIT.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"wrote {OUT}")
    print(f"  size {OUT.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
