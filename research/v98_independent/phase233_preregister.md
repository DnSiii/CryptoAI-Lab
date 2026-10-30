# V98 Independent Phase233 — preregistration

Status: FROZEN BEFORE ANY PHASE232 RESULT. Phase232 outcomes MUST NOT alter this hypothesis or grid.

## Hypothesis
Cross-sectional **lagged BTC-residual short-horizon reversal**: estimate each asset's rolling beta to BTC strictly from information available before `open(t)`, compute the asset's recent cumulative idiosyncratic return residual, then test whether extreme residual winners mean-revert relative to extreme residual losers over short horizons. This differs from Phase230's idiosyncratic momentum by testing the opposite economic mechanism (reversal) with a frozen short signal horizon and differs from Phase232 by ranking residual return rather than beta level.

## Information set / execution
- Fixed universe: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT.
- Decision at `open(t)` uses hourly open-to-open returns ending no later than `open(t-1)`.
- Rolling beta uses a frozen historical window and no future observations.
- Residual at each historical hour is `asset_return - beta_lagged * BTC_return`; signal is cumulative residual over a frozen recent horizon, ending at `t-1`.
- Rank deterministically by `(signal, symbol)`; long lowest residual-return assets and short highest residual-return assets; equal absolute weights, dollar-neutral, gross <= 1.
- No regime filter, sign flip, asset exclusion, threshold rescue, post-result tuning, or access to 2026+.

## Frozen grid — exactly 8 specs
`(beta_lookback_hours, residual_signal_hours, k_each_side, hold_hours)`:
- (168, 6, 1, 2), (168, 6, 1, 4)
- (168, 12, 1, 2), (168, 12, 1, 4)
- (336, 6, 1, 2), (336, 6, 1, 4)
- (336, 12, 2, 2), (336, 12, 2, 4)

## Evaluation
Chronological untouched training folds: calendar 2023, 2024, 2025. Holdout 2026+ remains unopened. Funding is point-in-time causal. Costs frozen at base 7 bp, severe 14 bp, supersevere 28 bp with turnover accounting.

For every spec/fold/stress record total return, max drawdown, Profit Factor, payoff, win rate, positive days, tails, asset contribution/concentration, funding contribution, and lagged BTC bull/bear/sideways regimes. Require deterministic reproduction, data firewall, gross-exposure invariant, cost monotonicity, and independent validation.

## Gate
Use the existing V98 mechanical annual discipline. Advance only if a spec satisfies the frozen validator across every chronological base-cost fold and remains economically coherent under severe/supersevere stress. No rescue. If none survives: `REJECT_FAMILY_NO_RESCUE`.

Phase232 results may determine only whether Phase233 is executed next; they may not modify this preregistration.
