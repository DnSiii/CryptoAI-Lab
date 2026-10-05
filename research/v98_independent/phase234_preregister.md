# V98 Independent Phase234 — preregistration

Status: FROZEN BEFORE ANY PHASE233 RESULT. Phase233 outcomes MUST NOT alter this hypothesis or grid.

## Hypothesis
Cross-sectional **lagged idiosyncratic-volatility relative value**: after removing contemporaneous BTC beta using only information available before `open(t)`, rank assets by realized residual volatility and test whether the low-residual-volatility side earns a relative premium versus the high-residual-volatility side over multi-hour horizons. This is economically distinct from Phase230 residual momentum, Phase231 total-volatility dispersion, Phase232 beta-level dispersion, and Phase233 residual-return reversal: the signal is the magnitude/dispersion of idiosyncratic risk, not residual direction.

## Information set / execution
- Fixed universe: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT.
- Decision at `open(t)` may use hourly open-to-open returns ending no later than `open(t-1)`.
- Rolling BTC beta is estimated causally from a frozen historical window; residual returns are `asset_return - beta_lagged * BTC_return`.
- Signal is rolling standard deviation of residual returns, evaluated at `t-1`.
- Rank deterministically by `(residual_volatility, symbol)`; long lowest residual-volatility assets and short highest residual-volatility assets; equal absolute weights, dollar-neutral, gross <= 1.
- No regime filter, sign flip, asset exclusion, threshold rescue, post-result tuning, or access to 2026+.

## Frozen grid — exactly 8 specs
`(beta_lookback_hours, residual_vol_lookback_hours, k_each_side, hold_hours)`:
- (168, 24, 1, 4), (168, 24, 1, 8)
- (168, 72, 1, 4), (168, 72, 1, 8)
- (336, 24, 1, 4), (336, 24, 1, 8)
- (336, 72, 2, 4), (336, 72, 2, 8)

## Evaluation
Chronological untouched training folds: calendar 2023, 2024, 2025. Holdout 2026+ remains unopened. Funding is point-in-time causal. Costs frozen at base 7 bp, severe 14 bp, supersevere 28 bp with turnover accounting.

For every spec/fold/stress record total return, max drawdown, Profit Factor, payoff, win rate, positive days, tails, asset contribution/concentration, funding contribution, and lagged BTC bull/bear/sideways regimes. Require deterministic reproduction, data firewall, gross-exposure invariant, cost monotonicity, and independent validation.

## Gate
Use the existing V98 mechanical annual discipline. Advance only if a spec satisfies the frozen validator across every chronological base-cost fold and remains economically coherent under severe/supersevere stress. No rescue. If none survives: `REJECT_FAMILY_NO_RESCUE`.

Phase233 results may determine only whether Phase234 is executed next; they may not modify this preregistration.
