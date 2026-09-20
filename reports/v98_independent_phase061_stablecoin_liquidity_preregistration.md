# V98 Independent — Phase061 Stablecoin Liquidity Preregistration

Status: FROZEN BEFORE ANY PNL.

## Hypothesis
Aggregate stablecoin supply is a causal crypto-liquidity state variable. Expansion represents increasing deployable dollar liquidity; contraction represents liquidity withdrawal. Test one fixed directional mechanism only: BTC long when trailing stablecoin supply growth is positive, BTC short when negative.

## Frozen construction
- External source: DefiLlama `stablecoincharts/all`, the same source that passed Phase060.
- Research period: training only, 2023-01-01 through 2025-12-31 UTC. Validation remains closed. Final holdout remains untouched.
- Signal observation frequency: daily UTC.
- Information lag: use only stablecoin observations timestamped no later than prior UTC day; no same-day crypto return may enter the signal.
- Lookback: fixed 30 calendar days, chosen ex ante as a monthly liquidity horizon; no alternate lookbacks.
- Signal: sign(total_stablecoin_usd[t-1] / total_stablecoin_usd[t-31] - 1). Exactly +1 for positive growth, -1 for negative growth, 0 if exactly zero or unavailable. No thresholds, quantiles, smoothing, coin/chain subset, source substitution, sign inversion, or rescue tuning.
- Instrument: BTCUSDT perpetual only, fixed gross exposure 0.75 when signal is non-zero.
- Rebalance: daily at 00:00 UTC after the lagged signal is known.
- Execution: next available hourly bar after rebalance; positions must be causal/future-invariant.

## Costs and funding
Use the existing V98 Independent realistic BTCUSDT funding treatment and the existing base/severe/supersevere friction schedule without calibration to Phase061 results. Report all three cost scenarios.

## Required training evidence
Report aggregate and chronological 2023/2024/2025 folds; total return/CAGR, max drawdown, Profit Factor, payoff, win rate, positive days, turnover; bull/bear/sideways regime attribution; concentration and daily tails; reproducibility/invariance checks.

## Frozen promotion gate
Training may open validation only if, under BASE costs: aggregate return > 0, PF > 1.05, max drawdown > -35%, each chronological yearly fold has return > 0 and PF > 1.02, and no regime exhibits catastrophic concentration. Severe and supersevere must be reported but are not used to rescue a BASE failure. Any failed required gate => REJECT_NO_RESCUE. No parameter/sign/lookback/subset/source search after seeing Phase061 PnL.

## Isolation
V99 is forbidden as input, benchmark for tuning, or selection evidence. V16 Frozen, V99 Frozen, V99 research/workflows/reports/paper state are untouched. Final holdout is forbidden until a formally frozen candidate passes training and validation gates.
