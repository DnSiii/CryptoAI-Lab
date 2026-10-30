# V98 Independent Phase190 — volatility-shock continuation preregistration

Status: **PREREGISTERED / TRAINING ONLY / NO VALUES INSPECTED FOR THIS FAMILY**

## Scientific motivation
Phase189 closed cross-sectional dispersion mean reversion because its apparent aggregate edge was sideways-only and collapsed under chronological folds and realistic stress costs. Phase190 therefore does not rescue, invert, retune, or subset Phase189. It tests a distinct mechanism: whether an asset-specific volatility expansion accompanied by same-direction price displacement has short-horizon continuation rather than reversal.

This is distinct from prior generic realized-volatility regimes, volatility compression, volatility-of-volatility, jump-breadth and idiosyncratic-momentum families: the frozen object is the *interaction* between a causal asset-level volatility shock and contemporaneous directional displacement, traded only after both are known.

## Data boundary and causality
- Training only: 2023-01-01 00:00 UTC through 2025-12-31 23:59:59 UTC.
- Canonical V98 five-asset data only; no V99/V16/Phase083 evidence.
- Every rolling statistic is computed from information available at or before signal timestamp t.
- Position generated at t is shifted one bar before earning return; no same-bar execution.
- Validation 2026-01-01..2026-07-31 and final holdout >=2026-08-01 are forbidden during selection.

## Frozen hypothesis and grid
For each asset and hour t:
1. `r24 = close_t / close_{t-24} - 1`.
2. `rv24 = sqrt(sum(r_1h^2 over trailing 24h))`.
3. `rv_ref = rolling median(rv24, W)` using only observations <=t.
4. `vol_shock = rv24 / rv_ref`.
5. Eligible when `vol_shock >= S` and `abs(r24) >= D`.
6. Direction = `sign(r24)` (continuation, never reversal).
7. Equal-weight eligible assets, normalized to frozen gross cap 1.0; if none eligible, flat.
8. Rebalance every H hours; positions persist between scheduled decisions and are shifted one hour before PnL.

Closed 2x2x2 grid, exactly 8 specifications:
- W in {168h, 336h}
- S in {1.5, 2.0}
- H in {6h, 12h}
- D fixed at 3.0% absolute 24h displacement.

No alternate threshold/window/holding period/direction/subset is permitted after results.

## Evaluation and costs
Use the established V98 economic stack and actual funding where available. Evaluate each frozen specification under base, severe and supersevere cost schedules used by the current V98 training harness. Report at minimum total return, max drawdown, Profit Factor, payoff, win rate, positive days, turnover/cost burden, chronological 2023/2024/2025 folds, bull/bear/sideways attribution, per-asset contribution, mean/p95 top-1 concentration, top-10 gain share and bottom-10 loss share.

## Frozen training eligibility gates
A candidate may advance only if all are true:
- base total return > 0 and PF > 1.05;
- each chronological year return > 0 and PF > 1.00;
- severe total return > 0 and PF > 1.00;
- supersevere total return > 0 and PF > 1.00;
- max drawdown no worse than -35% in every cost schedule;
- mean top-1 concentration <= 60%;
- top-10 gain share < 50% and bottom-10 loss share < 50%;
- at least two of bull/bear/sideways have non-negative contribution;
- deterministic rerun produces byte-identical economic report.

Selection order is frozen before execution: maximize minimum annual PF; ties by supersevere PF, then lower absolute MDD, then lower turnover. No aggregate-return tie-break before these robustness criteria.

## Decision rule
If no specification passes every gate: **REJECT_FAMILY_NO_RESCUE** and validation remains closed. If one or more pass: freeze exactly one by the selection order above and separately preregister untouched validation before any validation value is inspected.

Final holdout remains closed regardless of training result.