# V98 Independent Phase215 — preregistration

Status: **FROZEN BEFORE RESULTS**

## Hypothesis
A scientifically distinct family: **cross-sectional alt relative-strength dispersion**. Instead of forecasting each asset from its own candle/range state, test whether contemporaneously observable cross-sectional ranking among ETHUSDT, BNBUSDT, XRPUSDT and SOLUSDT has persistent continuation: long the strongest alt and short the weakest alt after sufficiently large causal return dispersion. This is market-neutral by construction and is orthogonal to Phase211 BTC lead-lag and Phase212–214 single-asset OHLC reversal/continuation families.

## Data / firewall
Training-only canonical 1h futures OHLC for ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT; realized PIT funding. Hard cutoff `<2026-01-01`. BTC is used only for the standard causal bull/bear/sideways regime label. Validation/final holdout remains closed. No V99 information may be used.

## Causality
At decision bar t, compute each alt's trailing return from close(t-1-L) to close(t-1), using only bars fully known before entry. Rank the four returns at t-1. Long rank 1 and short rank 4 only when cross-sectional dispersion (max return minus min return) exceeds frozen threshold D. Position starts at t and holds fixed H hours. Rankings/dispersion are not recomputed during a hold. No future or contemporaneous t information is used.

## Frozen grid — exactly 8 specs
Cross product:
- lookback L: {6h, 24h}
- minimum dispersion D: {0.015, 0.030} absolute return
- hold H: {3h, 6h}

Fixed, non-tuned constants:
- four-alt universe: ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT
- one equal-notional long and one equal-notional short per signal; gross notional normalized so portfolio exposure is comparable with prior V98 evaluators
- ties broken deterministically by fixed symbol order
- no asset deletion and no regime-conditioned entry
- overlapping signals handled with the same deterministic fixed-hold convention used by the V98 independent evaluators; no post-result execution change

## Evaluation
Chronological folds: 2023, 2024, 2025. Report base/severe/supersevere realistic round-trip costs using existing V98 conventions plus realized PIT funding on both legs. For every fold/spec/cost: return, max drawdown, Profit Factor, payoff, win rate, positive days, trades, p01/p05/p50/p95/p99, worst/best trade, per-asset contribution/concentration, and bull/bear/sideways regime metrics.

## Mechanical training gate
A spec is training-fold coherent only if base return > 0 AND base PF > 1 in each of 2023, 2024, 2025. This is necessary, not sufficient. A coherent spec must next survive severe/supersevere economics, tails, concentration, regimes and reproducibility without changing this definition. If 0/8 pass, close as `REJECT_FAMILY_NO_RESCUE`.

## Reproducibility / anti-overfit
Evaluator output must be deterministic and byte-identical on two executions. No sign inversion, asset removal, regime rescue, parameter expansion, threshold retuning, opened holdout, or V99-derived selection after results. Any successor family after rejection must be scientifically distinct and preregistered first.