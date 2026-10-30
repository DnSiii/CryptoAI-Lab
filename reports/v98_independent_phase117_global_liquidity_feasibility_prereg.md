# V98 Independent — Phase117 Global Liquidity DATA_ONLY preregistration

Status: PREREGISTERED BEFORE DATA INSPECTION.

## Scientific question
Can a genuinely orthogonal, public macro-liquidity family be acquired reproducibly for the frozen V98 training window without inspecting values, distributions, returns, correlations, alpha, or PnL?

## Frozen source and field
Source: FRED public CSV. Series: WALCL (Federal Reserve total assets). Exact source URL template: `https://fred.stlouisfed.org/graph/fredgraph.csv?id=WALCL&cosd=2023-01-01&coed=2025-12-31`.

This is intentionally distinct from Phase116 DTWEXBGS/DXY. No alternate series, source substitution, sign/window/cadence shopping, or partial-era rescue is allowed after seeing the result.

## Frozen window and gate
Training only: 2023-01-01 through 2025-12-31 inclusive. Validation and final holdout MUST NOT be accessed.

Because WALCL is weekly, the expected index is the set of Wednesdays in the frozen training window. Gate: HTTP 200; >=95% expected-Wednesday coverage; zero invalid/nonfinite observations after canonicalization; zero duplicate observation dates; zero outside-training rows; deterministic payload SHA256 and canonical-date-index SHA256.

Federal-holiday publication shifts are deliberately treated conservatively: a missing frozen Wednesday counts against coverage. No forward-fill or interpolation is permitted in DATA_ONLY.

## Forbidden before gate passes
No observation values in report output; no min/max/mean/median/quantiles; no changes/returns; no correlations; no crypto joins; no alpha/PnL; no parameter search; no use of V16, V99, Phase083, validation, or final holdout.

## Decision rule
All frozen gates pass => `PASS_DATA_ONLY`, which only authorizes preregistration of a trading hypothesis before any PnL is inspected. Any gate fails => `REJECT_DATA_SOURCE_NO_RESCUE`; close this exact family/source without source-shopping.
