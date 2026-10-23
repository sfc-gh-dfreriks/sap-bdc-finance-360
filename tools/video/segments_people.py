"""Script for the SAP People 360 narrated walkthrough.

One entry per beat. Each carries the narration (which sets the segment's length),
the caption card copy, and the actions that put the app in the right state.

Narration is written to be spoken, not read. Contractions, short sentences, and
`[[slnc n]]` pauses where a person would draw breath. Initialisms are spaced —
"S A P", "B D C", "H R" — because macOS `say` runs them together otherwise.
Figures are spelled out: "one hundred sixteen thousand" reads correctly aloud
where "$116,202" does not.

EVERY FIGURE HERE IS FROM /tmp/people_facts.json, verified 2026-09-24 against
SAP_PEOPLE_360 on account MSB89522.

FOUR HONESTY BEATS ARE SCRIPTED IN. This is workforce data, so a video that
glosses over its own limits is worse than useless — someone will find them live:

  * The people are synthetic. Said in the first twenty seconds, not buried.
  * Only DT_WORKFORCE_360 is a real dynamic table. The other three carry the
    DT_ prefix by convention and never refresh.
  * The semantic view covers ONE table, so the agent answers workforce questions
    only. Performance, learning and recruiting are dashboard-only.
  * Performance reviews stop at review year 2025 while everything else runs into
    2026 — there is no single "as of" date for this dataset.

THE ONBOARDING BEATS (07a-07f) run the live HR onboarding scenario end to end. Hire figures
are from the app on 2026-10-13 (Senior Engineer, US Operations, start = today + 17 days):
36 peer records, $127,200 offer, grade 5, 30% benefits load, $636 loaded cost per day; the
engineering laptop is backordered 42 days at the preferred reseller -> 17 idle workdays.
The laptop offers come from a LIVE web search and change every run, so the narration names
no vendor or price. Equipment, supplier and benefits data are demo enrichment, and the
SuccessFactors write-back is simulated (OData payload stored in Snowflake) - both said aloud.

Actions run at the start of a segment; the page then holds for whatever narration
time remains.
"""

# Page routes, by sidebar button label — navigation happens in-app, exactly as
# capture_shots.py does it. This app has no router to deep-link into.
NAV = {
    "overview": "Workforce Overview",
    "headcount": "Headcount",
    "diversity": "Diversity & Inclusion",
    "compensation": "Compensation",
    "attrition": "Attrition",
    "performance": "Performance",
    "learning": "Learning",
    "recruiting": "Recruiting",
    "org": "Org & Span",
    "employees": "Employees",
    "lineage": "BDC Sources & Lineage",
    "analyst": "Ask the Agent",
    "onboarding": "Onboarding Scenario",
}

SEGMENTS = [
    # ------------------------------------------------------------ opening
    dict(
        id="00_open", page="overview", actions=[],
        narration=(
            "This is workforce analytics on S A P B D C data, using B D C Connect "
            "zero copy. [[slnc 450]] Twelve hundred and ninety two active employees, "
            "across twelve departments and three operating companies — and not one "
            "row of it was copied out of S A P. [[slnc 400]] One thing first, "
            "because it matters more here than anywhere else: these people are not "
            "real. It's a synthetic dataset. No names, no real records, invented "
            "identifiers."
        ),
        popup=dict(title="SAP People 360", figure="1,292 active",
                   body="Twelve departments across three companies — read from an "
                        "SAP BDC workforce share. Synthetic data: no real employees."),
    ),
    dict(
        id="01_zero_copy", page="lineage", actions=[("wait", 1200)],
        narration=(
            "Here's the part worth pausing on. [[slnc 300]] B D C Connect shares the "
            "workforce data product straight into Snowflake, and between that share "
            "and this application there is exactly one view. [[slnc 350]] Not a "
            "copy — a passthrough view. Nobody built a pipeline to move H R data "
            "anywhere, which is usually the exact objection that stops a project "
            "like this."
        ),
        popup=dict(title="One view, zero copies", figure="no pipeline",
                   body="SAP_BDC_L1.WORKFORCE is a passthrough view over the "
                        "zero-copy share. No extract of employee data exists."),
    ),

    # ------------------------------------------------------------ the business
    dict(
        id="02_attrition", page="attrition", actions=[("wait", 800)],
        narration=(
            "Attrition. [[slnc 300]] Two hundred and eight terminations in the "
            "dataset — about fourteen percent of all the records here. [[slnc 400]] "
            "Be careful with that number. It's terminations as a share of every "
            "record, not an annual rate. If someone quotes it as annual attrition "
            "in a board pack, it's wrong."
        ),
        popup=dict(title="Attrition", figure="208 terminations",
                   body="13.9% of all records — NOT an annualised rate. By year, "
                        "reason and department."),
    ),
    dict(
        id="03_compensation", page="compensation", actions=[("wait", 800)],
        narration=(
            "Compensation. [[slnc 250]] Average base pay is about one hundred and "
            "sixteen thousand dollars, and the compa ratio sits almost exactly on "
            "one. [[slnc 400]] That means, on average, people are paid at the "
            "midpoint of the band S A P already holds for their grade. The "
            "comparison isn't something an analyst reconstructed — it came across "
            "with the record."
        ),
        popup=dict(title="Pay against the band", figure="compa-ratio 1.004",
                   body="$116,202 average base. The range midpoint comes from "
                        "SuccessFactors, so the comparison is SAP's own."),
    ),
    dict(
        id="04_diversity", page="diversity", actions=[("wait", 800)],
        narration=(
            "Representation. [[slnc 300]] Forty four percent of the active "
            "workforce is female, and just over half hold a managerial role. "
            "[[slnc 400]] There's no editorial here. The point is simply that it's "
            "measurable at all, by department, without anyone exporting a "
            "spreadsheet of employees to count it."
        ),
        popup=dict(title="Representation", figure="44.3% female",
                   body="51.7% of the active population are managers. Measurable "
                        "by department without an export."),
    ),
    dict(
        id="05_org", page="org", actions=[("wait", 900)],
        narration=(
            "Span of control, and this is the page that tends to change the "
            "conversation. [[slnc 350]] A hundred and ninety six positions are "
            "flagged critical. [[slnc 400]] That's succession exposure made "
            "visible — the roles where one resignation becomes a gap, rather than a "
            "worry someone raises in a meeting."
        ),
        popup=dict(title="Succession exposure", figure="196 critical roles",
                   body="Span of control with critical positions flagged on the "
                        "record — the flag is SAP's, so the definition is yours."),
    ),

    # ------------------------------------------------------------ the lifecycle
    dict(
        id="06_performance", page="performance", actions=[("wait", 800)],
        narration=(
            "Performance. [[slnc 250]] Two and a half thousand reviews, "
            "distributed the way real review cycles are — most people meeting "
            "expectations, a long tail either side. [[slnc 450]] And a caveat you "
            "should say out loud: these reviews stop at twenty twenty five. Hiring "
            "and learning data runs into twenty twenty six. There is no single "
            "as of date for this dataset."
        ),
        popup=dict(title="Performance", figure="2,584 reviews",
                   body="Review years 2024 to 2025 only — a year behind hiring, "
                        "learning and recruiting. Windows differ per table."),
    ),
    dict(
        id="07_recruiting", page="recruiting", actions=[("wait", 800)],
        narration=(
            "Recruiting. [[slnc 300]] A hundred and sixty requisitions — eighty "
            "filled, sixty two still open, eighteen cancelled. [[slnc 400]] Put "
            "that next to the critical roles from a moment ago and hiring demand "
            "stops being a queue you react to. It becomes something you can see "
            "coming."
        ),
        popup=dict(title="Recruiting", figure="62 open reqs",
                   body="160 requisitions: 80 filled, 62 open, 18 cancelled — "
                        "read against the 196 critical positions."),
    ),

    # ------------------------------------------------------------ onboarding scenario (live)
    dict(
        id="07a_onb_hire", page="onboarding", actions=[("wait_for_text", "Check onboarding equipment", 30000), ("wait", 800)],
        narration=(
            "Now a scenario that uses this data instead of just reporting on it. "
            "[[slnc 350]] A new hire — a senior engineer joining U S Operations. "
            "[[slnc 300]] The offer isn't typed in. It's derived from thirty six "
            "people already in that role: one hundred and twenty seven thousand "
            "dollars, pay grade five. [[slnc 350]] Add benefits, and every working "
            "day this person sits idle costs about six hundred and thirty six dollars."
        ),
        popup=dict(title="HR onboarding, end to end", figure="$636 / idle day",
                   body="Offer derived from 36 peer records in SuccessFactors: $127,200, "
                        "grade 5, 30% benefits load."),
    ),
    dict(
        id="07b_onb_kit", page="onboarding",
        actions=[("click_button", "Check onboarding equipment"), ("wait_for_text", "Supply-chain disruption", 30000),
                 ("scroll_to", "2. Equipment availability"), ("wait", 600)],
        narration=(
            "Next, the equipment kit for their start date. [[slnc 300]] Badge, "
            "monitor, dock — all in stock. [[slnc 250]] The laptop isn't. The "
            "preferred reseller has it on backorder, forty two days out. "
            "[[slnc 400]] That's seventeen working days without a machine — close to "
            "eleven thousand dollars of paid, idle time before they've written a "
            "line of code."
        ),
        popup=dict(title="The disruption", figure="17 idle workdays",
                   body="Engineering laptop backordered 42 days at the preferred "
                        "channel ≈ $10.8K of idle loaded cost."),
    ),
    dict(
        id="07c_onb_search", page="onboarding",
        actions=[("click_button", "Search the web for alternatives"), ("wait", 600)],
        narration=(
            "So the app goes looking. [[slnc 300]] It runs a live web search for the "
            "same spec, reads the retailer pages that come back, and Cortex A I "
            "extracts real offers from them — vendor, model, price and ship time. "
            "[[slnc 400]] One rule matters here. If a price isn't on the page it "
            "cites, the offer is dropped. [[slnc 300]] Nothing is invented, and "
            "every option links to its source."
        ),
        popup=dict(title="Live alternative sourcing", figure="web search + Cortex",
                   body="Offers extracted from the cited pages by AI_COMPLETE. "
                        "No price on the page, no offer."),
    ),
    dict(
        id="07d_onb_results", page="onboarding",
        actions=[("wait_for_text", "3. Cost / time analysis", 150000), ("scroll_to", "3. Cost / time analysis"), ("wait", 800)],
        narration=(
            "Here's the comparison. [[slnc 300]] Each option is scored on total "
            "impact — the hardware, plus the idle days it would still cost. "
            "[[slnc 350]] A machine that ships in two days usually costs less "
            "than the preferred laptop once you count the waiting. [[slnc 300]] "
            "Spec match is flagged too, so a cheaper but weaker machine doesn't "
            "slip through."
        ),
        popup=dict(title="Cost against time", figure="total impact",
                   body="Hardware cost + idle workdays × loaded daily cost. "
                        "Results are live, so they differ run to run."),
    ),
    dict(
        id="07e_onb_pick", page="onboarding",
        actions=[("click_css", "tbody tr.cursor-pointer:has-text(\"Reseller in stock\")"), ("wait", 900)],
        narration=(
            "Pick one, [[slnc 250]] and the chart shows where it sits against the "
            "preferred channel — lead time across, cost up the side. [[slnc 350]] "
            "The decision is one an H R coordinator can make in a minute, with the "
            "reasoning on screen."
        ),
        popup=dict(title="Choose a substitute", figure="one click",
                   body="The selected offer is plotted against the preferred "
                        "channel; net benefit is shown per option."),
    ),
    dict(
        id="07f_onb_writeback", page="onboarding",
        actions=[("click_button", "Substitute & write back to SuccessFactors"), ("wait_for_text", "4. Written back", 60000),
                 ("scroll_to", "4. Written back"), ("wait", 800)],
        narration=(
            "And it closes the loop. [[slnc 300]] The hire, the compensation record "
            "and the equipment request go back to SuccessFactors, with the sourcing "
            "decision kept for audit. [[slnc 400]] Two honest notes. In this demo "
            "the write back is simulated — the OData payload is stored in Snowflake "
            "rather than posted. And the inventory, supplier and benefits data is "
            "demo enrichment, not S A P."
        ),
        popup=dict(title="Written back (simulated)", figure="hire + kit + decision",
                   body="EmpJob / EmpCompensation / equipment request payloads stored "
                        "in Snowflake with the sourcing decision. Inventory and "
                        "supplier data are demo enrichment."),
    ),

    # ------------------------------------------------------------ the platform
    dict(
        id="08_layers", page="lineage", actions=[("wait", 1000)],
        narration=(
            "This page is the receipt. [[slnc 350]] It shows which S A P B D C "
            "objects feed each layer, inside the application rather than in a "
            "diagram. [[slnc 400]] One honest detail while we're here. Four tables "
            "sit in the analytics layer, but only one of them is a real dynamic "
            "table. The other three carry the same naming prefix and never refresh. "
            "For live data you'd fix that first."
        ),
        popup=dict(title="The layers, and a seam", figure="1 of 4 dynamic",
                   body="7,445 rows across four analytics tables. Only "
                        "DT_WORKFORCE_360 refreshes; the prefix is convention, "
                        "not a guarantee."),
    ),
    dict(
        id="09_agent", page="analyst", actions=[("wait", 1200)],
        narration=(
            "And then you can just ask. [[slnc 400]] Cortex Analyst sits on a "
            "governed semantic view — nineteen dimensions and eight facts — and it "
            "shows you the S Q L it wrote, so an answer can be checked instead of "
            "trusted. [[slnc 450]] The limit is worth stating. That view covers the "
            "workforce table only. Headcount, attrition, pay, tenure, diversity — "
            "all fine. Performance, learning and recruiting are on the dashboards "
            "but not yet available to the agent."
        ),
        popup=dict(title="Ask the Agent", figure="19 dims · 8 facts",
                   body="Workforce table only. Performance, learning and recruiting "
                        "are dashboard-only — extending the model is the next step."),
    ),
    dict(
        id="10_close", page="overview", actions=[("wait", 600)],
        narration=(
            "So that's the whole thing. [[slnc 400]] B D C Connect for the share, "
            "one passthrough view over it, a thin modelling layer, and natural "
            "language on top. "
            "[[slnc 400]] No employee data was copied anywhere to make this work. "
            "[[slnc 350]] Which means the real next conversation isn't about "
            "dashboards — it's about who's allowed to see compensation, and that's "
            "enforced by the platform rather than by who has the spreadsheet."
        ),
        popup=dict(title="Governance is the real question",
                   figure="nothing copied",
                   body="Masking and row access policies decide who sees pay — "
                        "enforced in Snowflake, not by spreadsheet convention."),
    ),
]
