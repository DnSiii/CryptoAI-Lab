# V99 R106 Phase113 — 8h premium-basis crowding reversal train-only preregistration

Pre-registered **after Phase112 completed** and **before any Phase113 PnL is observed**.

## Evidence permitting this hypothesis
Phase112 established train-only availability/integrity for official Binance USD-M hourly `premiumIndexKlines`: all 48 canonical symbols have data; 61,586 pre-train-end daily archives were inventoried; 2,108 deterministic monthly samples passed SHA256/ZIP/shape/timestamp checks; missing dates are explicit and remain missing. Phase112 computed no return/PnL relationship.

Earlier funding phases (37/42/43/45/46) used the canonical funding-event series. Phase113 is scientifically distinct: it uses the **continuous hourly premium index** itself, which captures intrainterval perpetual richness/cheapness rather than discrete funding observations or a retune of their horizons.

## Frozen hypothesis
Economic mechanism: persistent positive perpetual premium represents crowded/rich long demand and should mean-revert cross-sectionally; persistently cheap/negative premium should mean-revert upward.

Exact specification:
1. Source only official Binance USD-M `premiumIndexKlines`, canonical PIT48 symbols, and timestamps <= registered train end 2024-01-18.
2. Read the hourly premium-index **close**.
3. For every asset/hour compute the simple trailing **8-hour mean** of premium close, requiring all 8 observations. Eight hours is fixed ex ante because it matches the historical standard USD-M funding interval; there is no horizon grid.
4. At each hour independently cross-sectionally robust-standardize the 8h mean using median/MAD, requiring >=10 simultaneous valid assets and MAD > 1e-12.
5. Fixed direction: **negative** robust z-score (short relatively rich premium; long relatively cheap premium).
6. Bound with `tanh`, cross-sectional L1 normalize, fixed alpha gross 0.20.
7. Shift the complete signal exactly one hour (`t-1`) before trading. No same-bar information may enter execution.
8. Severe execution/cost model is the first PnL gate.
9. Selection is chronological train only using the existing temporal folds and `stable_train` criterion.
10. Missing archives/hours remain unavailable. No forward-fill, backfill, interpolation, or cross-asset imputation.

## Archive/reproducibility contract
For efficient deterministic loading:
- use checksum-verified official **monthly** premiumIndexKlines only for complete months ending no later than 2023-12;
- use checksum-verified **daily** archives for 2024-01-01 through 2024-01-18;
- never download a monthly January-2024 archive because it would contain post-train observations;
- clip every parsed row to <= train_end defensively;
- a missing monthly archive may fall back only to the exact audited daily pre-train dates for that month; missing observations are never synthesized.

## Prohibited
No parameter grid, alternative horizon, threshold search, sign flip, rescue pass, fold deletion, cost relaxation, or retuning after result. No holdout download/parsing/summary. No use of Phase113 result to modify V16 Frozen or V99 Frozen.

## Decision
PASS only if the existing `stable_train` gate passes. PASS freezes this exact specification and proceeds to supersevere cost, regime matrix, benchmark envelope and reproducibility checks **before** untouched holdout. FAIL permanently rejects this exact Phase113 hypothesis and moves to a genuinely distinct mechanism.

V16 Frozen and V99 Frozen remain immutable.
