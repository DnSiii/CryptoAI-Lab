# V98 Independent BV — immutable original 2023–2024 training rejection (2026-10-24)

**Decision: REJECT_BV_HISTORICAL_GROWTH_OR_MARGINAL.** The preregistered 336h periodic BTC/ETH momentum reentry portfolio with distinct BNB/SOL satellites is permanently rejected. It is not a validated champion, paper engine or live engine. Do not rescue by changing periods, thresholds, signs, leverage, friction, funding order, ablations or economic gates after observing results.

## Original preregistration and reproducible evidence

- [Preregistered original architecture](bv_preregistered_architecture_20261024.md) committed before BV source implementation and before any BV PnL.
- [Original 90-cell official run](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40089713051), source fix was mechanical `source_bundle` import/OS name substitution only, before historical run; no economic adjustment.
- **90/90 physical training cells survived** (five paths × three capitals × three fee tiers × two native funding orderings), Ubuntu 22.04/24.04 reconciled. Independent artifact-only arithmetic audit checked **180/180** receipts with zero errors.
- Independent event-level replay passed: **65,088 hourly settlements**, native signed funding and all **81 OHLC corners** per hour. The full pinned source has 9,144 authenticated funding events; executed-window replay has 8,136 event rows per case. These are accounting and feasibility checks, **not** evidence of investment edge.
- Only authenticated pinned Clean-4 BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT Binance USD-M 1h Dec2022–Dec2024. 2025 untouched, 2026+ forbidden, XRP quarantined, Phase083 holdout contaminated. No V14/V15/V99 external benchmarking. V16 Frozen, V99 Frozen, V99 branch/workflows/reports/paper untouched.

## Original complete portfolio USD10k, carried-before-fill, TRAINING ONLY

| Cost tier | 2023 CAGR | 2024 CAGR | Two-year CAGR | Max DD | Turnover USD | Physical fill hours | Forced ratchets |
|---|---:|---:|---:|---:|---:|---:|---:|
| Base | +20.276% | +17.445% | **+18.850%** | 15.814% | 850,159.11 | 106 | 30 |
| Severe | +4.67% | **−1.06%** | **+1.76%** | 22.53% | 721,668.87 | 106 | 30 |

Base explicit fees **USD425.08** plus slippage **USD425.08**, native signed funding **−USD266.12**. Both base annual growth gates passed; **both severe funding-order growth gates failed** due to 2024 net loss. Cost-sensitive execution churn is material.

## Original full-minus-ablation marginal annual log growth (USD10k)

| Sleeve | 2023 base | 2024 base | 2023 severe | 2024 severe |
|---|---:|---:|---:|---:|
| Opportunity | **−0.017475** | +0.017297 | **−0.030232** | +0.003819 |
| Relative Value | **−0.011222** | **−0.035457** | **−0.022260** | **−0.038067** |
| Stress/Recovery | +0.098623 | **−0.032283** | +0.091914 | **−0.040308** |

All three strict positive-marginal gates failed under the precommitted annual/fee/order grid. No isolated favorable year can rescue BV.

## Physical/economic diagnosis and decision

The original BV_core_only path earned +18.51% two-year base CAGR (2023 +18.74%, 2024 +18.29%) but fell to +6.30% under severe costs, with **57 physical fill hours, 21 risk ratchets and USD625,496 turnover** at USD10k initial capital. BV_full had **106 fill hours, 30 ratchets and USD850,159 turnover** at base. Periodic reentry restored participation versus BU's one-time inactive core, but substantially increased churn and friction. Original BV_full 2024 severe remained negative; Opportunity, Relative Value and Stress did not satisfy robust positive marginal contributions.

Next architecture must address **turnover caused by repeated physical risk ratchets and inventory replacement**, not simply increase rebalance frequency, decrease fees in the model, or revive rejected BV components. Any new candidate must have an independently preregistered structural hypothesis and full physical/accounting/economic validation. No 2025 holdout access until internally frozen and separately validated; no real trading.
