# V98 PK frozen historical rejection — 2026-11-01

**Decision: REJECT_PK_TRAINING (permanent; no post-result rescue).** Original preregistration `pk_premium_dislocation_prereg_20261101.md` committed **before** implementation and economic execution. Frozen receipt: `pk_full_training_frozen_result_20261101.json`. Run [41303578081](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41303578081) with full receipt artifact `13082158901`; independent audit artifact `13082585234`. Workflow's final failure is intentional enforcement of the economic rejection, not an accounting or source failure. Earlier run `41303558103` failed at source asset ordering before PnL; corrected solely alphabetical CSV ordering to canonical Clean-4 positions before successful run.

## Measured exposed-training-only physical result
30/30 physical cells feasible, 157 weekly decisions, 26,303 hourly cash reconciliations, 13,524 native funding events (hourly worst-side mark **envelope**, not exact event marks). Independent scalar signal+allocation oracle: **0 mismatches**; 60/60 independent receipt arithmetic checks; four receipt tamper cases detected; all 16 economic gate failures independently reproduced. Premium source 108,192 authenticated hourly asset rows with pinned SHA256 `c301a38642f229ca2746ae33baaf58e4bb21ac280a1a99dbbc328cc074caaad4`, only closed premium bar t-1 used.

| Full portfolio, carried-before-fill | Base | Severe | Supersevere |
|---|---:|---:|---:|
| CAGR simulated | +46.50% | +41.52% | +36.36% |
| Maximum drawdown | -23.97% | -24.77% | -25.61% |
| 2023 | +113.47% | +105.42% | +97.10% |
| 2024 | +38.89% | +34.29% | +29.52% |
| 2025 | +6.07% | +2.77% | -0.66% |
| Turnover USD from USD10k start | 1,678,610 | 1,579,269 | 1,480,440 |

Funding orders produced the same rounded metrics. Hourly NAV-change PF base **1.0450**, hourly win rate **51.72%** (NOT trade-level win rate). 139 net fill events, independent fill/cost/funding mismatches **0**.

## Binding failure diagnosis
Base CAGR <80% and severe CAGR <60%; base/severe turnover >USD1m; Relative Value leave-one-out log marginal **+0.01319 base / +0.01256 severe**, below preregistered +0.02; Stress/Recovery **zero** gross activations and zero marginal; Opportunity **four** raw activations, log marginal **+0.05716 base / +0.05541 severe**. Relative Value had only **one** raw activation. The composition is **not** a complete passing seven-slot engine despite favorable simulated headline CAGR. Exactly **16** binding failures across both funding orders. No parameters or signs changed after seeing results.

## Next architectural hypothesis boundary
Do **not** resurrect PK by changing its threshold, leverage, gross, funding order, or slot sign. A distinct, preregistered **realized-funding carry versus premium-persistence** mechanism may be investigated independently, with economic source-of-return attribution and nonzero optional module contribution. The core challenge remains compounded net wealth under costs, not merely low drawdown. Historical results cannot be described as prospective validation or external superiority.

## Blocking independent evidence
Exact exchange-origin 13,524 funding-event `markPrice` records (symbol, fundingTime, fundingRate, markPrice, raw response and headers, UTC pagination, SHA256, authorized provenance) remain unavailable due HTTP 451. Authorized exchange-origin export with independent verification is an alternative. Premium-index candles are not funding settlement ticks. Untouched forward validation/final holdout also absent; no V14/V15/V99 benchmarks accessed, no V99/Frozen/paper changes and no live authorization.
