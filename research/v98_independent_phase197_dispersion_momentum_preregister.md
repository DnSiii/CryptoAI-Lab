# V98 Independent — Phase197 preregistration

## Hypothesis

Test **cross-sectional dispersion-gated momentum** as a scientifically distinct family from Phase196. Hypothesis: relative momentum may be more persistent when the cross-sectional spread of recent returns is unusually high, because heterogeneous information shocks create leader/laggard separation; low-dispersion hours are excluded rather than retuned after results.

## Frozen design before outcome inspection

Training window only: 2023-01-01 through 2025-12-31. Validation and final holdout remain unopened.

Signal at decision time t uses data available no later than t-1.

1. For each asset compute trailing return over `lookback_hours` in {24, 72} ending at t-1.
2. At each t compute cross-sectional dispersion as the standard deviation of those trailing returns across eligible assets.
3. Compute a causal rolling dispersion reference using only observations through t-1 over 168h. Gate active when current dispersion exceeds rolling quantile `disp_q` in {0.60, 0.75}.
4. When active, rank assets by trailing return; long the top eligible asset and short the bottom eligible asset, equal absolute notional, gross target 1.0, net target 0.0.
5. Hold/rebalance cadence `hold_hours` in {6, 12}. No signal inversion or rescue is permitted.

Frozen grid: 2 × 2 × 2 = 8 specs.

## Eligibility / causality

Use only canonical V98 Independent training price/funding data already available in the namespace. Require finite lagged prices for the lookback and execution interval. No 2026 observations. No V16 or V99 state, reports, parameters, candidates, workflows, or paper state.

## Economics

Evaluate realistic trading costs and funding under the existing V98 Independent base, severe, and supersevere schedules. Funding must be applied with correct long/short sign and only when known causally.

## Required reporting

For each spec: chronological 2023/2024/2025 folds; total return/CAGR; max drawdown; daily Profit Factor; payoff; win rate; positive/negative days; turnover; activity; exposure; bull/bear/sideways attribution; tails; concentration; base/severe/supersevere results; reproducibility/invariant checks.

Zero-activity specs automatically fail regardless of undefined/Infinity ratio metrics.

## Gate discipline

A spec may advance only if it passes the pre-existing V98 Independent economic/robustness gates without post-hoc relaxation. Family failure means `REJECT_FAMILY_NO_RESCUE`; do not invert the failed signal, search nearby thresholds, or inspect validation/final holdout. Any promoted candidate must first be frozen before validation is opened.
