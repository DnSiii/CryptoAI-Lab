# V99 R106 Phase142 — Cross-Venue Volume/Price Absorption Preregistration

Status: **PREREGISTERED / BLOCKED UNTIL PHASE140 AND PHASE141 DECISIONS**

Frozen after Phase140 DATA_ONLY admissibility was established but before any Phase140/141 alpha result is observed. This is scientifically distinct from raw venue participation and turnover intensity: it tests whether disagreement between venue participation and contemporaneous venue return innovation identifies absorption rather than simply elevated activity.

## Frozen feature

Using only the same five Phase136 instruments and direct semantically comparable quote-notional fields admitted by Phase140, compute per asset/hour `volume_share_innovation = [log(OKX_notional)-log(Binance_notional)] - median_168h(same)` and `return_innovation = r_OKX-r_Binance`. Standardize each independently with exact same-window 168h MAD, then define `absorption = - z_volume_share * z_return_innovation`. Cross-sectionally demean the complete score and shift exactly t-1 before execution. Economic direction is frozen as written; no sign flip.

## Frozen contracts

- chronological TRAIN only; holdout construction/selection rows 0/0
- universe BTC, ETH, SOL, XRP, DOGE only
- direct Phase140-admitted notional fields; no proxy/substitution/imputation
- every log-consumed volume must be finite and strictly positive
- exact 168 completed-hour median/MAD; no alternate windows
- complete-score execution shift exactly t-1
- cross-sectional demeaning; gross/L1 <= 1
- four chronological temporal folds
- no grid, threshold rescue, sign flip, selective asset removal, or post-result redesign
- V16 Frozen and V99 Frozen immutable

## Gate sequence

Run only after Phase140/141 are formally decided. TRAIN alpha/folds -> severe/supersevere -> tails/concentration/regime matrix -> benchmark envelope/reproducibility -> formal freeze -> untouched holdout. Failure at TRAIN permanently rejects this exact hypothesis.
