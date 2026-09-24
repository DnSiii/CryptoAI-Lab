# V99 R106 — Phase127 rejection + Phase128 preregistration

## Phase127 decision
Phase127 (market-residual momentum continuation) is permanently REJECTED at the train-alpha gate. Severe train ROI=-0.6975712134, PF=0.5730536288, max DD=0.6978560505, positive-hour ratio=0.3778182402, robust mean ex-top1%=-0.0000783710, with 0/4 healthy chronological folds. Fold ROIs were -0.297096, -0.245507, -0.279171, -0.208885; every fold also had negative robust mean ex-top1%. The failure is broad through time and survives removal of the best 1% hours. No sign flip, alternate beta/momentum windows, threshold search, asset deletion, or holdout inspection is permitted as repair.

Causality/integrity evidence passed: feature input ended 2024-01-17 23:00 UTC, full score shift=1h, post-train targets zero, L1 invariant passed, V16 Frozen and V99 Frozen unchanged, holdout not parsed.

## Phase128 — preregistered hypothesis: Volatility-Normalized Momentum Continuation

Scientific distinction: Phase128 tests whether trend strength measured in units of each asset's own recent realized risk has severe-cost persistence. Unlike Phase127 it does not estimate common-market beta or residualize cross-sectionally before momentum construction. Unlike Phase125 it does not measure directional efficiency/path smoothness. It uses only canonical hourly closes and changes the economic object to risk-scaled trend.

### Frozen feature/specification before PnL
For each asset/hour using only canonical hourly closes available at feature time t:
1. Compute hourly log return `r_i(t)=log(close_i(t)/close_i(t-1))`.
2. Compute trailing 24h momentum `mom_i(t)=sum(r_i,24h)`, requiring all 24 observations.
3. Compute trailing 72h realized volatility as sample standard deviation of hourly log returns, requiring all 72 observations. No forward fill across missing returns.
4. Define risk-scaled momentum `vmom_i(t)=mom_i(t)/(rv72_i(t)*sqrt(24))` when realized volatility is finite and strictly positive. No clipping or thresholding of vmom before robust cross-sectional standardization.
5. Cross-sectionally robust-standardize `vmom` each hour using median and `1.4826*MAD`, requiring at least 8 assets; `score=tanh(z_vmom)`.
6. Direction is continuation only. Entire score is shifted exactly one hour before portfolio formation (`t-1`). No sign flip.
7. Normalize cross-sectionally to L1=1 when active and reuse the R106 train-alpha execution infrastructure with alpha gross allocation=0.20 and min assets=8.
8. Single hypothesis only: momentum window=24h and realized-volatility window=72h are frozen now. No grid, alternate horizons, volatility floors/caps, thresholds, sign search, selective asset deletion, or post-result repair.

Interpretation: a raw return move of identical magnitude should carry different information in a quiet versus intrinsically volatile asset. Phase128 asks whether normalizing trend by the asset's own recent risk isolates persistent cross-sectional trend quality rather than market beta, path efficiency, or breakout state.

### Selection and gates
- Selection is chronological train-only; train ends exclusively at 2024-01-18T00:00:00Z.
- Untouched holdout MUST NOT be parsed during train-alpha or any downstream pre-holdout gate.
- First gate: severe costs + four chronological temporal folds + robust mean excluding top 1% hours.
- PASS only under existing R106 health criteria; PASS freezes this exact specification.
- After PASS only: supersevere costs -> regime matrix -> tails/concentration -> benchmark envelope -> reproducibility/invariants -> untouched holdout.
- FAIL is permanent for this exact hypothesis. No retuning, sign flip, horizon search, volatility-floor search, threshold search, selective asset deletion, or holdout rescue.

V16 Frozen and V99 Frozen must be SHA256-snapshotted before/after every execution and remain unchanged.