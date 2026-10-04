# V98 Independent Phase232 — implementation audit

Status: PRE-RESULT / NO PHASE232 OUTPUT OBSERVED.

## Scope
Audit of `phase232_eval.py` and `phase232_validate.py` against the frozen Phase232 preregistration. This document is V98-only and does not inspect or use V99/V16 state.

## Causality
- Decision occurs at `open(t)`.
- Hourly open-to-open return row `j` is known at `open(j)`.
- Rolling covariance/variance beta row `i-1` therefore uses observations ending at `open(t-1)`; the decision loop reads only `beta.iloc[i-1]`.
- No return at `open(t)` or later enters beta ranking.
- BTC is included in the frozen universe; its beta to itself is mechanically near 1, as implied by the preregistered universe/ranking rule. No ex-post exclusion is allowed.

## Frozen design parity
Exactly 8 specs: (72,1,4), (72,1,8), (168,1,4), (168,1,8), (336,1,4), (336,1,8), (168,2,4), (336,2,8). Folds are calendar 2023/2024/2025. Costs remain 7/14/28 bp. Ranking is deterministic `(beta,symbol)`, long lowest beta and short highest beta, equal absolute weights, overlapping H-hour sleeves, gross normalized only when above 1.

## Data/firewall/funding
Price and funding loaders reject duplicates, non-monotonic timestamps and any timestamp >= 2026-01-01. Funding cash is delayed to the first hourly decision timestamp strictly after the raw funding timestamp and charged from lagged position, preserving point-in-time accounting.

## Diagnostics/invariants
Evaluator records return, max drawdown, PF, payoff, win rate, positive days, tails, asset contribution/concentration, funding contribution and lagged BTC regimes. Gross exposure is asserted <=1. Validator asserts exact grid/folds/cost labels and cost-return monotonicity, then applies one mechanical annual gate to all specs with no rescue.

## Known diagnostic limitation
As in the prior overlapping-sleeve families, the per-event `trade` tail attribution is diagnostic rather than an exact decomposition of portfolio PnL because sleeves overlap and portfolio gross normalization can couple sleeves. Portfolio hourly accounting, equity/DD, PF and annual gate are authoritative. Tail diagnostics cannot independently justify promotion.

## Anti-overfit disposition
No Phase232 result existed or was read while implementing/auditing these files. Phase231 may justify executing Phase232 but did not alter its hypothesis or grid. Holdout 2026+ remains unopened. Any future modification to economic parameters after observing Phase232 results is forbidden; if the frozen gate fails, disposition is `REJECT_FAMILY_NO_RESCUE`.
