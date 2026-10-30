# V98 Independent CG — FROZEN historical training rejection, 2026-10-24

**Decision: REJECT_CG_HISTORICAL_GROWTH_OR_MARGINAL.** No approved V98; no future validation, external benchmark, paper/live order or real PnL claim. CG original alpha signals, funding filters, windows, budgets, risk buffer and cost tiers are frozen rejected; no rescue by post-result threshold/sign/gross adjustment.

## Immutable evidence and chronology

- Preregistration **before any CG economic execution**: commit `da35a1d884ba2add92a69cc40c15fc460f9f353a`, `cg_preregistered_cross_sectional_carry_20261024.md`.
- Source implementation: `f4a3b9f261e8e1b99f0fe3d36a5e5aa4e16abd03`; original physical engine and independent replay isolated under CG namespaced files, first economic workflow commit `c2e103c3cca70ba096fc925b19e4219dbb415330`.
- [Original official CG full 90-cell training, two Ubuntu OS, economic reconciliation and independent replay](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40118160614): **90/90 physical cells survived**, cross-OS numerical reconciliation true, zero audit errors. Independently reconstructed six USD10k full-case funding/order/fee cashflows with **10,773 settled hours per case**, **872,613 actual 81-corner checks per case** (not 872,613 trades). Max independent cash/funding discrepancies **0**.
- [Separate frozen-source activation audit](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40118390560) uses unchanged CG source and original pinned Clean-4. It was executed *after* rejection to diagnose absent marginal sleeves; not a CG retune.
- Data: original pinned 2022-12 through 2024-12 Clean-4 Binance USD-M 1h BTC/ETH/BNB/SOL and signed native funding. 2025 untouched; 2026+ forbidden, XRP quarantined, old Phase083 ineligible. V14/V15/V99 benchmarks, V16/V99 Frozen and paper not accessed/modified.

## USD10k CG full, carried-before-fill, 2023–2024 training ONLY

| Measure | Base | Severe |
|---|---:|---:|
| 2023 net return | +100.7884% | +93.9658% |
| 2024 net return | +4.7133% | +1.1645% |
| Two-year CAGR | **+44.9639%** | **+40.0479%** |
| Maximum drawdown | 37.5130% | 38.1262% |
| Native signed funding | -USD1,698.24 | -USD1,609.03 |
| Fees + slippage | USD248.52 | USD1,183.81 |
| Turnover | USD248,518.35 | USD236,761.15 |
| Actual nonzero-turnover hours | 50 | 50 |
| Forced risk ratchets | 0 | 0 |
| Peak gross / NAV | 0.7835 | 0.7782 |
| Net hourly PF | 1.0386 | 1.0354 |
| Net hourly payoff | 0.9983 | 0.9963 |
| Net hourly win rate | 50.99% | 50.96% |
| Positive UTC days | 233 / 731 | 231 / 731 |
| Hourly 1% CVaR | -1.8138% | -1.8004% |

The original annual growth gates pass in both fee/funding orders and severe drawdown <45% passes. However the preregistered **base CAGR >50% gate fails**. The complete CG is therefore rejected independently of the satellite failures.

## Original full-minus-ablation marginal annual net log-growth (USD10k, carried-before-fill)

| Sleeve | 2023 base | 2024 base | 2023 severe | 2024 severe |
|---|---:|---:|---:|---:|
| Opportunity | 0.000000 | +0.002101 | 0.000000 | +0.002077 |
| Relative Value | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| Stress/Recovery | -0.015581 | +0.036459 | -0.023585 | +0.035475 |

All three original marginal gates **fail**. Values shown as zero for RV are numerical zero within floating precision, not proof of a profitable sleeve. Stress hurts net compounded wealth in 2023 despite helping 2024. No module may be transplanted as a rescue of rejected CG.

## Original causal activation audit — source-level mechanism, not inferred from PnL

- **2023:** Growth Core nonzero 8/15 scheduled epochs; Opportunity **0/22**; Relative Value **0/11**; Stress signal 5/22 (4 epochs with positive router budget).
- **2024:** Growth Core 11/17; Opportunity 2/26 (both BNB); Relative Value **0/13**; Stress 1/26.
- Thus Opportunity and RV's zero marginal is directly explained by **no eligible signals in the respective years**, not by hidden exchange fills or merely a risk-governor cap. Original CG preregistered filters were too restrictive to generate a meaningful sleeve in both years. This is a diagnostic for *future distinct* hypotheses, not permission to loosen CG thresholds after results.

## Critical path for next genuinely distinct architecture

Require independently justified economic roles and **preregistered source-level activation viability** before spending on another complete 90-cell run, without tuning old rejected CG thresholds to sample outcomes. Avoid sparse all-or-nothing gating that leaves a named slot inactive for entire chronological years. Then demand net positive full-minus-ablation contribution, annual net growth, high CAGR, native funding/cost stress, realistic physical capacity, independent replay and future holdout before any benchmark. Preserve V16/V99 Frozen and V99 paper. No delivery claim until those gates actually pass.
