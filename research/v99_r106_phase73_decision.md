# V99 R106 Phase73 — Decision

**Decision: REJECT permanently at TRAIN-ONLY gate.**

Phase73 tested exactly the preregistered continuation feature `diff(log(sum_toptrader_long_short_ratio),1).shift(1)` at fixed gross 0.20 under the locked severe-cost and temporal-fold diagnostic. The recorded evidence is not stable: TRAIN ROI -12.4023%, profit factor 0.94696, max drawdown 16.9268%, robust mean excluding top 1% -4.014e-05, with only 1/4 healthy folds. The one healthy first fold does not override the chronological instability across the subsequent three folds.

No sign flip, alternate horizon, smoothing, blend, threshold, field substitution, or rescue of this exact Phase73 hypothesis is permitted. Holdout was not parsed. V16 Frozen and V99 Frozen were untouched.

Phase74 is a separately preregistered complementary breadth hypothesis using the native top-trader *account/count* ratio change rather than aggregate position sizing. Its result must stand on its own train-only gate.