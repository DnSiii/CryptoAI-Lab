# V99 R106 Phase170 — Curve/Liquidity Shock preregistration

PREREGISTERED BEFORE ANY Phase170 PnL.

## Scientific purpose

Test one macro mechanism distinct from Phase169's equal-weight broad risk impulse: whether a *rates-curve/liquidity shock* contains causal information for crypto risk after costs. Phase170 is dormant while Phase169 is unresolved and may execute only if Phase169 is scientifically rejected (not merely transport-failed).

## Frozen hypothesis

- TRAIN only: `[2021-12-01, 2024-01-18)` UTC. Untouched holdout is forbidden for feature construction, selection, thresholds, orientation, debugging, or inspection.
- Inputs are restricted to the already DATA-gated Phase168 FRED panel: `DFF`, `DGS2`, `DGS10`. No additional series may be substituted after seeing PnL.
- At each macro observation, define curve slope `DGS10-DGS2` and front-end spread `DGS2-DFF`.
- For each spread, compute the change over exactly 5 finite observations. Standardize each change by expanding prior-only mean/std (`min_periods=60`, statistics shifted one observation), clipped to `[-4,4]`.
- Composite shock is `0.5*z(curve_slope_change) + 0.5*z(front_end_spread_change)`; no weight search.
- Macro availability uses only the latest finite observation strictly before the current UTC calendar date, then the complete hourly target is shifted one additional hour (`t-1`).
- Direction is frozen as defensive/contrarian: positive composite shock -> short crypto; negative -> long crypto. Scalar is `-tanh(abs(composite))*sign(composite)`.
- Gross exposure is fixed at `0.20`, equal-weighted over the same executable non-quarantined universe used by the R106 replay. No asset selection, no threshold/grid/sign search.

## Gates

First gate is TRAIN-only under the existing severe-cost evaluator and temporal-fold `stable_train` contract. A FAIL is permanent for this exact mechanism; no retuning/rescue. A PASS freezes the exact specification and proceeds, without parameter changes, through supersevere costs, temporal folds, regime matrix, concentration/tails, benchmark envelope and reproducibility before any untouched holdout use.

## Firewalls

V16 Frozen and V99 Frozen are read-only. Phase168 must remain `PASS_DATA_ONLY`. Phase169 transport failures do not authorize Phase170. Holdout rows used for construction/selection must remain exactly `0/0` until a formally frozen candidate has passed all pre-holdout gates.
