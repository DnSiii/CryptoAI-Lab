# V99 R106 — Phase182 TRAIN alpha freeze

Date: 2026-09-29
Status: FROZEN BEFORE PNL / TRAIN-ONLY / NO HOLDOUT

This document fixes the only Phase182 economic mapping before any Phase182 PnL is inspected.

## Frozen mapping

Instrument sleeve: BTCUSDT/ETHUSDT market-neutral relative-value pair, gross cap 0.20. The pair has equal absolute legs: positive score means long ETH / short BTC; negative score means short ETH / long BTC. No net directional BTC+ETH exposure is intentionally added.

At each hour, compute the five already-preregistered Phase182 features. Standardize each feature with expanding mean/std using only observations strictly earlier than the decision observation. Fixed economic signs are:

- relative_return_1: +1 (continuation)
- relative_return_24: +1 (continuation)
- rv_ratio_24: -1 (relative ETH volatility is stress, not alpha)
- volume_shock_diff_24: +1 (relative participation confirms continuation)
- stress_interaction: -1 (ETH-underperformance plus excess ETH volatility is defensive short-ETH pressure)

Composite = equal-weight mean of the five signed expanding z-scores. Position intensity = tanh(composite), with no threshold. The resulting pair is L1-normalized to the fixed 0.20 gross cap. Feature availability is structurally t-1 and the portfolio target receives the repository's normal execution lag; no contemporaneous/future bar may affect a target.

No feature deletion, sign flip, alternative normalization, window, threshold, gross, asset substitution, or weighting search is permitted after PnL inspection.

## Gates

Evaluation is TRAIN-only with exclusive end 2024-01-18. Use the existing chronological fold diagnostics, severe cost from the canonical execution config, then supersevere cost at exactly 2x severe. Report regime diagnostics, tail/concentration diagnostics, and deterministic rerun equality. Phase182 is rejected without retuning if stable TRAIN evidence fails, if severe/supersevere robustness fails, if results are dominated by a fold/regime/tail, or if deterministic rerun differs.

Holdout market values must not be parsed for Phase182 selection. V16 Frozen and V99 Frozen are immutable.
