# V98 Independent Phase235 — preregistration

Status: FROZEN BEFORE ANY PHASE234 RESULT. Phase234 outcomes MUST NOT alter this hypothesis or grid.

## Hypothesis
Cross-sectional **lagged idiosyncratic-skewness relative value**. After removing BTC beta causally, rank assets by the skewness of residual hourly returns using only information ending by `open(t-1)`. Test whether negative-residual-skew assets earn a relative premium versus positive-residual-skew assets over multi-hour horizons. This is distinct from Phase230 residual direction/momentum, Phase231 total-volatility dispersion, Phase232 beta-level dispersion, Phase233 residual-return reversal, and Phase234 residual-volatility magnitude.

## Information set / execution
- Fixed universe: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT.
- Decision at `open(t)` may use hourly open-to-open returns ending no later than `open(t-1)`.
- Rolling BTC beta is estimated causally; residual returns are `asset_return - beta_lagged * BTC_return`.
- Signal is rolling residual-return skewness at `t-1`; deterministic rank `(residual_skewness, symbol)`.
- Long lowest-skew assets and short highest-skew assets; equal absolute weights, dollar-neutral, gross <= 1.
- No regime filter, sign flip, asset exclusion, threshold rescue, post-result tuning, or access to 2026+.

## Frozen grid — exactly 8 specs
`(beta_lookback_hours, skew_lookback_hours, k_each_side, hold_hours)`:
- (168, 72, 1, 4), (168, 72, 1, 8)
- (168, 168, 1, 4), (168, 168, 1, 8)
- (336, 72, 1, 4), (336, 72, 1, 8)
- (336, 168, 2, 4), (336, 168, 2, 8)

## Evaluation and gate
Chronological untouched training folds are calendar 2023, 2024, 2025; holdout 2026+ remains unopened. Funding is point-in-time causal. Costs are frozen at base 7 bp, severe 14 bp, supersevere 28 bp with turnover accounting.

For every spec/fold/stress record total return, max drawdown, Profit Factor, payoff, win rate, positive days, tails, asset contribution/concentration, funding contribution, and lagged BTC bull/bear/sideways regimes. Require deterministic reproduction, data firewall, gross-exposure invariant, cost monotonicity, and independent validation.

Use the existing V98 annual mechanical gate unchanged: every base fold must have return > 0, PF > 1, positive-days > 0.5, max DD > -50%; severe PF > 0.90 and supersevere PF > 0.80. Every fold must pass. No survivors => `REJECT_FAMILY_NO_RESCUE`.

Phase234 results may determine only whether Phase235 is executed next; they may not modify this preregistration.
