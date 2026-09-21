# V98 Independent — Phase068 preregistration

Status: **FROZEN_BEFORE_PNL**

## Independent hypothesis
Cross-sectional short-term reversal. This is a new behavioral/temporary-price-pressure family, not a rescue or inversion of Phase067 volatility spread and not a retune of Phase065 momentum. Signal construction uses only recent return ranking and does not use realized-volatility ranking, Phase067 losses, Phase065 validation evidence, macro/liquidity, basis, OI, options, liquidations, stablecoins, or V99/V16 evidence.

Universe is frozen to BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT and XRPUSDT using existing V98 Independent canonical USD-M data. Training only: 2023-01-01 through 2025-12-31. Validation and final holdout are forbidden at this phase.

## Frozen mechanism
At each UTC daily decision, compute each asset's trailing 3-calendar-day close-to-close return ending at t-1. Require complete observations for every asset. Rank ascending by trailing return. Long the single worst performer and short the single best performer, each at 0.375 notional for fixed gross exposure 0.75 and net 0. Ties resolve lexicographically by symbol. Hold for the next daily interval and rebalance once daily. No volatility target, threshold, regime filter, stop, trend overlay, BTC direction filter, adaptive leverage, parameter search, or post-result inversion is permitted.

Funding must be applied causally using only observations known for the held interval under the existing V98 Independent accounting convention. Trading costs/slippage use the same BASE, severe and supersevere schedules already frozen for current V98 research.

## Frozen training gates
Evaluate aggregate training and chronological folds 2023, 2024 and 2025 separately. Promotion requires all of: aggregate BASE total return > 0; aggregate daily Profit Factor > 1.05; aggregate max drawdown >= -35%; each annual fold total return > 0; each annual fold daily PF > 1.00; severe total return > 0; supersevere total return > 0. Any failure means **REJECT_NO_RESCUE** and validation stays closed.

Mandatory diagnostics regardless of pass/fail: total return, CAGR, max drawdown, daily PF, payoff, win rate, positive/negative/flat days, turnover, funding contribution, trading-cost contribution, annual folds, BASE/severe/supersevere, causal bull/bear/sideways regime attribution, per-asset contribution, top/bottom tails, top-10 absolute-day concentration, and deterministic input/config/output hashes.

## Anti-overfit / isolation contract
No validation or final-holdout inspection is permitted. Final holdout 2026-08-01 through 2026-09-15 remains untouched. Phase065 validation and Phase067 PnL may not be used to alter Phase068. No alternative 1/2/5/7/14-day window, multi-rank basket, universe subset, gross, threshold, cadence, regime gate, cost schedule, or rescue is allowed after results. A failed Phase068 closes this exact family. V99 and V16 are excluded from selection and must not be read for tuning or modified.
