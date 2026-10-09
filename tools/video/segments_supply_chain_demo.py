"""Script for the SAP Supply Chain demo: Snowsight -> Supply Chain 360 -> Supply Chain Ontology.

One entry per beat. Each carries the narration (which sets the segment's length),
the caption card copy, the app it runs in, and the actions that put that app in
the right state. A segment whose page has no NAV entry navigates by its actions.

Narration is written to be spoken: initialisms spaced ("S A P", "B D C", "O E E"),
figures spelled out, `[[slnc n]]` pauses where a person would breathe.

FIGURES are what the apps return on their default views, pulled on 2026-10-06:
  * Snowsight: connector SAP_BDC_CONNECT_ZC, Connected; 9 data products shared,
    9 mounted, 0 errors (SalesBillOfMaterial mounted 2026-10-06 12:15) (e.g. CUSTOMER_V1, 11 tables).
  * Supply Chain 360 /api/overview (all 5 plants): 20 production orders, OEE 83.5%,
    on-time delivery 89.5% (average of plant monthly KPIs), yield 82.6%,
    scrap 2.02%, inventory turns 8.5.
  * Cortex Analyst, "What is the overall on-time delivery rate?": 68.0% across
    25 deliveries, answered from the verified query ON_TIME_DELIVERY_RATE.
    That is delivery-level, so it differs from the plant-KPI average above.
  * Ontology: 15 classes, 11 relations. Hurricane, Austin Fab offline:
    $16.1M monthly value at risk (28.3% of network), 4 customers, Penang impaired
    two hops out; plan protects $13.8M (91.4%) by rerouting to San Jose HQ
    (utilization 89.1% -> 98.6%); $1.3M unmitigable (Die Sorting for TSMC).

  * OPS_EXT pages (pulled 2026-10-08, all plants): 420 orders, OTIF 71.7%, 119 late,
    late cost $4.40M; component shortage is the top cause (67 orders, $2.73M);
    San Jose HQ OTIF 59.7% carrying $3.23M. Equipment: 2 tools at high risk,
    Stepper LIT2-1 at Austin 51% 48-hour failure probability, $622K value at risk.
    Components: 10 Critical, 15 Watch of 48; e.g. San Jose vacuum chamber 3 days of
    cover vs 28-day lead time. OPS_EXT is representative demo data, said on screen.

HONESTY BEAT: Supply Chain 360's L0 objects are BDC-shaped native tables that
follow the SAP BDC data product structures; they are not the mounted zero-copy
shares shown in Snowsight. The lineage segment says so.
"""

SNOWSIGHT = "https://app.snowflake.com/sfsenorthamerica/dfreriks_aws1_w2/"

# Page ids are prefixed by app because both apps have an "overview".
NAV = {
    # Supply Chain 360
    "sc_overview": "Executive Overview",
    "sc_optimization": "SC Optimization",
    "sc_forecasting": "SC Forecasting",
    "sc_fulfillment": "Fulfillment & Constraints",
    "sc_equipment": "Equipment Health",
    "sc_components": "Components & Digital Thread",
    "sc_lineage": "BDC Sources & Lineage",
    "sc_analyst": "Cortex Analyst",
    "sc_ontology": "Supply Chain Ontology",
    # Supply Chain Ontology app
    "on_overview": "Overview",
    "on_catalog": "SAP BDC Catalog",
    "on_scenario": "Scenario Studio",
    "on_ripple": "Ripple Map",
    "on_mitigation": "Mitigation",
    "on_optimize": "Optimization Map",
    # Snowsight pages navigate by actions, so they have no entry
}

SEGMENTS = [
    # ------------------------------------------------------------- Snowsight
    dict(
        id="00_open", app="snowsight", page="ss_zero_copy",
        actions=[("goto", SNOWSIGHT + "#/ingestion/zero-copy", 4000)],
        narration=(
            "This is S A P supply chain data, end to end on Snowflake. [[slnc 400]] "
            "We start in Snowsight, on the Zero Copy page. [[slnc 250]] S A P Business "
            "Data Cloud Connect lets S A P data products appear in Snowflake without "
            "copying a single row."
        ),
        popup=dict(title="Snowsight · Ingestion · Zero-Copy", figure="Zero copy",
                   body="SAP BDC Connect for Snowflake shares SAP data products "
                        "without moving data."),
    ),
    dict(
        id="01_connection", app="snowsight", page="ss_zero_copy",
        actions=[("click_role", "tab", "Available connectors"),
                 ("wait_for_text", "SAP_BDC_CONNECT_ZC", 60000)],
        narration=(
            "Here's our connection. [[slnc 250]] S A P underscore B D C underscore "
            "connect, [[slnc 150]] status: connected. [[slnc 350]] This is the link "
            "between our S A P Business Data Cloud tenant and this Snowflake account."
        ),
        popup=dict(title="Zero-copy connection", figure="Connected",
                   body="SAP_BDC_CONNECT_ZC links the SAP BDC tenant to this account."),
    ),
    dict(
        id="02_mounted", app="snowsight", page="ss_connector",
        actions=[("click_text", "SAP_BDC_CONNECT_ZC"),
                 ("wait_for_text", "CUSTOMER_V1", 90000), ("wait", 1500)],
        narration=(
            "Open it, and we see what S A P is sharing. [[slnc 300]] Nine data "
            "products shared, [[slnc 150]] all nine mounted, [[slnc 150]] zero errors. "
            "[[slnc 350]] Each mounted product is a catalog linked database. [[slnc 200]] "
            "Customer, for example, arrives as eleven tables, queryable in place."
        ),
        popup=dict(title="Mounted SAP BDC data products", figure="9 of 9 mounted",
                   body="Each mounted product is a catalog-linked database, "
                        "e.g. CUSTOMER_V1 with 11 tables. 0 errors."),
    ),

    # ------------------------------------------------------- Supply Chain 360
    dict(
        id="03_sc_overview", app="sc360", page="sc_overview", actions=[("wait", 1500)],
        narration=(
            "Now the Supply Chain three sixty app, running on Snowflake. [[slnc 350]] "
            "The executive overview covers five plants and twenty production orders. "
            "[[slnc 300]] Overall equipment effectiveness is eighty three and a half "
            "percent, [[slnc 150]] yield eighty two point six, [[slnc 150]] and "
            "inventory turns eight and a half times."
        ),
        popup=dict(title="Executive Overview", figure="OEE 83.5%",
                   body="5 plants · 20 production orders · yield 82.6% · "
                        "scrap 2.02% · inventory turns 8.5."),
    ),
    dict(
        id="04_ai_recommend", app="sc360", page="sc_optimization",
        actions=[("click_role", "tab", "AI Recommendations"),
                 ("wait_for_text", "Supplier Risk Alert", 20000)],
        narration=(
            "S C optimization turns those signals into recommendations. [[slnc 300]] "
            "Pre position inventory at Austin and Singapore ahead of demand. [[slnc 250]] "
            "Audit a supplier whose defect rate is climbing, and line up a backup. "
            "[[slnc 250]] Plus predictive maintenance, inventory, route and production scheduling."
        ),
        popup=dict(title="SC Optimization · AI Recommendations", figure="6 recommendations",
                   body="Demand, supplier risk, predictive maintenance, inventory, "
                        "route and production scheduling."),
    ),
    dict(
        id="05_forecast", app="sc360", page="sc_forecasting", actions=[("wait", 1500)],
        narration=(
            "S C forecasting projects demand forward. [[slnc 300]] The solid line is "
            "history from production orders. [[slnc 200]] The dashed line is the "
            "projection, from a three month moving average, so planners see where "
            "demand is heading by plant."
        ),
        popup=dict(title="SC Forecasting · AI projections", figure="Projected demand",
                   body="Historical production demand with a 3-month moving-average "
                        "projection (dashed line)."),
    ),
    # ------------------------------------------------- operations extension
    dict(
        id="05a_fulfillment", app="sc360", page="sc_fulfillment",
        # Start the Ask Cortex request here: the answer takes ~40s to generate,
        # and this beat plus the next one narrate over most of that wait.
        actions=[("wait_for_text", "Late cost by root cause", 30000),
                 ("click_button", "Ask Cortex: summarise fulfillment")],
        narration=(
            "Fulfillment and constraints asks the question customers actually feel. "
            "[[slnc 300]] Seventy two percent of four hundred and twenty orders shipped "
            "on time and in full. [[slnc 250]] The late ones cost four point four million "
            "dollars in penalties and expedite freight, [[slnc 200]] and component "
            "shortages caused over half of it."
        ),
        popup=dict(title="Fulfillment & Constraints", figure="71.7% OTIF · $4.4M late cost",
                   body="Order-level OTIF with root cause and late cost. OPS_EXT "
                        "demo enrichment keyed to SAP plants and materials."),
    ),
    dict(
        id="05b_ask_cortex", app="sc360", page="sc_fulfillment",
        actions=[("wait", 500)],
        narration=(
            "Every page has an Ask Cortex button. [[slnc 250]] It hands the numbers "
            "on screen to a Cortex model, [[slnc 200]] so the answer cites these plants "
            "and these dollars, [[slnc 150]] not generic advice."
        ),
        popup=dict(title="Ask Cortex", figure="Grounded in this view",
                   body="SNOWFLAKE.CORTEX.COMPLETE over the SQL facts behind the page."),
    ),
    dict(
        id="05c_ask_answer", app="sc360", page="sc_fulfillment",
        # The follow-up chips render only once the answer is in; "San Jose"
        # alone would match the sidebar's plant filter immediately.
        actions=[("wait_for_text", "Is equipment or components the bigger constraint", 120000)],
        narration=(
            "And it goes straight to San Jose. [[slnc 250]] Under sixty percent on "
            "time, [[slnc 150]] and three point two million of the late cost, "
            "[[slnc 200]] most of it from components that ran out."
        ),
        popup=dict(title="Cortex analysis", figure="San Jose HQ · 59.7% OTIF",
                   body="$3.23M of the $4.40M late cost sits at one plant."),
    ),
    dict(
        id="05d_equipment", app="sc360", page="sc_equipment",
        actions=[("wait_for_text", "Tools at high risk", 30000), ("wait", 800)],
        narration=(
            "Equipment health watches the tools that make the systems. [[slnc 300]] "
            "Two are at high risk. [[slnc 200]] The stepper on Austin's lithography "
            "line has about a fifty percent chance of failing in the next two days, "
            "[[slnc 200]] with six hundred thousand dollars of output riding on it."
        ),
        popup=dict(title="Equipment Health", figure="2 tools at high risk",
                   body="Stepper LIT2-1, Austin Fab: 51% 48-hour failure probability. "
                        "$622K value at risk."),
    ),
    dict(
        id="05e_components", app="sc360", page="sc_components",
        actions=[("wait", 2000)],
        narration=(
            "And components shows why the shortages happen. [[slnc 300]] Ten parts "
            "have less cover than their supplier lead time, [[slnc 200]] so the "
            "shortage is already locked in. [[slnc 250]] San Jose has three days of "
            "vacuum chambers, on a twenty eight day lead time."
        ),
        popup=dict(title="Components & Digital Thread", figure="10 critical components",
                   body="Days of cover vs supplier lead time. San Jose vacuum chamber: "
                        "3 days of cover, 28-day lead time."),
    ),
    dict(
        id="06_lineage", app="sc360", page="sc_lineage",
        actions=[("wait_for_text", "Honesty note", 60000), ("wait", 1000)],
        narration=(
            "B D C sources and lineage shows where every number comes from. [[slnc 300]] "
            "Twenty one S A P data products across manufacturing and logistics, "
            "[[slnc 200]] layered into nine curated tables. [[slnc 350]] One honest "
            "note: [[slnc 150]] in this demo the source tables follow the B D C data "
            "product structures, rather than being the mounted shares we just saw."
        ),
        popup=dict(title="BDC Sources & Lineage", figure="21 data products",
                   body="S/4HANA Manufacturing and Logistics → 9 curated tables. "
                        "Demo sources are BDC-shaped, not the mounted shares."),
    ),
    dict(
        id="07_analyst_ask", app="sc360", page="sc_analyst",
        actions=[("type_slow", "input[placeholder^='Ask a question']",
                  "What is the overall on-time delivery rate?"),
                 ("press", "Enter")],
        narration=(
            "Anyone can just ask. [[slnc 250]] Cortex Analyst turns a plain English "
            "question into S Q L, [[slnc 200]] using a semantic model of the supply chain."
        ),
        popup=dict(title="Ask Cortex Analyst", figure="Natural language",
                   body="“What is the overall on-time delivery rate?”"),
    ),
    dict(
        id="08_analyst_answer", app="sc360", page="sc_analyst",
        actions=[("wait_for_text", "interpretation", 90000), ("wait", 4000),
                 ("click_role", "button", "Table"), ("wait", 1500)],
        narration=(
            "The answer: sixty eight percent, across twenty five deliveries. "
            "[[slnc 300]] It used a verified query, so the S Q L is one we've already "
            "checked. [[slnc 300]] That's counted delivery by delivery, which is why "
            "it differs from the plant average on the overview."
        ),
        popup=dict(title="Answered from a verified query", figure="68% on time",
                   body="25 deliveries · verified query ON_TIME_DELIVERY_RATE · "
                        "delivery-level, unlike the plant KPI average."),
    ),
    dict(
        id="09_sc_ontology", app="sc360", page="sc_ontology", actions=[("wait", 2500)],
        narration=(
            "The supply chain ontology page connects it all. [[slnc 300]] Plants, "
            "suppliers, materials and customers, [[slnc 150]] linked by the flows "
            "between them."
        ),
        popup=dict(title="Supply Chain Ontology", figure="19 nodes · 27 flows",
                   body="Plants, suppliers, materials and customers as a connected network."),
    ),

    # --------------------------------------------------- Supply Chain Ontology
    dict(
        id="10_on_open", app="ontology", page="on_overview",
        actions=[("wait_for_text", "Ontology completeness", 30000), ("wait", 2000)],
        narration=(
            "For deeper what if analysis, we switch to the Supply Chain Ontology app. "
            "[[slnc 300]] Fifteen classes and eleven relations, [[slnc 150]] stored in "
            "Snowflake as a knowledge graph."
        ),
        popup=dict(title="Supply Chain Ontology app", figure="15 classes · 11 relations",
                   body="An ontology layer in SAP_SUPPLY_CHAIN.ONTOLOGY, backed by a "
                        "knowledge graph."),
    ),
    dict(
        id="11_catalog", app="ontology", page="on_catalog", actions=[("wait", 3000)],
        narration=(
            "The S A P B D C catalog view maps the business processes to the S A P "
            "data products that feed them, [[slnc 200]] so you can see which products "
            "matter for which decisions."
        ),
        popup=dict(title="SAP BDC Catalog", figure="Process → product",
                   body="Business processes mapped to the SAP BDC data products behind them."),
    ),
    dict(
        id="12_scenario", app="ontology", page="on_scenario",
        actions=[("click_text", "Hurricane — Austin Fab offline"), ("wait", 3000)],
        narration=(
            "Scenario studio. [[slnc 250]] Let's take the headline case: [[slnc 150]] "
            "a hurricane takes Austin Fab offline for sixty days. [[slnc 300]] "
            "One click runs the simulation across the whole network."
        ),
        popup=dict(title="Scenario Studio", figure="Austin offline · 60 days",
                   body="Hurricane preset: Austin Fab fully offline."),
    ),
    dict(
        id="13_ripple", app="ontology", page="on_ripple",
        actions=[("click_button", "Play from the start")],
        narration=(
            "The ripple map plays it out. [[slnc 300]] Austin goes down, [[slnc 200]] "
            "four customers lose supply, [[slnc 200]] and Penang is starved of test "
            "fixtures two hops away. [[slnc 350]] Sixteen million dollars of monthly "
            "value at risk, [[slnc 150]] twenty eight percent of the network."
        ),
        popup=dict(title="Ripple Map", figure="$16.1M at risk",
                   body="28.3% of monthly network value · 4 customers · "
                        "Penang impaired two hops out."),
    ),
    dict(
        id="14_mitigation", app="ontology", page="on_mitigation", actions=[("wait", 2000)],
        narration=(
            "Mitigation finds the fix. [[slnc 300]] Move five units a month to San "
            "Jose, taking it from eighty nine to ninety nine percent utilization. "
            "[[slnc 300]] That protects thirteen point eight million, [[slnc 150]] "
            "ninety one percent. [[slnc 300]] And it's honest about the rest: [[slnc 150]] "
            "one point three million can't be moved, because only Penang makes die sorting."
        ),
        popup=dict(title="Mitigation plan", figure="91% protected",
                   body="$13.8M protected via San Jose HQ (89% → 99% utilization). "
                        "$1.3M unmitigable: no alternative for Die Sorting."),
    ),
    dict(
        id="15_optimize", app="ontology", page="on_optimize",
        actions=[("click_button", "Play the recovery")],
        narration=(
            "And the optimization map plays the recovery, [[slnc 200]] showing the "
            "rerouted flows taking over. [[slnc 400]] From zero copy S A P data, "
            "[[slnc 150]] to a governed, A I driven supply chain decision, [[slnc 150]] "
            "all in Snowflake."
        ),
        popup=dict(title="Optimization Map", figure="Recovery",
                   body="Rerouted flows replace the lost Austin supply."),
    ),
]
