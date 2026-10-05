# V98 Independent — Phase235 pre-execution correction audit

Status: **PRE-RESULT / NO PHASE235 RESULTS OBSERVED**

This audit records implementation corrections made before Phase235 execution. It does not amend the frozen hypothesis or select parameters from results.

## Frozen-grid conformance
The preregistration defines exactly `2 beta lookbacks × 2 skew lookbacks × 2 horizons = 8` specifications and requires the same deterministic cross-sectional tail fraction in every specification. The initial evaluator accidentally encoded `k=2` in two rows and therefore was not the frozen Cartesian grid. The evaluator now constructs the Cartesian product directly and fixes `k=1` for all eight specifications (one long and one short in the five-asset universe), with an executable grid invariant.

## Causal residual construction
The preregistration requires beta/residual estimation from lagged/history-available observations. To avoid allowing the return being residualized to influence its own beta estimate, residual at hour `u` now uses `beta.shift(1)`, i.e. beta estimated through `u-1`. A decision at `open(t)` still ranks a skew signal ending at `t-1`. No centered or forward window is used.

## Tail/accounting correction
The initial evaluator's pseudo-trade tail attribution reused asset-level aggregate PnL across overlapping sleeves, so those pseudo-trades were not independent accounting units. They are removed from decision evidence. Phase235 now reports portfolio hourly quantiles plus explicit worst/best daily return, L1 turnover, signal-event count, asset PnL concentration, PIT funding contribution, regimes, max drawdown, Profit Factor, payoff, win rate and positive-day fraction.

## Mechanical validator
`phase235_validate.py` independently enforces the exact 8-spec key set, folds 2023/2024/2025, base/severe/supersevere metrics, finite payloads, cost monotonicity, and a conservative all-fold annual gate. It contains no rescue grid, sign flip, holdout access, or V99 dependency.

## Isolation
All changes are confined to `research/v98_independent/` on `research/v98-independent-zero`. Holdout timestamps `>=2026-01-01` remain forbidden by the evaluator firewall. V16, V99, V99 workflows/reports, and paper state are untouched.
