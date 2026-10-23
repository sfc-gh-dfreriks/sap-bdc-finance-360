# 5. Findings

Things that were not obvious, that cost time, and that anyone building or
presenting this stack should know. Four are properties of the data or the
objects; two are gaps in the AI layer that are still open.

All figures verified 2026-09-21.

---

## SAP amounts are signed, and the first answer is always wrong

In `OPERATIONALACCTGDOCITEM` the amount column carries the posting's natural
sign and the debit/credit character sits separately in `DEBITCREDITCODE`. A
revenue credit and an expense debit occupy the same column with opposing signs.

A bare `SUM(amount)` therefore returns neither revenue nor expense nor the
difference between them. It returns a number that depends on the debit/credit
mix inside the filter — which means it moves when you change the date range in
ways that look like a business trend and are not.

Correct aggregation needs **`ABS` on the amount plus a `DEBITCREDITCODE`
filter** selecting the side you mean. Both, not either.

This is the single most consequential fact in the stack, and it is invisible: the
wrong query succeeds, returns a plausible magnitude, and no error is raised.

L2 applies the pattern once, inside `DT_JOURNAL_ENTRY_360`, so the five
aggregates inherit it. Application SQL against the L0 shares does not inherit
it — see [the app straddles two layers](#the-app-straddles-two-layers).

---

## The reconciliation is exact, and that is the evidence

Revenue computed from L0 with `ABS` and a `DEBITCREDITCODE` filter, against
revenue reported by L2:

| Side | Value |
|---|---|
L0 `OPERATIONALACCTGDOCITEM` | $2,250,872,386 |
L2 `SUM(REVENUE)` over `DT_PNL_SUMMARY` | $2,250,872,386 |
Difference | **$0** |

Not "within rounding" — identical to the dollar. That is what makes the sign
handling defensible rather than merely asserted, and it is the check to run after
any change to L1 or L2.

The same total falls out of the per-year detail, which is a second independent
path to it:

| Fiscal year | Revenue | Expenses | Net income | Margin | Documents |
|---|---|---|---|---|---|
2023 | $968,827,521 | $726,047,817 | $242,779,704 | 25.1% | 2,293 |
2024 | $1,058,670,317 | $775,866,912 | $282,803,405 | 26.7% | 2,279 |
2025 | $223,374,548 | $207,676,009 | $15,698,539 | 7.0% | 578 |
**Total** | **$2,250,872,386** | **$1,709,590,738** | **$541,281,648** | **24.0%** | **5,150** |

### 2025 is a partial year and must be labelled as such

578 documents against roughly 2,285 in each of the two prior years, and the
ledger's last posting date is **2025-03-28**. Fiscal 2025 is about a quarter of
a year.

The 7.0% margin is therefore not a margin collapse. It is a quarter of revenue
carrying a quarter's worth of variable expense against a period's fixed costs,
and comparing it to a full-year 26.7% is comparing different things. Any
year-on-year chart built from `DT_PNL_SUMMARY` that does not mark 2025 partial
tells a story that did not happen — and it is an easy chart to build, because the
data offers no hint that the third bar is short.

### Documents and line items differ by exactly 2×

`DT_PNL_SUMMARY` accounts for 5,150 documents. `DT_JOURNAL_ENTRY_360` holds
10,300 rows — exactly twice that, with no remainder.

Every accounting document in this dataset has precisely two line items. That is
consistent with a balanced debit/credit pair per document, and it explains why
the sign problem above is so easy to trip over: for any document, the two lines
very nearly cancel. A `SUM` without `ABS` over the whole table is close to
measuring the residual of 5,150 near-cancellations rather than measuring money.

It also means row counts and document counts in this stack are never
interchangeable, and a "number of transactions" tile has to say which it counts.

---

## `DT_AR_AGING` is a plain table wearing a dynamic table's prefix

`ANALYTICS` holds seven objects. Six are dynamic tables. `DT_AR_AGING` is not —
`SHOW DYNAMIC TABLES` returns six names and this is not among them.

| | Value |
|---|---|
Objects in `ANALYTICS` | 7 |
`DT_`-prefixed | 7 |
Actually dynamic | 6 |
Prefixed but not dynamic | **`DT_AR_AGING`** |

The reason is sound: **the SAP BDC Standard Data Products in scope publish no
receivables object.** There is no L1 source for AR, so there is nothing for a
dynamic table to be defined over. It is generated data in a plain table.

The naming is what is wrong, not the decision. The prefix asserts a refresh
behaviour that does not exist, and the consequences are concrete:

- No refresh history, no lag metric, and `ALTER ... REFRESH` does not apply.
- A monitoring check that enumerates `DT_*` and expects lag reports a false
  failure on this one object.
- AR figures do not move when L0 moves, while the other six do.

The AR data window makes the same point independently: `INVOICEDATE` runs from
**2024-11-14 to 2026-05-07**, while the ledger ends 2025-03-28. AR extends more
than a year past the last real posting and starts nearly two years after the
first. No object derived from this ledger would have that shape.

Call this out when presenting. A customer architect who discovers it unprompted
reasonably starts doubting the other six.

---

## AP aging is concentrated in 90+ days, and the gross exceeds revenue

| Bucket | Invoices | Gross |
|---|---|---|
90+ Days | 294 | $2,988,769,953 |
31–60 Days | 52 | $760,068,090 |
61–90 Days | 45 | $367,579,488 |
Current | 28 | $223,910,152 |
**Total** | **419** | **$4,340,327,683** |

Two observations, one useful and one a caveat.

**70% of invoices by count and 69% by value sit in 90+ days.** As a demo asset
that is convenient — the Accounts Payable page has an obvious story. As a
representation of a real AP ledger it is extreme.

**The caveat is larger.** Total AP gross of $4.34bn exceeds three years of
recognised revenue ($2.25bn) by nearly a factor of two, across only 419
invoices — an average of $10.4m per invoice. That is not a plausible payables
position for the entity the P&L describes.

The explanation is that AP and the P&L are not derived from a common base: AP
comes from `SUPPLIERINVOICE` gross document amounts, while the P&L comes from
posted line items. They are different populations at different grains, and the
1.9× ratio is an artefact of that rather than a finding about the business.

Do not put AP gross and revenue on the same axis, and do not compute a
payables-to-revenue ratio from these two objects. Nothing in the data warns you
off it.

---

## AR reconciles internally, which is worth knowing

Unlike the AP-to-P&L comparison, AR is internally consistent — both its value
and its count totals tie exactly.

| Bucket | Invoices | Open amount | Overdue |
|---|---|---|---|
Current | 402 | $52,470,239 | 0 |
1–30 Days | 107 | $13,524,995 | 107 |
31–60 Days | 63 | $8,842,173 | 63 |
61–90 Days | 38 | $4,367,229 | 38 |
91–120 Days | 27 | $3,360,537 | 27 |
120+ Days | 248 | $29,739,586 | 248 |
Cleared | 2,983 | $0 | 0 |
**Total** | **3,868** | **$112,304,759** | **483** |

The open-amount column sums to exactly the independently extracted
`SUM(OPENAMOUNT)` of $112,304,759, and the overdue flags sum to exactly the
independently extracted overdue count of 483. Two reconciliations that hold.

The distribution has the same shape as AP — 248 of 483 overdue invoices, and
$29.7m of $59.8m overdue value, in the oldest bucket. The oldest bucket being the
largest in both AP and AR is a property of how this data was generated, not an
independent finding repeated twice.

`Cleared` at 2,983 invoices is 77% of the object and carries zero open amount.
Any AR average computed without excluding it is divided by a denominator four
times too large.

---

## The app straddles two layers

The Express server's `api.ts` reads both the L0 shares and L2, in almost equal
measure:

| | `FROM` clauses |
|---|---|
Directly against `SAP_BDC_DEMO_*` shares (L0) | **21** |
Against `SAP_FINANCE_360.ANALYTICS` (L2) | **20** |

The single largest source is `OPERATIONALACCTGDOCITEM` at 13 clauses — an L0
object, not an L2 one.

This was a deliberate choice and it demonstrates the zero-copy claim in the most
direct way available: a third of the application's queries execute against the
provider's storage, with no copy anywhere in the path. Page 8, BDC Data Products,
exists to make that visible.

It carries two costs.

**The sign discipline is duplicated.** Those 21 clauses do not inherit L2's `ABS`
and `DEBITCREDITCODE` handling. Every one of them has to get it right
independently, and a new query added against `OPERATIONALACCTGDOCITEM` is a fresh
opportunity to get it wrong silently.

**Two L2 objects are read by nothing.** `DT_GL_BALANCE` (1,793 rows) and
`DT_PNL_SUMMARY` (81 rows) appear in no `FROM` clause. The General Ledger and
Period Analysis pages compute from L0 instead of reading the matching aggregate.
Those two dynamic tables are maintained, refreshed and unused by the application.

That is not automatically wrong — `DT_PNL_SUMMARY` is the object this handbook
reconciles against, so it earns its keep as a control total. But it means the
dynamic-table refresh cost is being paid for objects no page reads, and a
reviewer who assumes "the app reads L2" will misjudge both the app and the
refresh footprint.

---

## Two semantic views, and neither is complete

| | `ANALYTICS.SAP_FINANCE_360` | `SEMANTIC.SAP_FINANCE_360_ANALYTICS` |
|---|---|---|
Logical tables | 4 | 5 |
Table names | `AR`, `EXPENSE`, `JOURNAL`, `REVENUE` | `AP_AGING`, `EXPENSE_BY_COSTCENTER`, `JOURNAL_ENTRY`, `PNL_SUMMARY`, `REVENUE_BY_PROFITCENTER` |
Relationships | **0** | 12 |
Metrics | 45 | **0** |

The two are complements rather than versions. One has the metrics and cannot
join; the other can join and has no metrics. Neither exposes `DT_GL_BALANCE`.

Neither is a subset of the other, so "use the newer one" is not available as
advice. A question needing a metric and a join across two tables cannot be
answered by either view alone.

This is the least defensible part of the stack. It is not a discovery about SAP
or about Snowflake — it is where iteration stopped. If you are reproducing this
pattern, build one view with both the relationships and the metrics.

The `DESCRIBE SEMANTIC VIEW` dimension tallies — 120 and 251 — are large because
SAP source objects are wide and each retained column becomes a dimension. Read
them as describe-output row counts, not as a count of curated dimensions; nobody
wrote 251 dimension descriptions.

---

## The Cortex Analyst model has zero verified queries

The app's Analyst page reads
`@SAP_FINANCE_360.SEMANTIC.SEMANTIC_MODELS/finance_360.semantic.yaml`:

| Property | Value |
|---|---|
Model name | `sap_finance_360` |
Base tables | 4 |
Dimensions | 24 |
Measures | 9 |
Facts | 0 |
**Verified queries** | **0** |

Zero verified queries is a real gap, and it should be stated rather than glossed.
Verified queries are how a Cortex Analyst model is told what question shapes it
exists to serve. With none, every question is answered from column names and
descriptions alone, and the model has no worked example of the very thing that is
hardest about this data — the `ABS` plus `DEBITCREDITCODE` pattern.

The likely failure mode is therefore not a refusal but a confidently wrong
aggregate, which is the worst available outcome for a finance demo in front of an
architect.

Three of the seven L2 objects are outside the model entirely:

| Excluded | Rows | Consequence |
|---|---|---|
`DT_AP_AGING` | 419 | no accounts-payable question can be answered |
`DT_GL_BALANCE` | 1,793 | no GL-balance question can be answered |
`DT_PNL_SUMMARY` | 81 | no P&L-summary question can be answered |

The app has dedicated pages for Accounts Payable, General Ledger and Period
Analysis. A user who sees those pages and then asks the Analyst page a question
about them gets nothing useful, and the interface gives no indication why.

Closing this is the highest-value remaining work on the stack. Detail in
[the analyst and agent layer](07-analyst-and-agent.md).

---

## Summary of open gaps

| Gap | Severity | Fix |
|---|---|---|
0 verified queries in the Analyst model | high | add queries, starting with signed-amount aggregation |
3 of 7 L2 tables outside the Analyst model | high | extend the model, or disclose the boundary in the UI |
Two incomplete semantic views | medium | consolidate into one with metrics and relationships |
`DT_AR_AGING` misnamed as dynamic | medium | rename, or document at every handover |
AP gross not comparable to P&L revenue | medium | never chart together; note the differing grain |
Signed-amount handling duplicated in 21 app clauses | medium | route app reads through L2, or centralise a helper |
`DT_GL_BALANCE`, `DT_PNL_SUMMARY` read by no page | low | point the pages at them, or drop them |
AR window does not overlap the ledger | low | state it wherever AR and revenue appear together |
