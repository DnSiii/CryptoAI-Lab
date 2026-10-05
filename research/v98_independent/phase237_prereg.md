# V98 Independent Phase237 — preregistration

## Frozen hypothesis
Cross-sectional **lagged idiosyncratic downside-semivariance relative value**. After removing lagged BTC beta, assets with persistently larger downside-only residual variance may carry a distinct cross-sectional risk premium from total variance, skewness, or kurtosis. This is a scientifically distinct downside-tail magnitude hypothesis; it is not a rescue/sign flip of Phase236.

## Information set / causality
- Universe remains BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT; BTC is the market factor and is not traded by the cross-sectional sleeve.
- Hourly close-to-close returns from training-only canonical data, cutoff strictly `<2026-01-01`.
- At each residual timestamp `u`, rolling beta is estimated only through `u-1`; residual(u) = r_asset(u) - beta_lagged(u)*r_BTC(u).
- Downside semivariance at decision timestamp `t-1` uses only residual observations through `t-1`: mean(square(min(residual,0))) over the frozen window.
- Position opened at open(t) uses the ranking known at t-1. No contemporaneous feature use.

## Frozen grid — exactly 8 specs
Cartesian product:
- beta lookback: {168h, 336h}
- downside-semivariance lookback: {72h, 168h}
- holding horizon: {4h, 8h}
- k=1 long and k=1 short

Direction is frozen **long highest downside semivariance / short lowest downside semivariance**. No sign flip or rescue after results.

## Evaluation
Chronological annual folds 2023, 2024, 2025 only. 2026+ is untouched holdout and must remain unread for selection/tuning. Equal-weight long/short with portfolio gross exposure <=1. Funding is point-in-time and applied according to held position. Trading costs are frozen at 7 bp base, 14 bp severe, 28 bp supersevere per unit L1 turnover.

For every spec/fold/cost report at minimum: return, max drawdown, Profit Factor, payoff, win rate, positive days, turnover, funding contribution, asset PnL contribution/concentration, hourly return tails, best/worst day, and bull/bear/sideways regime diagnostics.

## Mechanical gate / anti-overfit
A spec must satisfy the existing V98 annual decision gate in **every** chronological fold; no averaging away a failed year. Severe/supersevere results are robustness evidence and may not be ignored. No parameter additions, threshold search, sign reversal, cherry-picking, or holdout opening after observation. If all 8 fail, reject the family with `REJECT_FAMILY_NO_RESCUE` and move to a genuinely distinct preregistered hypothesis.

## Reproducibility / integrity
Before interpreting performance: assert cutoff/firewall, sorted unique timestamps, exact frozen grid, lagged beta and `signal[t-1] -> open(t)`, gross<=1, deterministic double execution with byte-identical output/SHA, and independent mechanical validation.

Preregistered before any Phase237 performance result is generated or inspected.