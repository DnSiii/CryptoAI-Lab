# V98 Independent — Phase190 rejection audit

Decision: **REJECT_FAMILY_NO_RESCUE**.

Scope: training-only 2023-01-01 through 2025-12-31. Validation and final holdout remain unopened. V16/V99 were not used.

## Evidence

The preregistered 8-spec volatility-shock continuation family produced no passing candidate. Every specification failed multiple structural gates including base edge/drawdown, fold consistency, regime breadth, concentration, and severe/supersevere edge/drawdown.

The least-bad base PF observed was approximately 1.012 (`w168_s1p5_h6`), but total return was -16.25%, MDD -53.78%, 2025 return -33.38% / PF 0.811, severe return -49.68% / PF 0.916, and supersevere return -77.76% / PF 0.784. This is not a cost-only failure.

The `w336_s1p5_h6` variant showed positive 2023 and 2024 folds (+12.68%, +9.67%) but collapsed in 2025 (-48.55%, PF 0.724), while aggregate return was -36.43% with MDD -67.40%. Thus the apparent early-period edge is nonstationary and fails chronological generalization.

Concentration is independently problematic: mean top-1 position share is roughly 0.72–0.77 across the grid, with p95 top-1 share 1.0. Regime evidence is also weak: bear returns are negative throughout the representative variants, and many variants depend on sideways/bull pockets rather than broad regime robustness.

Tails are not the sole explanation: representative top/bottom-10 contribution shares are often below 0.50, yet aggregate economics remain negative. Therefore removing a few extreme observations would not scientifically rescue the family.

## Integrity / reproducibility

The workflow rebuilt five canonical V98 assets with an explicit max-timestamp guard before 2026-01-01. Two complete executions were byte-identical with SHA256 `c782a777cdb20dbf8493e584d17d2a350eab968feeadcd662492f77239101fcf`. Output declares `training_only=true`, `validation=null`, `final_holdout=null`, `v16_used=false`, `v99_used=false`.

## Scientific conclusion

Volatility-shock continuation, as preregistered in Phase190, is rejected without tuning, sign flipping, threshold rescue, or validation inspection. The failure mechanism is broad: weak/negative net edge, severe drawdowns, high single-name concentration, poor bear behavior, and especially chronological degradation into 2025.

Next research must be a genuinely distinct training-only hypothesis rather than a local perturbation of Phase190.