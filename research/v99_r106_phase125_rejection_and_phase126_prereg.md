# V99 R106 — Phase125 rejection + Phase126 preregistration

## Phase125 decision
Phase125 (24h volatility efficiency / directional persistence) is permanently REJECTED at the train-alpha gate. Severe train ROI=-0.7094649716, PF=0.5441815279, max DD=0.7096922829, robust mean ex-top1%=-7.94748e-05, with 0/4 healthy chronological folds. All four folds are negative. No sign flip, alternate horizon, threshold search, or holdout inspection is permitted as a repair.

Causality/integrity evidence passed: feature input ended 2024-01-17 23:00 UTC, full score shift=1h, post-train targets zero, V16 Frozen and V99 Frozen unchanged, holdout not parsed.

## Phase126 — preregistered hypothesis: Range Compression Expansion Continuation

Scientific distinction: this tests price-path *compression state followed by directional expansion*, rather than Phase125's 24h directional-efficiency level. It does not use taker side, aggTrade concentration, OI, funding, positioning, premium, mark-index divergence, or Phase125 efficiency.

### Frozen feature/specification before PnL
For each asset/hour using only canonical hourly OHLC available at t:
1. `tr = max(high-low, abs(high-prev_close), abs(low-prev_close)) / prev_close`.
2. `fast_range = rolling_mean(tr, 6h)` and `slow_range = rolling_mean(tr, 72h)`.
3. `compression = log((fast_range + eps)/(slow_range + eps))`.
4. `breakout = log(close / close.shift(6))`.
5. Cross-sectionally robust-standardize `compression` and `breakout` each hour with median and `1.4826*MAD`.
6. Frozen score at feature time: `raw = (-z_compression).clip(lower=0) * z_breakout`; then `score=tanh(raw)`.
7. Direction is continuation only. Entire score is shifted exactly 1 hour before portfolio formation (`t-1`). No sign flip.
8. Portfolio construction and normalization reuse the R106 train-alpha infrastructure; alpha gross allocation = 0.20, min assets=8. No grid, threshold sweep, alternate windows, or parameter search.

Interpretation: an asset receives exposure only when its recent 6h true-range is compressed relative to its own 72h state and it already has a cross-sectionally strong 6h directional break. This is a single preregistered interaction, not a post-result filter.

### Selection and gates
- Selection is chronological train-only; train ends exclusively at 2024-01-18T00:00:00Z.
- Untouched holdout MUST NOT be parsed during train-alpha or downstream pre-holdout gates.
- First gate: severe costs + four chronological temporal folds + robust mean excluding top 1% hours.
- PASS only under the existing R106 health criteria; a PASS freezes this exact specification.
- After PASS only: supersevere costs -> regime matrix -> tails/concentration -> benchmark envelope -> reproducibility/invariants -> untouched holdout.
- FAIL is permanent for this exact hypothesis. No retuning, sign flip, window search, selective asset deletion, or holdout rescue.

V16 Frozen and V99 Frozen must be SHA256-snapshotted before/after every execution and remain unchanged.