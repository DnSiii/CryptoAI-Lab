# V99 R106 Phase137 — Exact-MAD Corrected Replay Protocol

Status: PREREGISTERED CORRECTION / TRAIN-ONLY / SAME FROZEN HYPOTHESIS / NO GRID

## Reason for correction

Independent implementation audit found that the first Phase137 runner did not compute the rolling 168h MAD literally as preregistered. It computed `median_t(|spread_t - rolling_median_t(spread)|)` over a second rolling window, where each deviation was referenced to a different contemporaneous rolling median. That is not the MAD of each 168h window around that window's own median.

The first Phase137 PnL therefore remains evidence about the executed implementation but is invalid for the final decision on the exact preregistered hypothesis.

## Frozen correction

No economic or portfolio parameter changes are authorized.

For each asset and each timestamp t, on the same trailing 168 observations:
- baseline_t = median(window_t(spread))
- MAD_t = median(abs(window_t(spread) - baseline_t))
- scale_t = 1.4826 * MAD_t
- standardized_t = (spread_t - baseline_t) / scale_t
- raw score = -tanh(standardized_t)
- cross-sectional demean
- shift the complete score by exactly 1 hour
- L1 normalize across the same five frozen assets

All other Phase137 contracts remain unchanged: same five symbols, same OKX Phase136 hashes, same TRAIN window, severe selection cost, alpha gross 0.20, four temporal folds, no sign flip, no alternate lookback, no threshold, no symbol substitution, no holdout feature construction/selection, and no V16/V99 Frozen mutation.

## Decision rule

The corrected replay is the authoritative Phase137 train gate for the exact preregistered hypothesis. PASS proceeds to the already-defined downstream stress gates. FAIL permanently rejects the exact hypothesis; no continuation sign flip or lookback rescue is permitted.

The correction is implementation fidelity only and was frozen before observing any corrected-replay PnL.
