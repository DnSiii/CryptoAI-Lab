# V99 R106 Phase152 — Cross-Venue Range-Efficiency Divergence — PRE-REGISTRATION

Status: FROZEN BEFORE ANY PHASE152 PNL.

## Scientific rationale
Phases 144–151 show repeated failure of cross-venue candle-location/body/gap transforms. Phase152 tests a distinct dimension: how efficiently each venue converts intrabar range into absolute close-to-close displacement. This is not a sign flip or rescue of Phase151.

For venue v and asset i at hour t:

- displacement_v(t) = abs(close_v(t) - close_v(t-1))
- true_range_v(t) = max(high-low, abs(high-close(t-1)), abs(low-close(t-1)))
- efficiency_v(t) = displacement_v(t) / true_range_v(t), only where true_range_v(t) > 0
- raw_i(t) = efficiency_OKX(t) - efficiency_Binance(t)

Cross-sectional signal construction is frozen to the existing Phase144–151 protocol: rolling exact median/MAD lookback 168h, no epsilon repair, invalid/zero-range rows remain missing, fixed REVERSION direction, final complete score shift t-1, max portfolio L1 <= 1.

## Data / integrity gates
- Same canonical V15 replay and Phase136 source-hash requirements.
- Same five preregistered assets and hourly chronology.
- OKX and Binance valid aligned coverage >= 98% per asset or reject.
- No interpolation/imputation of invalid OHLC/range values.
- Holdout rows used for feature construction = 0; selection = 0.

## Selection / validation gates
- TRAIN only, chronological.
- Four temporal TRAIN folds; no fold shuffling.
- Phase152 is rejected unless the existing TRAIN alpha gate is met.
- If and only if TRAIN gate passes: severe and supersevere costs, regime matrix, tails/concentration, benchmark envelope, then deterministic reproducibility.
- No post-result sign flip, threshold rescue, parameter sweep, clipping, or feature recombination.

## Frozen assets
V16 Frozen and V99 Frozen must remain byte-for-byte untouched.
