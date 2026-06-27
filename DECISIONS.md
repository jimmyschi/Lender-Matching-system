# DECISIONS.md

## Which Lender Requirements Were Prioritized

All five lenders' core credit criteria are implemented: FICO minimums, PayNet minimums, time in business, loan amount limits, geographic restrictions, industry exclusions, equipment type exclusions, bankruptcy history rules, and borrower-level flags (judgments, foreclosures, repossessions, tax liens, citizenship, homeownership).

**Stearns Bank** — All three program tracks (standard with PayNet, no-PayNet, corp-only) are modeled across all three tiers each, giving nine programs. The tier system (Tier 1 is best, tried first) reflects the real structure of their credit box.

**Apex Commercial Capital** — A+, Standard A/B/C, Medical A/B, and Corp Only programs are all modeled. The A+ program's restricted industry/equipment allowlist and 5-year collateral age cap are enforced. State restrictions (CA, NV, ND, VT) and the full excluded equipment list are included.

**Advantage+ Financing** — The non-trucking-only constraint, hard no-BK/judgment/foreclosure/repossession/lien rules, and US citizen requirement are all hard rejects. The $75K max and $10K min loan are enforced.

**Citizens Bank** — All four tiers (General app-only, Startup app-only, Non-Homeowner, and Full Financial Review) are modeled with their respective loan amount caps and documentation requirements described. The CA exclusion, cannabis exclusion, 5-year BK discharge rule, and US citizen requirement are enforced.

**Falcon Equipment Finance** — Standard commercial and trucking-specific (A/B only) programs with separate FICO/PayNet/TIB minimums. The fleet size requirement (5+ trucks) and 15-year BK discharge rule are modeled.

## Simplifications Made and Why

**One FICO field for all lenders.** Stearns and Apex use standard FICO, Citizens Bank uses TransUnion, and Advantage+ specifies FICO v5 (Equifax). A fully correct system would collect three separate bureau scores. With 48 hours available, one field is used with a note on the form and in criterion descriptions. This is the most visible gap.

**Comparable debt / trade line checks are not modeled.** Stearns requires comparable business borrowing (open/closed account equal to or exceeding the requested amount or 3+ $10K contracts in last 12 months). Apex requires 50% revolving available and comparable borrowing at higher amounts. These require detailed tradeline data that a real system would pull from a credit bureau. They are described in lender descriptions but not enforced as criteria.

**Advantage+ startup FICO (700) vs standard FICO (680) is not split into two programs.** The standard program uses 680, which is the non-startup floor. A startup applicant who meets 680 but not 700 will show as eligible at 680 but the lender description notes the higher requirement. This was simplified to avoid a separate startup program that adds UI complexity without much demo value.

**Citizens Bank CDL and fleet requirements for the startup program** are noted in the program description but not modeled as hard-reject criteria because verifying "Class A CDL for 5 years" requires additional time-series data the application form does not capture.

## What Would Be Added With More Time

**Multi-bureau credit score capture.** Separate fields for TransUnion, Equifax FICO v5, and Experian, with each lender's criteria mapping to the appropriate bureau.

**Comparable debt criteria.** A structured tradeline input (list of existing accounts with balance, type, payment status, age) would enable Stearns and Apex's comp-debt checks.

**Audit trail.** Track which criteria or program thresholds changed and when, so results from a prior underwriting run remain reproducible even after a lender updates their guidelines.

**Rate calculation.** Given a matched program and loan amount, compute the actual interest rate and monthly payment. The rate tables are in the PDF data but outputting a rate estimate was deprioritized in favor of showing eligibility and fit score clearly.
