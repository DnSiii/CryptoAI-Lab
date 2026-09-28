# V99 R106 Phase174 — Macro Stress Persistence — preregistration

PREREGISTERED BEFORE ANY Phase174 PnL.

## Scientific question
Phases169-173 rejected instantaneous macro impulse, curve/liquidity shock, VIX×rates interaction, breadth, and acceleration. Phase174 tests a distinct temporal mechanism: whether *persistent* same-direction macro stress across multiple already-causal daily observations, rather than the magnitude of a single shock, predicts crypto direction.

## Frozen hypothesis
- DATA: only the Phase168 TRAIN-only validated snapshot; series VIXCLS, DTWEXBGS, DGS2, DFF.
- WINDOW: [2021-12-01, 2024-01-18), no holdout fetch/parse.
- For VIXCLS, DTWEXBGS, and front-rate spread DGS2-DFF, compute the sign of the 1 finite-observation change.
- Persistence per series = rolling mean of those signs over exactly 5 finite observations, min_periods=5. This is bounded [-1,1] and uses no fitted scale/threshold.
- Composite persistence = equal-weight mean of the three persistence series. No fitted weights.
- Orientation fixed ex ante: positive persistence = persistent macro stress (VIX/USD/front-rate pressure rising) => short crypto; negative = long crypto.
- Macro availability: latest finite observation strictly before current UTC calendar date, then shift entire hourly target by one additional hour (t-1).
- Equal weight across non-quarantined assets; gross cap 0.20, scaled continuously by absolute composite persistence. No threshold.
- Severe cost gate and existing temporal-fold/robust-tail diagnostics unchanged.
- Single hypothesis. No grid, sign search, asset selection, threshold search, rescue, or retuning.

## Decision rule
Use the same `stable_train` gate as Phases169-173. PASS freezes this exact specification for downstream supersevere/regime/concentration/benchmark/reproducibility gates before any untouched holdout. FAIL permanently rejects Phase174 and does not authorize retuning.

## Firewalls
V16 Frozen and V99 Frozen are read-only. Phase168 must be PASS_DATA_ONLY. Phases169-173 must all be TRAIN_ALPHA_REJECT. Holdout rows used for feature construction and selection remain exactly 0/0.
