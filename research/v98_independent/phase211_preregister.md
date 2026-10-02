# V98 Independent Phase211 — preregistration

Status: **FROZEN BEFORE RESULTS**

## Hypothesis
A market-wide BTC impulse can lead delayed continuation in liquid alts over the next few hours. This is scientifically distinct from Phase207 residual cross-sectional momentum, Phase208 volatility-compression breakout, Phase209 dispersion-shock reversal, and Phase210 hour-of-week residual reversal: the predictor is a lagged BTC market impulse and the target is subsequent alt return, not contemporaneous cross-sectional ranking or seasonal residuals.

## Universe / folds / holdout
- Signal asset: BTCUSDT.
- Traded assets: ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT.
- Chronological training folds scored separately: calendar 2023, 2024, 2025.
- Data strictly `<2026-01-01` only. Validation/final holdout remains unopened.
- Warm-up may use earlier training history but may not originate scored positions.

## Causality
At decision/open time `t`, BTC impulse is computed only from closes known through `t-1`. Position opens at `t` open and exits at `t+H` open. No value at or after `t` may enter the signal. Funding is charged only when a realized funding timestamp lies inside the actual holding interval, using the position sign.

## Frozen signal
`btc_ret_L(t) = close_BTC(t-1) / close_BTC(t-1-L) - 1`.

Estimate a rolling robust scale of `btc_ret_L` using observations ending at `t-1`, with a fixed 90-day (2160 hourly observation) window; median and MAD are computed causally. Define robust z-score `z=(x-median)/(1.4826*MAD)`. When `z >= Z`, go long each available alt; when `z <= -Z`, go short each available alt; otherwise flat. Equal notional across available alts. No asset selection/ranking. No regime filter.

## Exactly 8 frozen specs
Cartesian grid:
- impulse lookback `L`: 6h, 12h
- threshold `Z`: 2.0, 2.5
- holding `H`: 6h, 12h

Names: `leadbtc_L{6|12}_z{20|25}_hold{6|12}`. No other parameter values may be tried for Phase211.

## Costs / funding
Use the same V98 Independent realized funding data and cost accounting convention already used by Phases206-210. Report base, severe, and supersevere costs separately. No cost-free headline selection.

## Required outputs per spec × fold × cost level
Return, max drawdown, Profit Factor, payoff, win rate, positive days, trade count, best/worst trade, p01/p05/p50/p95/p99 tails, asset returns/concentration, funding contribution by asset, and BTC-defined bull/bear/sideways regime metrics.

## Mechanical training gate
A spec is training-fold coherent only if **base return > 0 and base Profit Factor > 1 in each of 2023, 2024, and 2025**. If zero of 8 pass, reject family with no rescue. Passing the training gate is not sufficient for champion promotion or holdout opening; it only permits the next preregistered validation step.

## Reproducibility / invariants
- Rebuild training-only canonical data.
- Assert timestamps monotonic, unique, and `<2026-01-01` for price/funding inputs.
- Run evaluator twice and require byte-identical report SHA256.
- Assert exactly 8 specs and exact fold labels.
- No V99 evidence may be used for tuning/selection.
- No inversion, post-hoc threshold change, asset exclusion, regime rescue, or holdout inspection after seeing results.
