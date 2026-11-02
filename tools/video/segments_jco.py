"""Script for the SAP JCo Extractor narrated walkthrough.

One entry per beat: the narration (which sets the segment's length), the caption
card copy, and the actions that put the app in the right state.

Narration is written to be spoken: initialisms spaced ("S A P", "R F C"), JCo as
"Jay Co", figures spelled out, `[[slnc n]]` pauses where a person would breathe.

EVERY FIGURE HERE IS FROM THE LIVE APP on 2026-10-20 (S4H client 100, Snowflake
SAP_JCO_TEST on MSB89522), captured the same day in /tmp/jco_shots. The recording
never saves an object, starts a job or uploads a document, and never changes SAP;
the write-back beats only add a SIMULATED row to SAP_META.CDS_WRITEBACK_LOG.
"""

NAV = {
    "connection": "Connections",
    "catalog": "Object Catalog",
    "mapper": "Field Mapper",
    "jobs": "Extraction Jobs",
    "metadata": "Metadata Explorer",
    "data": "Data Preview",
    "existing": "Existing Data",
    "documents": "SAP Documents",
    "cdswrite": "CDS Write-back",
    "slt": "SLT Status",
    "security": "SAP Security",
}

SEGMENTS = [
    dict(
        id="00_open", page="connection", actions=[("wait", 1500)],
        narration=(
            "This is the S A P Jay Co Extractor. [[slnc 400]] It reads S A P A Bap tables, "
            "C D S views, documents and security straight over R F C, [[slnc 250]] and lands them in "
            "Snowflake as a governed bronze, silver and gold model. [[slnc 400]] No middleware, "
            "and nothing installed in S A P."
        ),
        popup=dict(title="SAP JCo Extractor", figure="RFC → Snowflake",
                   body="SAP ABAP tables, CDS views, documents and security over RFC, "
                        "landed as a medallion model."),
    ),
    dict(
        id="01_connect", page="connection", actions=[("wait", 1500)],
        narration=(
            "Connections shows both ends. [[slnc 300]] On the left, the S four H system, client one hundred, "
            "reached through a small Jay Co bridge, with an R F C ping of under a hundred milliseconds. "
            "[[slnc 350]] On the right, the Snowflake target database, and the layers the app builds in it."
        ),
        popup=dict(title="Connections", figure="S4H · client 100",
                   body="JCo 3.1 bridge on the SAP network; Snowflake database SAP_JCO_TEST "
                        "with RAW, BRONZE, SILVER, GOLD and CAPTURE_CONTROL."),
    ),
    dict(
        id="02_catalog", page="catalog",
        actions=[("fill", "input", "VBA*"), ("click_button", "Search"), ("wait_for_text", "VBAP", 30000),
                 ("wait", 2500)],
        narration=(
            "The object catalog searches the A Bap dictionary itself. [[slnc 300]] Type a prefix, "
            "and every matching table comes back with its description. [[slnc 350]] Below it are the "
            "extraction objects already defined: customers, suppliers, materials, "
            "and sales order headers and items."
        ),
        popup=dict(title="Object Catalog", figure="5 objects",
                   body="DD02L / DD02T searched live; KNA1, LFA1, MARA, VBAK and VBAP are defined."),
    ),
    dict(
        id="03_mapper", page="catalog",
        actions=[("click_last_button", "Edit"), ("wait_for_text", "Fields of VBAP", 30000), ("wait", 2000)],
        narration=(
            "The field mapper turns dictionary metadata into a Snowflake design. [[slnc 300]] For sales "
            "order items there are four hundred and forty one fields. [[slnc 250]] Each shows its S A P type, "
            "the Snowflake type, a business name, and any fixed values that will be decoded. "
            "[[slnc 350]] Keys come from the dictionary, and you pick a delta field for incremental loads."
        ),
        popup=dict(title="Field Mapper", figure="441 fields",
                   body="VBAP: DDIC type, Snowflake type, business name and decoded values per field."),
    ),
    dict(
        id="04_wide", page="mapper",
        actions=[("select", 1, "/BODS/RFC_READ_TABLE2"), ("wait", 2500)],
        narration=(
            "R F C read table only returns five hundred and twelve characters per row, [[slnc 250]] and "
            "paging through it lost rows on HANA. [[slnc 350]] So the bridge handles both. Wider rows are read "
            "in column groups joined on the key, [[slnc 250]] or in one call with slash bods R F C read "
            "table two, at up to thirty thousand characters. [[slnc 350]] Large tables are split "
            "automatically on a key median, with no paging at all."
        ),
        popup=dict(title="Wide and large tables", figure="512 → 30,000",
                   body="Column groups joined on the key, or /BODS/RFC_READ_TABLE2; slices over the row "
                        "cap split on a key median."),
    ),
    dict(
        id="05_proof", page="mapper", actions=[("wait", 1500)],
        narration=(
            "This was proven on this system. [[slnc 300]] All four hundred and forty one item fields, "
            "thirty five hundred characters a row, matched field for field between both methods. "
            "[[slnc 350]] And the full item table read in seventy one slices "
            "returned exactly the same seven thousand seven hundred and seventy eight rows as a single call."
        ),
        popup=dict(title="Verified on S4H", figure="0 differences",
                   body="VBAP: 441 fields, 3,500 characters per row; 7,778 rows identical across 1, 12 and "
                        "71 slices."),
    ),
    dict(
        id="06_jobs", page="jobs", actions=[("wait", 2000)],
        narration=(
            "Extraction jobs run full or delta loads and report exactly how the data was read. "
            "[[slnc 300]] The last run loaded the supplier master, all two hundred and ten fields, "
            "in seven column groups. [[slnc 350]] Every object then reconciles: rows in S A P, "
            "in silver and in gold, [[slnc 200]] and all five match."
        ),
        popup=dict(title="Extraction Jobs", figure="5 / 5 match",
                   body="LFA1: 130 rows, 7 column groups; reconciliation SAP vs Silver vs Gold for every object."),
    ),
    dict(
        id="07_control", page="jobs", actions=[("scroll_to", "Extraction objects"), ("wait", 2000)],
        narration=(
            "Capture control keeps the high water mark for each object, [[slnc 250]] so a delta run reads "
            "only what changed. [[slnc 350]] The polling and daily assurance tasks are created suspended, "
            "so nothing spends credits until you turn it on. [[slnc 300]] Every load is logged."
        ),
        popup=dict(title="Capture control", figure="delta by mark",
                   body="High-water marks per object; capture-cycle and daily assurance tasks created suspended."),
    ),
    dict(
        id="08_gold", page="data", actions=[("wait", 2500)],
        narration=(
            "Here is the result in gold. [[slnc 300]] Seven thousand seven hundred and seventy eight sales order "
            "items, with business column names, [[slnc 250]] and coded values decoded from the dictionary, "
            "so a category of T A N reads as standard item. [[slnc 350]] Rows deleted in S A P are tombstoned "
            "in silver and left out of gold."
        ),
        popup=dict(title="Gold: business-ready", figure="7,778 rows",
                   body="GOLD.DT_VBAP: business names and decoded domain values; deletions excluded."),
    ),
    dict(
        id="09_meta", page="metadata", actions=[("wait", 2000)],
        narration=(
            "The metadata explorer holds the replicated A Bap dictionary. [[slnc 300]] Tables, fields, "
            "data elements, domains and their fixed values, all in Snowflake. [[slnc 350]] It also copies the "
            "extractor catalog: five thousand five hundred and thirty two data sources, "
            "[[slnc 200]] of which only ninety three are active on this system."
        ),
        popup=dict(title="Metadata Explorer", figure="5,532 DataSources",
                   body="DD tables replicated to SAP_META; ROOSOURCE, ROOSFIELD, RODSAPPL and RODSAPPLT "
                        "copied in full."),
    ),
    dict(
        id="10_sql", page="metadata", actions=[("click_button", "Generated SQL"), ("wait", 2500)],
        narration=(
            "Nothing is hidden. [[slnc 250]] Every view, dynamic table and control object the app deploys "
            "is shown here as plain S Q L, [[slnc 250]] ready to review or check into source control."
        ),
        popup=dict(title="Generated SQL", figure="reviewable",
                   body="Bronze views, Silver and Gold incremental dynamic tables, CAPTURE_CONTROL objects."),
    ),
    dict(
        id="11_existing", page="existing",
        actions=[("click_button", "Open"), ("wait_for_text", "COLUMNS MAPPED", 30000), ("wait", 2000)],
        narration=(
            "Existing data brings S A P meaning to tables loaded by other tools. [[slnc 300]] Point it at a "
            "Snowflake table, name the S A P object, [[slnc 200]] and it auto-matches the columns to dictionary "
            "fields. [[slnc 350]] Here fourteen of sixteen matched, and it builds an enriched view, with "
            "descriptions and decoded values, without touching the source."
        ),
        popup=dict(title="Existing Data", figure="14 / 16 mapped",
                   body="Another tool's VBAK auto-matched to SAP fields; enriched view and drift checks."),
    ),
    dict(
        id="12_docs", page="documents",
        actions=[("wait_for_text", "0080000", 90000), ("wait", 2000)],
        narration=(
            "S A P documents reaches the files attached to business objects. [[slnc 300]] Four hundred and "
            "seventy three attachments, plus archive link content, listed by object. [[slnc 350]] Selected "
            "files are downloaded over R F C, staged in Snowflake, [[slnc 200]] and their text extracted "
            "with A I parse document."
        ),
        popup=dict(title="SAP Documents", figure="473 in SAP",
                   body="GOS attachments and ArchiveLink files, staged in Snowflake with AI_PARSE_DOCUMENT text."),
    ),
    dict(
        id="13_coco", page="documents", actions=[("scroll_to", "Analyze with CoCo"), ("wait", 2000)],
        narration=(
            "Once loaded, every document sits in one view with its S A P object and text, [[slnc 300]] so "
            "Cortex Code can summarize billing attachments, pull test steps into a table, [[slnc 200]] or "
            "build a search service over them for an agent."
        ),
        popup=dict(title="Analyze with CoCo", figure="4 loaded",
                   body="DOCS.V_DOCUMENTS_FOR_ANALYSIS: one row per document with object and extracted text."),
    ),
    dict(
        id="13b_wb_intro", page="cdswrite",
        actions=[("wait_for_text", "RAP BO (write)", 90000), ("wait_for_text", "0000003974", 90000), ("wait", 1500)],
        narration=(
            "C D S write-back shows how a change would flow back into S A P. [[slnc 300]] C D S views are read only, "
            "so each card shows the real path: [[slnc 200]] the view we read, the RAP business object that owns the data, "
            "and the released A P I. [[slnc 350]] All three were found live in this system."
        ),
        popup=dict(title="CDS Write-back", figure="view → RAP BO → API",
                   body="I_SALESDOCUMENT → I_SALESORDERTP → API_SALESORDER, each confirmed in TADIR."),
    ),
    dict(
        id="13c_wb_edit", page="cdswrite",
        actions=[("click_text", "0000003974"), ("fill", "label:has-text('Customer PO') input", "2021-122-REV1"),
                 ("fill", "label:has-text('Order reason') input", "002"), ("wait", 1500)],
        narration=(
            "Pick a sales order, and only the fields the business object allows to change are editable. "
            "[[slnc 300]] Here, the customer P O number and the order reason."
        ),
        popup=dict(title="Edit a sales order", figure="2 fields",
                   body="Customer PO and order reason on sales order 3974; every other field stays read-only."),
    ),
    dict(
        id="13d_wb_sim", page="cdswrite",
        actions=[("click_button", "Simulate write-back"), ("wait_for_text", "request (not sent)", 90000), ("wait", 1500)],
        narration=(
            "Simulate it, and every value is checked live. [[slnc 250]] The order reason against its S A P check table, "
            "[[slnc 200]] and the record against S A P right now, so a change someone else made is caught, "
            "just as an E tag mismatch would be. [[slnc 350]] Nothing is sent to S A P."
        ),
        popup=dict(title="Validated live", figure="2 / 2 checks",
                   body="Check table TVAU and a concurrency check against SAP; the result is SIMULATED, not sent."),
    ),
    dict(
        id="13e_wb_request", page="cdswrite", actions=[("scroll_to", "What would happen"), ("wait", 2000)],
        narration=(
            "Then it shows exactly what S A P would receive. [[slnc 250]] The O Data patch with its C S R F token and "
            "E tag, [[slnc 200]] the equivalent E M L on the business object, [[slnc 200]] and the authorizations the "
            "user would need. [[slnc 300]] Every request is logged in Snowflake."
        ),
        popup=dict(title="What SAP would receive", figure="PATCH · EML",
                   body="OData V4 PATCH to API_SALESORDER, MODIFY ENTITIES on I_SALESORDERTP, and the SAP authorizations."),
    ),
    dict(
        id="13f_wb_real", page="cdswrite", actions=[("scroll_to", "Write-back requests"), ("wait", 2000)],
        narration=(
            "To make it real, [[slnc 200]] the standard S A P change functions on this system can be called over the "
            "same bridge, with no A Bap coding, [[slnc 200]] once a write capable user is approved. [[slnc 300]] The "
            "released A P Is are the long term path, and the steps are in the write-back document."
        ),
        popup=dict(title="Making it real", figure="no ABAP coding",
                   body="Remote-enabled BAPIs over the bridge, or the released RAP APIs; see SAP_CDS_Writeback.docx."),
    ),
    dict(
        id="14_slt", page="slt", actions=[("wait", 3000)],
        narration=(
            "S L T status reads the landscape replication server, strictly read only. [[slnc 300]] "
            "Configurations, replicated tables, trigger state and change backlog. [[slnc 350]] On this system "
            "nothing is configured. The four mass transfers found are migration cockpit projects, "
            "[[slnc 200]] and the page says so, rather than guessing."
        ),
        popup=dict(title="SLT Status", figure="0 configured",
                   body="IUUC and DMC tables read only; the 4 mass transfers are Migration Cockpit projects."),
    ),
    dict(
        id="15_security", page="security", actions=[("wait_for_text", "COMPOSITE ROLES", 90000), ("wait", 2000)],
        narration=(
            "S A P security replicates roles and authorizations, read only, and never password data. "
            "[[slnc 300]] Five thousand five hundred roles, assigned to ninety one users. [[slnc 350]] Each "
            "authorization object is classed by what it means for Snowflake: [[slnc 200]] table access maps "
            "to grants, org restrictions map to row access policies."
        ),
        popup=dict(title="SAP Security", figure="5,500 roles",
                   body="AGR_* tables over RFC; authorization objects classed as table, row, HR or function."),
    ),
    dict(
        id="16_concept", page="security", actions=[("click_button", "Mapping concept"), ("wait", 2500)],
        narration=(
            "From that, the app proposes a Snowflake design, [[slnc 250]] database roles per table group, "
            "and row access policies on gold, [[slnc 250]] generated as S Q L for review. Nothing is applied "
            "automatically."
        ),
        popup=dict(title="Mapping concept", figure="SQL for review",
                   body="Database roles and row access policies generated, never applied."),
    ),
    dict(
        id="17_close", page="connection", actions=[("wait", 1500)],
        narration=(
            "So that is the S A P Jay Co Extractor. [[slnc 300]] Tables of any width and size, "
            "dictionary meaning, documents, replication status and security, [[slnc 250]] all from S A P "
            "into Snowflake over R F C, [[slnc 200]] a clear path for writing back, [[slnc 200]] and every step verified."
        ),
        popup=dict(title="SAP JCo Extractor", figure="github",
                   body="sfc-gh-dfreriks/sap-jco-snowflake"),
    ),
]
