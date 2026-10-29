# V98 Independent KS — permanently frozen training rejection (2026-10-29)

**Decision: REJECT KS PERMANENTLY.** KS preregistration commit `ac2357da559bcfc48c76ad05babdd9875a7b9be1` precedes source, PnL and economic runs. The 168-hour realized-volatility source window was corrected *before* any source/PnL result to match preregistration. No post-result signal, threshold, sign, weight, funding, window, gross or ablation rescue. **KS is not a V98 champion; no live trading.**

## Source and causality
[Authenticated KS source + historical future-mutation gate 40814779486](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40814779486): 18,288 pinned Phase243 Clean-4 hourly observations Dec-2022 warmup, 2023–2024 training, native signed 8h funding, manifest SHA256 `3270021b228825dbce3e56e80f3020f6cf6a1154574b472a062447a64daaf515`. All source and t-1 causal gates passed, no invalid-source entries or silent row rebalance. Source starts by year: Opportunity 36/29, Relative Value 24/11, Stress/Recovery 10/13 (2023/2024). These are source events, not fills or PnL.

## Complete historical physical and independent verification
[KS 30-cell original execution and audits 40814872078](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40814872078): five separately financed books x 3 native fee tiers x 2 funding orders x 2 Ubuntu OS. **30/30 physical cells survived**, original **60/60 receipts** independently audited, **5/5 every-settled-hour independent 81-corner ledger oracles** completed, cross-OS reproducible; these establish mechanical correctness, not economic acceptance. All historical numbers below are 2023–2024 training only, initial USD10,000, carried-before-fill.

| Metric | Full base | Full severe |
|---|---:|---:|
| CAGR (2023–2024) | +76.5672% | +63.3190% |
| 2023 net return | +189.6515% | +170.2094% |
| 2024 net return | +7.7165% | **-1.2211%** |
| Max drawdown | 35.6254% | 37.5936% |
| Turnover | **USD832,024.69** | **USD759,034.17** |
| Native signed funding | -USD2,180.70 | -USD1,993.74 |
| Fees + slippage | USD832.02 | USD3,795.17 |
| Peak gross / NAV | 88.9991% | 89.2624% |

**Independent original-receipt marginal net log-growth (Full minus ablated, base/severe):**
- Opportunity **+0.09777 / +0.03929**: passed both preregistered marginal gates, but did not save the complete system.
- Relative Value **-0.08745 / -0.09097**: failed both; low-volatility pair does not have positive marginal wealth.
- Stress/Recovery **-0.02340 / -0.03178**: failed both; crisis hedge was economically harmful over these training folds.

**Economic rejection:** severe 2024 negative, both base and severe turnover >USD600k, and Relative Value and Stress/Recovery negative marginal contributions. All three were hard preregistered gates. High CAGR alone cannot override them. The independently financed Core-only book showed +75.5470% base / +69.2390% severe CAGR, but this is **not a promoted or approved system** and must not be cosmetically reassembled from failed KS ablations.

## Independent cost attribution, no alpha rerun
[Frozen original-receipt forensic 40815105643](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40815105643) independently read the ten original book artifacts, quantified funding, fees, slippage and marginal turnover, and confirmed the rejection without modifying alpha or replaying PnL. Relative Value negative despite saving USD56,119 base turnover vs the minus-RV book; it failed for economic contribution, not solely friction. Opportunity added USD360,000 base turnover and USD312,611 severe turnover while contributing positive net marginal growth; full system still breached the turnover gate.

## Strict next critical path
Reject KS and do **not** salvage its Core, Opportunity, low-volatility spread, crisis overlay, or threshold by ablation-based selection. Investigate a genuinely distinct source of positive marginal growth in both Relative Value and Stress/Recovery, and low-turnover execution, with a new preregistered complete engine. No 2025 validation, future holdout, Phase083, external V14/V15/V99 internals, Frozen, V99 branch/workflows/reports/paper or real trading touched.
