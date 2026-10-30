# V98 Independent Phase214 — post-result audit

Status: **REJECT_FAMILY_NO_RESCUE**

## Mechanical result
The frozen Phase214 grid contained exactly 8 specs. The completed deterministic workflow reported zero training-fold coherent specs under the preregistered gate (base return > 0 and base PF > 1 in each of 2023, 2024, 2025). Validation/final holdout therefore remains unopened.

## Reproducibility / firewall
- workflow firewall passed with hard cutoff `<2026-01-01`
- deterministic run 1 SHA256: `dc7407a077a75732e2df04bd1d5d725b7837235a9fd97497b4ef7b634787622c`
- deterministic run 2 SHA256: identical
- no V99 information used

## Failure-mechanism audit
Representative frozen spec `comp_C12_q70_hold3` illustrates the instability rather than a single-tail accident:
- 2023 base: return +4.21%, PF 1.160, MDD -4.76%, 159 trades. However severe already turns negative (-1.09%, PF 0.973) and supersevere is -10.89%, PF 0.720. Bear regime is negative even at base (-1.50%, PF 0.647).
- 2024 base: return -9.44%, PF 0.714, MDD -10.47%, 175 trades. All four asset returns are negative; bull, bear and sideways regimes are all negative. Severe falls to -14.70% / PF 0.592 and supersevere to -24.33% / PF 0.423.
- 2025 base: return -6.75%, PF 0.821, MDD -10.41%, 196 trades. All four asset returns are negative. Only the bear slice is slightly positive (+0.66%, PF 1.137), while bull and sideways are negative; severe is -12.62% / PF 0.693.

The family therefore fails across time, assets, regimes and transaction-cost stress. The 2023 base edge is too small to survive realistic stress and does not persist into 2024/2025. This is not a concentration-only or isolated extreme-tail failure, so no asset deletion, regime filter, sign inversion, threshold expansion or parameter rescue is scientifically justified.

## Decision
Close Phase214 as `REJECT_FAMILY_NO_RESCUE`. Keep current champion unchanged. Continue only with a scientifically distinct family preregistered before seeing its results.