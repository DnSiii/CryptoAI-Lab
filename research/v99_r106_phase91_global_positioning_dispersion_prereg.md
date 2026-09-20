# V99 R106 Phase91 — Cross-sectional global-positioning dispersion state (pre-registration)

## Scientific question
Does an asset's causal deviation from the simultaneous cross-sectional median of Binance USD-M global account long/short positioning contain information distinct from the rejected Phase89 change signal and Phase90 raw-level rank?

## Frozen hypothesis
At each hourly timestamp, use native `count_long_short_ratio` levels only and require positive finite observations. Compute `log(count_long_short_ratio)` and shift each asset feature exactly one bar (`t-1`) before portfolio formation. Require at least 10 simultaneously observed assets. For each timestamp compute the cross-sectional median of the lagged log-ratio and the cross-sectional median absolute deviation (MAD). Define a robust dispersion score `(x - median) / max(MAD, 1e-12)`. Winsorize only by deterministic rank mapping, not a fitted threshold: convert the robust score to simultaneous percentile rank and center it at 0.5. Fixed hypothesis is mean-reverting dispersion: assets far above the contemporaneous crowd receive negative weights and assets far below receive positive weights. Normalize absolute weights to 1; fixed alpha gross 0.20.

This tests relative distance from the crowd center rather than Phase89's first difference or Phase90's direct raw-level rank. Phase89 and Phase90 remain rejected regardless of this result. No sign inversion is permitted after observing results.

## Frozen evaluation discipline
- chronological train-only selection using existing native-metrics train end;
- untouched holdout: do not list, parse, inspect, score, or optimize holdout;
- causal `t-1` lag on asset positioning before any portfolio formation;
- simultaneous cross-sectional median/MAD and ranking, minimum 10 valid assets;
- fixed mean-reverting direction; no grid, threshold sweep, sign flip, rescue, or retuning;
- alpha gross 0.20;
- existing severe cost model and temporal-fold `stable_train` gate;
- native archives only, SHA256 checksum + ZIP CRC verification;
- missing archives remain missing; no synthetic fill/interpolation;
- V16 Frozen and V99 Frozen untouched.

## Decision rule
PASS only if existing deterministic `stable_train` gate passes. PASS freezes this exact specification and advances without tuning to supersevere, regime matrix, benchmark envelope, and reproducibility before any untouched-holdout gate. FAIL permanently rejects Phase91; no inversion/tuning.
