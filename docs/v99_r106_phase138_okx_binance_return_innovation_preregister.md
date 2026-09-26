# V99 R106 Phase138 — OKX/Binance return-innovation lead-lag (PREREGISTERED)

Status: PREREGISTERED ONLY — DO NOT EXECUTE UNTIL PHASE137 EXACT-MAD DECISION IS HARVESTED.

## Scientific distinction
Phase138 is not a rescue, sign-flip, threshold retune, or alternate normalization of Phase137. Phase137 tests the level of the cross-venue log-price dislocation. Phase138 tests a one-hour cross-venue return innovation: OKX 1h log return minus Binance 1h log return. The economic hypothesis is short-horizon continuation/price-discovery transmission after one venue moves relatively more than the other.

## Frozen hypothesis before PnL
- Universe: exactly the Phase136/137 common symbols; no substitution after observing results.
- Raw feature at hour t: `innovation_t = r_OKX,t - r_Binance,t`, where each return uses only closes available at t.
- Robust scale: exact same-window 168h MAD of innovation around that window's median; zero/invalid MAD => zero score.
- Cross-sectional neutralization: demean robust innovation across available symbols at each t.
- Direction: continuation, not mean reversion. Positive relative OKX innovation implies positive next-position score for that symbol after neutralization.
- Causality: tradable score/position at t uses the complete feature shifted by one full hour (`t-1`).
- Portfolio: deterministic L1 normalization with gross exposure <= 1; no leverage/grid/search.
- Selection/evaluation: chronological TRAIN only; temporal folds identical to the current V99 R106 discipline.
- Costs: baseline plus severe and supersevere schedules already defined by the V99 R106 protocol; no cost assumption may be changed after PnL.
- Holdout: zero rows may be used for feature construction, selection, diagnostics, thresholds, sign choice, or rejection/promotion until a candidate is formally frozen and reaches the authorized holdout gate.
- Regime matrix and benchmark envelope: unchanged from V99 R106.
- No sign flip, no parameter grid, no symbol cherry-pick, no post-result rescue tuning.

## Decision discipline
First execute the single preregistered specification on TRAIN. If it fails the existing TRAIN gate, reject it and do not invert or tune it. If it passes, freeze the candidate and continue through the existing temporal-fold, severe/supersevere-cost, regime, concentration/tail, benchmark-envelope and reproducibility gates in order. Holdout remains untouched unless all upstream gates authorize it.

## Dependency
Phase138 execution is intentionally blocked until the corrected Phase137 Exact-MAD replay is harvested and its decision documented. This preregistration exists now so Phase138 cannot be redesigned in response to the Phase137 corrected PnL.
