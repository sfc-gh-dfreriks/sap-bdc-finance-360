"""Script for the Orders to Cash narrated walkthrough (mfg-use-cases use case 09).

One entry per beat. Narration sets each segment's length; actions run BEFORE the line.

Every figure is read from /tmp/mfg_o2c_facts.json, written by
mfg-use-cases/use_cases/09_order_to_cash/tools/o2c_facts.py from the live app API.

Windows, said aloud where they matter: flows are all history (Jul 2024 to Sep 2026),
balances are as of 30 Sep 2026, DSO and CEI are for August 2026. The Ask Cortex answer is
generated live, so the narration does not quote its figures.
"""

import json
import pathlib

F = json.loads(pathlib.Path("/tmp/mfg_o2c_facts.json").read_text())["facts"]

_ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen "
         "fourteen fifteen sixteen seventeen eighteen nineteen").split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def words(n):
    """Integer to spoken English (enough for counts in this script)."""
    n = int(round(n))
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + ("" if n % 10 == 0 else " " + _ONES[n % 10])
    if n < 1000:
        rest = n % 100
        return _ONES[n // 100] + " hundred" + ("" if not rest else " and " + words(rest))
    for div, name in ((10 ** 9, "billion"), (10 ** 6, "million"), (1000, "thousand")):
        if n >= div:
            rest = n % div
            sep = "" if not rest else (" and " if rest < 100 else " ")
            return words(n // div) + " " + name + ("" if not rest else sep + words(rest))


def _decimal(x, places):
    """3.28 -> 'three point two eight'."""
    s = f"{x:.{places}f}".rstrip("0").rstrip(".")
    whole, _, frac = s.partition(".")
    out = words(int(whole))
    if frac:
        out += " point " + " ".join(_ONES[int(c)] for c in frac)
    return out


def money(x):
    """Dollar amount spoken to three significant figures."""
    for div, name in ((10 ** 9, "billion"), (10 ** 6, "million"), (1000, "thousand")):
        if x >= div:
            v = x / div
            return f"{_decimal(v, 2 if v < 10 else 1 if v < 100 else 0)} {name} dollars"
    return f"{words(x)} dollars"


def pct(x):
    return f"{words(x)} percent"


def fig(x):
    """Dollar amount for a caption card."""
    for div, sfx in ((10 ** 9, "B"), (10 ** 6, "M"), (1000, "K")):
        if x >= div:
            v = x / div
            return f"${v:.{2 if v < 10 else 1 if v < 100 else 0}f}{sfx}"
    return f"${x:,.0f}"



def days(x):
    return f"{_decimal(x, 1)} days"


ov = F["overview"]["kpis"]
stg = F["overview"]["stages"]
fu = F["fulfillment"]
rc = F["receivables"]
co = F["collections"]
ca = F["cash_application"]["kpis"]
cu = F["customers"]["kpis"]
mty = next(p for p in fu["byPlant"] if p["name"] == "Monterrey, MX")
worst = max(rc["dsoByCompany"], key=lambda r: r["dso"])
cause = max(co["rootCauses"], key=lambda r: r["lost"])
call = co["worklist"][0]
dbt = F["dbt_counts"]

NAV = {
    "overview": "Executive Dashboard",
    "orders": "Order Book & Quotes",
    "fulfillment": "Fulfillment & OTIF",
    "receivables": "Receivables & DSO",
    "collections": "Collections & Disputes",
    "cash": "Cash Application",
    "customers": "Customer 360",
    "sources": "Data Sources",
    "lineage": "Sources & Lineage (dbt)",
    "ask": "Ask Cortex",
}

SEGMENTS = [
    dict(
        id="00_problem", page="overview", actions=[("wait", 1500)],
        narration=(
            "Order to cash crosses more systems than any other process. [[slnc 350]] The quote is in "
            "Salesforce, the order, delivery, invoice and receivable are in S A P, [[slnc 250]] here two "
            "instances, one on E C C and one on S 4 HANA. [[slnc 300]] The real delivery date is in the "
            "carrier's tracking, disputes are in an A R automation tool, and the cash is on a bank "
            "statement. [[slnc 350]] Nobody sees the whole cycle."
        ),
        popup=dict(title="One cycle, six systems", figure="Quote → cash",
                   body="Salesforce CPQ · SAP ECC and S/4HANA · carrier tracking · AR automation · bank."),
    ),
    dict(
        id="01_dashboard", page="overview", actions=[("wait", 800)],
        narration=(
            f"This app shows it, on Snowflake. [[slnc 300]] {money(ov['bookings'])} booked across all "
            f"history. [[slnc 250]] On time in full is {pct(ov['otif_pct'])}, [[slnc 200]] and the cycle "
            f"from order to cash takes {days(ov['o2c_days'])}. [[slnc 300]] Most of that, "
            f"{days(stg['bill_to_cash'])}, is between the invoice and the cash. [[slnc 250]] The data is "
            f"synthetic, but the shapes are real."
        ),
        popup=dict(title="Executive Dashboard · all history", figure=fig(ov["bookings"]),
                   body=f"OTIF {ov['otif_pct']:.1f}% · order to cash {ov['o2c_days']:.1f} days · "
                        f"bill to cash {stg['bill_to_cash']:.1f} days. Synthetic data."),
    ),
    dict(
        id="02_orders", page="orders", actions=[("wait", 1000)],
        narration=(
            f"It starts with the quote. [[slnc 300]] {pct(F['order_book']['quotes']['conversion_pct'])} of "
            f"C P Q quotes become S A P orders, in {days(F['order_book']['quotes']['quote_to_order_days'])} "
            f"on average. [[slnc 300]] Today's backlog is {money(F['order_book']['kpis']['backlog'])}, and "
            f"{money(F['order_book']['kpis']['past_due_backlog'])} of it is already past the date the "
            f"customer asked for."
        ),
        popup=dict(title="Order Book & Quotes", figure=fig(F["order_book"]["kpis"]["backlog"]),
                   body=f"Backlog as of 30 Sep 2026 · {fig(F['order_book']['kpis']['past_due_backlog'])} past due · "
                        f"{F['order_book']['quotes']['conversion_pct']:.1f}% quote conversion."),
    ),
    dict(
        id="03_otif", page="fulfillment", actions=[("wait", 1000)],
        narration=(
            f"Fulfillment. [[slnc 300]] The delivered date comes from the carrier, not the goods issue. "
            f"[[slnc 300]] In full is {pct(fu['kpis']['in_full_pct'])}, so the problem is time. "
            f"[[slnc 250]] Monterrey is the weakest plant at {pct(mty['otif_pct'])}, [[slnc 200]] and the "
            f"biggest cause is a promise date that was already late when the order was confirmed."
        ),
        popup=dict(title="Fulfillment & OTIF · all history", figure=f"{fu['kpis']['otif_pct']:.1f}%",
                   body=f"Monterrey {mty['otif_pct']:.1f}% · top cause: {fu['missCauses'][0]['name'].lower()}."),
    ),
    dict(
        id="04_dso", page="receivables", actions=[("wait", 1000)],
        narration=(
            f"Receivables. [[slnc 300]] {money(ov['open_ar'])} is open today, {money(ov['past_due'])} past "
            f"due. [[slnc 300]] In August, D S O was {days(ov['dso'])}, against a best possible "
            f"{days(ov['bpdso'])}. [[slnc 300]] That gap is collections, not sales. [[slnc 250]] The worst "
            f"company is {worst['name'].replace('(', '').replace(')', '')}."
        ),
        popup=dict(title="Receivables & DSO · Aug 2026", figure=f"{ov['dso']:.1f} days",
                   body=f"Best possible {ov['bpdso']:.1f} days · CEI {ov['cei']:.1f}% · "
                        f"open AR {fig(ov['open_ar'])} as of 30 Sep 2026."),
    ),
    dict(
        id="05_collections", page="collections", actions=[("wait", 1000)],
        narration=(
            f"Collections and disputes. [[slnc 300]] The worklist tells collectors who to call first: "
            f"today, {call['customer'].replace('LLC', 'L L C')}. [[slnc 300]] Disputes from S A P and the "
            f"A R tool are de-duplicated, then traced to their root cause. [[slnc 250]] "
            f"{money(co['kpis']['revenue_lost'])} has been credited or written off, [[slnc 200]] most of "
            f"it from billing errors and carrier problems."
        ),
        popup=dict(title="Collections & Disputes", figure=fig(co["kpis"]["revenue_lost"]),
                   body=f"Credited or written off · {co['kpis']['open_disputes']} disputes still open · "
                        f"largest root cause {cause['name'].replace('_', ' ').lower()}."),
    ),
    dict(
        id="06_cash", page="cash", actions=[("wait", 1000)],
        narration=(
            f"Cash application. [[slnc 300]] Bank statement lines match S A P clearing on the bank "
            f"reference. [[slnc 250]] {pct(ca['auto_match_pct'])} of receipts match automatically. "
            f"[[slnc 300]] {money(ca['unapplied'])} is unapplied: cash in the bank that still counts as "
            f"receivable."
        ),
        popup=dict(title="Cash Application", figure=f"{ca['auto_match_pct']:.1f}%",
                   body=f"Auto-matched · {fig(ca['unapplied'])} unapplied in {ca['unapplied_count']} receipts."),
    ),
    dict(
        id="07_customers", page="customers", actions=[("wait", 1000)],
        narration=(
            f"Customer three sixty joins the Salesforce account to the S A P customer in both instances. "
            f"[[slnc 300]] {money(cu['high_risk_ar'])} of receivables sits with high or critical risk "
            f"customers, [[slnc 200]] and {words(cu['over_limit'])} are over their credit limit."
        ),
        popup=dict(title="Customer 360", figure=fig(cu["high_risk_ar"]),
                   body=f"Open AR with High or Critical customers · {cu['over_limit']} over credit limit."),
    ),
    dict(
        id="08_sources", page="sources", actions=[("wait", 1200)],
        narration=(
            "Here's what makes it portable. [[slnc 300]] Each S A P instance can be read four ways: "
            "[[slnc 200]] E C C tables, S 4 HANA tables, B W InfoProviders, or S A P B D C data products. "
            "[[slnc 300]] Salesforce, the carrier, the A R tool and the bank each have their own adapter."
        ),
        popup=dict(title="Data Sources", figure="ECC · S/4 · BW · BDC",
                   body="Pick the SAP source type per instance; non-SAP feeds switch on and off."),
    ),
    dict(
        id="09_bdc", page="sources", actions=[("click_text", "Zero-copy data products"), ("wait", 1500)],
        narration=(
            "Switch the Americas instance to B D C, and the app is honest about the gaps. [[slnc 300]] B D C "
            "carries no disputes and no bank lines, [[slnc 200]] so the A R tool and the bank feed fill "
            "them. [[slnc 300]] Apply would rebuild every layer with D B T; we won't press it here."
        ),
        popup=dict(title="Coverage gaps, shown not hidden", figure="SAP BDC",
                   body="No disputes · no bank lines · no quotes or carrier events. Not applied."),
    ),
    dict(
        id="10_lineage", page="lineage", actions=[("wait", 1200)],
        narration=(
            f"Sources and lineage. [[slnc 300]] One D B T project on Snowflake: "
            f"{words(F['adapter_views'])} generated adapter views map native tables to one canonical "
            f"model, [[slnc 200]] feeding {words(len(F['gold_dynamic_tables']))} gold dynamic tables, a "
            f"semantic view and a Cortex agent."
        ),
        popup=dict(title="Sources & Lineage (dbt)", figure=f"{dbt['models']} models",
                   body=f"{F['adapter_views']} adapter views · {len(F['gold_dynamic_tables'])} gold dynamic tables · "
                        f"{dbt['tests']} tests."),
    ),
    dict(
        id="11_ask", page="ask",
        actions=[("click_button", "Analyse order-to-cash performance"),
                 ("wait_for_text", "Recommended Actions", 120000), ("wait", 1500)],
        narration=(
            "And Ask Cortex. [[slnc 300]] One click, and Cortex analyses the cycle stage by stage, "
            "[[slnc 250]] with findings and recommended actions, grounded on the gold layer."
        ),
        popup=dict(title="Ask Cortex", figure="Cortex",
                   body="Grounded on live gold facts for the current filters; generated live."),
    ),
    dict(
        id="12_close", page="ask", actions=[("scroll", -3000), ("wait", 800)],
        narration=(
            "So: any S A P, whether E C C, S 4 HANA, B W or B D C, [[slnc 200]] plus C R M, carriers, "
            "A R automation and banks, [[slnc 250]] in one order to cash view, on Snowflake. [[slnc 300]] "
            "The public demo and the source are linked at the end."
        ),
        popup=dict(title="Quote to cash, one view", figure="Any SAP",
                   body="ECC, S/4HANA, BW or BDC, with Salesforce, carrier, AR automation and bank feeds."),
    ),
]
