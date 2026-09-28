#!/usr/bin/env python3
"""Build the Finance 360 per-persona demo scripts.

    ~/Documents/SAP/Finance_360_Presales_Kit/02_Demo_Scripts_by_Persona.docx

Six self-contained scripts, one per persona, each a page or two, so a single
script can be handed to whoever is presenting to that audience.

They are deliberately NOT one template with the role name swapped. Each persona
opens on a different page, drives different figures and closes on a different
point, because that is the only way the demo lands as being about the listener's
own job. A finance audience notices a generic walkthrough faster than most.

Every figure comes from /tmp/finance_facts.json, produced by
tools/finance_facts.py from the account. Spoken figures are rounded, because
nobody says "one hundred and twelve million three hundred and four thousand"
out loud; the exact value stays in the reference tables.

Run the extractor first:

    python3 tools/finance_facts.py
    python3 tools/build_demo_scripts.py
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
OUT = KIT / "02_Demo_Scripts_by_Persona.docx"
FACTS_FILE = pathlib.Path("/tmp/finance_facts.json")
DATE = date.today().strftime("%d %B %Y")

WARN_FILL = "FBEEEE"
SAY_FILL = "EEF4F8"


# ------------------------------------------------------------------ utilities

def load_facts() -> dict:
    if not FACTS_FILE.exists():
        sys.exit(
            f"missing input: {FACTS_FILE}\n"
            "The demo scripts quote verified figures and will not be built without "
            "them. Produce the file first:\n"
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
    return f"${float(n):,.0f}"


def spoken(n) -> str:
    """The figure as a presenter says it."""
    n = float(n)
    if abs(n) >= 1e9:
        return f"${n / 1e9:.2f} billion"
    if abs(n) >= 1e6:
        return f"${n / 1e6:.0f} million"
    if abs(n) >= 1e3:
        return f"${n / 1e3:.0f} thousand"
    return usd(n)


def bucket(rows, name, key):
    return next((r[key] for r in rows if r["AGING_BUCKET"] == name), 0)


# ---------------------------------------------------------- script scaffolding

def persona_header(doc, n, role, minutes, audience, question, opens_on):
    h1(doc, f"Script {n} · {role}", size=17, before=0, after=2)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run(f"{minutes} minutes   ·   Audience: {audience}   ·   Opens on: {opens_on}")
    r.font.size = Pt(9.5)
    r.font.color.rgb = GREY
    callout(doc, "The question they walk in with:", question, fill=SAY_FILL, size=10)


def who(doc, text):
    h2(doc, "Who they are, and what they care about")
    body(doc, text, size=9.5)


def open_on(doc, page, why):
    h2(doc, f"Open on: {page}")
    body(doc, why, size=9.5)


def say(doc, lines):
    """The say-this beats. Presenter reads down the right-hand column."""
    h2(doc, "Say this")
    table(doc, ["#", "Point", "Say it like this"],
          [[str(i), pt, line] for i, (pt, line) in enumerate(lines, start=1)],
          [0.3, 1.7, 4.9], size=8.5, zebra=True)


def ask(doc, question, why):
    h2(doc, "Ask them this")
    callout(doc, "Ask:", f"**{question}**  {why}", fill=SAY_FILL, size=9.5)


def close(doc, line):
    h2(doc, "Close on")
    body(doc, line, size=10.5, italic=True, color=SAP_NAVY)


def avoid(doc, items):
    h2(doc, "What not to show them")
    for item in items:
        bullet(doc, item, size=9.5)


# ------------------------------------------------------------------ the cover

def cover(doc, F):
    for text_, size, bold, color, after in (
        ("SAP Finance 360", 22, True, SAP_NAVY, 2),
        ("Demo scripts by persona", 12, False, SNOW_BLUE, 2),
        (f"{DATE}  ·  figures verified {F['verified_on']}  ·  {F['app_url']}",
         9, False, GREY, 14),
    ):
        p = doc.add_paragraph()
        r = p.add_run(text_)
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color
        p.paragraph_format.space_after = Pt(after)

    body(doc,
         "Six scripts, each written for one audience. They are not variants of one "
         "walkthrough. Every script opens on a different page, drives different figures "
         "and closes on a different point, because a demo only lands when it is visibly "
         "about the listener's own job.",
         size=10.5)
    body(doc,
         "Pick the one script that matches the room. Scripts 1 and 3 pair well back to "
         "back; scripts 4 and 5 do not, for a reason set out in both.")

    table(doc, ["#", "Persona", "Opens on", "Closes on", "Mins"], [
        ["1", "**CFO**", "Executive Overview",
         "the ledger and the report cannot disagree, because there is one copy", "6"],
        ["2", "Group Controller", "General Ledger",
         "the audit trail runs from the summary to the SAP document item", "8"],
        ["3", "FP&A Lead", "Period Analysis",
         "the partial period is visible, so it cannot be read as a trend", "7"],
        ["4", "AP Manager", "Accounts Payable",
         "the payables backlog is concentrated in one bucket", "6"],
        ["5", "AR / Credit Manager", "Accounts Receivable",
         "overdue exposure is a named worklist, not a number", "7"],
        ["6", "IT / Data Platform Owner", "BDC Data Products",
         "what still needs building, stated before they find it", "9"],
    ], [0.3, 1.75, 1.5, 2.75, 0.55], size=9)

    h2(doc, "Before any demo, whoever the audience is")
    w = F["data_windows"]
    bullet(doc,
           f"Open the application at **{F['app_url']}** and confirm the Executive "
           f"Overview loads before the room does.", size=9.5)
    bullet(doc,
           f"Know the date windows. Ledger runs to **{w['DT_JOURNAL_ENTRY_360']['max']}**, "
           f"payables to **{w['DT_AP_AGING']['max']}**, receivables "
           f"{w['DT_AR_AGING']['min']} to **{w['DT_AR_AGING']['max']}**. They are not the "
           f"same window, and a finance audience will spot it.", size=9.5)
    bullet(doc,
           "Say once, early, that this is a fixed reference snapshot rather than a live "
           "SAP feed. Volunteering it costs nothing. Being caught on it costs the "
           "meeting.", size=9.5)
    bullet(doc,
           f"Never put a payables trend and a receivables trend on one axis. Different "
           f"windows, so the shape would be an artefact.", size=9.5)
    bullet(doc,
           f"Fiscal 2025 is partial: "
           f"{next(y['DOCS'] for y in F['pnl_by_year'] if y['FISCALYEAR'] == '2025'):,} "
           f"documents against "
           f"{next(y['DOCS'] for y in F['pnl_by_year'] if y['FISCALYEAR'] == '2023'):,} "
           f"in a full year. It is not a decline. Say so before anyone reads it as one.",
           size=9.5)

    am = F["analyst_model"]
    callout(
        doc,
        "The agent's coverage, before you promise anything",
        f"Cortex Analyst reads a model file on a stage ({am['stage_file']}) covering "
        f"{len(am['tables'])} tables, {am['dimensions']} dimensions and {am['measures']} "
        f"measures, with {am['verified_queries']} verified queries. "
        f"{', '.join(F['analyst_not_covered'])} are **not in it**. So the agent cannot "
        f"answer payables, GL-balance or P&L-summary questions. Do not type one in and "
        f"hope. And do not claim one governed contract sits behind both the dashboard and "
        f"the agent — it does not: {F['app_reads_share_directly']} dashboard queries read "
        f"the raw share and {F['app_reads_l2']} read the analytics tables.",
        fill=WARN_FILL,
    )


# -------------------------------------------------------------------- script 1

def script_cfo(doc, F):
    persona_header(
        doc, 1, "CFO", 6, "CFO and finance leadership",
        "Can I trust a number that did not come out of SAP?",
        "Executive Overview")

    who(doc,
        "A CFO is not buying a dashboard. They already have dashboards. What they do not "
        "have is confidence that a figure produced outside SAP will survive being "
        "compared with SAP. Every reporting project they have signed off has eventually "
        "produced two versions of the same number, and someone spent a quarter "
        "reconciling them. That is the fear to address, and it is the only one that "
        "matters in six minutes.")

    open_on(doc, "Executive Overview",
            "Because it carries the P&L headline, and the headline is the figure they "
            "would challenge first. Starting anywhere else looks like you are working up "
            "to it.")

    y23 = next(y for y in F["pnl_by_year"] if y["FISCALYEAR"] == "2023")
    y24 = next(y for y in F["pnl_by_year"] if y["FISCALYEAR"] == "2024")

    say(doc, [
        ("Establish the scale",
         f"“This is {F['company_codes']} company codes and three fiscal years of finance "
         f"data. Revenue across the whole set is {spoken(F['revenue_raw_share'])}.”"),
        ("Name the test, then run it",
         f"“Here's the part worth your attention. I added up revenue twice. Once from the "
         f"raw SAP accounting document items, and once from the summary table this "
         f"dashboard actually charts. Both come out at "
         f"{usd(F['revenue_raw_share'])}. Identical to the cent.”"),
        ("Say why that is not luck",
         "“That's not a rounding coincidence. It's identical because there is only one "
         "copy of the data. We didn't extract anything out of SAP. The dashboard reads "
         "the SAP share in place.”"),
        ("Give them the year-on-year",
         f"“{y23['FISCALYEAR']} net income {spoken(y23['NET_INCOME'])}, "
         f"{y24['FISCALYEAR']} {spoken(y24['NET_INCOME'])}. Those two years are "
         f"complete.”"),
        ("Flag the partial year yourself",
         f"“The 2025 bar is short and I want to say why before you ask. It's "
         f"{next(y['DOCS'] for y in F['pnl_by_year'] if y['FISCALYEAR'] == '2025'):,} "
         f"documents against about {y23['DOCS']:,} in a full year. It's a partial period, "
         f"not a downturn. I'd rather tell you that than have you read a cliff.”"),
    ])

    ask(doc, "How long does it currently take you to reconcile a management number "
             "back to SAP?",
        "Whatever they answer is the value case, and it comes out of their mouth rather "
        "than yours. If they say it never fully reconciles, that is the better answer.")

    close(doc,
          f"“{usd(F['revenue_raw_share'])} from the raw SAP data, and "
          f"{usd(F['revenue_l2_summary'])} from the reporting layer. The ledger and the "
          f"report can't disagree, because there's only one copy of the ledger. That's "
          f"the whole claim.”")

    avoid(doc, [
        "**The Cortex Analyst page. **A CFO asks it something about payables or the P&L "
        "summary within two questions, and it cannot answer either. Neither table is in "
        "the model.",
        "**The aging screens. **They sit on different date windows from the P&L, and "
        "explaining that costs two of your six minutes and buys nothing.",
        "**Anything about layers, dynamic tables or semantic views. **Not their question.",
        "**A three-year trend line through fiscal 2025. **Show the years as bars with the "
        "partial period called out, never as a trend.",
    ])


# -------------------------------------------------------------------- script 2

def script_controller(doc, F):
    persona_header(
        doc, 2, "Group Controller", 8, "Group and statutory controllers, internal audit",
        "If I'm asked to defend this figure, can I get from it to the SAP document?",
        "General Ledger")

    who(doc,
        "The controller owns the number when it is questioned. Their instinct on seeing "
        "an aggregate is to distrust it until they can walk down to the posting that "
        "produced it. They also care, more than anyone else in the building, that the "
        "sign convention is right, that company codes are not silently blended, and that "
        "nobody has re-derived revenue with a slightly different rule. Give them the "
        "drill-down early or they will spend the meeting asking for it.")

    open_on(doc, "General Ledger",
            "Because it is the only page that goes down to the SAP document item. "
            "Starting on a summary page invites the question you would rather answer by "
            "demonstration.")

    j = F["data_windows"]["DT_JOURNAL_ENTRY_360"]
    je = next(t for t in F["analytics_objects"] if t["TABLE_NAME"] == "DT_JOURNAL_ENTRY_360")
    gl = next(t for t in F["analytics_objects"] if t["TABLE_NAME"] == "DT_GL_BALANCE")

    say(doc, [
        ("Start at the detail, not the total",
         f"“{je['ROW_COUNT']:,} journal entry lines, {j['min']} to {j['max']}, across "
         f"{F['company_codes']} company codes. This is line-item detail, not a "
         f"pre-canned extract.”"),
        ("Walk the trail down",
         "“Pick an account. Now a company code. Now a document. We're reading the SAP "
         "accounting document item at the bottom of that path, not a copy of it. The path "
         "from the aggregate to the source is three clicks and it doesn't leave SAP's "
         "data.”"),
        ("Show the balance view",
         f"“{gl['ROW_COUNT']:,} GL balance rows sit behind this, built from those same "
         f"line items. If the balance and the detail ever disagreed, they'd be reading "
         f"two different copies. They can't, because there aren't two.”"),
        ("Be precise about the P&L summary",
         f"“Revenue on the summary is {usd(F['revenue_l2_summary'])}. Summed straight off "
         f"the raw SAP items it's {usd(F['revenue_raw_share'])}. Same figure. And that "
         f"summary is pre-signed, so expenses are already positive — worth knowing before "
         f"you query it yourself.”"),
        ("Name the window limit yourself",
         f"“The ledger stops at {j['max']}. Payables and receivables have their own "
         f"windows. So don't reconcile a receivables aging screen to a ledger period — "
         f"they don't cover the same months, and that's a property of this snapshot, not "
         f"of the design.”"),
    ])

    ask(doc, "Which figure in your current management pack would you least like to be "
             "asked to trace back to source?",
        "Controllers always have one. It tells you where the drill-down is worth the most, "
        "and it usually turns out to be a derived measure nobody owns.")

    close(doc,
          f"“You can get from the P&L headline to the SAP accounting document item without "
          f"leaving the data SAP shared. That's the audit trail. It isn't a copy that "
          f"resembles SAP's, it's SAP's.”")

    avoid(doc, [
        "**The Cortex Analyst page for anything involving GL balance. **DT_GL_BALANCE is "
        "not in the model, so it will answer from the wrong table or not at all. A "
        "controller will notice, and then trust nothing else you showed.",
        "**Talk of a single governed contract behind every screen. **Not true here: "
        f"{F['app_reads_share_directly']} queries read the raw share and "
        f"{F['app_reads_l2']} read the analytics tables. A controller is precisely the "
        "person who will check.",
        "**Cross-period comparisons between AP and AR. **Different windows.",
        "**Cost and profit centre pages. **Interesting, but they belong to FP&A, and they "
        "dilute the audit-trail point.",
    ])


# -------------------------------------------------------------------- script 3

def script_fpa(doc, F):
    persona_header(
        doc, 3, "FP&A Lead", 7, "FP&A, business partnering and planning teams",
        "Can I get period comparisons without waiting on a data team?",
        "Period Analysis")

    who(doc,
        "FP&A lives on period-over-period movement and on explaining variance to someone "
        "who is mildly annoyed about it. Their constraint is rarely analysis and almost "
        "always access: the comparison they want does not exist yet, and the request sits "
        "in a queue. They are also the group most likely to mistake a partial period for "
        "a decline, so the honesty here is doing them a favour rather than covering you.")

    open_on(doc, "Period Analysis",
            "Because period comparison is the job. Opening on the Executive Overview "
            "shows them a conclusion; this page shows them the instrument they would "
            "actually use.")

    y = {x["FISCALYEAR"]: x for x in F["pnl_by_year"]}
    pnl = next(t for t in F["analytics_objects"] if t["TABLE_NAME"] == "DT_PNL_SUMMARY")
    exp = next(t for t in F["analytics_objects"] if t["TABLE_NAME"] == "DT_EXPENSE_BY_COSTCENTER")

    say(doc, [
        ("Frame the comparison",
         f"“Fiscal 2023 against 2024. Revenue {spoken(y['2023']['REVENUE'])} to "
         f"{spoken(y['2024']['REVENUE'])}. Expenses {spoken(y['2023']['EXPENSES'])} to "
         f"{spoken(y['2024']['EXPENSES'])}. Net income {spoken(y['2023']['NET_INCOME'])} "
         f"to {spoken(y['2024']['NET_INCOME'])}. Both years complete.”"),
        ("Deal with 2025 immediately",
         f"“2025 shows {spoken(y['2025']['REVENUE'])}, and I'm going to tell you not to "
         f"read that as a fall. It's {y['2025']['DOCS']:,} documents against "
         f"{y['2023']['DOCS']:,} in a full year. The period is cut short. If this were "
         f"your pack, that's the footnote that stops the wrong conversation.”"),
        ("Move to where the money went",
         f"“Now the same movement by cost centre — {exp['ROW_COUNT']:,} rows of expense "
         f"by centre and period. This is the variance question: not what changed, but "
         f"which centre changed it.”"),
        ("Show the turnaround time",
         f"“That took seconds, and nobody had to build it. The period summary behind it "
         f"is {pnl['ROW_COUNT']} rows, and {F['dynamic_table_count']} of the tables "
         f"underneath rebuild themselves when the source moves.”"),
        ("Be clear about actuals only",
         "“One thing this doesn't have: plan or budget. There's no plan-versus-actual "
         "here, because no plan data was shared. Everything you're looking at is "
         "actuals.”"),
    ])

    ask(doc, "How many of your recurring period comparisons still involve exporting to "
             "a spreadsheet?",
        "It surfaces the volume of low-value work, which is what makes self-service worth "
        "funding. Ask for a number, not a feeling.")

    close(doc,
          f"“Period comparison in seconds, on the same data the ledger uses, with the "
          f"partial period labelled instead of hidden. You'd have caught the 2025 cut "
          f"yourself — but you shouldn't have had to, and here you don't.”")

    avoid(doc, [
        "**A smoothed three-year trend line. **The partial year makes it misleading, and "
        "FP&A are the audience most likely to screenshot it.",
        "**Plan-versus-actual of any kind. **There is no plan data. Do not mock one up.",
        "**Payables aging next to a P&L period. **Different windows.",
        "**The Cortex Analyst page for P&L summary questions. **DT_PNL_SUMMARY is not in "
        "the model, and the P&L is the first thing an FP&A lead would type.",
    ])


# -------------------------------------------------------------------- script 4

def script_ap(doc, F):
    persona_header(
        doc, 4, "AP Manager", 6, "Accounts payable and shared-service leads",
        "Where is my payables backlog, and which invoices are actually old?",
        "Accounts Payable")

    who(doc,
        "An AP manager works a queue. They are judged on invoices cleared, on discounts "
        "not lost, and on nobody important ringing up about a missed payment. They do not "
        "want a chart of payables; they want to know which bucket the trouble is in and "
        "how big it is. Six minutes is plenty, and this is the shortest script for a "
        "reason.")

    open_on(doc, "Accounts Payable",
            "Because the aging buckets are the whole of their working view. Anything "
            "else on the way there is someone else's job.")

    ap = F["ap_aging"]
    ap_sorted = sorted(ap, key=lambda r: -r["GROSS"])
    worst = ap_sorted[0]
    total_inv = sum(r["INVOICES"] for r in ap)
    total_gross = sum(r["GROSS"] for r in ap)
    w = F["data_windows"]["DT_AP_AGING"]

    say(doc, [
        ("Put the whole queue up first",
         f"“{total_inv} supplier invoices in the aging view, {spoken(total_gross)} gross "
         f"across all buckets. That's the queue.”"),
        ("Go straight to the concentration",
         f"“Look at where it sits. {worst['INVOICES']} invoices in the "
         f"{worst['AGING_BUCKET'].lower()} bucket, {spoken(worst['GROSS'])}. That's "
         f"{round(100 * worst['INVOICES'] / total_inv)}% of the invoice count and "
         f"{round(100 * worst['GROSS'] / total_gross)}% of the value in the oldest "
         f"bucket.”"),
        ("Contrast with current",
         f"“Current is {bucket(ap, 'Current', 'INVOICES')} invoices, "
         f"{spoken(bucket(ap, 'Current', 'GROSS'))}. So the problem isn't throughput on "
         f"new invoices. It's a tail that stopped moving.”"),
        ("Name the window",
         f"“Payables here run {w['min']} to {w['max']}. That's the window for this "
         f"screen and it isn't the same as the receivables screen. I'll come back to why "
         f"that matters if you want the AR view too.”"),
        ("Say what this is not",
         "“This is a fixed snapshot, not a live feed off SAP. So don't read a specific "
         "invoice as today's position. What's real is the shape of the queue and where "
         "it's stuck.”"),
    ])

    callout(
        doc,
        "Do not demo the agent to this persona",
        f"The Cortex Analyst page cannot answer payables questions. DT_AP_AGING is "
        f"**not** in the semantic model file — the model covers "
        f"{', '.join(F['analyst_covered'])} and nothing else. If you open the agent in "
        f"front of an AP manager, the first thing they will type is a payables question, "
        f"and it will either fail or answer from the wrong table. This is the single "
        f"worst pairing of page and persona in the whole application. Skip the agent "
        f"page entirely in this script and say so if asked: payables coverage in the "
        f"model is on the list, not done.",
        fill=WARN_FILL,
    )

    ask(doc, "How many of those oldest invoices are genuinely disputed, as opposed to "
             "simply not looked at?",
        "It splits the backlog into a process problem and a supplier problem, which are "
        "fixed by different people. An AP manager usually knows the answer and rarely "
        "gets asked.")

    close(doc,
          f"“Your payables backlog isn't spread out. It's "
          f"{round(100 * worst['GROSS'] / total_gross)}% of the value sitting in one "
          f"bucket, {worst['INVOICES']} invoices. That's a worklist you could start on "
          f"this afternoon, and it came out of SAP data nobody had to extract.”")

    avoid(doc, [
        "**The Cortex Analyst page. **See the warning above. This is not a preference, it "
        "is a coverage gap.",
        "**The receivables screens in the same breath. **Different date window, and "
        "putting the two aging views side by side invites a comparison that is not valid.",
        "**The P&L pages. **An AP manager does not own them.",
        "**Any suggestion that clearing the backlog is visible here. **This is a "
        "snapshot; it does not track movement.",
    ])


# -------------------------------------------------------------------- script 5

def script_ar(doc, F):
    persona_header(
        doc, 5, "AR / Credit Manager", 7, "Credit control, collections and treasury",
        "What's overdue, how bad is it, and who do I chase first?",
        "Accounts Receivable")

    who(doc,
        "Credit control is the one finance role where the demo can hand over something "
        "actionable in the room. They care about cash landing, about which accounts are "
        "drifting, and about not chasing a customer who has already paid. They will judge "
        "the screen on whether it gives them an ordered list rather than a total.")

    open_on(doc, "Accounts Receivable",
            "Because the overdue position is the job, and it is the only figure in the "
            "application somebody would act on the same day they see it.")

    ar = F["ar_aging"]
    oldest = next(r for r in ar if r["AGING_BUCKET"] == "120+ Days")
    cleared = next(r for r in ar if r["AGING_BUCKET"] == "Cleared")
    current = next(r for r in ar if r["AGING_BUCKET"] == "Current")
    overdue_val = sum(r["OPEN_AMOUNT"] for r in ar if r["OVERDUE"])
    w = F["data_windows"]["DT_AR_AGING"]

    say(doc, [
        ("Lead with the exposure",
         f"“{spoken(F['ar_open_total'])} open receivables, and "
         f"{F['ar_overdue_count']} invoices of that are past due. The overdue slice is "
         f"{spoken(overdue_val)}.”"),
        ("Show where the risk concentrates",
         f"“{oldest['INVOICES']} invoices are beyond 120 days, worth "
         f"{spoken(oldest['OPEN_AMOUNT'])}. That's more overdue value than every other "
         f"overdue bucket put together. If you only worked one bucket this week, it's "
         f"that one.”"),
        ("Separate the healthy part",
         f"“{current['INVOICES']} invoices are current, {spoken(current['OPEN_AMOUNT'])}, "
         f"nothing overdue in there. And {cleared['INVOICES']:,} are already cleared and "
         f"carry zero open. So the screen isn't asking you to chase the whole book.”"),
        ("Make it a worklist",
         "“Sort by bucket, then open amount, and you have a call list in priority order. "
         "That's the useful output — not the total, the order.”"),
        ("Be honest about freshness",
         f"“Two caveats and I'd rather give them to you than have you find them. This is "
         f"a fixed snapshot, not live SAP. And the receivables table behind it doesn't "
         f"refresh itself the way the others do, so it can fall behind quietly. Treat the "
         f"shape as real and check a specific invoice in SAP before you ring anyone.”"),
    ])

    callout(
        doc,
        "The staleness point, precisely",
        f"{', '.join(F['dt_prefixed_not_dynamic'])} carries the DT_ prefix but is a plain "
        f"table, not a dynamic table. The other {F['dynamic_table_count']} analytics "
        f"objects refresh themselves when the source moves; this one does not, and it will "
        f"not signal that it has gone stale. It is also the table carrying the figures "
        f"this persona would act on, which is why it is worth saying out loud rather than "
        f"hoping. Receivables also run to {w['max']}, well past the ledger, so do not "
        f"reconcile this screen to a P&L period.",
        fill=WARN_FILL,
    )

    ask(doc, "What's your current cut-off for escalating an invoice from collections to "
             "credit hold?",
        "It converts the 120-plus bucket from a number into a decision they already have a "
        "policy for, and it tells you whether the bucket boundaries here match how they "
        "actually work.")

    close(doc,
          f"“{F['ar_overdue_count']} overdue invoices, "
          f"{spoken(oldest['OPEN_AMOUNT'])} of it beyond 120 days, in priority order. "
          f"That's not a number for a report. That's this week's call list, and it came "
          f"from SAP data nobody copied.”")

    avoid(doc, [
        "**The payables screen alongside this one. **Payables stop at "
        f"{F['data_windows']['DT_AP_AGING']['max']} and receivables run to {w['max']}. "
        "Two aging views on different windows look comparable and are not.",
        "**A working-capital or DSO story spanning both AP and AR. **Same reason. There is "
        "no shared period to compute it over.",
        "**The Cortex Analyst page, unless you stay strictly on receivables. **AR aging is "
        "in the model, so a receivables question will work, but there are zero verified "
        "queries behind it and one step sideways into payables fails.",
        "**Named-customer promises. **The screen supports a worklist; treat any individual "
        "invoice as needing a check in SAP first.",
    ])


# -------------------------------------------------------------------- script 6

def script_platform(doc, F):
    persona_header(
        doc, 6, "IT / Data Platform Owner", 9,
        "Data platform, integration and enterprise architecture",
        "What did you actually build, and what is still missing?",
        "BDC Data Products")

    who(doc,
        "This is the only persona who will read the code. They are not impressed by "
        "screens and they are deeply suspicious of anyone who says a thing is finished. "
        "Their real question is what they would inherit. The way to win the room is to "
        "name the gaps before they find them, because they will find them, and everything "
        "you claimed before that moment gets re-evaluated.")

    open_on(doc, "BDC Data Products",
            "Because it shows the SAP BDC catalog the data came from, which is where "
            "their scepticism starts. Opening on a finance screen means spending the "
            "first three minutes being asked what is underneath it.")

    am = F["analyst_model"]
    sv = F["semantic_view_detail"].get(
        "SAP_FINANCE_360.SEMANTIC.SAP_FINANCE_360_ANALYTICS", {})

    say(doc, [
        ("Start with zero copy, and prove it",
         f"“The application reads SAP BDC shares in place. "
         f"{F['app_reads_share_directly']} of its queries hit the raw share directly and "
         f"{F['app_reads_l2']} hit derived analytics tables. No extract, no pipeline out "
         f"of SAP, no second copy to reconcile.”"),
        ("Walk the layers",
         f"“L0 is the shares. L1 is {F['l1_views']} passthrough views so nothing "
         f"downstream hard-codes a share name. L2 is "
         f"{len(F['analytics_objects'])} analytics tables, {F['analytics_rows']:,} rows, "
         f"and {F['dynamic_table_count']} of those are dynamic tables that rebuild "
         f"themselves.”"),
        ("Give them the reconciliation as an engineering claim",
         f"“Revenue off the raw SAP document items is {usd(F['revenue_raw_share'])}. "
         f"Revenue off DT_PNL_SUMMARY is {usd(F['revenue_l2_summary'])}. Identical. That's "
         f"the transformation layer proving it doesn't lose or double anything.”"),
        ("Name the architecture gap before they do",
         f"“Now the part I'd want to know if I were inheriting this. The dashboard does "
         f"not read a semantic view. There's a semantic layer in the account — "
         f"{sv.get('dimensions', 0)} dimensions, {sv.get('facts', 0)} facts, "
         f"{sv.get('relationships', 0)} relationships — but the app reads tables and the "
         f"raw share directly. So there isn't one governed contract behind both the "
         f"dashboard and the agent. That's the obvious next piece of work.”"),
        ("Name the agent gap too",
         f"“The agent reads a model file on a stage, {am['stage_file']}: "
         f"{len(am['tables'])} tables, {am['dimensions']} dimensions, {am['measures']} "
         f"measures, {am['verified_queries']} verified queries. "
         f"{', '.join(F['analyst_not_covered'])} aren't in it, so payables, GL balance and "
         f"the P&L summary are out of scope for natural language today.”"),
        ("And the one that will bite operationally",
         f"“{', '.join(F['dt_prefixed_not_dynamic'])} is named like a dynamic table and "
         f"isn't one. It's a plain table, so it can go stale without saying anything. It's "
         f"also the table holding the receivables exposure. First thing I'd convert.”"),
    ])

    ask(doc, "Would you rather we closed the semantic-view gap or the agent coverage gap "
             "first?",
        "It is a genuine fork and they are the right person to choose. It also converts "
        "the conversation from evaluating your work to planning theirs.")

    close(doc,
          f"“What works is the zero-copy pattern and the reconciliation — "
          f"{usd(F['revenue_raw_share'])} both ways, no copy of SAP data anywhere. What's "
          f"unfinished is the governance layer: the dashboard bypasses the semantic view, "
          f"the agent covers four of seven tables, and one table can go stale silently. "
          f"You'd have found all three. I'd rather you heard them from me.”")

    avoid(doc, [
        "**Any claim of one governed contract behind the dashboard and the AI. **This "
        "persona will open the code and check. It is not true here.",
        "**The word 'live'. **It is a fixed reference snapshot verified "
        f"{F['verified_on']}.",
        "**A live agent demo on payables, GL balance or the P&L summary. **Those tables "
        "are outside the model.",
        "**Row-count bragging. **"
        f"{F['analytics_rows']:,} rows is a reference dataset, and pitching it as scale "
        "invites exactly the scepticism you are trying to avoid.",
    ])


# ----------------------------------------------------------------------- main

SCRIPTS = (
    script_cfo,
    script_controller,
    script_fpa,
    script_ap,
    script_ar,
    script_platform,
)


def main():
    F = load_facts()

    doc = Document()
    setup_page(doc)
    cover(doc, F)

    for build in SCRIPTS:
        doc.add_page_break()
        build(doc, F)

    KIT.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"wrote {OUT}")
    print(f"  size {OUT.stat().st_size / 1024:.0f} KB")
    print(f"  {len(SCRIPTS)} persona scripts")


if __name__ == "__main__":
    main()
