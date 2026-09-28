"""Script for the SAP Spend 360 narrated walkthrough.

One entry per beat. Each carries the narration (which sets the segment's length),
the caption card copy, and the actions that put the app in the right state.

Narration is written to be spoken: initialisms spaced ("S A P", "B D C", "P O"),
figures spelled out, `[[slnc n]]` pauses where a person would breathe.

EVERY FIGURE HERE IS FROM /tmp/spend_facts.json, verified 2026-09-28 against
SAP_SPEND_360 on account MSB89522. Money is USD, each PO line converted at the
ECB reference rate for its PO date - exactly what the app shows with USD selected.

THREE HONESTY BEATS ARE SCRIPTED IN:
  * Currency. Each company buys in its own currency; the recording shows the
    reporting-currency switch converting every PO line at its PO-date rate.
  * Risk, ESG, taxonomy and savings are representative enrichment values. The
    savings figures are quoted with that caveat.
  * Only DT_SPEND_360 is a real dynamic table.
"""

NAV = {
    "overview": "Spend Overview",
    "categories": "Categories",
    "suppliers": "Suppliers",
    "risk": "Supplier Risk",
    "sustainability": "Sustainability & Diversity",
    "savings": "Savings Pipeline",
    "contracts": "Contract Compliance",
    "orders": "Purchase Orders",
    "lineage": "BDC Sources & Lineage",
    "analyst": "Ask the Agent",
}

SEGMENTS = [
    dict(
        id="00_open", page="overview", actions=[("wait", 1200)],
        narration=(
            "This is spend intelligence on S A P B D C data, using B D C Connect zero copy. "
            "[[slnc 450]] Purchase orders and suppliers, shared straight from S A P into "
            "Snowflake. Nothing extracted, nothing copied. [[slnc 400]] Three companies, "
            "buying in dollars, euros and yen, and about four point seven million dollars "
            "of spend across three thousand P O lines."
        ),
        popup=dict(title="SAP Spend 360", figure="$4.69M",
                   body="3,000 PO lines across US, EU and Japan operations, "
                        "shown in USD."),
    ),
    # The engine runs a segment's actions BEFORE its narration starts, so each
    # currency flip is its own segment and lands on the words that describe it.
    dict(
        id="00b_eur", page="overview", actions=[("click_button", "EUR"), ("wait", 1800)],
        narration=(
            "Each company buys in its own currency, so you pick the one you report in. "
            "[[slnc 300]] Here it is in euros."
        ),
        popup=dict(title="Reporting currency", figure="€4.17M",
                   body="Every page follows the switch in the sidebar."),
    ),
    dict(
        id="00c_jpy", page="overview", actions=[("click_button", "JPY"), ("wait", 1800)],
        narration="In yen. [[slnc 500]]",
        popup=dict(title="Reporting currency", figure="¥711.6M",
                   body="Same three thousand PO lines, converted to yen."),
    ),
    dict(
        id="00d_usd", page="overview", actions=[("click_button", "USD"), ("wait", 1800)],
        narration=(
            "And back to dollars. [[slnc 350]] Every P O line converts at the European "
            "Central Bank rate for the day it was raised, not one rate at period end."
        ),
        popup=dict(title="Converted per transaction", figure="ECB daily rates",
                   body="Each PO line converted at the reference rate for its PO date."),
    ),
    dict(
        id="01_zero_copy", page="lineage", actions=[("wait", 1200)],
        narration=(
            "Here's why that matters. [[slnc 300]] Two S A P B D C data products, "
            "purchase order items and suppliers, come in through B D C Connect. "
            "[[slnc 350]] Between those shares and this app there's a passthrough view "
            "and one gold table. No pipeline moved procurement data anywhere."
        ),
        popup=dict(title="Zero copy, end to end", figure="2 data products",
                   body="Purchase Order (item) and Supplier, shared zero copy, "
                        "through L1 views into one gold spend table."),
    ),
    dict(
        id="02_categories", page="categories", actions=[("wait", 800)],
        narration=(
            "Categories. [[slnc 300]] Fifteen of them, on a three level taxonomy. "
            "Fleet and equipment is by far "
            "the largest, at about two point three million dollars. [[slnc 400]] Thirteen of the "
            "fifteen categories are addressable, which is where sourcing can actually act."
        ),
        popup=dict(title="Where the money goes", figure="15 categories",
                   body="Fleet & Equipment leads at $2.32M; "
                        "13 of 15 categories are addressable."),
    ),
    dict(
        id="03_suppliers", page="suppliers", actions=[("wait", 800)],
        narration=(
            "Suppliers. [[slnc 300]] Two hundred and forty five of them. The top ten hold "
            "about a fifth of spend, [[slnc 250]] which means four fifths sits in a long "
            "tail. That tail is the consolidation opportunity every category manager is "
            "looking for."
        ),
        popup=dict(title="Concentration and the tail", figure="Top 10 = 19.8%",
                   body="245 suppliers. Four-fifths of spend sits outside the top ten."),
    ),
    dict(
        id="04_contracts", page="contracts", actions=[("wait", 800)],
        narration=(
            "Contract compliance, and this is the page procurement leaders lean into. "
            "[[slnc 350]] Only about thirty percent of spend is on contract. [[slnc 300]] "
            "That's about three point three million dollars off contract, across the "
            "three companies. [[slnc 350]] That's savings you've already negotiated, "
            "leaking out."
        ),
        popup=dict(title="Contract leakage", figure="30.0% on contract",
                   body="$3.28M off contract. The controllable number."),
    ),
    dict(
        id="05_risk", page="risk", actions=[("wait", 900)],
        narration=(
            "Supplier risk. [[slnc 300]] Sixty four suppliers score seventy or higher, "
            "and two are single source. [[slnc 400]] Be clear about what this is. Risk, "
            "E S G and diversity scores here are representative values, the kind S A P "
            "Spend Intelligence or a third party provider would supply. The pattern is "
            "the point."
        ),
        popup=dict(title="Supplier risk", figure="64 high-risk",
                   body="Risk score 70+, 2 single-source. Representative enrichment values."),
    ),
    dict(
        id="06_sustainability", page="sustainability", actions=[("wait", 800)],
        narration=(
            "Sustainability and diversity. [[slnc 300]] An average E S G score of about "
            "sixty four, and fifty five diverse suppliers. [[slnc 350]] Again, "
            "representative. What's real is that it sits in the same model as spend, so "
            "an E S G target can be measured against actual purchasing."
        ),
        popup=dict(title="ESG and diversity", figure="55 diverse",
                   body="Average ESG 63.8. Representative values in the same governed model as spend."),
    ),
    dict(
        id="07_savings", page="savings", actions=[("wait", 800)],
        narration=(
            "The savings pipeline. [[slnc 300]] Five levers, each with the saving it "
            "typically delivers: [[slnc 200]] six percent for off contract consolidation, "
            "five for price variance, four for tail spend, three for demand management, "
            "two for payment terms. [[slnc 400]] About nine hundred thousand dollars in "
            "the pipeline, all representative, converted with the spend it sits on."
        ),
        popup=dict(title="Savings levers", figure="2–6% per lever",
                   body="75 representative opportunities across identified, in progress and realised."),
    ),
    dict(
        id="08_layers", page="lineage", actions=[("wait", 900)],
        narration=(
            "One honest detail about the build. [[slnc 300]] Five tables sit in the "
            "analytics layer, but only one of them, the spend fact, is a real dynamic "
            "table. The others hold enrichment values and don't refresh. [[slnc 350]] "
            "For live data, you'd fix that first, and swap the E C B rates for your own "
            "treasury rates."
        ),
        popup=dict(title="The layers, and two seams", figure="1 of 5 dynamic",
                   body="DT_SPEND_360 refreshes; enrichment tables do not. "
                        "FX rates come from an ECB rates table."),
    ),
    dict(
        id="09_agent", page="analyst", actions=[("wait", 1200)],
        narration=(
            "And then you can just ask. [[slnc 400]] The agent sits on a governed "
            "semantic view: four tables, twenty one dimensions, thirteen metrics. "
            "[[slnc 300]] It shows the S Q L it wrote, so an answer can be checked "
            "rather than trusted. [[slnc 350]] One limit: the agent doesn't use the "
            "currency switch yet, so ask it per company, or have it group by currency."
        ),
        popup=dict(title="Ask the Agent", figure="21 dims · 13 metrics",
                   body="Spend, suppliers, risk, taxonomy and savings. Ask per company, or group by currency."),
    ),
    dict(
        id="10_close", page="overview", actions=[("wait", 600)],
        narration=(
            "So that's Spend three sixty. [[slnc 350]] S A P procurement data, shared "
            "with zero copy, modelled once, and open to plain English questions. "
            "[[slnc 400]] Install it from the internal marketplace in your region, and "
            "you can run this demo today."
        ),
        popup=dict(title="SAP Spend 360", figure="3 regions",
                   body="Native App listing SPEND_360_ORG, published in three regions."),
    ),
]
