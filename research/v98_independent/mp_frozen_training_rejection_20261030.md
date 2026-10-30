# V98 MP — immutable early-training rejection (2026-10-30)

**REJECT_EARLY_TRAINING; DO NOT RESCUE, RETUNE OR PROMOTE.** MP was preregistered before source/PnL at commit `68b6e1e4b179dbacc3d96ae37f635867c9f838a6`, with a new causal virtual sleeve-productivity allocator. All MP parameters, thresholds, signs, windows, weights and economic gates are frozen. Previous rejected candidates remain rejected.

## Source gate (PASS; not PnL)
[Original source run 41004758690](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41004758690) independently reconciled all 17,544 training-hour target weights and entries (zero mismatches), 27/27 scheduled core refreshes, 9,144 native 8h funding events, zero silent changes and future-mutation causal test. 2023 entries: Opportunity 9, RV 14, Stress 11. 2024: Opportunity 14, RV 14, Stress 12. Source activity is not profit.

## Frozen physical economics (REJECT)
[Original 30-cell run 41004807221](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41004807221): 30/30 physically survived; workflow exit code 2 is the **correct economic rejection**, not a missing job. All values below are 2023–24 training only, initial USD10,000:
- Base full CAGR **72.9884%**, severe **71.6130%**, supersevere **70.239%**. Predeclared base gate required >80%.
- Severe maximum drawdown **29.7682%** (<45% limit), severe turnover **USD214,238.49** (<USD600,000 limit). Both severe annual returns positive: 2023 **+90.5944%**, 2024 **+54.6363%**.
- Marginal log-growth from leave-one-sleeve-out ablations, base: Opportunity **-0.042008**, Relative Value **+0.049879**, Stress/Recovery **+0.025637**. Severe: Opportunity **-0.047317**, RV **+0.044352**, Stress **+0.021645**.
- Opportunity annual marginal 2024: base **-0.048635**, severe **-0.051742**, breaching the preregistered -0.03 annual floor. Severe RV 2024 marginal **-0.001565** remained above the -0.03 floor.
- Full severe CAGR and turnover gates passed, but the **base CAGR** and **Opportunity total/annual marginal** gates failed in both funding orderings. Positive RV/Stress marginal contribution cannot rescue the rejected full MP.

## Independent reconciliation (PASS forensic, NOT economic approval)
[Read-only audit 41004885553](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41004885553): all 30 physical-cell receipts independently reconciled with **zero arithmetic mismatches** and no failed physical cell. Independent source-weight and strategy-to-fill oracle reconstructed **17,543/17,543 original hours**, **zero quantity mismatches**, **114 rebalance events**, 27 mandatory core refreshes and successful synthetic fill-tamper detection. Independent signed funding and hourly PnL accounting also reconciled all 17,543 hours. Original rejection unchanged.

## Critical path and isolation
No V98 complete seven-slot champion is approved. The novel productivity allocator did not prevent Opportunity from harming 2024 compounded growth; this is a **mechanism failure**, not a justification to adjust MP's thresholds/signs/gross after results. A genuinely distinct economic hypothesis is required, not an MP patch. Exact exchange funding-tick `fundingTime,fundingRate,markPrice` records (2,286 per asset, four assets, authenticated source digest) remain unavailable from the blocked official API (HTTP 451 in run 40906303351); SHA-pinned official mark OHLC worst-side envelope remains a conservative alternative, **not exact settlement**. No 2025 separate validation, 2026+ holdout, XRP, V14/V15/V99 benchmark signals, V16/V99 Frozen, paper or live state accessed or modified. No real trading authorized.
