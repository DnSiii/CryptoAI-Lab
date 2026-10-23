# V98 Independent AP — frozen official 90-cell rejection (2026-10-23)

**Decision: REJECT_AP_HISTORICAL_MARGINAL.** No retuning AP, promoting AP_core_only, deleting weak sleeves, or choosing favorable cost/year/order. Official preregistered source+workflow at SHA `40dc5878a136c016e2d629fb9d65f9097b74dbd8`; run https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40036125324. Authenticated Clean-4 2023/24 with Dec-2022 warmup and native 8h funding/mark bounds. No 2025/2026+, XRP, Phase083, V14/V15/V99, Frozen or paper.

**Reproducibility/survival:** 90/90 funded historical cells mechanically survived, ten Ubuntu 22.04/24.04 training jobs and independent numerical reconciliation PASS; max normalized cross-OS delta 0.000165 of permitted tolerance. This is NOT a system approval.

**AP_full USD10k base, carried-before-fill:** 2023 CAGR **+150.1416%**, 2024 **+34.1621%**, 2y **+83.1145%**, max DD **45.0016%**, native funding **-USD5,214.18**, fees **USD173.74**, slippage **USD173.74**, turnover **USD347,470.45**, 823 nonzero-turnover hours. Hourly PF 1.02699, payoff 0.97776, win rate 51.228%, positive days 333/731, gross/NAV max 1.41684, largest single-asset concentration 49.10%, hourly 1% CVaR -2.8775%. Severe costs: 2023 +145.255%, 2024 +28.527%, two-year +77.465%; supersevere: 2023 +129.246%, 2024 +18.358%, two-year +64.647%. All are in-sample 2023/24 training, not future validation or trading performance.

**Growth gates:** base and severe annual positive under both native funding orderings **PASS**.

**Full-minus-ablation marginal net log wealth (USD10k base, carried-before-fill):**
- Opportunity: 2023 **-0.000937**, 2024 **-0.036572** → FAIL.
- RV: 2023 **-0.010450**, 2024 **+0.008411** → FAIL.
- Stress: 2023 **-0.013924**, 2024 **+0.000585** → FAIL.
- Severe marginal: Opportunity 2023 -0.000558 / 2024 -0.041341; RV -0.005514 / +0.008458; Stress -0.014265 / +0.000506. All fail the preregistered both-year requirement.

**Interpretation:** the structurally diversified core generated unusually strong two-year training growth even after severe costs, but the *composed* AP engine is NOT qualified: all three overlays fail robust positive marginal contribution. AP is permanently rejected. Next architecture must make incremental net-wealth decisions at the portfolio level, not just require positive standalone virtual sleeve wealth. A distinct new hypothesis may reuse only common independent mechanical accounting, never tune/relabel AP results. Holdout sealed.
