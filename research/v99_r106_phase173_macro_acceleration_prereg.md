# V99 R106 Phase173 — Macro Shock Acceleration — preregistration

PREREGISTERED BEFORE ANY Phase173 PnL.

## Scientific question
Phases169-172 rejected macro shock level, curve/liquidity, interaction, and breadth formulations. Phase173 tests a distinct temporal hypothesis: whether *acceleration* of macro stress (change in the already causal 5-observation shock), rather than shock level or breadth, predicts crypto direction.

## Frozen hypothesis
- DATA: only the Phase168 TRAIN-only validated snapshot; series VIXCLS, DTWEXBGS, DGS2, DFF.
- WINDOW: [2021-12-01, 2024-01-18), no holdout fetch/parse.
- For VIXCLS, DTWEXBGS, and front-rate spread DGS2-DFF, compute 5 finite-observation change, then acceleration as the first finite-observation difference of that change.
- Standardize each acceleration with expanding mean/std shifted one finite observation, min 60, clip [-4,4].
- Composite acceleration = equal-weight mean(z_vix_accel, z_usd_accel, z_front_accel). No fitted weights.
- Orientation fixed ex ante: positive composite acceleration = increasing macro stress => short crypto; negative = long crypto.
- Macro availability: latest finite observation strictly before current UTC calendar date, then shift entire hourly target by one additional hour (t-1).
- Equal weight across non-quarantined assets; gross cap 0.20, scaled continuously by clipped composite/4 so the cap is reached only at the preregistered clip boundary.
- Severe cost gate and existing temporal-fold/robust-tail diagnostics unchanged.
- Single hypothesis. No grid, sign search, asset selection, threshold search, rescue, or retuning.

## Decision rule
Use the same `stable_train` gate as Phases169-172. PASS freezes this exact specification for downstream supersevere/regime/concentration/benchmark/reproducibility gates before any untouched holdout. FAIL permanently rejects Phase173 and does not authorize retuning.

## Firewalls
V16 Frozen and V99 Frozen are read-only. Phase168 must be PASS_DATA_ONLY. Phases169-172 must all be TRAIN_ALPHA_REJECT. Holdout rows used for feature construction and selection remain exactly 0/0.
