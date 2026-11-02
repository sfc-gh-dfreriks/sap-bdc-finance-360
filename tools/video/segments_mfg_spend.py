"""Script for the Multi-ERP Spend & Supplier Risk narrated walkthrough.

One entry per beat. Narration sets each segment's length; actions run BEFORE the
line starts, so each segment carries one visible change.

Every figure is read from /tmp/mfg_spend_facts.json, written by
mfg-use-cases/use_cases/01_multi_erp_spend/tools/spend_risk_facts.py from the live
app API. Nothing is hand-typed: regenerate the facts and re-run the build.

Time windows, said aloud where they matter:
  * Executive Dashboard, Supplier Risk, Golden Record: all PO history.
  * Price Variance: last four quarters.
  * Supplier Optimization: trailing twelve months.
The Cortex Recommendation and the Ask Cortex answer are generated live, so the
narration does not quote their figures.
"""

import json
import pathlib

FACTS = json.loads(pathlib.Path("/tmp/mfg_spend_facts.json").read_text())["facts"]
F = FACTS

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


g = F["golden"]
rc = F["risk_coverage"]
tiers = {t["tier"]: t for t in F["risk_tiers"]}
base, opt = F["opt_baseline"], F["opt_default"]
crit = next(i for i in F["top_issues"] if i["severity"] == "Critical")
sev = F["issues_by_severity"]
dbt = F["dbt_counts"]
tax_id = next(m["records"] for m in F["match_methods"] if m["method"] == "tax_id")

NAV = {
    "overview": "Executive Dashboard",
    "golden": "Supplier Golden Record",
    "price": "Price Variance Across Plants",
    "risk": "Supplier Risk",
    "opt": "Supplier Optimization",
    "sources": "Data Sources",
    "lineage": "Sources & Lineage (dbt)",
    "ask": "Ask Cortex",
}

SEGMENTS = [
    dict(
        id="00_problem", page="overview", actions=[("wait", 1500)],
        narration=(
            "Here's a manufacturer that grew by acquisition. [[slnc 350]] Two S A P instances of "
            "different vintages, one on E C C and one on S 4 HANA. [[slnc 300]] Plus acquired "
            "companies running Oracle E B S, Dynamics three sixty five and NetSuite, and Coupa for "
            "indirect spend. [[slnc 400]] Nobody can answer a simple question: what do we spend "
            "with each supplier, and how risky is it?"
        ),
        popup=dict(title="Six ERPs, one question", figure=f"{F['erps']} ERPs",
                   body="SAP ECC and S/4HANA, plus Oracle EBS, Dynamics 365, NetSuite and Coupa."),
    ),
    dict(
        id="01_dashboard", page="overview", actions=[("wait", 800)],
        narration=(
            f"This app answers it, on Snowflake. [[slnc 300]] Across all P O history, "
            f"{money(F['total_spend_usd'])} of spend, {words(F['po_lines'])} P O lines, "
            f"{words(F['suppliers_with_spend'])} suppliers and {words(F['plants'])} plants. "
            f"[[slnc 350]] Maverick spend, bought off contract, is {money(F['maverick_spend_usd'])}. "
            f"[[slnc 300]] The data is synthetic, but the shapes are real."
        ),
        popup=dict(title="Executive Dashboard · all history", figure=fig(F["total_spend_usd"]),
                   body=f"{F['po_lines']:,} PO lines · {F['suppliers_with_spend']} suppliers · "
                        f"{fig(F['maverick_spend_usd'])} maverick spend. Synthetic data."),
    ),
    dict(
        id="02_golden", page="golden", actions=[("wait", 1000)],
        narration=(
            f"It starts with one supplier, across every E R P. [[slnc 300]] "
            f"{words(g['source_records'])} supplier records from six systems resolve to "
            f"{words(g['golden'])} golden suppliers. [[slnc 300]] {words(g['multi_source'])} of them "
            f"appear in more than one E R P, often under a different spelling. [[slnc 300]] Most "
            f"are matched on tax I D, the rest on D U N S number or name and country."
        ),
        popup=dict(title="Supplier Golden Record", figure=f"{g['source_records']} → {g['golden']}",
                   body=f"{g['multi_source']} golden suppliers span several ERPs; "
                        f"{tax_id} records matched on tax ID."),
    ),
    dict(
        id="03_price", page="price", actions=[("wait", 1000)],
        narration=(
            f"Once suppliers and materials line up, plants can be compared. [[slnc 300]] Over the "
            f"last four quarters, {words(F['price_materials'])} materials are bought at more than "
            f"one plant at different prices. [[slnc 300]] Paying the best plant price everywhere "
            f"would save {money(F['price_savings_usd'])}, about {pct(F['price_savings_pct'])} of "
            f"that spend."
        ),
        popup=dict(title="Price Variance · last 4 quarters", figure=fig(F["price_savings_usd"]),
                   body=f"{F['price_materials']} materials bought at several plants; "
                        f"{F['price_savings_pct']:.1f}% saving at best plant price."),
    ),
    dict(
        id="04_risk", page="risk", actions=[("wait", 1000)],
        narration=(
            f"Supplier risk. [[slnc 300]] {words(rc['dnb_matched'])} of {words(rc['suppliers'])} "
            f"suppliers are matched to third party risk data. [[slnc 300]] "
            f"{words(F['high_risk_suppliers'])} are high or critical risk, carrying "
            f"{money(F['high_risk_spend_usd'])} across all history. [[slnc 300]] "
            f"{words(rc['single_source'])} are single source, and {words(rc['sanctions_hits'])} "
            f"hits a sanctions watchlist."
        ),
        popup=dict(title="Supplier Risk · all history", figure=fig(F["high_risk_spend_usd"]),
                   body=f"{F['high_risk_suppliers']} high or critical suppliers · "
                        f"{rc['single_source']} single-source · {rc['sanctions_hits']} sanctions hit."),
    ),
    dict(
        id="05_scenario", page="opt", actions=[("wait", 1500)],
        narration=(
            f"Now, what to do about it. [[slnc 300]] Supplier Optimization works on the trailing "
            f"twelve months, {money(base['spend'])} of spend. [[slnc 300]] Each lever is a "
            f"slider. At the default settings the scenario saves {money(opt['savings'])}, and "
            f"cuts the supplier count from {words(base['suppliers'])} to {words(opt['suppliers'])}."
        ),
        popup=dict(title="Scenario Builder · trailing 12 months", figure=fig(opt["savings"]),
                   body=f"Default levers: {base['suppliers']} → {opt['suppliers']} suppliers, "
                        f"on-contract {base['on_contract_pct']:.0%} → {opt['on_contract_pct']:.0%}."),
    ),
    dict(
        id="06_slider", page="opt", actions=[("set_range", 0, 0.9), ("wait", 1500)],
        narration=(
            "Push price harmonization from half to ninety percent captured, [[slnc 250]] and "
            "savings, supplier count and risk exposure recalculate at once. [[slnc 300]] "
            "Procurement can try a plan before committing to it."
        ),
        popup=dict(title="Move a lever", figure="Price capture 90%",
                   body="Every KPI recalculates as the slider moves."),
    ),
    dict(
        id="07_issues", page="opt",
        actions=[("set_range", 0, 0.5), ("click_button", "Issues & Remedies"), ("wait", 1500)],
        narration=(
            f"Behind the levers sit {words(F['issues_total'])} concrete issues: [[slnc 250]] "
            f"maverick spend, fragmented suppliers, plant price premiums, single source "
            f"sub-tiers. [[slnc 300]] {words(sev['Critical'])} is critical, and "
            f"{words(sev['High'])} are high."
        ),
        popup=dict(title="Issues & Remedies", figure=f"{F['issues_total']} issues",
                   body=f"{sev['Critical']} critical · {sev['High']} high · {sev['Medium']} medium, "
                        "each with a standard remedy."),
    ),
    dict(
        id="08_remedy", page="opt",
        actions=[("click_button", "Critical"), ("click_button", "Cortex remedy"),
                 ("wait_for_text", "Remedy steps", 90000)],
        narration=(
            f"The critical one is a sanctions hit: {crit['entity']}, still being paid through "
            f"two E R Ps. [[slnc 300]] Ask Cortex for a remedy, and it writes the steps from "
            f"the evidence: [[slnc 250]] the watchlist, the spend, the plants affected, and who "
            f"needs to act."
        ),
        popup=dict(title="Cortex remedy", figure="Sanctions exposure",
                   body=f"{crit['entity']} · {crit['evidence']['watchlist']} · "
                        f"{fig(crit['impact_usd'])} trailing-12-month spend."),
    ),
    dict(
        id="09_rec", page="opt",
        actions=[("dismiss", "div.fixed.inset-0.z-50"),  # close the remedy drawer
                 ("click_button", "Ask Cortex to recommend a scenario"),
                 ("wait_for_text", "Recommended levers", 150000), ("scroll_to", "Recommended levers")],
        narration=(
            "Or let Cortex propose the whole scenario. [[slnc 300]] It reads the issues and the "
            "baseline, sets every lever, [[slnc 200]] and explains why, with priority actions by "
            "category. [[slnc 300]] One click loads it into the scenario builder."
        ),
        popup=dict(title="Cortex Recommendation", figure="Recommended levers",
                   body="Cortex sets each lever and explains the reasoning; generated live."),
    ),
    dict(
        id="10_sources", page="sources", actions=[("wait", 1200)],
        narration=(
            "Here's what makes it portable. [[slnc 300]] Each S A P instance can be read four "
            "ways: [[slnc 200]] E C C tables, S 4 HANA tables, B W InfoProviders, or S A P B D C "
            "data products, zero copy. [[slnc 300]] The non S A P E R Ps each have their own "
            "adapter."
        ),
        popup=dict(title="Data Sources", figure="ECC · S/4 · BW · BDC",
                   body="Pick the SAP source type per instance; non-SAP ERPs have their own adapters."),
    ),
    dict(
        id="11_bdc", page="sources", actions=[("click_text", "Zero-copy data products"), ("wait", 1500)],
        narration=(
            "Switch the Americas instance to B D C, and the app is honest about the gaps. "
            "[[slnc 300]] B D C data products carry no goods receipts and no price conditions, "
            "so three way match drops to two way. [[slnc 300]] Apply would rebuild every layer "
            "with D B T; we won't press it here."
        ),
        popup=dict(title="Coverage gaps, shown not hidden", figure="SAP BDC",
                   body="No goods receipts · no price conditions. Apply rebuilds with dbt (not pressed)."),
    ),
    dict(
        id="12_lineage", page="lineage", actions=[("wait", 1200)],
        narration=(
            f"Sources and lineage. [[slnc 300]] One D B T project on Snowflake: "
            f"{words(dbt['sources'])} sources, {words(F['adapter_views'])} adapter views mapping "
            f"native tables to one canonical model, [[slnc 200]] and "
            f"{words(len(F['gold_dynamic_tables']))} gold dynamic tables. [[slnc 300]] "
            f"{words(dbt['models'])} models and {words(dbt['tests'])} tests in all."
        ),
        popup=dict(title="Sources & Lineage (dbt)", figure=f"{dbt['models']} models",
                   body=f"{dbt['sources']} sources · {F['adapter_views']} adapter views · "
                        f"{len(F['gold_dynamic_tables'])} gold dynamic tables · {dbt['tests']} tests."),
    ),
    dict(
        id="13_ask", page="ask",
        actions=[("click_button", "Analyse global spend and supplier risk"),
                 ("wait_for_text", "Recommended Actions", 120000), ("wait", 1500)],
        narration=(
            "And Ask Cortex. [[slnc 300]] One click, and Cortex analyses spend, risk, prices and "
            "payments over the gold layer, [[slnc 250]] with findings and recommended actions. "
            "[[slnc 300]] Its answers follow whichever sources you selected."
        ),
        popup=dict(title="Ask Cortex", figure="Cortex Agent",
                   body="Answers from the semantic view over the dbt gold layer, generated live."),
    ),
    dict(
        id="14_close", page="ask", actions=[("scroll", -3000), ("wait", 800)],
        narration=(
            "So: any S A P, whether E C C, S 4 HANA, B W or B D C, [[slnc 200]] plus the non S A P "
            "E R Ps that came with every acquisition, [[slnc 250]] in one spend and supplier risk "
            "view, on Snowflake. [[slnc 300]] The public demo and the source are linked at the end."
        ),
        popup=dict(title="Any SAP, plus non-SAP ERPs", figure="One view",
                   body="ECC, S/4HANA, BW or BDC, with Oracle EBS, Dynamics 365, NetSuite and Coupa."),
    ),
]
