"""Script for the SAP Enterprise Ontology DEEP DIVE (~15-20 minutes).

Eight chapters: the problem, the model, identity, the 360s, scenario modelling,
management use cases, asking in plain language, and how it is deployed and governed.

EVERY FIGURE is what the app shows, taken from /tmp/enterprise_facts.json and the
scenario engine (client/src/lib/entScenario.ts) run on the exported data on
2026-10-08, US account. Independent SQL check: supplier failure GS-002 x 8 weeks
= $15,893,854 output lost, the figure narrated below.

HONESTY BEATS SCRIPTED IN: the demo crosswalk; the different scales of the demo
apps (Sales and People run far larger than demo Finance revenue); scenario
assumptions; what Ask Cortex does and does not do.

Ask Cortex calls take 10-40 s. To keep silence short, a segment that CLICKS Ask
Cortex narrates over the wait, and the NEXT segment waits for the answer.
"""

NAV = {
    "overview": "Enterprise Overview",
    "usecases": "Management Use Cases",
    "scenario": "Enterprise Scenario Studio",
    "model": "Master Ontology Model",
    "customers": "Customer 360",
    "suppliers": "Supplier 360",
    "crosswalk": "Golden-Record Crosswalk",
    "graph": "Enterprise Graph",
    "ask": "Ask the Enterprise",
}

W = ("wait", 900)

SEGMENTS = [
    # ------------------------------------------------------------------ 1. the problem
    dict(id="01_open", page="overview", actions=[("wait", 1500)],
         narration=("This is a deep dive into the S A P enterprise ontology, [[slnc 250]] and what it does for "
                    "running an organisation. [[slnc 400]] We have six S A P B D C three sixty applications. "
                    "[[slnc 250]] Finance, Sales, People, Spend, Working Capital and Supply Chain. [[slnc 300]] Each one "
                    "is good at its own domain. [[slnc 300]] But a business is not six domains. [[slnc 250]] It is one set "
                    "of companies, customers and suppliers, seen from six sides."),
         popup=dict(title="SAP Enterprise Ontology — deep dive", figure="6 apps · 1 ontology",
                    body="Finance · Sales · People · Spend · Working Capital · Supply Chain")),
    dict(id="02_gap", page="overview", actions=[W],
         narration=("Here is the gap. [[slnc 300]] Spend knows how much we buy from a supplier. [[slnc 200]] Working "
                    "Capital knows how much we owe it. [[slnc 200]] Supply Chain knows which of our systems contain its "
                    "parts. [[slnc 300]] But in each app that supplier has a different key. [[slnc 300]] So no app can "
                    "tell you that it is the same supplier, [[slnc 200]] or what happens to the rest of the business "
                    "if it fails."),
         popup=dict(title="The gap", figure="no shared keys",
                    body="Each app holds its own copy of every customer and supplier.")),
    dict(id="03_numbers", page="overview", actions=[W],
         narration=("The master ontology closes that gap. [[slnc 250]] Across three legal entities: [[slnc 200]] forty "
                    "four point four million dollars of revenue from Finance, [[slnc 200]] twelve hundred and ninety two "
                    "people from People, [[slnc 200]] four point seven million of spend, [[slnc 200]] and four point four "
                    "million of late delivery cost from Supply Chain. [[slnc 300]] All on one page, because all of them "
                    "now point at the same company."),
         popup=dict(title="One page, five apps", figure="$44.4M revenue",
                    body="1,292 people · $4.7M spend · $4.4M late-delivery cost")),
    dict(id="04_modules", page="overview", actions=[("scroll", 330), W],
         narration=("Each app is a module of the ontology. [[slnc 250]] The core holds the shared vocabulary and the "
                    "golden records. [[slnc 250]] Each module reads straight from its own Snowflake database, [[slnc 200]] "
                    "so nothing is copied out of the apps. [[slnc 300]] The ontology sits on top of them."),
         popup=dict(title="Seven modules", figure="CORE + 6 apps",
                    body="Each module reads its own 360 database; nothing is copied out.")),
    dict(id="05_entities", page="overview", actions=[("scroll", 300), W],
         narration=("Now read across a row. [[slnc 250]] U S Operations has the best margin, [[slnc 200]] twenty five "
                    "point three percent. [[slnc 300]] But its plants deliver on time and in full only sixty four point "
                    "eight percent of the time, [[slnc 200]] with three point six million dollars of late cost. "
                    "[[slnc 300]] Finance alone would call it the strongest entity. [[slnc 250]] Supply Chain alone would "
                    "call it the weakest. [[slnc 250]] You only see the tension when both are on the same company."),
         popup=dict(title="US Operations", figure="25.3% margin · 64.8% OTIF",
                    body="Best margin, worst delivery — visible only when both apps share the entity.")),

    # ------------------------------------------------------------------ 2. the model
    dict(id="06_model", page="model", actions=[("wait", 1200)],
         narration=("Underneath is the model. [[slnc 250]] Thirty two classes and seventeen relations. [[slnc 300]] "
                    "It is built on the Supply Chain ontology: [[slnc 200]] its abstract classes, party, org unit, "
                    "facility, transaction, item, asset and product, [[slnc 200]] become the upper ontology for the whole "
                    "enterprise."),
         popup=dict(title="Master ontology", figure="32 classes · 17 relations",
                    body="Upper classes generalised from the Supply Chain ontology.")),
    dict(id="07_model_modules", page="model", actions=[W],
         narration=("Every module adds only what it alone owns. [[slnc 250]] Finance adds cost centers, profit centers "
                    "and G L accounts. [[slnc 200]] Sales adds orders and opportunities. [[slnc 200]] People adds the "
                    "employee. [[slnc 200]] Supply Chain adds plants, tools, systems and component lots. [[slnc 300]] And "
                    "all of them point at the same golden customer, supplier and legal entity."),
         popup=dict(title="Modules add, the core conforms", figure="1 Supplier class",
                    body="Spend, Working Capital and Supply Chain relations land on the same class.")),
    dict(id="08_relations", page="model", actions=[("scroll", 650), W],
         narration=("The relations are where the value is. [[slnc 250]] Buys from comes from Spend. [[slnc 200]] Owes to "
                    "comes from Working Capital. [[slnc 200]] Supplies comes from Supply Chain. [[slnc 300]] Three apps, "
                    "three relations, [[slnc 150]] one supplier. [[slnc 300]] That is what lets a question travel from one "
                    "app to another."),
         popup=dict(title="Relations cross apps", figure="buysFrom · owesTo · supplies",
                    body="Each relation is asserted by one app and lands on a shared class.")),

    # ------------------------------------------------------------------ 3. identity
    dict(id="09_crosswalk", page="crosswalk", actions=[("wait", 1200)],
         narration=("So how do six apps agree on who is who? [[slnc 300]] Through golden records. [[slnc 250]] Four hundred "
                    "and seventy four local records, from every app, [[slnc 200]] resolve to twenty golden customers, "
                    "twenty five golden suppliers and three legal entities."),
         popup=dict(title="Golden records", figure="474 → 48",
                    body="20 customers · 25 suppliers · 3 legal entities.")),
    dict(id="10_match", page="crosswalk", actions=[W],
         narration=("Every link keeps its match method, [[slnc 200]] so nothing is hidden. [[slnc 300]] And to be clear: "
                    "[[slnc 200]] these six demo apps came from different tenants and share no keys, [[slnc 200]] so this is "
                    "a deterministic demo crosswalk, labelled on every page. [[slnc 300]] In production it is replaced by "
                    "S A P master data governance, [[slnc 150]] and nothing else changes."),
         popup=dict(title="Demo crosswalk, labelled", figure="match method on every link",
                    body="Production: SAP MDG / match-merge replaces XWALK; the model is unchanged.")),
    dict(id="11_suppliers_tab", page="crosswalk", actions=[("click_last_button", "Supplier"), W],
         narration=("The supplier side is the same. [[slnc 250]] Two hundred and forty five Spend suppliers, [[slnc 200]] "
                    "fifty vendor keys shared by Finance and Working Capital, [[slnc 200]] and the six Supply Chain suppliers "
                    "all fold into twenty five golden suppliers."),
         popup=dict(title="Suppliers", figure="351 → 25",
                    body="Spend, Finance, Working Capital and Supply Chain records.")),

    # ------------------------------------------------------------------ 4. the 360s
    dict(id="12_supplier", page="suppliers", actions=[("wait", 1200)],
         narration=("Now open a supplier. [[slnc 250]] Teledyne DALSA is our largest by spend. [[slnc 250]] Three hundred "
                    "and twenty two thousand dollars, [[slnc 200]] under ten percent of it on contract, [[slnc 200]] risk "
                    "score seventy eight. [[slnc 300]] Spend alone would call it a small, slightly risky supplier."),
         popup=dict(title="Teledyne DALSA — Spend's view", figure="$322K spend",
                    body="9.7% on contract · risk score 78.")),
    dict(id="13_supplier_more", page="suppliers", actions=[("scroll", 650), W],
         narration=("The ontology adds the rest. [[slnc 250]] Three point six million dollars of open payables from Working "
                    "Capital and Finance. [[slnc 250]] Eleven component lots in Supply Chain, [[slnc 200]] two critical "
                    "components, [[slnc 200]] and a deviating lot that sits inside orders for T S M C, Samsung and Micron. "
                    "[[slnc 300]] Four apps, [[slnc 150]] one record."),
         popup=dict(title="Teledyne DALSA — the ontology's view", figure="4 apps",
                    body="$3.6M open payables · 11 lots · 2 critical components.")),
    dict(id="14_supplier_ask", page="suppliers",
         actions=[("click_last_button", "Ask Cortex"), ("wait", 600)],
         narration=("Ask Cortex on this record. [[slnc 250]] The server gathers the facts on screen from all four apps, "
                    "[[slnc 200]] and asks Cortex to reason over them, [[slnc 200]] with an instruction never to invent a "
                    "number. [[slnc 300]] While it thinks: [[slnc 150]] this is the question a category manager actually "
                    "has. [[slnc 200]] Should we pay early, hold, or find a second source?"),
         popup=dict(title="Ask Cortex", figure="grounded in 4 apps",
                    body="Facts from Spend, Working Capital, Finance and Supply Chain.")),
    dict(id="15_supplier_answer", page="suppliers",
         actions=[("wait_for_text", "Should we pay this supplier early", 150000), ("wait", 1200)],
         narration=("And here is the answer. [[slnc 250]] It puts the evidence in one table, [[slnc 200]] names the app "
                    "behind each number, [[slnc 200]] and turns it into actions. [[slnc 300]] That is the pattern for every "
                    "Ask Cortex in this app: [[slnc 200]] grounded in the view, cross app, and specific."),
         popup=dict(title="A grounded recommendation", figure="cites each app",
                    body="Evidence table, then actions — no invented figures.")),
    dict(id="16_customers", page="customers", actions=[("wait", 1200)],
         narration=("Customers work the same way. [[slnc 250]] Here, Finance receivables, Working Capital disputes, "
                    "[[slnc 200]] Sales orders and pipeline, [[slnc 200]] and Supply Chain delivery, [[slnc 200]] all on the "
                    "golden customer."),
         popup=dict(title="Customer 360", figure="20 golden customers",
                    body="Finance · Sales · Working Capital · Supply Chain.")),
    dict(id="17_skhynix", page="customers", actions=[W],
         narration=("Look at S K Hynix. [[slnc 250]] Two point seven million dollars overdue, [[slnc 200]] and the largest "
                    "late delivery cost of any customer. [[slnc 300]] Collections is chasing a customer that operations is "
                    "letting down. [[slnc 300]] Without the ontology those two teams never see each other's number."),
         popup=dict(title="SK Hynix", figure="$2.7M overdue",
                    body="…and the largest Supply Chain late-delivery cost.")),
    dict(id="18_scale", page="customers", actions=[W],
         narration=("One honest note on scale. [[slnc 250]] The Sales app comes from a large S A P demo tenant, "
                    "[[slnc 200]] so its order values are far bigger than the Supply Chain demo orders. [[slnc 300]] The "
                    "app labels this, [[slnc 150]] and the rule is simple: [[slnc 150]] compare within an app, not across."),
         popup=dict(title="Different demo scales", figure="compare within an app",
                    body="Sales demo orders dwarf Supply Chain demo orders.")),

    # ------------------------------------------------------------------ 5. scenario modelling
    dict(id="20_studio", page="scenario", actions=[("wait", 1500)],
         narration=("Now the part that matters most for running the business: [[slnc 200]] scenario modelling. "
                    "[[slnc 300]] The enterprise scenario studio takes one shock, [[slnc 200]] and walks it through the "
                    "ontology into all six apps."),
         popup=dict(title="Enterprise Scenario Studio", figure="1 shock · 6 apps",
                    body="Supplier, plant, customer, FX, payment terms, workforce.")),
    dict(id="21_how", page="scenario", actions=[W],
         narration=("A design choice worth knowing. [[slnc 250]] The apps run at different scales, [[slnc 200]] so the "
                    "engine never adds dollars across apps. [[slnc 300]] The shock travels as a share of activity, "
                    "[[slnc 200]] and each app applies that share to its own baseline. [[slnc 300]] Every row says which "
                    "baseline it used."),
         popup=dict(title="Shares, not summed dollars", figure="each app, its own baseline",
                    body="The shock travels as a share through golden-record edges.")),
    dict(id="22_supplier_fail", page="scenario", actions=[("click_button", "Top-spend supplier fails"), W],
         narration=("Scenario one. [[slnc 200]] Teledyne DALSA stops shipping for eight weeks. [[slnc 300]] Fifteen point "
                    "nine million dollars of output is lost, [[slnc 200]] reaching all eight customers and all three "
                    "legal entities."),
         popup=dict(title="Teledyne DALSA out for 8 weeks", figure="$15.9M output lost",
                    body="8 customers · 3 legal entities.")),
    dict(id="23_path", page="scenario", actions=[("scroll", 420), W],
         narration=("Here is the path it took. [[slnc 250]] Teledyne supplies four plants. [[slnc 200]] At Austin forty "
                    "seven percent of the systems built contain its lots. [[slnc 300]] Those plants ship to our customers, "
                    "[[slnc 200]] and they are owned by our legal entities. [[slnc 300]] Every step is a relation in the "
                    "ontology."),
         popup=dict(title="Propagation path", figure="supplies → shipsTo → ownedBy",
                    body="47% of Austin's systems contain Teledyne lots.")),
    dict(id="24_effects", page="scenario", actions=[("scroll", 420), W],
         narration=("And what each app would see. [[slnc 250]] Supply Chain: [[slnc 150]] eight point three million of "
                    "margin lost. [[slnc 200]] Sales: [[slnc 150]] five point five million of open pipeline at risk. "
                    "[[slnc 200]] Finance: [[slnc 150]] seven hundred and forty six thousand of revenue at risk. "
                    "[[slnc 200]] Working Capital: [[slnc 150]] Europe's cash cycle stretches five days."),
         popup=dict(title="What each app sees", figure="5 apps move",
                    body="Margin −$8.3M · pipeline −$5.5M · revenue −$746K · EU CCC +5.1 d.")),
    dict(id="25_cust_ranked", page="scenario", actions=[("scroll", 420), W],
         narration=("The customers it lands on are ranked. [[slnc 250]] S K Hynix first, [[slnc 150]] then T S M C and "
                    "Intel. [[slnc 300]] That is the list the account teams need on day one of a disruption."),
         popup=dict(title="Who feels it", figure="SK Hynix · TSMC · Intel",
                    body="Customers ranked by deliveries at risk.")),
    dict(id="26_dual", page="scenario", actions=[("scroll", -1400), ("click_button", "Festo fails, 50% dual-sourced"), W],
         narration=("Scenario two asks what a second source is worth. [[slnc 250]] Festo out for eight weeks, [[slnc 200]] "
                    "with half its volume covered elsewhere. [[slnc 300]] Seventeen point five million of output still "
                    "lost. [[slnc 300]] Without the second source it would be thirty five million. [[slnc 250]] So that "
                    "contract is worth seventeen and a half million dollars of output in one bad quarter."),
         popup=dict(title="Festo, 50% dual-sourced", figure="saves $17.5M",
                    body="$35.0M → $17.5M of output lost over 8 weeks.")),
    dict(id="27_plant", page="scenario", actions=[("click_button", "San Jose HQ down 4 weeks"), W],
         narration=("Scenario three. [[slnc 200]] Our largest plant, San Jose, goes down for four weeks. [[slnc 300]] "
                    "Fifteen point four million of output, [[slnc 200]] ten point five million of pipeline at risk, "
                    "[[slnc 200]] and U S Operations' cash cycle goes from fifty five to sixty one days."),
         popup=dict(title="San Jose HQ down 4 weeks", figure="$15.4M output",
                    body="Pipeline −$10.5M · US CCC 54.9 → 60.9 days.")),
    dict(id="28_plant_suppliers", page="scenario", actions=[("scroll", 1300), W],
         narration=("It also tells procurement what to do. [[slnc 250]] Aerotech's lots are in seventy one percent of San "
                    "Jose's systems. [[slnc 200]] That inbound needs to pause, or move, [[slnc 150]] the day the plant goes "
                    "down."),
         popup=dict(title="Inbound to pause", figure="Aerotech 71%",
                    body="Suppliers ranked by share of the plant's systems.")),
    dict(id="29_customer", page="scenario", actions=[("scroll", -1400), ("click_button", "SK Hynix defaults"), W],
         narration=("Scenario four. [[slnc 200]] S K Hynix defaults, [[slnc 150]] and we recover forty percent. "
                    "[[slnc 300]] Three point seven million is written off, [[slnc 200]] split across all three legal "
                    "entities. [[slnc 250]] Four point one million of pipeline disappears, [[slnc 200]] and forty four "
                    "million of order book is freed for other customers."),
         popup=dict(title="SK Hynix defaults", figure="$3.7M write-off",
                    body="Pipeline −$4.1M · $44.3M of order book freed.")),
    dict(id="30_fx", page="scenario", actions=[("click_button", "EUR −10% vs USD"), W],
         narration=("Scenario five, [[slnc 150]] a ten percent weaker euro. [[slnc 300]] Europe's reported revenue falls one "
                    "point four five million, [[slnc 200]] its net income three hundred and thirty two thousand. "
                    "[[slnc 300]] Payroll in dollars falls five and a half million. [[slnc 250]] That number is large because "
                    "the People demo data runs at a bigger scale than demo Finance revenue, [[slnc 200]] which is why each "
                    "app keeps its own baseline."),
         popup=dict(title="EUR −10% vs USD", figure="revenue −$1.45M",
                    body="Net income −$332K · spend −$152K · payroll −$5.5M (People scale).")),
    dict(id="31_terms", page="scenario", actions=[("click_button", "Pay 10 days later"), W],
         narration=("Scenario six is a treasurer's favourite. [[slnc 250]] Pay suppliers ten days later, [[slnc 150]] "
                    "collect five days sooner. [[slnc 300]] Two million dollars of cash is released, [[slnc 200]] and every "
                    "company's cash cycle shortens by fifteen days."),
         popup=dict(title="Payment terms", figure="$2.0M cash released",
                    body="CCC −15 days at every legal entity.")),
    dict(id="32_terms_cost", page="scenario", actions=[("scroll", 420), W],
         narration=("But the ontology shows who pays for it. [[slnc 250]] The suppliers squeezed hardest include TRUMPF, "
                    "Festo and Coherent, [[slnc 200]] and four of them hold critical components in Supply Chain. "
                    "[[slnc 300]] Working Capital alone would just say yes. [[slnc 250]] The ontology says, [[slnc 150]] "
                    "not with those four."),
         popup=dict(title="Who pays for it", figure="4 critical suppliers",
                    body="TRUMPF, Festo, Coherent — critical components in Supply Chain.")),
    dict(id="33_workforce", page="scenario", actions=[("scroll", -1400), ("click_button", "US Operations −5% headcount"), W],
         narration=("And scenario seven, [[slnc 150]] a five percent headcount reduction at U S Operations. [[slnc 300]] "
                    "Two point six million of payroll saved, [[slnc 200]] twenty two roles. [[slnc 300]] But the studio "
                    "flags it: [[slnc 150]] these plants already run at sixty four point eight percent on time in full. "
                    "[[slnc 250]] Cutting capacity here compounds a delivery problem."),
         popup=dict(title="US Operations −5%", figure="$2.6M payroll",
                    body="Flagged: plants already at 64.8% OTIF.")),
    dict(id="34_custom", page="scenario",
         actions=[("click_button", "Supplier failure"), ("click_role", "slider", "Covered by alternate source"), ("press", "Home"),
                  ("press", "ArrowRight"), ("press", "ArrowRight"), ("press", "ArrowRight"), W],
         narration=("Every preset is a starting point. [[slnc 250]] Pick any supplier, plant, customer or company, "
                    "[[slnc 200]] set the duration or the size, [[slnc 200]] and the whole enterprise recalculates "
                    "instantly. [[slnc 300]] Here, thirty percent covered by an alternate source."),
         popup=dict(title="Build your own", figure="instant recalculation",
                    body="Any supplier, plant, customer, currency, terms or headcount.")),
    dict(id="35_scenario_ask", page="scenario",
         actions=[("click_button", "Top-spend supplier fails"), ("click_button", "Ask Cortex about this scenario"), ("wait", 600)],
         narration=("And you can ask Cortex about any scenario. [[slnc 250]] The server re-runs the same engine from the "
                    "scenario's settings, [[slnc 200]] so Cortex reads exactly the result on screen. [[slnc 300]] The question "
                    "here is the one a leadership team asks: [[slnc 150]] what do we decide this week?"),
         popup=dict(title="Ask Cortex about the scenario", figure="same engine, same numbers",
                    body="The server recomputes the scenario Cortex explains.")),
    dict(id="36_scenario_answer", page="scenario",
         actions=[("wait_for_text", "What should we decide this week?", 150000), ("wait", 1200)],
         narration=("Cortex walks the propagation, [[slnc 200]] names the biggest effect in each app, [[slnc 200]] and "
                    "turns it into decisions. [[slnc 300]] A disruption review that usually takes a day of spreadsheets "
                    "from six teams."),
         popup=dict(title="From scenario to decision", figure="minutes, not a day",
                    body="Propagation, per-app effect, recommended actions.")),

    # ------------------------------------------------------------------ 6. management use cases
    dict(id="40_usecases", page="usecases", actions=[("wait", 1500)],
         narration=("Which brings us to use cases. [[slnc 250]] This page lists ten management questions that no single "
                    "three sixty app can answer, [[slnc 200]] each with its live answer, [[slnc 150]] the ontology path it "
                    "travels, [[slnc 150]] and the page that explores it."),
         popup=dict(title="Management use cases", figure="10 questions",
                    body="Each needs facts from two or more apps.")),
    dict(id="41_uc_ceo", page="usecases", actions=[W],
         narration=("For the C E O and C F O: [[slnc 200]] which entity is weakest across finance, cash, people and "
                    "delivery. [[slnc 300]] For the C P O: [[slnc 200]] which supplier is cheap to buy from but expensive "
                    "to depend on."),
         popup=dict(title="CEO / CFO · CPO", figure="entity health · supplier dependence",
                    body="US Operations at 64.8% OTIF · Teledyne $322K spend vs $3.6M payables.")),
    dict(id="42_uc_ops", page="usecases", actions=[("scroll", 520), W],
         narration=("For the C O O: [[slnc 200]] what a supplier failure or a plant outage costs the enterprise, "
                    "[[slnc 200]] and what a second source is worth. [[slnc 300]] Each one opens the scenario studio "
                    "already set up."),
         popup=dict(title="COO", figure="disruption → P&L",
                    body="Supplier failure, dual sourcing, plant outage.")),
    dict(id="43_uc_finance", page="usecases", actions=[("scroll", 520), W],
         narration=("For credit and treasury: [[slnc 200]] which customers are both late to pay and badly served, "
                    "[[slnc 200]] where a default would land, [[slnc 200]] and how much cash new terms release, and at "
                    "whose expense."),
         popup=dict(title="Credit · Treasury", figure="AR × delivery · terms × supply",
                    body="Account health, customer default, payment terms.")),
    dict(id="44_uc_people", page="usecases", actions=[("scroll", 520), W],
         narration=("And for the C F O and C H R O: [[slnc 200]] what a currency move does to reported results, "
                    "[[slnc 200]] and where a headcount change is safe, [[slnc 150]] or where it would compound a delivery "
                    "problem."),
         popup=dict(title="CFO · CHRO", figure="FX · workforce",
                    body="Translation across Finance, Spend, People; headcount vs OTIF.")),
    dict(id="45_uc_run", page="usecases",
         actions=[("scroll", -1400), W],
         narration=("Each card has its own Ask Cortex, [[slnc 200]] and a button that runs the scenario. [[slnc 250]] "
                    "Use cases are the way into the ontology for someone who does not want to learn it first."),
         popup=dict(title="Start from the question", figure="one click to the answer",
                    body="Ask Cortex or run the scenario from every card.")),

    # ------------------------------------------------------------------ 7. graph and plain language
    dict(id="50_graph", page="graph", actions=[("wait", 2500)],
         narration=("All of this is one graph. [[slnc 250]] Nineteen hundred and twenty eight nodes, [[slnc 150]] three "
                    "thousand seven hundred and ninety edges, [[slnc 150]] and zero dangling edges. [[slnc 300]] Each edge "
                    "is coloured by the app that asserts it."),
         popup=dict(title="Enterprise knowledge graph", figure="1,928 nodes · 3,790 edges",
                    body="0 dangling edges. Edge colour = asserting app.")),
    dict(id="51_graph_filter", page="graph", actions=[("click_last_button", "PPL"), ("click_last_button", "FIN"), ("wait", 2000)],
         narration=("Turn apps off and the structure is clear. [[slnc 250]] Companies at the centre, [[slnc 150]] suppliers "
                    "and customers around them, [[slnc 150]] and plants and tools out on the Supply Chain side."),
         popup=dict(title="Filter by app", figure="structure, not a hairball",
                    body="Companies · suppliers · customers · plants · tools.")),
    dict(id="52_ask", page="ask",
         actions=[("click_text", "Which customers have overdue receivables"), ("wait", 600)],
         narration=("And for questions nobody prepared a page for, [[slnc 200]] ask in plain language. [[slnc 250]] Cortex "
                    "Analyst writes the S Q L against the enterprise semantic view, [[slnc 200]] which covers every app "
                    "through the golden records."),
         popup=dict(title="Ask the Enterprise", figure="Cortex Analyst",
                    body="SQL over SAP_ENTERPRISE_360, the master semantic view.")),
    dict(id="53_ask_answer", page="ask", actions=[("wait_for_text", "show SQL", 150000), ("wait", 1500)],
         narration=("The answer comes back as a table, [[slnc 150]] with the S Q L one click away, [[slnc 200]] so anyone "
                    "can check how it was worked out."),
         popup=dict(title="Answer and SQL", figure="auditable",
                    body="Every answer shows the SQL behind it.")),

    # ------------------------------------------------------------------ 8. deployed and governed
    dict(id="60_regions", page="overview", actions=[("wait", 1200)],
         narration=("Finally, how it is built and run. [[slnc 250]] Everything lives in one Snowflake database, "
                    "[[slnc 200]] with a semantic view and a Cortex agent on top. [[slnc 300]] It is deployed in the U S, "
                    "Europe and Asia Pacific, [[slnc 200]] and the deployment fails unless every region matches the U S "
                    "totals."),
         popup=dict(title="Three regions, gated on parity", figure="US · EU · APAC",
                    body="Deploy fails unless totals match the US source of truth.")),
    dict(id="61_proof", page="overview", actions=[W],
         narration=("And the totals reconcile with every source app. [[slnc 250]] Spend matches Spend three sixty to the "
                    "dollar. [[slnc 200]] Late cost matches Supply Chain. [[slnc 200]] Headcount matches People. [[slnc 300]] "
                    "Because every source is summed to the golden record before it is joined, [[slnc 200]] nothing is "
                    "double counted."),
         popup=dict(title="Reconciles with every app", figure="to the dollar",
                    body="Spend $4,658,904 · late cost $4,404,745 · headcount 1,292.")),
    dict(id="62_close", page="overview", actions=[("wait", 1500)],
         narration=("So that is the enterprise ontology. [[slnc 250]] One identity for every company, customer and supplier. "
                    "[[slnc 200]] Scenarios that travel across all six apps. [[slnc 200]] Use cases that start from the "
                    "question. [[slnc 200]] And Cortex reasoning over the evidence. [[slnc 400]] It is public, [[slnc 150]] "
                    "with no login, [[slnc 150]] at the address on screen."),
         popup=dict(title="SAP Enterprise Ontology", figure="try it",
                    body="sfc-gh-dfreriks.github.io/enterprise-ontology")),
]
