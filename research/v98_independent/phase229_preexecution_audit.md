# V98 Independent — Phase229 pre-execution audit

Status: **PASS — SAFE TO IMPLEMENT WITHOUT RESULT OBSERVATION**

## Independence audit
Phase229 tests calendar periodicity estimated causally from repeated UTC buckets. It does not rescue Phase228 by changing compression/breakout windows, thresholds, assets, regimes, or costs. It does not use V99 information or state.

## Leakage / causality audit
For decision timestamp `t`, the bucket statistic may contain only completed open-to-open returns whose ending timestamp is `< t`. The occurrence at `t` is never part of its own estimator. Hour-of-day and hour-of-week labels are deterministic calendar metadata, not future information. Full selected lookback count is mandatory before eligibility.

## Frozen implementation invariants
1. Exactly 8 specs: 2 bucket definitions × 2 lookbacks × 2 holdings.
2. Universe exactly BTC/ETH/BNB/XRP/SOL USDT.
3. Entry `open(t)`; exit `open(t+h)`; no same-asset overlap; gross <=1.
4. Costs exactly 7/14/28 bp round-trip plus realized PIT funding.
5. Independent calendar folds 2023/2024/2025; no 2026+ reads.
6. Report DD, PF, payoff, win rate, positive days, trades, tails, concentration, asset/funding contribution and bear/bull/sideways regimes.
7. Two byte-identical deterministic evaluations required.
8. Gate may not be altered after results.

## Failure-mechanism checks required after run
- Determine whether any apparent edge is dominated by a single asset or small UTC bucket subset without deleting those buckets post hoc.
- Inspect p01/p05 and worst trade versus median/payoff to detect tail dependence.
- Compare bear/bull/sideways without introducing a regime filter.
- Verify severe/supersevere monotonic deterioration and whether base edge survives realistic friction.
- Reconstruct sampled bucket estimates from strictly prior rows as an independent causal invariant.

Champion and untouched holdout remain unchanged.