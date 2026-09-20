# V99 R106 Phase90 — Cross-sectional global-positioning level crowding (pre-registration)

## Scientific question
Does the *level* of Binance USD-M global account long/short positioning contain a causal cross-sectional crowding premium distinct from rejected Phase89 change signal?

## Frozen hypothesis
At each hourly timestamp, use native `count_long_short_ratio` levels only. Require positive finite observations. Shift feature exactly one bar (`t-1`) before portfolio formation. Across simultaneously available assets, percentile-rank `log(count_long_short_ratio)`; require at least 10 assets. Fixed contrarian crowding portfolio: relatively high ratios get negative weights and relatively low ratios positive weights. Normalize absolute weights to 1; fixed alpha gross 0.20.

This is a level/crowding-state hypothesis, not a sign-flip or rescue of Phase89 first-difference hypothesis. Phase89 remains rejected regardless of this result.

## Frozen evaluation discipline
- chronological train-only selection using existing native-metrics train end;
- untouched holdout: do not list, parse, inspect, score, or optimize holdout;
- causal `t-1` lag;
- simultaneous cross-sectional ranking, minimum 10 valid assets;
- fixed contrarian direction; no grid, threshold sweep, sign flip, rescue, or retuning;
- alpha gross 0.20;
- existing severe cost model and temporal-fold `stable_train` gate;
- native archives only, SHA256 checksum + ZIP CRC verification;
- missing archives remain missing; no synthetic fill/interpolation;
- V16 Frozen and V99 Frozen untouched.

## Decision rule
PASS only if existing deterministic `stable_train` gate passes. PASS freezes this exact specification and advances without tuning to supersevere, regime matrix, benchmark envelope, and reproducibility before any untouched-holdout gate. FAIL permanently rejects Phase90; no inversion/tuning.
