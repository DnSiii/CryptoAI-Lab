# V98 Independent — AL complete 90-cell historical rejection (2026-10-23)

**Final irreversible decision: REJECT_AL_HISTORICAL_GROWTH_OR_MARGINAL.** Do not rescue AL with sign, window, threshold, leverage, fee, cost or ablation selection. Official GitHub Actions: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40029261169, launch SHA `60109f36cea6232582401b8e57fad84b60131773`. Frozen AL blob SHAs are in `al_pre_economic_freeze_20261023.md`.

**Authenticated scope:** original Clean-4 BTC/ETH/BNB/SOL, Dec-2022 warmup and 2023/2024 only, 9,144 native funding events and pinned mark/quote archives; no 2025 validation, 2026+, XRP, Phase083 or external V14/V15/V99. 5 full/ablated paths × 3 capitals × 3 cost levels × 2 funding orderings = **90/90 mechanically survived**. All ten independent Ubuntu 22.04/24.04 training jobs and cross-OS numeric reconciliation **PASSED**, max normalized numeric delta 0.000231 of permitted tolerance.

**Frozen AL_full, USD 10,000, base costs, carried-before-fill native funding:**
- 2023 CAGR **+113.6335%**, 2024 CAGR **+0.9354%**, combined two-year CAGR **+46.7688%**.
- Max DD **48.4105%**; hourly net PF **1.026409**, hourly payoff **0.970667**, hourly win rate **51.3956%**, positive UTC days **208/731**.
- Max gross/NAV **1.430335**, peak single-asset gross concentration **100%** (when only one position active).
- Turnover **USD 3,868,563.74**, fees **USD 1,934.28**, slippage **USD 1,934.28**, native funding **-USD 2,999.18**.

**Severe costs:** two-year CAGR **+2.4419%** but 2024 CAGR **-39.582%**, DD **65.32%** (carried-before-fill). Alternative funding order: 2024 **-38.952%**. **Supersevere:** combined CAGR **-62.187%**, 2024 **-84.893%**, DD **87.94%**. These fail preregistered growth and survival-quality gates. All numbers are historical training, not future validation or live returns.

**Sleeve marginal log-growth (AL_full minus ablation, USD10k, carried-before-fill):**
- Opportunity: base 2023 **-0.157412**, 2024 **-0.012711**; severe 2023 **-0.125762**, 2024 **-0.002415** → **FAIL**.
- Relative Value: base 2023 **+0.096475**, 2024 **+0.027317**; severe 2023 **+0.203530**, 2024 **+0.108779** → **PASS**.
- Stress/Recovery: base 2023 **-0.025089**, 2024 **-0.032352**; severe 2023 **-0.026019**, 2024 **-0.049425** → **FAIL**.

**Critical-path conclusion:** AL is not the finished V98. Growth under severe costs, positive-day consistency, concentrated risk and Opportunity/Stress marginal wealth fail. Diagnostic ablations are not replacement champions. The next hypothesis must be a **genuinely distinct complete seven-slot portfolio** with stronger net growth and cost resilience; no tuning AL or using untouched validation to select it. V16 Frozen, V99 Frozen/research/workflows/paper remain unchanged.
