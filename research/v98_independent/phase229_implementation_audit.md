# V98 Independent — Phase229 implementation audit

Status: **PRE-RESULT / NO RESULT OBSERVED**

## Scope
Independent code-to-preregistration audit after implementation and before any Phase229 result observation. Only `research/v98_independent/*` on `research/v98-independent-zero` is in scope.

## Frozen-grid audit
`phase229_eval.py` enumerates exactly 8 specs: `{hour_of_day,hour_of_week} × {12,24} prior occurrences × {1,4}h holding`. Universe is the frozen five assets. Folds are independent calendar 2023/2024/2025 and costs are exactly 7/14/28 bp.

## Causality audit
At decision row `i`, the history deque is updated only with the completed return `open(i-1) -> open(i)`, assigned to the bucket whose occurrence began at `i-1`. The decision bucket at `i` therefore contains no return beginning at `i`, and no future row. A bucket cannot trade before exactly the frozen number of prior occurrences exists. Direction is the sign of the trailing mean with no threshold, bucket deletion, asset deletion, or regime conditioning.

## Execution/accounting audit
Positions enter at `open(t)` and persist deterministically for `H`; same-asset overlap is blocked. Simultaneous signals equal-weight subject to remaining gross capacity and an explicit `gross <= 1` invariant. Turnover costs are charged from absolute weight changes; realized PIT funding is mapped to the next executable hourly cash row and charged while exposure is carried.

## Firewall/reproducibility audit
Price and funding loaders reject duplicate/non-monotonic timestamps and any timestamp >= 2026-01-01. Result JSON uses sorted deterministic serialization and embeds SHA-256. `phase229_validate.py` checks the exact grid/folds/costs, required decision metrics, monotonic cost degradation, deterministic payload SHA, and the preregistered annual gate.

## Diagnostics retained
Each fold/cost reports return, max drawdown, PF, payoff, win rate, positive days, trades, five tail quantiles, best/worst trade, per-asset PnL and maximum concentration, realized funding contribution, and causal BTC 168h bull/bear/sideways decomposition.

## Decision discipline
No Phase229 result has been observed while writing this audit. Zero survivors means `REJECT_FAMILY_NO_RESCUE`; a survivor must still clear concentration/tails/regime/stress/reproducibility gates. Champion and 2026+ holdout remain unchanged/closed.
