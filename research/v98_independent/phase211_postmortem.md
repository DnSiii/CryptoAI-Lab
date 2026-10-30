# V98 Independent Phase211 — post-mortem

Status: **REJECT_FAMILY_NO_RESCUE**.

## Reproducibility / integrity
- Workflow run 36980639771 completed successfully.
- Training-only rebuild and `<2026-01-01` firewall passed.
- Two deterministic evaluations produced identical report SHA256 `d993b68aa245deb6ae0286ea79a102cbd0f5544b171d32bbaa074bda0764640a`.
- Mechanical gate: `training-fold coherent specs: []` (0/8).
- Validation/final holdout remains unopened.

## Failure mechanism audit
The first frozen spec (`leadbtc_L12_z20_hold12`) illustrates the instability without selecting it as a rescue target:
- 2023 base: +11.13%, PF 1.031, MDD -24.27%; severe -12.80%, supersevere -46.35%.
- 2024 base: -13.87%, PF 0.991, MDD -41.89%; severe -31.13%, supersevere -55.99%.
- 2025 base: +1.16%, PF 1.014, MDD -27.48%.

The apparent edge is not robust to chronology or costs. 2023 base profit is concentrated in SOL (+16.05%) while BNB is negative; 2024 has only ETH positive while BNB/SOL/XRP are negative. Regime decomposition is likewise unstable: bull is positive in 2023/24/25 for this spec, but bear is negative in all observed folds and sideways flips. This is insufficient for a robust independent engine and severe/supersevere costs destroy the already marginal base economics.

## Decision
No threshold tweak, asset exclusion, regime filter, direction inversion, or Phase211 rescue is permitted after seeing these results. Phase211 is closed. Champion unchanged. V16/V99 and V99 paper state untouched.
