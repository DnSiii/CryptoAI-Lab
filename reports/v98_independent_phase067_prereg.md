# V98 Independent — Phase067 preregistration

Status: **FROZEN_BEFORE_PNL**

## Independent hypothesis
Cross-sectional realized-volatility defensive spread. This is a new risk-premium family, not a rescue of Phase065 residual momentum: the signal contains no return direction, momentum sign, Phase065 validation outcome, macro/liquidity input, basis, OI positioning, options, liquidation, stablecoin, or V99/V16 evidence.

Universe is frozen to BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT and XRPUSDT using the existing V98 Independent canonical daily USD-M data. Training only: 2023-01-01 through 2025-12-31. Validation and final holdout are forbidden at this phase.

## Frozen mechanism
At each UTC daily decision, compute each asset's trailing 20-calendar-observation realized volatility from close-to-close log returns ending at t-1. Require a complete 20-return lookback for every asset. Rank ascending by realized volatility. Long the single lowest-volatility asset and short the single highest-volatility asset, each at 0.375 notional for fixed gross exposure 0.75 and net 0. Ties resolve lexicographically by symbol. Hold for the next daily interval and rebalance once daily. No threshold, regime filter, volatility target, leverage adaptation, stop, momentum overlay, BTC direction filter, or parameter search is permitted.

Funding must be applied causally using only funding observations known for the held interval under the existing V98 Independent accounting convention. Trading costs/slippage use the same BASE, severe and supersevere schedules already frozen for current V98 research; no cost assumption may be changed after results are observed.

## Frozen training gates
Evaluate aggregate training and chronological folds 2023, 2024 and 2025 separately. Promotion requires all of: aggregate BASE total return > 0; aggregate daily Profit Factor > 1.05; aggregate max drawdown >= -35%; each annual fold total return > 0; each annual fold daily PF > 1.00; severe total return > 0; supersevere total return > 0. Any failure means **REJECT_NO_RESCUE** and validation stays closed.

Mandatory diagnostics regardless of pass/fail: total return, CAGR where defined, max drawdown, daily PF, payoff, win rate, positive/negative/flat days, turnover, funding contribution, trading-cost contribution, annual folds, BASE/severe/supersevere, bull/bear/sideways regime attribution using the existing causal V98 regime convention, per-asset contribution, top-day and bottom-day tails, top-10 absolute-day concentration, and deterministic input/config/output hashes sufficient for reproducibility.

## Anti-overfit / isolation contract
No inspection or optimization on validation or final holdout is permitted. Final holdout 2026-08-01 through 2026-09-15 remains untouched. Phase065 validation evidence may not be used to alter Phase067. No alternative 10/30/60-day window, inversion, multi-rank basket, universe subset, gross, threshold, cadence, regime gate, cost schedule, or post-result rescue is allowed. A failed Phase067 closes this exact family. V99 and V16 are excluded from selection and must not be read for tuning or modified.
