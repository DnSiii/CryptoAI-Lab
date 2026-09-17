# V99 R106 Phase28 — Volatility-Compression Breakout Alpha Precommit

Status: PRECOMMITTED_DIAGNOSTIC_ONLY

Phase27 cross-sectional reversal is rejected without horizon/grid tuning: all three fixed sleeves had 0/4 healthy train folds and negative severe-cost train ROI. Phase28 therefore moves to a structurally distinct mechanism rather than cosmetically modifying reversal.

## Fixed hypothesis

Test whether low-volatility compression followed by directional price expansion contains robust standalone alpha across the liquid cross-section.

Three economically distinct, fixed families only:

1. `compression_breakout_24h`: direction from causal 24h return; eligibility requires trailing 24h realized volatility below its trailing 30-day median and absolute 24h move above trailing volatility scale.
2. `compression_breakout_72h`: same concept on a slower 72h directional horizon, with the same causal compression state.
3. `compression_breakout_24h_volume_confirmed`: exact 24h family additionally requires trailing 24h quote-volume mean above its trailing 7-day mean.

No parameter grid or adaptive horizon search is permitted. All features are shifted to t-1 before target construction. Portfolio construction remains cross-sectional, market-neutral, inverse-volatility weighted, top-2 each side, 20% gross, 24h rebalance/hold so comparison to Phase27 is controlled.

## Selection gate

Chronological train only through the existing fixed TRAIN_END. Severe cost is the selection cost. A sleeve is eligible only with >=30 days active, train ROI > 0, PF > 1.08, robust mean excluding top 1% > 0, and >=3 healthy eligible temporal folds. Healthy fold requires ROI > 0, PF > 1, robust mean excluding top 1% > 0.

Untouched holdout is inspected only for the single train-selected sleeve. Holdout cannot change the selected family. Holdout pass requires >=10 days active, ROI > 0, PF > 1.05 and robust mean excluding top 1% > 0.

If no sleeve passes train stability, reject the entire compression-breakout hypothesis without tuning and do not create a candidate. If train+holdout pass, only then proceed to a separate full severe+supersevere / temporal-fold / regime-matrix / benchmark-envelope candidate gate.

V16 Frozen, V99 Frozen, F7/F9 and paper state must remain untouched.