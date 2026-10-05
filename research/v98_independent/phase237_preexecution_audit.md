# V98 Independent Phase237 — pre-execution integrity audit

Recorded before any Phase237 performance result is generated or inspected.

## Preregister-to-code audit
- Frozen grid is exactly 2 beta lookbacks x 2 downside-semivariance windows x 2 holding horizons = 8 specs; k=1 fixed.
- Frozen direction is long highest downside semivariance / short lowest; no sign rescue is implemented.
- Residual construction uses `beta.shift(1)` so residual(u) uses beta estimated through u-1.
- Decision uses `signal.iloc[i-1]`; positions opened at t therefore use information available through t-1.
- Downside feature is exactly `mean(square(min(residual,0)))` via `clip(upper=0).pow(2).rolling(...).mean()`.
- Position normalization enforces portfolio gross <=1.

## Evaluation/integrity audit
- Annual chronological folds are 2023, 2024, 2025 only; cutoff firewall is strictly `<2026-01-01`.
- Costs remain 7/14/28 bp per unit L1 turnover.
- Funding is point-in-time and charged to lagged held position using the existing Phase206 V98 funding dataset.
- Reports include return, max drawdown, Profit Factor, payoff, win rate, positive days, turnover, funding contribution, asset contribution/concentration, hourly tails, best/worst day, and lagged BTC bull/bear/sideways regimes.
- Independent validator requires the exact grid/folds/cost tiers, finite payload, cost monotonicity, and the existing annual gate in every fold.
- Decision is mechanical: promote only if at least one frozen spec passes every annual fold; otherwise `REJECT_FAMILY_NO_RESCUE`.
- Deterministic workflow must execute evaluator twice and require byte-identical output before interpretation.

## Scope isolation
Only Phase237 V98 Independent namespaced files/workflow are authorized. 2026+ holdout, V16, V99 research/frozen state/workflows/reports, and V99 paper state are not inputs to selection or tuning and must remain untouched.
