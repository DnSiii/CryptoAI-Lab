# V99 R106 Phase85 — Decision

Status: **PERMANENT REJECT — TRAIN-ONLY**

Phase85 tested the preregistered OI-contraction taker-absorption mechanism exactly once, with causal t-1, severe costs, fixed gross 0.20, chronological train-only evaluation and four temporal folds. The untouched holdout was not parsed.

Evidence from `reports/candidate_v99_r106_phase85_oi_contraction_taker_absorption_train_alpha.json`:
- train ROI: -25.8124%
- profit factor: 0.91065
- max drawdown: 27.7537%
- robust mean excluding top 1%: -4.4733e-05
- healthy folds: 0/4
- all four temporal folds negative
- archives consumed: 37,836, with SHA256+CRC verification

Decision: reject Phase85 permanently. No sign flip, threshold search, horizon search, smoothing search, amplitude tuning or rescue variant is permitted. The result is evidence against this exact absorption formulation, not permission to invert it after observing the outcome.

V16 Frozen and V99 Frozen remain untouched. Holdout remains sealed. Any next experiment must be preregistered and mechanistically distinct before execution.