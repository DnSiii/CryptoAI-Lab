# V98 Independent Phase222 — pre-result tail/concentration audit

Status: **completed before any Phase222 result harvest**. Holdout >= 2026-01-01 UTC remains unopened.

## Failure found

The initial evaluator formed each event tail by summing the **whole portfolio** PnL over the event window. With concurrent positions, that duplicates unrelated assets' PnL across multiple events and can contaminate p01/p05/p50/p95/p99 and worst/best trade diagnostics. It also stopped at the last holding row and therefore could omit exit turnover cost.

This is a diagnostic-integrity defect, not a scientific parameter choice. No Phase222 result had been harvested when corrected; frozen c/H/direction, universe, folds, costs, funding rules and mechanical gate are unchanged.

## Correction frozen before result

Trade-tail observations are now closed, asset-attributed PnL only. For an event entering at index j and ending before index e, the diagnostic sums that asset's realized portfolio contribution from j through e inclusive, so entry/rebalancing/exit turnover and PIT funding represented in the asset PnL stream are included. Fold-boundary-censored events are excluded from trade tails rather than partially scored.

Per-asset concentration is now explicitly based on additive per-asset PnL contribution (`asset_pnl_contribution`) rather than a product-return label. The validator requires the exact tail-definition marker, all five assets, ordered tail quantiles, metric domains, stress monotonicity, deterministic payload SHA and byte-identical rerun.

## Scientific boundary

This correction must not be used to alter Phase222 parameters or gate thresholds. Phase223 remains frozen contingency only. If a future Phase222 execution is produced from any evaluator version preceding commit `d2725934ab14428a8f93a92d8a03bd19792132aa`, that output is invalid for tails/concentration and must not be used for promotion/rejection until rerun with the corrected evaluator and validator.
