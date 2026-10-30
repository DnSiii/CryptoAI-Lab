# V98 Independent — Phase235 preregistration

Status: **FROZEN BEFORE PHASE235 RESULTS**

## Hypothesis
Cross-sectional residual skewness relative value: after removing contemporaneously unavailable information via lagged BTC beta/residual construction, assets with unusually negative trailing idiosyncratic return skewness may earn a different next-period return than assets with unusually positive residual skewness. This is scientifically distinct from Phase234 idiosyncratic-volatility level: the ranking variable is the third standardized moment, not dispersion magnitude.

## Information / causality contract
- Universe and training-only source contract inherit the V98 Independent firewall; timestamps >= 2026-01-01 are forbidden.
- Decision for `open(t)` may use observations only through `open(t-1)` (or earlier).
- BTC beta and residuals must be estimated only from lagged/history-available observations. No centered/forward windows.
- Funding must be point-in-time and charged consistently with held signed exposure.
- Portfolio is cross-sectional, dollar-neutral where both sides are available, gross exposure <= 1.

## Frozen grid — exactly 8 specs
Cartesian product:
- beta lookback: {168h, 336h}
- residual-skew lookback: {72h, 168h}
- hold/rebalance horizon: {4h, 8h}

Rank residual skewness cross-sectionally at each decision time; long the lowest-skew tail and short the highest-skew tail using the same deterministic tail fraction for every spec. No threshold optimization after results.

## Chronological evaluation
Decision folds are calendar years 2023, 2024, 2025. Every promoted spec must satisfy the frozen mechanical gate in **all three** folds; no fold may be removed or pooled away.

## Costs / diagnostics
Evaluate realistic/base 7 bp, severe 14 bp, supersevere 28 bp turnover costs, plus PIT funding. Report at minimum: net return, max drawdown, Profit Factor, payoff, win rate, positive-day fraction, turnover/trade count, regime breakdown, asset concentration, tail dependence/worst-day diagnostics and cost monotonicity.

## Reproducibility / anti-overfit
- Two deterministic executions must produce identical canonical report SHA256.
- Frozen-grid/information-set invariants must run before decision.
- No rescue grid, no sign flip selected from observed results, no V99 information, no holdout >=2026, no cherry-picking.
- Failure of the frozen family => `REJECT_FAMILY_NO_RESCUE` and move to a genuinely distinct preregistered hypothesis.

## Promotion discipline
Only a spec that clears the annual robustness gate across 2023/2024/2025 and survives severe/supersevere cost scrutiny may advance. Opening the untouched holdout requires a separately justified promotion decision; Phase235 itself must not access it.