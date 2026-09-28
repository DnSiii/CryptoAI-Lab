# V99 R106 Phase171 — VIX × rates interaction preregistration

PREREGISTERED BEFORE ANY Phase171 PnL.

## Scientific purpose

Phase169 showed that a broad additive macro impulse was not temporally stable; Phase170 showed that rates-curve/liquidity spreads alone were also not robust. Test one scientifically distinct interaction mechanism: whether crypto responds defensively specifically when equity volatility and front-end rate pressure move together, rather than to either additive component in isolation.

## Frozen hypothesis

- TRAIN only: `[2021-12-01, 2024-01-18)` UTC. Untouched holdout is forbidden for feature construction, selection, thresholds, orientation, debugging, or inspection.
- Inputs restricted to the already DATA-gated Phase168 FRED panel: `VIXCLS`, `DGS2`, `DFF`. No additional series/substitution after seeing PnL.
- At each macro observation define `front = DGS2-DFF`.
- Compute changes over exactly 5 finite observations for `VIXCLS` and `front`.
- Standardize each change with expanding prior-only mean/std (`min_periods=60`, statistics shifted one observation), clipped to `[-4,4]`.
- Interaction score is exactly `z_vix * z_front`; no additive term and no weight search.
- Macro availability uses only the latest finite observation strictly before the current UTC calendar date, then the complete hourly target is shifted one additional hour (`t-1`).
- Direction frozen defensive: positive interaction -> short crypto; negative interaction -> long crypto. Scalar is `-tanh(abs(interaction))*sign(interaction)`.
- Gross exposure fixed at `0.20`, equal-weighted over the same executable non-quarantined universe used by R106 replay. No asset selection, threshold/grid/sign search.

## Gates

First gate is TRAIN-only under existing severe-cost evaluator and temporal-fold `stable_train` contract. FAIL is permanent for this exact mechanism; no retuning/rescue. PASS freezes exact specification and proceeds unchanged through supersevere costs, temporal folds, regime matrix, concentration/tails, benchmark envelope and reproducibility before any untouched holdout use.

## Firewalls

V16 Frozen and V99 Frozen are read-only. Phase168 must remain `PASS_DATA_ONLY`; Phase169 and Phase170 must remain scientifically rejected. Holdout rows used for construction/selection must remain exactly `0/0` until a formally frozen candidate has passed all pre-holdout gates.
