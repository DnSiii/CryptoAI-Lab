# V98 C13 complete-system preregistration — 2026-11-18

**Status: TRAINING ONLY / NOT VALIDATED / NOT FROZEN / NOT PAPER.** This record precedes any C13 economic run. C11 and C12 were rejected. Their numerical outcomes must not be used to tune C13.

## Hypothesis
A 30-day channel breakout Growth Core, 14-day down/7-day reversal Opportunity Sleeve, positive cross-sectional 14-day leadership Relative-Value Sleeve, breadth-triggered Stress/Recovery Sleeve, channel-location Regime Router, inverse-volatility Dynamic Allocator and pre-open equity Risk Governor may capture persistent asymmetric trends while avoiding prolonged weak conditions. The relative-value sleeve is *relative allocation*, not a market-neutral pair trade.

## Immutable choices for this hypothesis
2160-hour warmup, 24-hour rebalance, 720-hour breakout channel, 168-hour realized-volatility window, 336-hour medium window, sleeve budgets 0.32/0.20/0.12/0.12, gross cap 0.76, per-asset cap 0.38, five-rebalance recovery latch; router channel-position thresholds 0.35/0.65 with multipliers 0.2/0.5/1.0. Existing completed-equity pre-open governor unchanged. No parameter changes after observing results; rejected candidates stay rejected.

## Provenance and execution
Only authenticated Clean-4 BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT Binance USD-M 1h; Dec-2022 warmup through Dec-2025; native funding. Enforce pinned hashes, 27,048 hours, next-open t-1 causal execution, costs 1x/2x/4x, independent equity/funding/fee reconciliation and reproducibility. Exclude XRP, 2026+ and contaminated Phase083 holdout.

## Decision gates
Require chronological training folds, distinct untouched validation, full-system marginal ablations, year-by-year compounded equity, severe and supersevere cost outcomes, maximum drawdown, concentration, profit factor, payoff, win rate, positive days, tails and regime slices. Reject if no durable positive compounded growth, if results depend materially on one year, or if execution/provenance gates fail. Do not rescue sign, windows, budgets or gross exposure based on results. V14/V15/V99 only after C13 internal freeze and separate validation. A successful workflow or unit test is not a successful economic gate.

Implementation: `research/v98_independent/v98_composed_c13.py`. This preregistration does not assert that a runner or replay has been executed.
