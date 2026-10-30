# V98 Independent — Phase216 pre-result implementation audit

Status: pre-result audit; no Phase216 outcome was inspected when this document was written.

## Scope
Audited only the V98 Independent Phase216 preregistration, evaluator, and deterministic workflow on `research/v98-independent-zero`. No V16/V99 state or reports were used for selection or tuning.

## Causality index audit
For decision row `t`:
- hourly returns are close-to-close observations;
- rolling beta is computed from 168 observations and shifted one row, so the beta applied to residual return at `t-1` is estimated through `t-2`;
- the shock feature is the residual shifted one additional row and therefore uses only the completed `t-1` return;
- residual-volatility is a 24-observation rolling standard deviation shifted two rows, so its window ends at `t-2`;
- the volatility-floor percentile is expanding and shifted once more, so the threshold used at `t` excludes the contemporaneous `rv(t)` value;
- positions are written beginning at `t`, while PnL uses `position.shift(1) * open.pct_change()`, preventing capture of the already-known `t` open move.

No forward shift, centered window, future funding observation, or post-entry price enters signal construction.

## Fold/history audit
Each calendar fold is scored only inside its frozen 2023, 2024, or 2025 interval. Feature construction receives observations strictly earlier than the fold stop, preserving the complete expanding historical distribution available before each decision rather than resetting the percentile at fold boundaries. Validation/final holdout is not loaded or referenced.

## Exposure / overlap audit
There is at most one live position per asset. Concurrent positions across assets are normalized by contemporaneous gross exposure so aggregate gross does not exceed 1.0. The normalization depends only on signals known at that timestamp. Ignored signals during an active hold cannot alter the existing holding period.

## Cost / funding audit
The frozen base/severe/supersevere round-trip-equivalent conventions are 0.07%, 0.14%, and 0.28%. Turnover is charged on position changes. Funding is aligned to funding timestamps, multiplied by lagged live position, and therefore cannot enter the signal. The workflow additionally asserts supersevere return cannot exceed base return for any spec/fold.

## Reproducibility / integrity audit
The workflow rebuilds training-only canonical prices, asserts monotonic unique timestamps and `<2026-01-01` firewall for prices and funding, executes the evaluator twice, compares full-file SHA256 hashes, asserts exactly 8 specs and all three cost stresses for all three folds, then applies only the preregistered mechanical gate.

## Decision discipline
No result-dependent threshold, beta lookback, volatility lookback, percentile, hold, direction inversion, asset subset, or regime filter may be introduced after harvest. If all 8 frozen specs fail the three-fold base gate, the family is rejected without rescue. If any survives, stress/tail/concentration/regime and reproducibility audits remain mandatory before validation can be considered.
