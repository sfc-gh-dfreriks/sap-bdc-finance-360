"""Script for the SAP Sales 360 narrated walkthrough.

One entry per beat. Each carries the narration (which sets the segment's length),
the caption card copy, and the actions that put the app in the right state.

Narration is written to be spoken, not read. Contractions, short sentences, and
`[[slnc n]]` pauses where a person would draw breath. Figures are spelled out —
"one point nine billion" reads correctly aloud where "$1,903,302,819" does not.

EVERY FIGURE HERE IS FROM /tmp/sales_facts.json, verified 2026-09-21 against
SAP_SALES_360 on account MSB89522. Two caveats are scripted in deliberately,
because both are the kind a sharp customer architect finds in the first ten
minutes and neither survives being discovered rather than disclosed:

  * The open pipeline is ENTIRELY past due. All 3,201 open opportunities have a
    close date in the past and not one has a future date. That is a demo-data
    artifact, and it means the forecast page shows method, not a real forecast.
  * L1 here is NOT zero-copy. Unlike Finance 360's six passthrough views, Sales
    360's L1 is 31 materialised plain tables, and 1,437,370 rows are duplicated
    between L1 and L2. It works, but it is a copy, and it should be called one.

The win-rate beat is the analytically interesting one: 50.4% of deals are won by
count but only 43.8% by value, because the deals they lose are materially larger
than the deals they win. That contrast is real in the data, not a talking point.
"""

# Page routes, by sidebar button label — navigation happens in-app, exactly as
# capture_shots.py does it.
NAV = {
    "dashboard": "Dashboard",
    "funnel": "Sales Funnel",
    "health": "Customer Health",
    "products": "Products",
    "leaderboard": "Rep Leaderboard",
    "forecast": "Sales Forecast",
    "chat": "Ask the Agent",
}

SEGMENTS = [
    # ------------------------------------------------------------ opening
    dict(
        id="00_open", page="dashboard", actions=[],
        narration=(
            "This is a sales organisation's entire book, running on S A P data in "
            "Snowflake. [[slnc 450]] Three thousand seven hundred seventy-four "
            "opportunities, eight reps, and two hundred thirty million dollars of "
            "quota to cover. [[slnc 350]] Pipeline, quota, forecast and customer "
            "health, in one place."
        ),
        popup=dict(title="SAP Sales 360", figure="3,774 opportunities",
                   body="Eight reps carrying $229,988,389 of quota — pipeline, "
                        "health and forecast over SAP CRM data in Snowflake."),
    ),
    dict(
        id="01_scale", page="dashboard", actions=[("wait", 1200)],
        narration=(
            "And one architectural note up front, because it differs from our "
            "finance application. [[slnc 400]] Sales 360's landing layer is thirty-one "
            "materialised tables — about two and a half million rows. [[slnc 350]] "
            "That's a copy, not a passthrough view. It performs well, but I'm going "
            "to call it what it is."
        ),
        popup=dict(title="L1 is materialised, not zero-copy",
                   figure="31 tables · 2.55M rows",
                   body="Unlike Finance 360's six passthrough views, this L1 is a "
                        "physical copy. 1,437,370 rows are duplicated into L2."),
    ),

    # ------------------------------------------------------------ the funnel
    dict(
        id="02_funnel", page="funnel", actions=[("wait", 900)],
        narration=(
            "The funnel. [[slnc 300]] One point nine billion dollars of open "
            "pipeline. Two hundred three million won, two hundred sixty million "
            "lost. [[slnc 400]] Four thousand deals, staged from needs analysis "
            "through to close."
        ),
        popup=dict(title="Pipeline and outcomes", figure="$1.9B open",
                   body="Won $203.3M across 289 deals; lost $260.6M across 284. "
                        "Every figure computed live from L2."),
    ),
    dict(
        id="03_winrate", page="funnel", actions=[("wait", 600)],
        narration=(
            "Now look at those two numbers together. [[slnc 400]] They win half "
            "their deals — fifty point four percent by count. [[slnc 350]] But only "
            "forty-three point eight percent by value. [[slnc 400]] Average deal "
            "won, seven hundred three thousand dollars. Average deal lost, nine "
            "hundred seventeen thousand. [[slnc 350]] They're losing the big ones. "
            "That's the finding, and no leaderboard would have shown it."
        ),
        popup=dict(title="They lose the larger deals",
                   figure="50.4% count · 43.8% value",
                   body="Avg won $703K against avg lost $917K. Win rate by count "
                        "flatters a book that is leaking at the top end."),
    ),
    dict(
        id="04_pastdue", page="funnel", actions=[("wait", 600)],
        narration=(
            "And the caveat you'd find yourself. [[slnc 400]] Every single open "
            "opportunity in here is past due. All three thousand two hundred and "
            "one of them, one point nine billion dollars, and not one with a close "
            "date in the future. [[slnc 450]] That's demo data, not a pipeline "
            "problem. It does mean the forecast page is showing you method rather "
            "than a live call."
        ),
        popup=dict(title="The whole open book is past due",
                   figure="3,201 of 3,201",
                   body="Zero open opportunities carry a future close date. A "
                        "data-generation artifact — disclosed, not hidden."),
    ),

    # ------------------------------------------------------------ the book
    dict(
        id="05_health", page="health", actions=[("wait", 900)],
        narration=(
            "Customer health. [[slnc 300]] This is the retention lens — who's "
            "engaged, who's gone quiet, and which accounts are worth a call this "
            "week. [[slnc 350]] It reads the same modelled layer as everything "
            "else, so a number here can't disagree with a number on the funnel."
        ),
        popup=dict(title="Customer health", figure="one shared layer",
                   body="Health, funnel and forecast all read SALES_360_L2, so no "
                        "two pages can disagree about the same account."),
    ),
    dict(
        id="06_products", page="products", actions=[("wait", 900)],
        narration=(
            "Product performance, from the order side rather than the opportunity "
            "side. [[slnc 400]] This is where S A P's sales order items earn their "
            "keep — seven hundred thirty-five thousand line items behind this page."
        ),
        popup=dict(title="Product mix", figure="735K order items",
                   body="SALESORDERS_SALESORDERITEM — actual booked lines, not "
                        "opportunity estimates."),
    ),
    dict(
        id="07_leaderboard", page="leaderboard", actions=[("wait", 900)],
        narration=(
            "The leaderboard. [[slnc 300]] Eight reps against quota. [[slnc 350]] "
            "And this is a page you'd hand to a sales manager on a Monday without "
            "explaining it first — which is the real test of whether a dashboard "
            "works."
        ),
        popup=dict(title="Attainment by rep", figure="8 reps",
                   body="Quota coverage per rep against $229,988,389 of total "
                        "quota, computed from booked revenue."),
    ),
    dict(
        id="08_forecast", page="forecast", actions=[("wait", 1000)],
        narration=(
            "Forecast. [[slnc 350]] Three of the fourteen tables in the modelled "
            "layer are machine-learning outputs — predictions and attainment, "
            "written back as tables so the application reads them like anything "
            "else. [[slnc 400]] Monthly attainment runs from eighty percent up to "
            "a hundred and eighteen, so there's genuine variance in here to model, "
            "not a flat line."
        ),
        popup=dict(title="Forecast and ML outputs",
                   figure="80% – 118% monthly",
                   body="Three ML tables land alongside 11 dynamic tables. Real "
                        "attainment spread, standard deviation 9.4 points."),
    ),

    # ------------------------------------------------------------ the agent
    dict(
        id="09_agent", page="chat", actions=[("wait", 1400)],
        narration=(
            "And then you stop clicking and just ask. [[slnc 400]] There's a Cortex "
            "Agent behind this page, wired to text-to-S Q L over the semantic model. "
            "[[slnc 350]] Sixty-four tables and three hundred sixty-nine dimensions "
            "are reachable from a plain English question."
        ),
        popup=dict(title="Cortex Agent", figure="64 tables reachable",
                   body="SAP_SALES_360_AGENT with cortex_analyst_text_to_sql over "
                        "a 369-dimension semantic view."),
    ),
    dict(
        id="10_close", page="dashboard", actions=[("wait", 600)],
        narration=(
            "So — pipeline, health, product, quota, forecast and an agent, over S A P "
            "data in Snowflake. [[slnc 450]] Two things to fix before a customer "
            "deployment: make L1 a passthrough instead of a copy, and give the open "
            "pipeline real close dates. [[slnc 350]] Everything else here is ready "
            "to show."
        ),
        popup=dict(title="What to fix first",
                   figure="2 known gaps",
                   body="Make L1 zero-copy like Finance 360, and regenerate open "
                        "opportunity close dates. The rest is demo-ready."),
    ),
]
