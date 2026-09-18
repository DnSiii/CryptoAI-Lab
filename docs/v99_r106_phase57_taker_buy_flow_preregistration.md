# V99 R106 Phase57 — taker-buy flow extraction preregistration

Status: PRE-REGISTERED / DATA-AVAILABILITY GATE ONLY

## Scientific motivation
Phase56 rejected the OHLC close-location-pressure family under the existing train-only stability gate. Its preregistered next orthogonal path was direct taker-buy flow, which is structurally different from OHLC proxies and should not be approximated by retuning rejected price/funding/volume families.

## Immutable safeguards
- V16 Frozen and V99 Frozen MUST remain untouched.
- No strategy/candidate mutation in Phase57.
- No holdout inspection for feature/horizon/direction/threshold choice.
- Any usable feature MUST be based on completed observations and shifted to t-1 before target construction.
- Chronological train-only selection; same temporal-fold discipline as prior R106 phases.
- Severe cost is the selection cost. Any promoted exact frozen sleeve must subsequently pass supersevere costs, regime matrix and benchmark envelope before becoming actionable.
- No parameter grid and no direction flip after observing results.

## Phase57A — deterministic data-availability gate
Before calculating returns, audit the existing research/canonical inputs for a genuine exchange-provided taker-buy field (for example taker buy base asset volume / quote asset volume) with timestamp, symbol coverage, missingness, duplicate and monotonic-time diagnostics. Do not infer this field from candle direction or other OHLCV proxies.

Required evidence per source: provenance/path, exact column names, timestamp semantics, earliest/latest timestamp, symbol count, coverage against the persistent universe, missingness, duplicate timestamps, and whether the source can be joined causally without forward fill from the future.

If no genuine taker-buy field exists locally, Phase57 is DATA_BLOCKED_NO_PROXY and must not manufacture a candidate. The next justified work is a research-only ingestion specification/cache path; canonical/frozen datasets remain unchanged.

## Phase57B — feature family, only if Phase57A passes
Use a single precommitted economic direction: taker-buy imbalance = 2 * taker_buy_base_volume / total_base_volume - 1, clipped only to the mathematically valid [-1,1] interval. Test fixed aggregation horizons 24h, 72h, 168h solely as the same coarse horizon family used by prior audits; every rolling score is shifted one completed hour (t-1). Cross-sectional weights reuse the established deterministic weighting implementation. Alpha gross remains 0.20.

Train gate is unchanged from Phase56: minimum 720 active train hours; train ROI > 0; PF > 1.08; robust mean excluding top 1% > 0; at least 3 valid temporal folds and at least 3 healthy folds, where a healthy fold has ROI > 0, PF > 1 and robust mean excluding top 1% > 0. Minimum fold active hours = 120.

Select at most one sleeve using train-only quality score. Only after exact selection is frozen may its untouched holdout be described once using the existing minimum 240 active hours, ROI > 0, PF > 1.05 and robust mean excluding top 1% > 0 gate. A failed holdout rejects; it cannot trigger another horizon/direction/threshold attempt.

## Promotion gate
Passing Phase57B is not promotion to V99. It only permits a subsequent exact-sleeve validation phase with severe + supersevere costs, temporal robustness, regime matrix, concentration/tail diagnostics and benchmark envelope. Cosmetic improvement or aggregate ROI without temporal stability is rejection.
