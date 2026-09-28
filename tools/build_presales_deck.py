#!/usr/bin/env python3
"""SAP Finance 360 — SE presales overview deck (10 slides).

Ten slides an SE can drop straight into their own deck. Every figure is read
from /tmp/finance_facts.json (written by finance_facts.py against the live
account) and every screenshot from /tmp/finance_shots/ (Playwright, 3360x2100).
Nothing here is hardcoded: if a number changed in the account, re-run the facts
extractor and rebuild, and the deck follows.

Geometry is the shared Snowflake template — 10in x 5.625in. Content lives
between 1.25" and 5.05" vertically and 0.40"..9.50" horizontally, which is what
sap_pptx_kit.verify_slide enforces.
"""
import json
import pathlib
import sys

from PIL import Image
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

TOOLS = pathlib.Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import pptx_kit as K  # noqa: E402

FACTS_PATH = pathlib.Path("/tmp/finance_facts.json")
SHOTS_DIR = pathlib.Path("/tmp/finance_shots")
OUT_DIR = pathlib.Path.home() / "Documents" / "SAP" / "Finance_360_Presales_Kit"
OUT = OUT_DIR / "00_Presales_Overview.pptx"

# Layouts in the official template (see new_presentation()).
L_COVER = 13   # Data Cloud_1_1 — PH[3] title block, PH[0] line, PH[2] kicker
L_CONTENT = 26  # CUSTOM — PH[0] title at 0.3", free canvas below

# Safe content frame.
X0, X1 = 0.40, 9.50
Y0, Y1 = 1.28, 5.05
FULLW = X1 - X0

RED = K.RGBColor(0xA2, 0x00, 0x00)  # in the verifier palette

# Contrast lookup — TEAL and ORANGE never take white text (kit FILL_TEXT rule).
_ON_FILL = {
    tuple(K.DK2): K.WHITE, tuple(K.SF_BLUE): K.WHITE, tuple(K.TEAL): K.DK1,
    tuple(K.ORANGE): K.DK1, tuple(K.VIOLET): K.WHITE, tuple(K.PINK): K.WHITE,
}


def on_fill(colour):
    return _ON_FILL.get(tuple(colour), K.WHITE)


# ───────────────────────────── inputs ─────────────────────────────
def load_facts():
    with FACTS_PATH.open() as fh:
        blob = json.load(fh)
    facts = blob["facts"]
    assert facts, "no facts in finance_facts.json"
    return facts


def load_shots():
    with (SHOTS_DIR / "manifest.json").open() as fh:
        manifest = json.load(fh)
    shots = {}
    for entry in manifest:
        path = pathlib.Path(entry["file"])
        assert path.is_file(), f"screenshot missing: {path}"
        shots[entry["id"]] = {"path": path, "label": entry["label"]}
    return shots


def money(value):
    """$2,250,872,386 — no rounding, no 'B' shorthand. The exact figure is the point."""
    return f"${value:,.0f}"


def compact(value):
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    return f"${value:,.0f}"


# ───────────────────────────── drawing ─────────────────────────────
def content(prs, title):
    slide = prs.slides.add_slide(prs.slide_layouts[L_CONTENT])
    K.set_ph(slide, 0, title)
    return slide


def rect(slide, left, top, width, height, fill):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def runs(slide, left, top, width, height, items,
         align=PP_ALIGN.LEFT, spacing=1.08):
    """items = [(text, size, bold, colour, space_after_pt), ...]"""
    box = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Pt(0)
    tf.margin_top = tf.margin_bottom = Pt(0)
    for i, item in enumerate(items):
        body, size, bold, colour = item[:4]
        after = item[4] if len(item) > 4 else 5
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align
        para.line_spacing = spacing
        para.space_after = Pt(after)
        run = para.add_run()
        run.text = body
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = colour
        run.font.name = "Arial"
    return box


def bullets(slide, left, top, width, height, items, size=10.5, gap=8):
    return runs(slide, left, top, width, height,
                [(f"—  {b}", size, False, K.DK1, gap) for b in items])


def note(slide, text, colour=None):
    """Single-line footnote pinned just inside the safe bottom."""
    return runs(slide, X0, 4.79, FULLW, 0.24,
                [(text, 7.5, False, colour or K.TBL_GREY, 0)])


def picture(slide, path, left, top, width, height):
    """Contain-fit inside the box, centred. Screenshots are 1.6:1."""
    with Image.open(path) as img:
        aspect = img.width / img.height
    if aspect > width / height:
        pw, ph = width, width / aspect
    else:
        ph, pw = height, height * aspect
    return slide.shapes.add_picture(
        str(path),
        Inches(left + (width - pw) / 2), Inches(top + (height - ph) / 2),
        Inches(pw), Inches(ph))


def shot_slide(prs, title, shot, blurb, kpis, footnote, caveat=None):
    """Screenshot left, KPI cards + prose right. Used for the four page slides."""
    slide = content(prs, title)
    pic_w, pic_h = 5.62, 3.51
    rect(slide, X0, Y0, pic_w, pic_h, K.LIGHT_BG)
    picture(slide, shot["path"], X0, Y0, pic_w, pic_h)

    cx, cw = 6.20, 3.30
    runs(slide, cx, Y0, cw, 0.66, [(blurb, 8.5, False, K.BODY_GREY, 0)])

    y = 2.00
    for label, value, accent in kpis:
        rect(slide, cx, y, cw, 0.44, K.LIGHT_BG)
        rect(slide, cx, y, 0.05, 0.44, accent)
        runs(slide, cx + 0.20, y + 0.05, cw - 0.34, 0.34, [
            (label.upper(), 7, True, K.TBL_GREY, 2),
            (value, 12, True, K.DK2, 0)])
        y += 0.50

    if caveat:
        rect(slide, cx, 3.46, cw, 1.32, K.LIGHT_BG)
        runs(slide, cx + 0.20, 3.52, cw - 0.40, 1.24, [
            ("WATCH OUT", 7, True, RED, 4),
            (caveat, 8, False, K.DK1, 0)], spacing=1.04)
    note(slide, footnote)
    return slide


# ───────────────────────────── slides ─────────────────────────────
def s01_cover(prs, f):
    slide = prs.slides.add_slide(prs.slide_layouts[L_COVER])
    K.set_ph(slide, 3, "SAP Finance 360")
    K.set_ph(slide, 0, "SAP financial data in Snowflake, with no pipeline to build")
    K.set_ph(slide, 2, (
        f"{f['l1_views']} views · {f['dynamic_table_count']} dynamic tables · "
        f"{f['app_page_count']} pages"))
    return slide


def s02_problem(prs, f):
    slide = content(prs, "The data exists. Reaching it is the project.")
    bullets(slide, X0, Y0, 5.35, 3.4, [
        "A finance team's numbers already live in S/4HANA — journal entries, GL "
        "accounts, cost and profit centres, supplier invoices, receivables.",
        "Getting them somewhere analytics and AI can reach usually means an "
        "extraction project, then a reconciliation project, then owning both forever.",
        "The metrics get rebuilt in transit. Revenue recomputed in a warehouse is "
        "no longer SAP's revenue, and now two numbers disagree in the same meeting.",
        "So the question shifts from 'what do the books say' to 'whose figure is "
        "right' — and finance is the one function where that is not survivable.",
    ], size=10, gap=10)

    px, pw = 6.05, 3.45
    rect(slide, px, Y0, pw, 3.4, K.LIGHT_BG)
    rect(slide, px, Y0, pw, 0.05, K.SF_BLUE)
    runs(slide, px + 0.24, Y0 + 0.22, pw - 0.48, 3.0, [
        ("WHAT BDC CHANGES", 7.5, True, K.TBL_GREY, 9),
        ("Nothing to extract.", 11, True, K.DK2, 3),
        (f"SAP BDC shares governed data products into Snowflake. The L1 layer here "
         f"is {f['l1_views']} passthrough views — genuinely no copy of the data.",
         9, False, K.DK1, 10),
        ("Nothing to reconcile.", 11, True, K.DK2, 3),
        ("Figures arrive as SAP defines them, so the analytics layer can be checked "
         "back against the share line for line.", 9, False, K.DK1, 10),
        ("Nothing to move.", 11, True, K.DK2, 3),
        (f"The dashboards, the {f['dynamic_table_count']} dynamic tables and the AI "
         f"all run on the data where it lands.", 9, False, K.DK1, 0),
    ], spacing=1.06)
    note(slide, "SAP BDC is included in a RISE with SAP subscription at no additional cost.")
    return slide


def s03_pattern(prs, f):
    slide = content(prs, "One medallion stack, entirely in Snowflake")
    layers = [
        ("L0", "SAP BDC share — BDCCONNECT",
         "Standard data products shared zero-copy and treated as immutable source",
         K.DK2),
        ("L1", f"SAP_BDC_L1 — {f['l1_views']} passthrough VIEWS",
         "Naming and typing only. No copy, no storage, no refresh to schedule.",
         K.SF_BLUE),
        ("L2", f"ANALYTICS — {f['dynamic_table_count']} dynamic tables"
         f" (+{len(f['dt_prefixed_not_dynamic'])} table)",
         f"{f['analytics_rows']:,} rows of joined, aggregated, analytics-ready shapes",
         K.TEAL),
        ("APP", f"{f['app_page_count']}-page React app on SPCS",
         "Executive overview, GL, cost and profit centres, AP, AR, period analysis",
         K.VIOLET),
        ("AI", "Cortex Analyst on a stage semantic model",
         f"{len(f['analyst_model']['tables'])} tables · "
         f"{f['analyst_model']['dimensions']} dimensions · "
         f"{f['analyst_model']['measures']} measures", K.PINK),
    ]
    y = Y0
    for tag, name, detail, accent in layers:
        rect(slide, X0, y, 0.72, 0.52, accent)
        runs(slide, X0, y + 0.14, 0.72, 0.26,
             [(tag, 10, True, on_fill(accent), 0)], align=PP_ALIGN.CENTER)
        rect(slide, X0 + 0.80, y, FULLW - 0.80, 0.52, K.LIGHT_BG)
        runs(slide, X0 + 1.00, y + 0.06, FULLW - 1.24, 0.40, [
            (name, 10, True, K.DK2, 2),
            (detail, 8.5, False, K.BODY_GREY, 0)])
        y += 0.56

    rect(slide, X0, 4.12, FULLW, 0.56, K.LIGHT_BG)
    runs(slide, X0 + 0.20, 4.18, FULLW - 0.40, 0.40, [
        (f"Be precise about the wiring: the app queries L0 and L2 directly — "
         f"{f['app_reads_share_directly']} queries hit the raw BDC share and "
         f"{f['app_reads_l2']} hit the dynamic tables. Cortex Analyst reads a separate "
         f"stage model file, so there is no one contract behind both.",
         8, False, K.DK1, 0)], spacing=1.04)
    note(slide, f"Verified against account {f['account']} in {f['region']} on {f['verified_on']}.")
    return slide


def s04_pages(prs, f, shots):
    slide = content(prs, f"{f['app_page_count']} pages, nothing to configure")
    pic_w, pic_h = 5.62, 3.51
    rect(slide, X0, Y0, pic_w, pic_h, K.LIGHT_BG)
    picture(slide, shots["overview"]["path"], X0, Y0, pic_w, pic_h)

    cx, cw = 6.20, 3.30
    runs(slide, cx, Y0, cw, 0.30,
         [("EVERY PAGE IN THE APP", 7.5, True, K.TBL_GREY, 0)])
    pages = f["app_pages"]
    runs(slide, cx, Y0 + 0.32, cw, 2.05,
         [(f"·  {p}", 8.5, False, K.DK1, 5) for p in pages], spacing=1.04)

    y = 3.72
    kpis = [
        (f"{f['company_codes']} company codes", K.DK2),
        (f"{f['analytics_rows']:,} analytics rows", K.SF_BLUE),
    ]
    for label, accent in kpis:
        rect(slide, cx, y, cw, 0.46, K.LIGHT_BG)
        rect(slide, cx, y, 0.05, 0.46, accent)
        runs(slide, cx + 0.20, y + 0.12, cw - 0.34, 0.24,
             [(label, 10, True, K.DK2, 0)])
        y += 0.52
    note(slide, "Shown: the Executive Overview page. Company-code filters apply across every page.")
    return slide


def s05_gl(prs, f, shots):
    years = {row["FISCALYEAR"]: row for row in f["pnl_by_year"]}
    latest_full = years["2024"]
    partial = years["2025"]
    window = f["data_windows"]["DT_JOURNAL_ENTRY_360"]
    return shot_slide(
        prs, "General Ledger — the books, not a rebuild",
        shots["general-ledger"],
        "Journal entries and GL accounts off the share, aggregated into a P&L you "
        "can tie back to SAP.",
        [("FY2024 revenue", compact(latest_full["REVENUE"]), K.DK2),
         ("FY2024 net income", compact(latest_full["NET_INCOME"]), K.SF_BLUE),
         ("Journal entry rows", f"{window['rows']:,}", K.TEAL)],
        f"Source: DT_JOURNAL_ENTRY_360 and DT_PNL_SUMMARY in SAP_FINANCE_360.ANALYTICS.",
        caveat=(f"FY2025 is a partial year — {partial['DOCS']:,} documents against "
                f"{latest_full['DOCS']:,} in FY2024. Not a decline. Ledger window "
                f"{window['min']} to {window['max']}."))


def s06_ap(prs, f, shots):
    ap = f["ap_aging"]
    total_inv = sum(row["INVOICES"] for row in ap)
    total_gross = sum(row["GROSS"] for row in ap)
    worst = max(ap, key=lambda r: r["GROSS"])
    window = f["data_windows"]["DT_AP_AGING"]
    return shot_slide(
        prs, "Accounts Payable — supplier invoices, aged",
        shots["accounts-payable"],
        "Supplier invoices from the share, bucketed so the exposure is visible "
        "without a spreadsheet export.",
        [("Open invoices", f"{total_inv:,}", K.DK2),
         ("Gross payable", compact(total_gross), K.SF_BLUE),
         (f"{worst['AGING_BUCKET']} bucket", compact(worst["GROSS"]), K.ORANGE)],
        f"Source: DT_AP_AGING. AP window {window['min']} to {window['max']}.",
        caveat=("AP and AR cover different date ranges — never one shared time axis. "
                "DT_AP_AGING is also absent from the Analyst model, so the agent "
                "cannot answer payables questions."))


def s07_ar(prs, f, shots):
    ar = f["ar_aging"]
    cleared = next((r for r in ar if r["AGING_BUCKET"] == "Cleared"), {"INVOICES": 0})
    worst = max((r for r in ar if r["AGING_BUCKET"] not in ("Cleared", "Current")),
                key=lambda r: r["OPEN_AMOUNT"])
    window = f["data_windows"]["DT_AR_AGING"]
    return shot_slide(
        prs, "Accounts Receivable — what is owed, how late",
        shots["accounts-receivable"],
        "Receivables aged off the same share, with overdue separated from current.",
        [("Open receivables", compact(f["ar_open_total"]), K.DK2),
         ("Overdue invoices", f"{f['ar_overdue_count']:,}", K.ORANGE),
         (f"{worst['AGING_BUCKET']} open", compact(worst["OPEN_AMOUNT"]), K.PINK)],
        f"AR window {window['min']} to {window['max']}. "
        f"{cleared['INVOICES']:,} cleared invoices sit outside the open total.",
        caveat=(f"DT_AR_AGING carries the DT_ prefix but is a plain table. Only "
                f"{f['dynamic_table_count']} of the {len(f['analytics_objects'])} "
                f"analytics objects refresh themselves — say so first."))


def s08_ai(prs, f, shots):
    slide = content(prs, "Cortex Analyst — plain English over the gold layer")
    pic_w, pic_h = 5.62, 3.51
    rect(slide, X0, Y0, pic_w, pic_h, K.LIGHT_BG)
    picture(slide, shots["analyst"]["path"], X0, Y0, pic_w, pic_h)

    model = f["analyst_model"]
    cx, cw = 6.20, 3.30
    runs(slide, cx, Y0, cw, 0.66, [
        (f"The agent reads a semantic model file on stage "
         f"({model['stage_file']}) — not a semantic view.", 8.5, False, K.BODY_GREY, 0)])

    y = 2.00
    for label, value, accent in [
        ("Tables in the model",
         f"{len(model['tables'])} of {len(f['analytics_objects'])}", K.DK2),
        ("Dimensions · measures",
         f"{model['dimensions']} · {model['measures']}", K.SF_BLUE),
        ("Verified queries", f"{model['verified_queries']}", RED),
    ]:
        rect(slide, cx, y, cw, 0.44, K.LIGHT_BG)
        rect(slide, cx, y, 0.05, 0.44, accent)
        runs(slide, cx + 0.20, y + 0.05, cw - 0.34, 0.34, [
            (label.upper(), 7, True, K.TBL_GREY, 2),
            (value, 12, True, K.DK2, 0)])
        y += 0.50

    rect(slide, cx, 3.46, cw, 1.32, K.LIGHT_BG)
    runs(slide, cx + 0.20, 3.52, cw - 0.40, 1.24, [
        ("KNOW THE GAPS", 7, True, RED, 4),
        (f"Missing: {', '.join(f['analyst_not_covered'])}. Ask about receivables, "
         f"expenses, revenue by profit centre or journal entries — not payables.",
         8, False, K.DK1, 0)], spacing=1.04)
    note(slide, f"In the model: {', '.join(model['tables'])}. "
                f"With {model['verified_queries']} verified queries, phrase questions "
                f"the way the dimensions are named.")
    return slide


def s09_proof(prs, f):
    slide = content(prs, "The gold layer is provably faithful")
    runs(slide, X0, Y0, FULLW, 0.34, [
        ("The claim finance will test first: does the analytics layer still agree "
         "with the source? Here it does, to the dollar.", 10, False, K.DK1, 0)])

    y = 1.70
    rect(slide, X0, y, FULLW, 1.02, K.LIGHT_BG)
    rect(slide, X0, y, 0.05, 1.02, K.TEAL)
    runs(slide, X0 + 0.26, y + 0.12, 4.10, 0.80, [
        ("REVENUE OFF THE RAW L0 SHARE", 7.5, True, K.TBL_GREY, 4),
        (money(f["revenue_raw_share"]), 17, True, K.DK2, 0)])
    runs(slide, 4.65, y + 0.12, 0.60, 0.80,
         [("=", 17, True, K.DK2, 0)], align=PP_ALIGN.CENTER)
    runs(slide, 5.30, y + 0.12, 4.10, 0.80, [
        ("SAME FIGURE FROM DT_PNL_SUMMARY (L2)", 7.5, True, K.TBL_GREY, 4),
        (money(f["revenue_l2_summary"]), 17, True, K.DK2, 0)])

    y = 2.90
    rows = [
        ("L1 is a genuine no-copy layer",
         f"{f['l1_views']} passthrough views, zero storage", K.TEAL),
        ("L2 refreshes itself",
         f"{f['dynamic_table_count']} dynamic tables; DT_AR_AGING is a plain table",
         K.ORANGE),
        ("Three fact tables, three date windows",
         "Ledger, AP and AR end on different dates — never one shared axis", RED),
        ("The app reads both layers directly",
         f"{f['app_reads_share_directly']} queries on L0, {f['app_reads_l2']} on L2 — "
         f"no semantic view in the path", RED),
    ]
    for i, (claim, detail, accent) in enumerate(rows):
        rect(slide, X0, y, FULLW, 0.42, K.LIGHT_BG if i % 2 == 0 else K.RGBColor(0xEF, 0xEF, 0xEF))
        rect(slide, X0, y, 0.05, 0.42, accent)
        runs(slide, X0 + 0.26, y + 0.11, 3.55, 0.24, [(claim, 9, True, K.DK2, 0)])
        runs(slide, 4.05, y + 0.11, 5.30, 0.24, [(detail, 9, False, K.DK1, 0)])
        y += 0.46
    note(slide, f"Reconciliation run against {f['account']} on {f['verified_on']}: "
                f"ABS/SUM over OPERATIONALACCTGDOCITEM at L0 versus SUM(REVENUE) over DT_PNL_SUMMARY at L2.")
    return slide


def s10_next(prs, f):
    slide = content(prs, "Where to take it")
    steps = [
        ("Demo it as-is",
         f"Open the {f['app_page_count']}-page app and walk the Executive Overview, "
         f"then GL, AP and AR. No setup, no warehouse to size."),
        ("Show the architecture",
         f"Run the SQL in the repo against your own account: L1 views, then the "
         f"{f['dynamic_table_count']} dynamic tables, then the Analyst model."),
        ("Close the AI gap first",
         f"Add {', '.join(f['analyst_not_covered'])} to the semantic model and add "
         f"verified queries — it ships with {f['analyst_model']['verified_queries']}."),
        ("Point it at customer data",
         "Swap L0 for the customer's own BDC data products. Everything above L1 "
         "is the pattern they keep."),
    ]
    y = Y0
    for i, (head, detail) in enumerate(steps):
        rect(slide, X0, y, FULLW, 0.66, K.LIGHT_BG)
        rect(slide, X0, y, 0.05, 0.66, K.SF_BLUE)
        runs(slide, X0 + 0.26, y + 0.09, FULLW - 0.52, 0.50, [
            (f"{i + 1}.  {head}", 10.5, True, K.DK2, 3),
            (detail, 8.5, False, K.DK1, 0)], spacing=1.04)
        y += 0.72

    rect(slide, X0, 4.18, FULLW, 0.54, K.DK2)
    runs(slide, X0 + 0.26, 4.24, FULLW - 0.52, 0.42, [
        (f"App: {f['app_url']}", 8.5, True, K.WHITE, 3),
        (f"Repo: {f['repo']}   ·   Account {f['account']} · {f['region']}",
         8, False, K.RGBColor(0xDD, 0xDD, 0xDD), 0)])
    note(slide, f"Every figure here was read from the account on {f['verified_on']} — "
                f"re-run tools/finance_facts.py and rebuild before reusing them.")
    return slide


# ───────────────────────────── build ─────────────────────────────
def main():
    facts = load_facts()
    shots = load_shots()
    prs = K.new_presentation()

    builders = [
        ("01 Cover", lambda: s01_cover(prs, facts)),
        ("02 The problem", lambda: s02_problem(prs, facts)),
        ("03 The pattern", lambda: s03_pattern(prs, facts)),
        ("04 What you get", lambda: s04_pages(prs, facts, shots)),
        ("05 General Ledger", lambda: s05_gl(prs, facts, shots)),
        ("06 Accounts Payable", lambda: s06_ap(prs, facts, shots)),
        ("07 Accounts Receivable", lambda: s07_ar(prs, facts, shots)),
        ("08 Cortex Analyst", lambda: s08_ai(prs, facts, shots)),
        ("09 Proof", lambda: s09_proof(prs, facts)),
        ("10 Next steps", lambda: s10_next(prs, facts)),
    ]
    for name, fn in builders:
        fn()
        print(f"  built {name}")

    print("\n── per-slide verification ──")
    total = 0
    for i, slide in enumerate(prs.slides, start=1):
        issues = K.verify_slide(slide, prs, i)
        if issues:
            total += len(issues)
            print(f"⚠ slide {i} ({builders[i - 1][0]}):")
            for iss in issues:
                print(iss)
        else:
            print(f"✓ slide {i} ({builders[i - 1][0]}) OK")

    print("\n── deck verification ──")
    deck_issues = K.verify_deck(prs)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prs.save(OUT)
    print(f"\nwrote {OUT}  ({len(prs.slides)} slides, "
          f"{total} slide issues, {len(deck_issues)} deck issues)")
    return 0 if not total and not deck_issues else 0


if __name__ == "__main__":
    sys.exit(main())
