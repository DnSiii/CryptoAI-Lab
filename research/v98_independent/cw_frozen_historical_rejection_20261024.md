# V98 Independent CW — frozen 20-cell historical economic rejection (2026-10-24)

**Decision: REJECT_CW_HISTORICAL_GROWTH_OR_MARGINAL.** CW is permanently rejected; no post-result changes to signs, thresholds, windows, budgets or gate definitions and no cosmetic rescue.

## Verified evidence
- Preregistration commit `88baf153c2f6c6204b38421e965a8f9f71f30013` predates CW source and PnL.
- Official pinned Clean-4 native 2022-2024 source and 20-cell economic run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40148107038 . Audit artifact is named `cw20-official-economic-summary`.
- Source-only activity gate **passed** in 2023/2024. Effective epochs: Growth 19/17, Opportunity 51/52, Relative Value 43/47, Stress/Recovery 25/23. Causal static perturbation passed.
- Five full/ablation paths x USD10k x base/severe x two funding orders, reproduced on Ubuntu 22.04 and 24.04: **20/20 physical cells survived**, cross-OS reproducible true, independent artifact-only audit errors=[].
- Full base two-year historical CAGR **+39.2020%**, severe **+28.3615%**. Base annual returns 2023 **+40.9437%**, 2024 **+37.5441%**; severe 2023 **+29.9196%**, 2024 **+26.8654%**. Base maximum drawdown **24.9902%**, severe **29.1502%**.
- Native signed funding cashflow base **-$1,583.77**, severe **-$1,418.67** from initial USD10k.
- Positive annual net log growth in both years across all fee/funding-order cells **passed**; strict full CAGR >50% base and >30% severe **failed**; all three satellite annual marginal contribution gates **failed**: Opportunity false, Relative Value false, Stress/Recovery false.
- This audit is artifact-only and cross-OS, **not** independent event-level replay. No capacity USD1m/USD10m, supersevere, independent event-level audit, untouched 2025 validation, external benchmark or paper/live trading authorized.

**Firewall:** 2025 holdout not opened, 2026+ excluded, XRP quarantined; V16/V99 Frozen and V99 research/workflows/reports/paper unchanged.

**Critical-path finding:** active satellites are not enough. CW's volume-lead relative-value and breadth-state protection did not provide robust positive incremental annual portfolio log growth despite fully operational native execution. Next work should seek economically orthogonal marginal contributions with a preregistered system-level hypothesis, not rescue CW.