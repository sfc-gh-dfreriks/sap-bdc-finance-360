"""Script for the SAP Working Capital 360 narrated walkthrough.

One entry per beat. Each carries the narration (which sets the segment's length),
the caption card copy, and the actions that put the app in the right state.

Narration is written to be spoken: initialisms spaced ("S A P", "B D C", "D S O"),
figures spelled out, `[[slnc n]]` pauses where a person would breathe.

EVERY FIGURE HERE IS WHAT THE APP SHOWS on its default view: all three companies,
period 2024-04 to 2025-03, latest month 2025-03 vs 2024-03, USD at fixed
illustrative FX. Pulled from the running API (/api/*) on 2026-09-29 against
SAP_WORKING_CAPITAL_360 on dfreriksdemo; they match /tmp/wc_facts.json.

THREE HONESTY BEATS ARE SCRIPTED IN:
  * AR and AP invoices, amounts and dates are real B D C journal lines; payment
    terms, early-pay programs, inventory, bank balances and partner names are
    demo enrichment.
  * Money is USD at fixed illustrative rates, never summed in local currency.
  * Net working capital is negative because A P is about three times A R in the
    demo tenant.
"""

NAV = {
    "overview": "Working Capital Overview",
    "cash": "Cash & Liquidity",
    "ar": "Accounts Receivable",
    "ap": "Accounts Payable",
    "early": "Early Payment & SCF",
    "inventory": "Inventory",
    "opps": "WC Opportunities",
    "lineage": "BDC Sources & Lineage",
    "analyst": "Ask the Agent",
}

SEGMENTS = [
    dict(
        id="00_open", page="overview", actions=[("wait", 1200)],
        narration=(
            "This is working capital insight on S A P B D C data, using B D C Connect "
            "zero copy. [[slnc 450]] The C F O's question is simple: [[slnc 200]] why did "
            "our cash conversion cycle get longer? [[slnc 400]] Three companies, in the "
            "U S, Europe and Japan, with every figure shown in U S dollars."
        ),
        popup=dict(title="SAP Working Capital 360", figure="3 companies",
                   body="US, EU and Japan operations. USD at fixed illustrative FX."),
    ),
    dict(
        id="01_ccc", page="overview", actions=[("wait", 800)],
        narration=(
            "First, the four numbers. [[slnc 300]] Days sales outstanding, how long "
            "customers take to pay: about forty six days. [[slnc 250]] Days payables "
            "outstanding, how long we take to pay suppliers: forty four and a half. "
            "[[slnc 250]] Days inventory outstanding: about fifty seven. [[slnc 350]] "
            "The cash conversion cycle is D S O plus D I O, minus D P O. [[slnc 250]] "
            "It's fifty eight point seven days, up four point seven on a year ago."
        ),
        popup=dict(title="Cash conversion cycle = DSO + DIO − DPO", figure="58.7 days",
                   body="Up 4.7 days vs March 2024. The days cash is tied up "
                        "between paying suppliers and collecting from customers."),
    ),
    dict(
        id="02_driver", page="overview", actions=[("scroll", 520), ("wait", 900)],
        narration=(
            "And the bridge shows why. [[slnc 300]] D S O actually improved, by almost "
            "two days. [[slnc 250]] The cycle grew because D P O fell five and a half "
            "days. [[slnc 300]] We're paying suppliers faster. [[slnc 400]] By company, "
            "Japan has the longest cycle, at sixty six days, driven by its inventory."
        ),
        popup=dict(title="The driver is payables", figure="DPO −5.5 days",
                   body="DPO 50.0 → 44.5 days. DSO improved 1.8. "
                        "Japan Operations is highest at 66.0 days."),
    ),
    dict(
        id="03_honesty", page="overview", actions=[("scroll", -520), ("wait", 700)],
        narration=(
            "One honest note before we go on. [[slnc 300]] Net working capital shows "
            "negative, because in this demo tenant payables are about three times "
            "receivables. [[slnc 350]] The app shows that as it is, rather than hiding it."
        ),
        popup=dict(title="Shown as-is", figure="NWC −$2.8M",
                   body="AP is about 3× AR in the demo tenant, so payables "
                        "exceed receivables plus inventory."),
    ),
    dict(
        id="04_cash", page="cash", actions=[("wait", 900)],
        narration=(
            "Cash and liquidity. [[slnc 300]] Eighteen point four million dollars across "
            "nine bank accounts. [[slnc 300]] The thirteen week forecast builds from open "
            "receivables and open payables, plus payroll, [[slnc 200]] and nets out at "
            "minus six point four million, [[slnc 200]] ending near twelve million. "
            "[[slnc 350]] Bank balances here are demo enrichment."
        ),
        popup=dict(title="13-week cash forecast", figure="$18.4M",
                   body="9 accounts today; net −$6.4M over 13 weeks. "
                        "Balances are demo enrichment."),
    ),
    dict(
        id="05_ar", page="ar", actions=[("wait", 900)],
        narration=(
            "Receivables. [[slnc 300]] Two point two million dollars open, thirteen point "
            "six percent of it overdue, [[slnc 200]] and about a hundred and seventy "
            "seven thousand in dispute. [[slnc 350]] Summit Retail Group tops the "
            "overdue list at a hundred and twenty five thousand, forty two days late. "
            "[[slnc 300]] That's where the collections team calls first."
        ),
        popup=dict(title="Who to call first", figure="13.6% overdue",
                   body="$2.23M open AR; $177K disputed. "
                        "Summit Retail Group: $125K overdue, 42 days."),
    ),
    dict(
        id="06_ap", page="ap", actions=[("wait", 900)],
        narration=(
            "Payables. [[slnc 300]] Seven point one million dollars open. [[slnc 250]] "
            "Sixty one percent of invoices paid on time. [[slnc 300]] And over the year, "
            "about two hundred and five thousand dollars of discounts captured, "
            "[[slnc 200]] against a hundred and forty one thousand lost."
        ),
        popup=dict(title="Discounts captured vs lost", figure="$141K lost",
                   body="$7.07M open AP; 61% paid on time; "
                        "$205K captured over the last 12 months."),
    ),
    dict(
        id="07_early", page="early", actions=[("wait", 1000)],
        narration=(
            "This is where S A P Taulia comes in. [[slnc 300]] Dynamic discounting pays "
            "suppliers early with our own cash, for a discount, about ten percent "
            "annualised here. [[slnc 300]] Supply chain finance lets a funder pay them "
            "early while we keep our terms. [[slnc 350]] The what if says it plainly: "
            "[[slnc 200]] extend terms fifteen days through supply chain finance, and "
            "about two point four million dollars of cash comes back."
        ),
        popup=dict(title="SAP Taulia levers", figure="$2.4M",
                   body="Extend terms 15 days via SCF. Programs and payment "
                        "outcomes are demo enrichment modelled on SAP Taulia."),
    ),
    dict(
        id="08_inventory", page="inventory", actions=[("wait", 900)],
        narration=(
            "Inventory. [[slnc 300]] Two million dollars, and all six categories are "
            "running above their target days. [[slnc 300]] Finished goods sit at eighty "
            "days against a target of sixty four. [[slnc 300]] Inventory values are demo "
            "enrichment too."
        ),
        popup=dict(title="DIO vs target", figure="6 of 6 over",
                   body="$2.0M inventory; Finished Goods 80.1 days vs 64 target. "
                        "Demo enrichment."),
    ),
    dict(
        id="09_opps", page="opps", actions=[("wait", 900)],
        narration=(
            "Put it together, and the opportunities page sizes each lever. [[slnc 300]] "
            "About three million dollars of cash release, [[slnc 200]] most of it from "
            "extending D P O through supply chain finance, [[slnc 250]] plus about two "
            "hundred and sixty thousand dollars of discounts back in the P and L."
        ),
        popup=dict(title="Cash release by lever", figure="$3.0M",
                   body="SCF-extended DPO is the largest lever at $2.5M; "
                        "$261K P&L from discounts."),
    ),
    dict(
        id="10_lineage", page="lineage", actions=[("wait", 1000)],
        narration=(
            "Here's why you can trust it. [[slnc 300]] Receivables and payables come "
            "straight from the S A P journal entry data product, ten thousand three "
            "hundred lines, [[slnc 200]] shared zero copy through B D C Connect. "
            "[[slnc 350]] Views, dynamic tables and one semantic view. No pipeline moved "
            "finance data anywhere."
        ),
        popup=dict(title="Zero copy, end to end", figure="12 data products",
                   body="Entry View Journal Entry → 1,584 AR and 3,566 AP invoices, "
                        "via L1 views into L2 dynamic tables."),
    ),
    dict(
        id="11_agent", page="analyst", actions=[("wait", 1200)],
        narration=(
            "And then you can just ask. [[slnc 400]] The agent sits on a governed "
            "semantic view: five tables and twenty one metrics. [[slnc 300]] Ask why the "
            "cash conversion cycle rose in Japan, [[slnc 200]] and it shows the S Q L it "
            "wrote, so the answer can be checked rather than trusted."
        ),
        popup=dict(title="Ask the Agent", figure="21 metrics",
                   body="Cortex Analyst over SAP_WORKING_CAPITAL_360_ANALYTICS, "
                        "with the generated SQL shown."),
    ),
    dict(
        id="12_close", page="overview", actions=[("wait", 600)],
        narration=(
            "So that's Working Capital three sixty. [[slnc 350]] S A P finance data, "
            "shared with zero copy, modelled once, with the S A P Taulia levers sized "
            "and open to plain English questions. [[slnc 400]] Install it from the "
            "internal marketplace, or try the public demo."
        ),
        popup=dict(title="SAP Working Capital 360", figure="Native App",
                   body="Listing WORKING_CAPITAL_360_ORG (US West 2) "
                        "and a public GitHub Pages demo."),
    ),
]
