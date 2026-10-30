# V98 Independent Phase203 — preregistration

## Hypothesis
Directional efficiency / path persistence is scientifically distinct from Phase199 cross-sectional trend, Phase200 compression breakout, Phase201 volume shock, and Phase202 range reversal. A move whose net displacement is large relative to total path length may contain short-horizon continuation information; noisy low-efficiency paths should not trigger.

## Frozen signal
OHLCV-only, computed per symbol. At decision time t, all features use data through t-1 only.

For lookback L, define efficiency = abs(close[t-1] / close[t-1-L] - 1) / sum(abs(hourly close returns)) over the same completed L-hour window. Direction is sign(close[t-1] / close[t-1-L] - 1). Enter only when efficiency >= E and absolute displacement >= M. Position follows Direction for fixed H hours, no pyramiding/re-entry while active, equal risk/notional treatment consistent with prior V98 independent phases.

## Frozen grid — 8 specs
L ∈ {24h, 72h}; E ∈ {0.35, 0.55}; H ∈ {3h, 6h}. Minimum displacement M is fixed, not tuned: 1.0% for L=24h and 2.0% for L=72h. Exactly 8 specs; no threshold rescue or inversion after results.

## Evaluation contract
Chronological folds: calendar 2023, 2024, 2025. Training-only data cutoff 2025-12-31. Validation and final holdout forbidden unless a candidate later passes all preregistered training gates and is formally frozen.

Report base, severe and supersevere transaction-cost scenarios and funding when available; max drawdown, Profit Factor, payoff, win rate, positive days, turnover/activity, per-symbol PnL/concentration, gain/loss tails, and bear/bull/sideways regimes. Require causal t-1 implementation, cutoff invariant, deterministic byte-identical rerun, and input hashes.

## Promotion discipline
No promotion from attractive aggregate return alone. A candidate must show robust positive economics across chronological folds, survive severe/supersevere costs, avoid pathological drawdown/concentration/tail dependence, and retain acceptable regime breadth. Any failure closes the family with no rescue. V99 evidence must not be used for tuning or selection.