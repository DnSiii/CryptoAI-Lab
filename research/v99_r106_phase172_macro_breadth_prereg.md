# V99 R106 Phase172 — Macro Shock Breadth — preregistration

PREREGISTERED BEFORE ANY Phase172 PnL.

## Scientific question
Phase169 rejected a linear macro-risk impulse, Phase170 rejected curve/liquidity shock, and Phase171 rejected a VIX×rates interaction. Phase172 tests a scientifically distinct nonlinear question: whether the *breadth* of simultaneous macro stress, rather than its summed magnitude or pairwise interaction, carries a causal crypto risk signal.

## Frozen hypothesis
- DATA: only the Phase168 TRAIN-only validated snapshot; series VIXCLS, DTWEXBGS, DGS2, DFF.
- WINDOW: [2021-12-01, 2024-01-18), no holdout fetch/parse.
- For each series use 5 finite-observation change; standardize with expanding mean/std shifted one finite observation, min 60, clip [-4,4].
- Construct stress signs with no tuned threshold: VIX shock positive = stress; broad USD shock positive = stress; front-rate spread shock (DGS2-DFF) positive = stress.
- breadth = mean(sign(z_vix), sign(z_usd), sign(z_front)), each sign in {-1,0,+1}.
- Orientation fixed ex ante: positive breadth => short crypto, negative breadth => long crypto.
- Magnitude = abs(breadth), so unanimous signals have larger exposure than split signals. No magnitude fitting.
- Macro availability: latest finite observation strictly before the current UTC calendar date, then shift the entire hourly target by one additional hour (t-1).
- Equal weight across non-quarantined assets; gross cap 0.20.
- Severe cost gate and the existing temporal-fold/robust-tail diagnostics are unchanged.
- Single hypothesis. No grid, sign search, asset selection, threshold search, rescue, or retuning.

## Decision rule
Use the same `stable_train` gate used by Phases169-171. PASS freezes this exact specification for downstream supersevere/regime/concentration/benchmark/reproducibility gates before any untouched holdout. FAIL permanently rejects Phase172 and does not authorize retuning.

## Firewalls
V16 Frozen and V99 Frozen are read-only. Phase168 must be PASS_DATA_ONLY. Phases169,170,171 must be TRAIN_ALPHA_REJECT. Holdout rows used for feature construction and selection must remain exactly 0/0.
