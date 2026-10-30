# V98 Independent BM — immutable historical rejection (2026-10-24)

**Decision: REJECT_BM_HISTORICAL_GROWTH_OR_MARGINAL.** BM and its ablations are rejected as candidates; no after-the-fact rescue of sign, thresholds, windows, budgets, gross exposure, fees, or funding order. No ablation promotion.

**Frozen pre-result architecture and source:** `bm_preregistered_architecture_20261024.md`, source/allocator/engine at commit `1e9d7374b9269a8a991e67942e7b1a730bf3c1d3`. The only later changes corrected the audit report's accidental string-replacement typo (reproducibme/BMOCK) without altering the source, allocator, governor or economic receipts. Original training run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40071731297 . Corrected **audit-only** of those exact original receipts: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40071976005 . Event-level independent replay: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40071822773 .

**Historical training only:** pinned Clean-4 BTC/ETH/BNB/SOL USD-M 1h Dec2022–Dec2024, 2023 and 2024 evaluated chronologically, native signed funding, actual-next-open execution. 90/90 physical scenarios survived (five paths, three capitals, three friction levels, two funding settlement orders); two-OS reconciliation 90/90 with zero discrepancies beyond declared numerical tolerance. Independent original-artifact arithmetic audit: 180/180 receipts, zero errors. This proves neither future generalization nor superiority.

**USD 10k full BM, base, carried-before-fill, 2023–2024:** two-year CAGR **+28.6373%**, 2023 annualized **+85.9198%**, 2024 annualized **−10.9066%**; max drawdown **31.2175%**; turnover **$964,998.99**, fees **$482.50**, slippage **$482.50**, signed native funding **−$1.39**. Hourly net Profit Factor **1.04767**, payoff **0.99844**, win rate **51.203%**, positive UTC days **142/731** (2023 54/365; 2024 88/366). Severe carried-before-fill two-year CAGR **+16.4342%**, 2023 **+69.5623%**, 2024 **−19.9654%**. Full-system annual growth gates failed all four required base/severe x funding-order combinations.

**Full-minus-ablation marginal annual net log growth [2023, 2024], immediate $10k carried-before-fill:**
- Opportunity: base **[+0.051013, −0.092991]**; severe **[+0.035015, −0.112182]** — FAIL.
- Relative Value: base **[+0.015259, +0.016605]**; severe **[−0.002323, +0.013603]** — FAIL.
- Stress/Recovery: base **[+0.135951, −0.011120]**; severe **[+0.113731, −0.054027]** — FAIL.

**Independent event replay added and passed:** a separate auditor rederived cashflows, fees, turnover, native funding and all 81 intrabar margin corners from pinned raw arrays for **16,272 executed hours per case** in four full-system immediate base/severe x funding-order cases (**65,088 hourly replays**, **8,136 native funding slots per case**). Source has **9,144 total native events** including pre-execution warmup. Original ledger's 2023–24 cashflow identities matched independently; event audit does not certify price-tick ordering inside each OHLC hour or 2025 holdout performance.

**Structural diagnosis:** BM's volatility-compression opportunity and diversified crisis short improved 2023 but damaged 2024; cross-sectional rotation lost marginal growth under severe 2023 costs. The composed engine lost in 2024 despite a positive two-year CAGR. A physically safe, arithmetically reproducible strategy with positive training CAGR is not an approved V98.

**Firewalls:** no 2025 holdout accessed, no 2026+ market data accessed, XRP quarantined, Phase083 excluded; V14/V15/V99 not consulted; V16/V99 Frozen, V99 workflows/reports/research/paper untouched. No live trading or future performance claim.

**Next critical path:** a genuinely distinct preregistered seven-slot architecture must achieve positive *full portfolio* annual growth and positive *marginal* annual growth under severe costs, then independent future validation and external benchmark only after freeze. Do not retune or revive BM.
