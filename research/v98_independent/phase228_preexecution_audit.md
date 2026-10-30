# V98 Independent — Phase228 pre-execution audit

Status: **PASS_FOR_EXECUTION; NO RESULT OBSERVED**

## Scope
Independent static audit against `phase228_preregister.md` before any Phase228 result exists.

## Causality / leakage
- Signal at execution row `t` uses close/high/low and realized-volatility information ending at `t-1`.
- Breakout reference is `shift(2).rolling(BW)`, therefore excludes both current bar `t` and breakout bar `t-1` from its reference extrema.
- Compression observation is realized volatility through `t-1`; its causal 20th-percentile reference uses the preceding 720 observations via an additional shift and therefore excludes the tested observation.
- Entry accounting is open-to-open through lagged positions; funding is realized PIT only.
- Price and funding loaders fail closed on duplicates, non-monotonic timestamps, or any timestamp >= 2026-01-01.

## Frozen design parity
- Universe exactly BTC/ETH/BNB/XRP/SOL perpetual symbols used by the preregistration.
- Exactly 8 specs: compression window {24,72} x breakout window {24,72} x holding {4,8}.
- Calendar folds 2023, 2024, 2025 are evaluated independently.
- Round-trip cost stresses remain 7/14/28 bp plus realized PIT funding.
- No same-asset overlap; portfolio gross exposure invariant <=1; existing positions are never rescaled.

## Decision evidence
Evaluator emits return, max drawdown, PF, payoff, win rate, positive days, trades, five trade-tail quantiles, best/worst trade, asset contribution/concentration, funding contribution and causal BTC bear/bull/sideways decomposition. Independent validator enforces exact grid/folds/cost labels, deterministic payload SHA, monotonic return deterioration under cost stresses, and the preregistered annual base gate.

## Risks to inspect after execution
1. Sparse breakouts after compression may fail the >=30 trades/year gate.
2. Breakout continuation can be dominated by a few right-tail events; inspect median/p01/p05 and concentration even if aggregate return is positive.
3. Simultaneous signals share remaining gross capacity; inspect whether a single asset/year dominates realized PnL.
4. Severe/supersevere deterioration can veto apparent base-cost success.
5. Regime dependence must not be retroactively filtered; it is diagnostic only.

No rescue, threshold extension, asset deletion, regime selection or holdout access is authorized after observing Phase228 results.
