# V98 Independent — AJ frozen historical training economic rejection (2026-10-23)

**Final decision: REJECT_AJ1261_ECONOMIC_GROWTH_OR_MARGINAL.** The AJ seven-slot candidate remains frozen at `f8715ced50d56576bbc88a79bb573e23fb305103`. Do not retune, rescue, or relabel this rejected experiment.

**Evidence:** The original authenticated Dec-2022 warmup / 2023–2024 chronological training run `40019549401` produced all 90 of 90 economic cells successfully in Ubuntu 22.04 and 24.04 (five frozen portfolio/ablation paths × three capitals × three fee modes × two native funding timings). The original final job failed solely at an absolute turnover tolerance of USD 0.00001; it did not invalidate the completed cells. Immutable-artifact-only cross-OS reconciliation `40020654110` succeeded without rerunning strategies or reading 2025. Source manifests, structural fields and economic cells agreed within strict scale-aware numerical tolerance (maximum normalized discrepancy 0.3891 of allowed tolerance; no mismatches).

**Frozen AJ_full, initial USD 10,000, base costs, carried-before-fill:** 2023 net annualized CAGR +0.4934% (NAV USD 10,049.30); 2024 net annualized CAGR -56.0011% (NAV USD 4,414.14). Two-year CAGR **-33.5425%**, net log wealth -0.81777, total max drawdown **67.1368%**, 2024 max DD 63.2032%. Net hourly Profit Factor 2023 1.00097 and 2024 0.85126; positive UTC days 49/365 and 32/366. Realized fees USD 3,840.76, slippage USD 3,840.76, native funding -USD 576.78. These are historical training figures only, not forward performance.

**Preregistered eligibility failed:** AJ_full net log growth in 2024 is negative under base and severe costs and both funding timings; sleeve marginal-growth gates are negative for Opportunity and Stress (RV passes its marginal gate). All 90 cells survived mechanically, but survival alone is insufficient. **Do not open 2025 validation or V14/V15/V99 benchmarks.** XRP, 2026+, contaminated Phase083, V16 Frozen, V99 Frozen and V99 paper remain untouched.

**Critical-path consequence:** Do not spend another cycle repeating synthetic structural tests or changing AJ parameters. The next genuinely distinct complete seven-slot V98 candidate must first address economic compounding and realized turnover/cost drag through a preregistered architecture, then run authentic chronological training and separate validation. No claim of a working profitable engine is justified by AJ.

Official original run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40019549401
Immutable reconciliation: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40020654110
