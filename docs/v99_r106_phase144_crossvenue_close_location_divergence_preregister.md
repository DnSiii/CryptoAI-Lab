# V99 R106 Phase144 — Cross-Venue Close-Location Divergence Preregistration

Status: **PREREGISTERED / NO PNL OBSERVED**

Frozen after Phase140 was rejected as data-inadmissible and before any Phase144 PnL. This hypothesis is deliberately independent of notional volume and therefore does not inherit the zero-volume pathology of Phase140/141.

## Scientific premise

For the same five Phase136 instruments, compare where each venue's completed hourly close lies inside its own contemporaneous high-low range. A persistent difference in close location can represent venue-specific intrabar pressure without using volume, funding, future data, or a price-level spread.

For venue `v`, asset `i`, completed hour `t`:

`CLV[v,i,t] = ((close-open) / (high-low))` when `high > low`.

If `high == low`, the observation is inadmissible for that asset/hour and remains missing; no epsilon, imputation, forward/back fill, or symbol substitution is allowed. Before PnL, each asset must have >=98% aligned valid TRAIN observations on both venues; otherwise Phase144 is DATA_INADMISSIBLE.

Define:

`divergence[i,t] = CLV[OKX,i,t] - CLV[Binance,i,t]`

Normalize each asset using exact same-window 168-hour median/MAD (`median(abs(window - median(window)))`), then cross-sectionally demean the normalized scores. Freeze **reversion** direction: relatively stronger OKX close-location versus Binance receives lower next-hour relative weight. Shift the complete score by exactly `t-1` before execution.

## Frozen contracts

- universe: BTC, ETH, SOL, XRP, DOGE mappings already audited in Phase136
- source: direct completed 1h OHLC from OKX and canonical Binance futures klines; no proxy source
- TRAIN only for construction and selection
- aligned-valid coverage gate: >=98% per asset before any PnL
- no epsilon or rescue for zero-range candles
- normalization: exact 168h same-window median/MAD
- cross-sectional demeaning: yes
- direction: reversion
- complete score execution shift: exactly t-1
- gross/L1 <= 1
- four chronological temporal folds
- no grid, sign flip, symbol substitution, threshold rescue, selective asset removal, or post-hoc direction change
- holdout rows used for feature construction/selection: 0/0
- V16 Frozen and V99 Frozen immutable

## Gate sequence

1. OHLC semantic/alignment/coverage/integrity gate only, no PnL;
2. TRAIN alpha + four temporal folds;
3. only if TRAIN passes: severe and supersevere costs;
4. only if costs pass: tails, concentration, regime matrix, benchmark envelope, reproducibility;
5. untouched holdout only after formal freeze under the existing protocol.

Failure at any gate is permanent for this frozen formulation; do not rescue or tune it.
