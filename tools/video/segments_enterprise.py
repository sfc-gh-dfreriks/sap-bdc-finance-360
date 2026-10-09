"""Script for the SAP Enterprise Ontology narrated walkthrough.

One entry per beat: narration (sets the segment's length), caption card, and the
actions that put the app in the right state. Narration is written to be spoken —
initialisms spaced, figures as words, `[[slnc n]]` pauses.

EVERY FIGURE HERE IS WHAT THE APP SHOWS, checked against /tmp/enterprise_facts.json
(tools/enterprise_facts.py in the enterprise-ontology repo) on 2026-10-08, US account.

HONESTY BEATS SCRIPTED IN: golden records come from a demo crosswalk (the six apps
share no keys), and money is USD at planning rates.
"""

NAV = {
    "overview": "Enterprise Overview",
    "model": "Master Ontology Model",
    "customers": "Customer 360",
    "suppliers": "Supplier 360",
    "crosswalk": "Golden-Record Crosswalk",
    "graph": "Enterprise Graph",
    "ask": "Ask the Enterprise",
}

SEGMENTS = [
    dict(
        id="00_open", page="overview", actions=[("wait", 1500)],
        narration=(
            "Six S A P B D C three sixty apps. [[slnc 250]] Finance, Sales, People, Spend, "
            "Working Capital and Supply Chain. [[slnc 400]] Each one answers its own domain well. "
            "[[slnc 300]] None of them knows that the supplier in Spend is the same supplier in "
            "Working Capital, and in Supply Chain. [[slnc 400]] This is the master ontology that does."
        ),
        popup=dict(title="SAP Enterprise Ontology", figure="6 apps, 1 ontology",
                   body="Finance · Sales · People · Spend · Working Capital · Supply Chain"),
    ),
    dict(
        id="01_companies", page="overview", actions=[("scroll", 560), ("wait", 900)],
        narration=(
            "Three legal entities, read across every app at once. [[slnc 300]] Revenue from Finance, "
            "cash conversion from Working Capital, headcount from People, spend, and on time in full "
            "from Supply Chain. [[slnc 400]] U S Operations stands out: [[slnc 200]] sixty four point "
            "eight percent on time in full, and three point six million dollars of late delivery cost."
        ),
        popup=dict(title="US Operations", figure="64.8% OTIF",
                   body="$3.6M late-delivery cost — the weakest entity across all six apps."),
    ),
    dict(
        id="02_model", page="model", actions=[("wait", 1200)],
        narration=(
            "Underneath is one model. [[slnc 250]] Thirty two classes and seventeen relations. "
            "[[slnc 300]] The upper classes, party, org unit, facility, transaction, come from the "
            "Supply Chain ontology. [[slnc 300]] Each app is a module that adds only what it alone owns."
        ),
        popup=dict(title="Master ontology", figure="32 classes · 17 relations",
                   body="Supply Chain upper classes; one module per 360 app."),
    ),
    dict(
        id="03_supplier", page="suppliers", actions=[("wait", 1200)],
        narration=(
            "Here is what that buys you. [[slnc 300]] Teledyne DALSA is our largest supplier by spend. "
            "[[slnc 250]] One golden record, seen by four apps. [[slnc 300]] Three hundred and twenty two "
            "thousand dollars of spend, under ten percent on contract, [[slnc 200]] three point six million "
            "in open payables, [[slnc 200]] and a deviating component lot inside customer orders."
        ),
        popup=dict(title="Teledyne DALSA — one golden supplier", figure="4 apps",
                   body="Spend, Working Capital, Finance and Supply Chain in one record."),
    ),
    dict(
        id="04_cortex", page="suppliers",
        actions=[("scroll", 700), ("click_last_button", "Ask Cortex"), ("wait_for_text", "Should we pay this supplier early", 150000), ("wait", 1500)],
        narration=(
            "Ask Cortex on that record. [[slnc 300]] It reasons from the facts on screen, from all "
            "four apps, [[slnc 200]] puts the evidence in one table, [[slnc 200]] and recommends what "
            "to do next, [[slnc 150]] citing the app behind every number."
        ),
        popup=dict(title="Ask Cortex", figure="grounded in 4 apps",
                   body="The answer cites each app's evidence; it does not invent numbers."),
    ),
    dict(
        id="05_customers", page="customers", actions=[("wait", 1200)],
        narration=(
            "The same works for customers. [[slnc 300]] Twenty golden customers. [[slnc 250]] S K Hynix "
            "is overdue on two point seven million dollars of receivables, [[slnc 200]] and carries the "
            "largest late delivery cost. [[slnc 300]] Collections and operations are looking at the same account."
        ),
        popup=dict(title="SK Hynix", figure="$2.7M overdue AR",
                   body="…and the largest Supply Chain late-delivery cost."),
    ),
    dict(
        id="06_crosswalk", page="crosswalk", actions=[("wait", 1200)],
        narration=(
            "How do the apps agree on who is who? [[slnc 300]] Four hundred and seventy four app records "
            "resolve to golden records, each with its match method shown. [[slnc 300]] To be clear, "
            "[[slnc 150]] this is a demo crosswalk, because these demo apps share no keys. "
            "[[slnc 250]] In production it is S A P master data governance."
        ),
        popup=dict(title="Golden-record crosswalk", figure="474 records",
                   body="Demo crosswalk, labelled as such. Production: SAP MDG / match-merge."),
    ),
    dict(
        id="07_graph", page="graph", actions=[("wait", 2500)],
        narration=(
            "And it is a graph. [[slnc 250]] Nineteen hundred and twenty eight nodes, three thousand "
            "seven hundred and ninety edges, [[slnc 200]] coloured by the app that asserts them."
        ),
        popup=dict(title="Enterprise knowledge graph", figure="1,928 nodes",
                   body="3,790 edges, 0 dangling. Deployed identically in US, EU and APAC."),
    ),
    dict(
        id="08_ask", page="ask",
        actions=[("click_text", "Which suppliers have the highest open payables"),
                 ("wait_for_text", "show SQL", 150000), ("wait", 1500)],
        narration=(
            "Finally, plain language. [[slnc 250]] Cortex Analyst writes the S Q L against the enterprise "
            "semantic view, across every app. [[slnc 400]] Six apps, one ontology, [[slnc 200]] in U S, "
            "Europe and Asia Pacific."
        ),
        popup=dict(title="Ask the Enterprise", figure="Cortex Analyst",
                   body="SQL over SAP_ENTERPRISE_360, the master semantic view."),
    ),
]
