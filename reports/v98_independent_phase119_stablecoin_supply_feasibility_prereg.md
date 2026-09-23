# V98 Independent — Phase119 preregistration

## Hypothesis family
Orthogonal external liquidity data family: aggregate stablecoin circulating supply / market capitalization history. This phase is DATA_ONLY and must not test a trading hypothesis.

## Scientific purpose
Determine whether an independent historical stablecoin-supply source is sufficiently complete, canonical, reproducible and causally usable over the frozen V98 training window before any values, descriptive statistics, correlations, returns, alpha or PnL are inspected.

## Frozen training-only window
- 2023-01-01 through 2025-12-31 UTC only.
- Validation and final holdout MUST NOT be accessed.
- V16 and every V99 artifact/state MUST NOT be used.

## Source contract
- Primary family: DefiLlama stablecoins historical aggregate supply / market-cap API.
- Use aggregate stablecoin supply only; no individual-coin selection.
- Raw payload SHA256 and canonical date-index SHA256 must be persisted.
- No forward-fill, interpolation, backfill, smoothing, resampling that manufactures observations, or source substitution after seeing values.

## DATA_ONLY gate
PASS_DATA_ONLY requires all of:
1. >=95% expected daily-date coverage in the frozen training window.
2. zero invalid canonical records.
3. zero duplicate dates after canonicalization.
4. zero observations outside the frozen training window in the evaluated canonical frame.
5. deterministic ordering and reproducible hashes.

Otherwise: REJECT_DATA_SOURCE. No rescue by weakening these gates.

## Isolation contract before gate decision
Forbidden before DATA_ONLY decision:
- exposing or reporting stablecoin-supply values;
- descriptive distribution/statistics;
- deltas/growth rates;
- correlations with crypto prices/returns;
- trading returns, alpha or PnL;
- threshold/lag/window/asset/gross search;
- validation/final-holdout access;
- V16/V99 use.

## Conditional next step
Only if Phase119 returns PASS_DATA_ONLY may a scientifically distinct Phase120 trading hypothesis be preregistered. Its direction, lag, transformation, gross, folds, realistic funding/cost assumptions, severe/supersevere stresses and rejection gates must be frozen before any PnL is computed.
