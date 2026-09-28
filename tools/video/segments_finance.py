"""Script for the SAP Finance 360 narrated walkthrough.

One entry per beat. Each carries the narration (which sets the segment's length),
the caption card copy, and the actions that put the app in the right state.

Narration is written to be spoken, not read. Contractions, short sentences, and
`[[slnc n]]` pauses where a person would draw breath. Figures are spelled out —
"two and a quarter billion" reads correctly aloud where "$2,250,872,386" does not.
macOS `say` is the only synthesiser available offline, so the phrasing does the
work the voice cannot.

EVERY FIGURE HERE IS FROM /tmp/finance_facts.json, verified 2026-09-21 against
SAP_FINANCE_360 on account MSB89522. Two deliberate honesty beats are scripted in,
because a demo that hides its own caveats gets caught in the room:

  * DT_AR_AGING carries the DT_ prefix but is a PLAIN table, not a dynamic table.
  * Accounts Payable gross is a signed-amount total, not a balance. Correct
    aggregation needs ABS plus a DEBITCREDITCODE filter, and 294 invoices summing
    to nearly three billion is the tell that it hasn't been applied yet.

Actions run at the start of a segment; the page then holds for whatever narration
time remains.
"""

# Page routes, by sidebar button label — navigation happens in-app, exactly as
# capture_shots.py does it. These apps have no router to deep-link into.
NAV = {
    "overview": "Executive Overview",
    "gl": "General Ledger",
    "cost": "Cost Centers",
    "profit": "Profit Centers",
    "ap": "Accounts Payable",
    "ar": "Accounts Receivable",
    "period": "Period Analysis",
    "products": "BDC Data Products",
    "analyst": "Cortex Analyst",
}

SEGMENTS = [
    # ------------------------------------------------------------ opening
    dict(
        id="00_open", page="overview", actions=[],
        narration=(
            "This is a finance close, running on S A P data that never moved. "
            "[[slnc 450]] Three company codes, a full general ledger, payables, "
            "receivables — and two and a quarter billion dollars of revenue. "
            "[[slnc 350]] No extract, no pipeline, no copy."
        ),
        popup=dict(title="SAP Finance 360", figure="$2.25B revenue",
                   body="Three company codes across GL, AP, AR and profitability — "
                        "read live from an SAP BDC share."),
    ),
    dict(
        id="01_zero_copy", page="overview", actions=[("wait", 1200)],
        narration=(
            "Here's the part worth pausing on. [[slnc 300]] The layer underneath "
            "this app is six views. [[slnc 350]] Not six copies — six passthrough "
            "views straight onto the S A P share. When S A P changes, this changes. "
            "There's nothing in between to fall behind."
        ),
        popup=dict(title="Six views, zero copies", figure="6 L1 views",
                   body="SAP_BDC_L1 holds six passthrough VIEWS over the zero-copy "
                        "share. No ingestion step exists to break."),
    ),

    # ------------------------------------------------------------ the ledger
    dict(
        id="02_gl", page="gl", actions=[("wait", 800)],
        narration=(
            "The general ledger. [[slnc 250]] Ten thousand three hundred journal "
            "entries, modelled into a single analytics table. [[slnc 400]] The "
            "whole analytics layer is about twenty thousand rows across seven "
            "tables — small, because it's a demo, but the shape is production."
        ),
        popup=dict(title="General ledger", figure="10,300 entries",
                   body="DT_JOURNAL_ENTRY_360 — part of a 7-table, 20,011-row "
                        "analytics layer refreshed by dynamic tables."),
    ),
    dict(
        id="03_cost", page="cost", actions=[("wait", 800)],
        narration=(
            "Spend by cost centre. [[slnc 300]] This is the view a controller "
            "actually opens — where the money went, by whose budget it came out of. "
            "[[slnc 350]] It's a dynamic table, so it refreshes itself. Nobody "
            "schedules this."
        ),
        popup=dict(title="Cost centre spend", figure="dynamic refresh",
                   body="DT_EXPENSE_BY_COSTCENTER is one of six dynamic tables — "
                        "declarative refresh, no orchestration to maintain."),
    ),
    dict(
        id="04_profit", page="profit", actions=[("wait", 800)],
        narration=(
            "Profitability. [[slnc 300]] And this is the number I'd stake the demo "
            "on. [[slnc 400]] Revenue at the raw share is two billion, two hundred "
            "fifty million, eight hundred seventy-two thousand, three hundred "
            "eighty-six dollars. [[slnc 300]] Revenue at the top of the analytics "
            "layer is the same figure. To the dollar."
        ),
        popup=dict(title="Reconciles to the dollar",
                   figure="$2,250,872,386",
                   body="Identical at L0 raw share and L2 analytics. The modelling "
                        "layer adds shape without changing the answer."),
    ),

    # ------------------------------------------------------------ working capital
    dict(
        id="05_ap", page="ap", actions=[("wait", 800)],
        narration=(
            "Payables. [[slnc 300]] And here's an honest caveat, because you'll spot "
            "it before I do. [[slnc 400]] Two hundred ninety-four invoices in the "
            "ninety-plus bucket, totalling close to three billion dollars. That's "
            "ten million an invoice, which is nonsense. [[slnc 350]] S A P amounts "
            "are signed. Aggregate them without an absolute value and a debit-credit "
            "filter, and debits and credits pile up instead of netting out."
        ),
        popup=dict(title="Signed amounts, not a balance",
                   figure="needs ABS + D/C",
                   body="294 invoices at 90+ days summing to ~$2.99B is the tell: "
                        "SAP amounts need ABS and a DEBITCREDITCODE filter."),
    ),
    dict(
        id="06_ar", page="ar", actions=[("wait", 800)],
        narration=(
            "Receivables, by contrast, are clean. [[slnc 350]] One hundred twelve "
            "million, three hundred four thousand dollars open. Four hundred "
            "eighty-three invoices overdue. [[slnc 400]] That's a collections "
            "worklist, not a report — and it's the one page a treasury team would "
            "keep open all day."
        ),
        popup=dict(title="Receivables", figure="$112.3M open",
                   body="483 invoices overdue out of an open AR book of "
                        "$112,304,759 — a worklist, not a summary."),
    ),
    dict(
        id="07_period", page="period", actions=[("wait", 800)],
        narration=(
            "Period comparison. [[slnc 300]] Two thousand twenty-three closed at "
            "nine hundred sixty-nine million in revenue against seven hundred "
            "twenty-six million of expense. [[slnc 400]] Two hundred forty-three "
            "million of net income, computed from the ledger rather than typed into "
            "a slide."
        ),
        popup=dict(title="FY2023", figure="$242.8M net",
                   body="Revenue $968.8M less expenses $726.0M, aggregated from "
                        "journal entries at query time."),
    ),

    # ------------------------------------------------------------ the plumbing
    dict(
        id="08_products", page="products", actions=[("wait", 1000)],
        narration=(
            "This page is the receipt. [[slnc 350]] It lists the S A P B D C data "
            "products this application is standing on, so the architecture isn't a "
            "claim in a deck — it's visible inside the app itself."
        ),
        popup=dict(title="The data products behind it",
                   figure="SAP BDC shares",
                   body="The app exposes its own lineage: which BDC data products "
                        "it reads, in the app, not in a diagram."),
    ),
    dict(
        id="09_analyst", page="analyst", actions=[("wait", 1200)],
        narration=(
            "And then you can just ask. [[slnc 400]] Cortex Analyst sits on a "
            "semantic model with four tables, twenty-four dimensions and nine "
            "measures. [[slnc 350]] One caveat worth stating out loud — there are "
            "zero verified queries on it today. For a customer deployment you'd "
            "add those before you trusted it in front of a C F O."
        ),
        popup=dict(title="Cortex Analyst", figure="4 tables · 9 measures",
                   body="24 dimensions over the stage semantic model. Zero verified "
                        "queries today — the first thing to add before production."),
    ),
    dict(
        id="10_close", page="overview", actions=[("wait", 600)],
        narration=(
            "So that's the whole thing. [[slnc 400]] Six views over an S A P share, "
            "a thin modelling layer, a reconciled revenue number, and natural "
            "language on top. [[slnc 450]] The data never left S A P's landscape, "
            "and the close still runs."
        ),
        popup=dict(title="No pipeline, no copies",
                   figure="live SAP data",
                   body="Six passthrough views, six dynamic tables, one reconciled "
                        "revenue figure, and Cortex Analyst on top."),
    ),
]
