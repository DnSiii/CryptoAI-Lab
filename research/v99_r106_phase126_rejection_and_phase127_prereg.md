# V99 R106 — Phase126 rejection + Phase127 preregistration

## Phase126 decision
Phase126 (6h/72h range-compression × 6h breakout continuation) is permanently REJECTED at the train-alpha gate after the corrected canonical-OHLC execution. Severe train ROI=-0.9629258604, PF=0.4429126433, max DD=0.9629221906, positive-hour ratio=0.3114121994, robust mean ex-top1%=-0.0002068678, with 0/4 healthy chronological folds. Fold ROIs were -0.580403, -0.551314, -0.572405, -0.539463; every fold also had negative robust mean ex-top1%. This is broad temporal failure, not a single tail or regime accident. No sign flip, alternate windows, threshold search, asset deletion, or holdout inspection is permitted as repair.

Causality/integrity evidence passed: feature input ended 2024-01-17 23:00 UTC, full score shift=1h, post-train targets zero, max L1 invariant passed, V16 Frozen and V99 Frozen unchanged, holdout not parsed.

## Phase127 — preregistered hypothesis: Market-Residual Momentum Continuation

Scientific distinction: Phase127 asks whether asset-specific trend survives after removing contemporaneous common crypto-market movement. It is distinct from Phase125 directional efficiency and Phase126 compression/breakout, and uses no taker side, aggTrade concentration, OI, funding, positioning, premium, mark-index divergence, range state, or frozen-engine output.

### Frozen feature/specification before PnL
For each asset/hour using only canonical hourly closes available at feature time t:
1. Compute log return `r_i(t)=log(close_i(t)/close_i(t-1))`.
2. Define common-market return `m(t)` as the equal-weight cross-sectional median of valid asset log returns at t (minimum 8 assets). The median is fixed to reduce single-asset domination.
3. Estimate each asset's rolling 72h beta causally from trailing observations only: `beta_i = cov(r_i,m)/var(m)`, requiring 48 valid observations; no forward fill across missing asset returns.
4. Residual return is `e_i(t)=r_i(t)-beta_i(t)*m(t)`.
5. Asset-specific residual momentum is the trailing 24h sum `resmom_i(t)=sum(e_i,24h)`, requiring all 24 residual observations.
6. Cross-sectionally robust-standardize residual momentum each hour using median and `1.4826*MAD`, requiring at least 8 assets; `score=tanh(z_resmom)`.
7. Direction is continuation only. Entire score is shifted exactly one hour before portfolio formation (`t-1`). No sign flip.
8. Normalize cross-sectionally to L1=1 when active and reuse the R106 train-alpha execution infrastructure with alpha gross allocation=0.20 and min assets=8.
9. Single hypothesis only: beta window=72h, minimum beta observations=48, residual-momentum window=24h are frozen now. No grid, alternate horizons, thresholds, sign search, selective asset deletion, or post-result repair.

Interpretation: raw crypto momentum can simply be market beta in disguise. Phase127 removes the common market component first and tests whether idiosyncratic relative trend itself has persistent severe-cost expectancy.

### Selection and gates
- Selection is chronological train-only; train ends exclusively at 2024-01-18T00:00:00Z.
- Untouched holdout MUST NOT be parsed during train-alpha or any downstream pre-holdout gate.
- First gate: severe costs + four chronological temporal folds + robust mean excluding top 1% hours.
- PASS only under existing R106 health criteria; PASS freezes this exact specification.
- After PASS only: supersevere costs -> regime matrix -> tails/concentration -> benchmark envelope -> reproducibility/invariants -> untouched holdout.
- FAIL is permanent for this exact hypothesis. No retuning, sign flip, horizon search, threshold search, selective asset deletion, or holdout rescue.

V16 Frozen and V99 Frozen must be SHA256-snapshotted before/after every execution and remain unchanged.