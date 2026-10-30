# V98 NK — immutable original 2023–24 training rejection (2026-10-30)

**REJECT_EARLY_TRAINING. PERMANENT. NO RETUNE/RESCUE.** Original preregistration `36a9abe1be1483b479037e13bb257509d6af1171`, source/strategy/physical SHA `6f6c49df7a40062d02ba0c18380766b53baad0f2`. A single technical import-identifier typo was fixed before any real source or PnL result, without changing any signal, weight, threshold, or economic gate. Original complete run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41084687737, artifact ID `12991795180`.

**Source PASS:** authenticated 17,544h Clean-4 2022-12..2024-12, 9,144 native signed funding events, 53/53 core refreshes, zero all-hour independent weight/activity mismatches and zero silent changes; causal future-mutation PASS. 2023 active weekly Opportunity/RV/Stress=53/53/11; 2024=51/52/12. No 2025 or future holdout.

**Physical 30/30 PASS, ECONOMIC REJECT:** both funding orders and all five books x three cost tiers physically valid. Original full carried-before-fill USD10k:
- Base CAGR **+15.8340%**, final **USD13,420.21**, DD **-45.2802%**, turnover **USD570,518.29**, funding **-USD860.37**; 2023 +26.20%, 2024 +6.34%.
- Severe CAGR **+11.4820%**, final **USD12,430.10**, DD **-46.4044%**, turnover **USD547,593.35**, funding **-USD821.35**; 2023 +21.60%, 2024 +2.22%.
- Supersevere CAGR **+6.9846%**, final **USD11,446.76**, DD **-47.5870%**; 2024 -2.03%.
- Base marginal log growth Opportunity **+.015353** (<+.020 gate), RV **-.037020**, Stress **+.064978**; severe Opportunity **+.006197**, RV **-.037710**, Stress **+.062815**. **22 immutable economic gate failures**, including both base/severe CAGR, severe DD, Opportunity/RV marginals and annual marginal checks. No promotion.

**Independent audits PASS as forensic checks of a REJECTED engine:** 17,543 original hourly funding/PnL ledger entries reconciled to exact USD13,420.21, 17,543 causal source-to-net-fill quantities with **zero mismatches** and tamper detection, 30/30 cost arithmetic cells and 22 original rejection reasons independently recomputed. True UTC daily positive **347/731** base; hourly net PF **1.01619**, payoff **1.01457**, win rate **50.04%**, daily 1% CVaR **-5.7465%**. These hourly metrics are not trade-level statistics.

**Immutable receipts:** 30-cell JSON SHA256 `82328e5d2ade8099c7cbb363a5f5c259444d175aefd0e901ebc6e7d7d34ceda1`; 17,543-hour JSONL SHA256 `0981e7613b24c0a8b4d63f903d9ddf45041cb6af3805e8453f92c2cfbbfc2add`; independent arithmetic JSON SHA256 `f091610fe196e8d3673a2bd96cb73764d688d0de7c779ea2bd76c24eafe00286`. The original runner's JSON decision string has a **cosmetic transcription typo** `REJECT_EARLY_TRAINKNG` (instead of `REJECT_EARLY_TRAINING`); independent auditor confirms the immutable rejection, and no strategy/execution re-run is authorized.

**Scope:** exact funding-tick markPrice still missing due exchange API HTTP451; official signed funding rates and conservative worst-side OHLC envelope are independently attested. Only V98 Independent files modified; no 2025 validation unsealed, no 2026+, XRP, Phase083, external benchmarks, Frozen, V99 or paper/live state touched.
