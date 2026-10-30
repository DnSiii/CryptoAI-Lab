# V98 Independent Phase189 — decision

Decision: **REJECT_FAMILY_NO_RESCUE**.

Phase189 tested the preregistered cross-sectional dispersion mean-reversion family on training only (2023-01-01 through 2025-12-31), with validation and final holdout untouched and V16/V99 unused.

## Evidence

All 8 preregistered specifications failed the eligibility gate with the same failure classes: `fold_inconsistency`, `stress_nonpositive`, and `stress_pf_not_robust`.

The closest base-case specification was `h6_w60_q80`: total return +3.8934%, daily PF 1.0824, MDD -6.5702%, payoff 1.3208, 168 positive days / 1095, daily win rate 15.34%. This apparent aggregate edge is not robust: 2023 returned +6.3102% with PF 1.2870, 2024 -0.2648% with PF 0.9894, and 2025 -2.0138% with PF 0.8586. Severe costs turn the full-period result negative (-2.6372%, PF 0.9606), and supersevere costs deteriorate to -12.2122%, PF 0.7979, MDD -14.6083%.

Regime attribution for that closest specification is also structurally weak: approximate return contribution is negative in bear (-0.00278) and bull (-0.01564) and positive only in sideways (+0.06111). Tails are not the primary failure mechanism (bottom-10 loss share 27.28%, top-10 gain share 30.93%), and concentration is not extreme (mean top-1 weight share 50.48%, p95 51.61%). The failure is therefore generalization/cost robustness rather than a single tail or concentration pathology.

A second superficially promising 6h specification (`h6_w120_q80`) is already negative in aggregate base (-1.5028%, PF 0.9791) and degrades under severe/supersevere costs, reinforcing rejection of the family rather than parameter rescue.

## Scientific decision

Do not tune thresholds, windows, or costs around these results. Do not open validation. Phase189 is closed as a rejected training family. Any subsequent V98 experiment must be a scientifically distinct preregistered hypothesis and remain training-only until it independently passes all training robustness gates.

Reproducibility/integrity: workflow rebuilt training-only data, asserted all canonical timestamps < 2026-01-01, ran Phase189 twice with byte-identical SHA-256 `e64f92c48ac44905f15e14927b69c568fb29fa6ec1bea1f842616cc603398f9f`, and recorded `validation=null`, `final_holdout=null`, `v16_used=false`, `v99_used=false`.
