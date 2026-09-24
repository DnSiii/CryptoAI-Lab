# V99 R106 — Phase128 rejection + Phase129 preregistration

## Phase128 decision
Phase128 (volatility-normalized momentum continuation) is permanently REJECTED at the train-alpha gate. Severe train ROI=-0.7061309879, PF=0.5529714297, max DD=0.7063269822, positive-hour ratio=0.3720344883, robust mean ex-top1%=-0.0000793825, with 0/4 healthy chronological folds. Fold ROIs were -0.292906, -0.264615, -0.274426, -0.221102; every fold also had negative robust mean ex-top1%. Failure is broad through time and survives removal of the best 1% hours. No sign flip, alternate momentum/volatility windows, threshold search, asset deletion, or holdout inspection is permitted as repair.

Causality/integrity evidence passed: feature input ended 2024-01-17 23:00 UTC, full score shift=1h, post-train targets zero, L1 invariant passed, V16 Frozen and V99 Frozen unchanged, holdout not parsed.

## Phase129 — preregistered hypothesis: Cross-Sectional Short-Horizon Reversal

Scientific distinction: Phases125-128 tested continuation/persistence objects and failed broadly. Phase129 tests a different economic mechanism: temporary cross-sectional price dislocation and subsequent short-horizon mean reversion. This is not a sign flip of Phase128: the feature horizon and economic object are independently specified as short-horizon standardized return shock, not risk-scaled 24h momentum.

### Frozen feature/specification before PnL
For each asset/hour using only canonical hourly closes available at feature time t:
1. Compute hourly log return r_i(t)=log(close_i(t)/close_i(t-1)).
2. Compute trailing 3h return shock `shock_i(t)=sum(r_i,3h)`, requiring all 3 observations.
3. Cross-sectionally robust-standardize shock each hour using median and 1.4826*MAD, requiring at least 8 assets.
4. Define reversal score `score_i(t)=-tanh(z_shock_i(t))`: recent relative winners are short and relative losers long. Direction is frozen now because the hypothesis is liquidity/dislocation mean reversion, not continuation.
5. Shift the entire score exactly one hour before portfolio formation (`t-1`).
6. Normalize cross-sectionally to L1=1 when active and reuse R106 train-alpha execution infrastructure with alpha gross allocation=0.20 and min assets=8.
7. Single hypothesis only: 3h shock horizon is frozen. No grid, alternate horizons, volatility scaling, thresholds, clipping, sign search, selective asset deletion, or post-result repair.

Interpretation: if short-lived cross-sectional dislocations are partially liquidity-driven, extreme relative 3h moves should mean-revert after a one-hour causal delay strongly enough to survive severe execution costs. The 3h horizon is deliberately short and mechanistically distinct from the failed 24h/72h continuation family.

### Selection and gates
- Selection is chronological train-only; train ends exclusively at 2024-01-18T00:00:00Z.
- Untouched holdout MUST NOT be parsed during train-alpha or any downstream pre-holdout gate.
- First gate: severe costs + four chronological temporal folds + robust mean excluding top 1% hours.
- PASS only under existing R106 health criteria; PASS freezes this exact specification.
- After PASS only: supersevere costs -> regime matrix -> tails/concentration -> benchmark envelope -> reproducibility/invariants -> untouched holdout.
- FAIL is permanent for this exact hypothesis. No retuning, sign flip, horizon search, threshold search, selective asset deletion, or holdout rescue.

V16 Frozen and V99 Frozen must be SHA256-snapshotted before/after every execution and remain unchanged.