# V99 R106 — Phase129 rejection + Phase130 preregistration

## Phase129 decision
Phase129 (cross-sectional short-horizon reversal) is permanently REJECTED at the train-alpha gate. Severe train ROI=-0.9577672410, PF=0.2302012322, max DD=0.9577662367, positive-hour ratio=0.2343490601, robust mean ex-top1%=-0.0001826581, with 0/4 healthy chronological folds. Fold ROIs were -0.531209, -0.540875, -0.554501, -0.559554; every fold also had negative robust mean ex-top1%. Failure is broad through time and survives removal of the best 1% hours. No sign flip, alternate shock horizon, threshold search, volatility scaling, selective asset deletion, or holdout inspection is permitted as repair.

Causality/integrity evidence passed: feature input ended 2024-01-17 23:00 UTC, full score shift=1h, post-train targets zero, L1 invariant passed, V16 Frozen and V99 Frozen unchanged, holdout not parsed.

## Phase130 — preregistered hypothesis: Downside-Semivariance Asymmetry Continuation

Scientific distinction: Phases125-129 exhausted several symmetric price-path objects (efficiency, range expansion, residual momentum, risk-scaled momentum, short-horizon reversal). Phase130 tests an asymmetric risk-state mechanism: assets whose recent realized variance is disproportionately downside-driven may carry persistent negative information relative to assets with upside-dominated realized variance. This is not a sign flip or horizon repair of Phase129; the economic object is signed realized semivariance composition.

### Frozen feature/specification before PnL
For each asset/hour using only canonical hourly closes available at feature time t:
1. Compute hourly log return r_i(t)=log(close_i(t)/close_i(t-1)).
2. Over a trailing 24h window requiring all 24 returns, compute downside semivariance `down_i(t)=sum(min(r,0)^2)` and upside semivariance `up_i(t)=sum(max(r,0)^2)`.
3. Define signed downside asymmetry `asym_i(t)=(down-up)/(down+up+1e-12)`. Positive values mean downside-dominated realized variation.
4. Cross-sectionally robust-standardize asymmetry each hour using median and 1.4826*MAD, requiring at least 8 assets.
5. Define continuation score `score_i(t)=-tanh(z_asym_i(t))`: downside-dominated assets are short and upside-dominated assets long. Direction is frozen now from the persistent-negative-information hypothesis.
6. Shift the entire score exactly one hour before portfolio formation (`t-1`).
7. Normalize cross-sectionally to L1=1 when active and reuse R106 train-alpha execution infrastructure with alpha gross allocation=0.20 and min assets=8.
8. Single hypothesis only: 24h semivariance window is frozen. No grid, alternate windows, thresholds, clipping, sign search, volatility scaling, selective asset deletion, or post-result repair.

Interpretation: downside-dominated realized variance can proxy adverse information and deleveraging pressure, while upside-dominated variance can proxy persistent demand. The test asks whether this asymmetry contains cross-sectional continuation information strong enough to survive severe execution costs after a full one-hour causal delay.

### Selection and gates
- Selection is chronological train-only; train ends exclusively at 2024-01-18T00:00:00Z.
- Untouched holdout MUST NOT be parsed during train-alpha or any downstream pre-holdout gate.
- First gate: severe costs + four chronological temporal folds + robust mean excluding top 1% hours.
- PASS only under existing R106 health criteria; PASS freezes this exact specification.
- After PASS only: supersevere costs -> regime matrix -> tails/concentration -> benchmark envelope -> reproducibility/invariants -> untouched holdout.
- FAIL is permanent for this exact hypothesis. No retuning, sign flip, horizon search, threshold search, selective asset deletion, or holdout rescue.

V16 Frozen and V99 Frozen must be SHA256-snapshotted before/after every execution and remain unchanged.