# V98 Independent Phase089 — Preregistration

Status: **PREREGISTERED BEFORE PNL**.

## Hypothesis

Cross-sectional **UTC session-boundary gap continuation**: assets whose prior completed daily close-to-next-open discontinuity is stronger than peers retain a short-lived relative continuation premium after the boundary. This is a discontinuous repricing hypothesis, not a trend, candle-location, wick, range-concentration, UTC-block seasonality, volume, funding, positioning, or residual-momentum rescue.

## Frozen construction

- Research universe, canonical training dates, execution conventions and eligibility: identical to the current V98 Independent training infrastructure.
- Training only: no Phase083 dates and no later opened-holdout information may enter features, selection, parameter choice or gates.
- Daily UTC rebalance.
- For each asset and completed day d, define gap = open[d] / close[d-1] - 1. At the rebalance for day d+1, the newest admissible signal is gap[d]; no same-day close or future bar is admissible.
- Fixed signal: 7-completed-day arithmetic mean of gap, chosen ex ante to reduce single-boundary noise. No alternative lookback is permitted after PnL.
- Cross-sectionally demean the signal over eligible assets; rank ascending/descending; long top quartile and short bottom quartile with equal weight inside each side.
- Dollar-neutral target, gross 0.75, with the same causal BTC-beta neutralization convention used by the current V98 training framework. No sign flip, threshold, quartile, lookback, gross, cadence, symbol subset or regime rescue.
- Positions are lagged/formed before the return interval they earn.

## Costs and funding

Use the existing V98 realistic BASE transaction-cost/funding accounting unchanged, plus the existing severe and supersevere schedules unchanged. Funding must be charged with the same causal convention as the current V98 framework.

## Required evidence

Report aggregate and chronological 2023/2024/2025 folds; BASE/severe/supersevere; total return, CAGR, max drawdown, Profit Factor, payoff, win rate, positive/negative days, worst/best day, p01/p05/CVaR05, turnover, gross/net exposure and ruin; bull/bear/sideways regime attribution; symbol contribution; top-1 concentration/tails; input/config/script hashes and deterministic reproducibility metadata.

## Frozen training gate

The candidate advances only if all existing V98 training thresholds are satisfied without exception: aggregate positive return, PF >= 1.15, max DD >= -35%; each 2023/2024/2025 fold positive with PF >= 1.05; severe positive with PF >= 1.10; supersevere positive with PF >= 1.03 and DD >= -55%; and existing concentration/tail invariants including p95 top-1 <= 45%. Any failed gate => **REJECT_NO_RESCUE** and validation remains closed.

## Validation / final discipline

If and only if training passes, freeze the candidate before a separately preregistered validation run. The already-open Phase083 interval (2026-08-01..2026-09-15) is permanently forbidden for validation, tuning or final selection. Even after validation passes, no final claim is allowed until a new forward untouched window exists and is opened exactly once under a separate preregistration.

V99 and V16 evidence/files/state/workflows are excluded from this experiment.
