# V98 Independent — Phase198 failure audit

Decision: **REJECT_FAMILY_NO_RESCUE**.

Scope: training-only evidence from chronological folds 2023/2024/2025. Validation and final holdout remain unopened. No V16/V99 state is used.

## Mechanism audit

The intraday residual-reversal hypothesis fails as a broad economic mechanism rather than from a removable isolated tail. Representative active spec `lb168_z15_h3` loses materially in every chronological fold and in bull, bear, and sideways regimes. Daily PF is far below 1 and drawdown is extreme. Bottom-10 negative days account for only about 14% of negative mass, which is inconsistent with a small set of catastrophic observations being the sole explanation.

Observed representative evidence: total return -85.63%, PF 0.428, MDD -85.82%; folds 2023 -52.72%, 2024 -46.88%, 2025 -42.67%; bull/bear/sideways return sums all negative. The failure list includes base edge/drawdown, fold inconsistency, regime breadth and both severe/supersevere edge/drawdown gates.

## Scientific decision

Do not invert, trim tails, cherry-pick a fold, change thresholds, or rescue this family. Such changes would be conditioned on observed failure. Phase198 is closed as a rejected family.

## Next independent direction

Preregister a genuinely distinct training-only hypothesis before implementation. Candidate family: cross-sectional **funding-pressure mean reversion gated by persistent funding extremes**, using lagged funding information only, fixed sparse grid, explicit turnover/funding accounting, and the existing chronological/stress/reproducibility gates. This direction is orthogonal to Phase198's residual-return shock trigger and must not be tuned from validation/holdout or V99 evidence.
