# V98 Independent — Phase206 mechanical audit

Decision: **REJECT_FAMILY_NO_RESCUE**

Deterministic payload SHA256: `675a59ece03b654326eb8e133b8669a1a49db9e2ee127f94cafacb38d332557e`

Mechanical gate: every 2023/2024/2025 base fold must have return > 0 and PF > 1; severe/supersevere are reported independently and are not used to rescue a failed base fold.

| spec | base 3/3 | severe 3/3 | super 3/3 | base returns 23/24/25 | base PF 23/24/25 | worst MDD | max conc | worst p01 | trades |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| lb30d_z1p5_h24 | False | False | False | 0.274 / -0.122 / 0.003 | 1.069 / 0.980 / 1.005 | -0.236 | 0.438 | -0.137 | 1268 |
| lb30d_z1p5_h8 | False | False | False | 0.171 / -0.167 / -0.058 | 1.071 / 0.951 / 0.981 | -0.198 | 0.503 | -0.069 | 2261 |
| lb30d_z2p5_h24 | False | False | False | 0.186 / -0.027 / -0.017 | 1.104 / 0.992 / 0.991 | -0.132 | 0.431 | -0.112 | 435 |
| lb30d_z2p5_h8 | False | False | False | 0.079 / -0.159 / 0.012 | 1.083 / 0.864 / 1.022 | -0.200 | 0.653 | -0.070 | 695 |
| lb90d_z1p5_h24 | False | False | False | 0.247 / -0.206 / -0.075 | 1.073 / 0.960 / 0.985 | -0.264 | 0.401 | -0.132 | 1045 |
| lb90d_z1p5_h8 | False | False | False | 0.170 / -0.155 / -0.008 | 1.082 / 0.957 / 1.000 | -0.180 | 0.364 | -0.075 | 1970 |
| lb90d_z2p5_h24 | False | False | False | 0.115 / -0.161 / -0.009 | 1.075 / 0.931 / 0.996 | -0.195 | 0.508 | -0.137 | 404 |
| lb90d_z2p5_h8 | False | False | False | 0.084 / -0.068 / 0.009 | 1.097 / 0.956 / 1.018 | -0.114 | 0.493 | -0.071 | 667 |

## Integrity / anti-overfit notes

- This audit evaluates all eight frozen specs; it does not add thresholds, invert signals, select assets, or gate regimes.
- Validation/final holdout remains unopened.
- Regime, concentration and complete-trade tails remain diagnostic only; isolated pockets cannot rescue a failed family.
- Funding source timestamps are causally restricted to <= t-1 by evaluator invariant.

Base-fold-stable specs: 0/8.
