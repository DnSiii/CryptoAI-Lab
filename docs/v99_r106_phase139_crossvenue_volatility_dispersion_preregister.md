# V99 R106 Phase139 — Cross-Venue Volatility-Dispersion Preregistration

Status: **PREREGISTERED / NOT YET EXECUTED**

This hypothesis is frozen before observing any Phase139 PnL. It is deliberately distinct from Phase137 price-level dislocation and Phase138 return-innovation direction.

## Hypothesis

Cross-venue disagreement in **realized volatility**, rather than price or return direction, may identify temporary asset-specific stress that predicts next-hour relative reversal. For each of the same five Phase136 instruments, compute causal 24h realized volatility independently from OKX and Binance hourly log returns, then form:

`vol_gap_t = RV24_OKX_t - RV24_Binance_t`

Normalize `vol_gap` using the exact same-window 168h median and MAD. Cross-sectionally demean the normalized score each hour to remove common venue-wide effects. Freeze the economic direction as **reversion**: assets with unusually positive relative OKX volatility receive lower next-hour relative weight; unusually negative gaps receive higher weight.

## Frozen implementation contract

- universe: BTC, ETH, SOL, XRP, DOGE mappings already audited in Phase136
- source: Phase136 OKX history + existing Binance canonical TRAIN data only
- return frequency: 1h
- realized-volatility window: 24 completed hourly returns
- robust normalization lookback: 168h
- MAD definition: `median(abs(window - median(window)))` on that exact window
- cross-sectional demeaning: yes
- direction: reversion, frozen before PnL
- execution: complete final score shifted by exactly t-1
- gross/L1 cap: <= 1
- missing venue observations: no forward/back fill; score unavailable when required input unavailable
- selection: chronological TRAIN only
- temporal validation: same four chronological folds used by the R106 research protocol
- no grid, no sign flip, no symbol substitution, no asset cherry-picking
- holdout rows for feature construction: 0
- holdout rows for selection: 0

## Gate sequence

1. source-integrity/hash reproduction and causal invariant checks;
2. TRAIN alpha gate and temporal folds;
3. only if TRAIN passes: severe and supersevere costs;
4. only if those pass: tails/concentration/regime matrix and benchmark envelope;
5. holdout remains untouched until a candidate is formally frozen for the protocol's final downstream gate.

## Rejection rule

If the preregistered TRAIN alpha gate fails, reject Phase139 without sign-flip, parameter rescue, alternate RV windows, threshold search, or selective asset removal. Any such idea requires a new preregistration.
