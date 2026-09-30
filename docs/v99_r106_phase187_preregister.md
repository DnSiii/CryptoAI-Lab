# V99 R106 Phase187 — preregistration

## Hypothesis

**Cross-venue BTC/ETH relative return disagreement persistence (OKX vs Binance), TRAIN-only.**

This phase is intentionally orthogonal to Phase182–186's single-venue price/residual/shock family. It returns to the independently audited OKX second-venue source already admitted by Phase136, rather than creating another cosmetic transform of Binance OHLCV.

Economic hypothesis: when the point-in-time OKX-vs-Binance *relative* BTC/ETH return spread shows a sufficiently unusual venue disagreement at t-1, the relative disagreement can persist for the next hour because price discovery is temporarily uneven across venues. This is a continuation hypothesis on a cross-venue discrepancy, not a post-hoc sign flip of Phase186.

## Frozen construction before PnL

- Universe: BTC and ETH perpetual hourly streams on Binance and OKX, restricted to the already audited common TRAIN window.
- TRAIN end exclusive: `2024-01-18T00:00:00+00:00`.
- No holdout values may be parsed during selection/evaluation.
- For each venue at t-1, compute one-hour BTC and ETH close-to-close returns using information available no later than t-1.
- Relative return per venue: `ETH_return - BTC_return`.
- Cross-venue disagreement: `OKX_relative_return - Binance_relative_return`.
- Standardize disagreement using trailing 168 completed hours ending at t-2 only.
- Trigger: `abs(z_disagreement) >= 2.0`.
- Direction: continuation, `sign(z_disagreement)`.
- Position at t: market-neutral ETH/BTC sleeve, gross 0.20: ETH `+/-0.10`, BTC opposite `-/+0.10` according to direction.
- No parameter sweep, no threshold alternatives, no sign inversion after observing PnL.

## Mandatory evaluation

1. Causality test proving mutations at t cannot alter the signal at t.
2. Chronological temporal folds; no shuffled CV.
3. Severe costs and supersevere = 2x severe.
4. Deterministic replay / reproducibility check.
5. Tail/concentration audit including remove-best-hour.
6. V16 Frozen and V99 Frozen hash/integrity check before and after.
7. If TRAIN alpha gate passes, freeze the candidate before regime matrix and benchmark envelope. Holdout remains untouched until all pre-holdout gates are complete.

## Kill criteria

Permanent rejection without retuning if aggregate economics are negative/weak under severe costs, temporal support is absent, supersevere destroys the edge, or the apparent edge depends materially on one tail observation/fold. A rejection closes this exact hypothesis; it does not authorize sign inversion or parameter search.

## Scientific distinction

Phase186 asked whether a Binance BTC volatility shock predicts Binance ETH/BTC continuation. Phase187 asks whether *venue disagreement in the ETH-vs-BTC relative return itself* carries forward. The information source and mechanism are therefore different, while execution discipline remains identical.
