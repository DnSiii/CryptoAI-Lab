# V99 R106 Phase92 — Robust cross-sectional global-positioning distance (pre-registration)

## Scientific question
Does the *magnitude* of an asset's causal distance from the simultaneous cross-sectional center of Binance USD-M global account long/short positioning contain train-stable information that was discarded by the rejected Phase90 rank signal?

## Frozen hypothesis
At each hourly timestamp use native `count_long_short_ratio` levels only, requiring positive finite observations. Compute `x = log(count_long_short_ratio)` and shift each asset feature exactly one bar (`t-1`) before portfolio formation. Require at least 10 simultaneously observed assets. Compute the simultaneous cross-sectional median `m` and MAD `median(|x-m|)`. If MAD is non-finite or <= 1e-12, hold zero exposure for that timestamp. Otherwise define robust distance `z=(x-m)/MAD` and fixed mean-reverting raw signal `raw=-tanh(z)`. `tanh` is frozen with unit scale and is not fitted or swept. Normalize absolute raw weights to 1 and apply fixed alpha gross 0.20.

Unlike Phase90/91 percentile ranking, this specification preserves robust distance magnitude (with deterministic bounded influence), so two assets on the same side of the median can receive different magnitudes according to their distance. No sign inversion is permitted after observing results.

## Frozen evaluation discipline
- chronological train-only selection using existing native-metrics train end;
- untouched holdout: do not list, parse, inspect, score, or optimize holdout;
- causal `t-1` lag before portfolio formation;
- simultaneous cross-sectional median/MAD, minimum 10 valid assets;
- zero exposure when MAD is degenerate/non-finite;
- fixed `-tanh(z)` mean-reverting direction and unit scale; no grid, threshold sweep, sign flip, rescue, or retuning;
- alpha gross 0.20;
- existing severe cost model and temporal-fold `stable_train` gate;
- native archives only, SHA256 checksum + ZIP CRC verification;
- missing archives remain missing; no synthetic fill/interpolation;
- V16 Frozen and V99 Frozen untouched.

## Decision rule
PASS only if the existing deterministic `stable_train` gate passes. PASS freezes this exact specification and advances without tuning to supersevere, regime matrix, benchmark envelope, and reproducibility before any untouched-holdout gate. FAIL permanently rejects Phase92; no inversion/tuning.
