# V98 PR — permanently frozen historical rejection (2026-11-01)

**Decision: REJECT_PR_TRAINING. NOT a validated V98 engine.** Original preregistration committed as `e8836d6ef462a5f386561d495785c69a2337b052` **before** PR implementation or historical PR PnL. Full physical run [41343484985](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41343484985); its final workflow failure is the **intentional economic rejection gate**, not a missing test. The first pre-PnL attempt failed on a synthetic test bound copied from the earlier template (.82 vs preregistered .84); corrected **before** any source/PnL load, without changing economic thresholds. No further changes to PR signals, costs, weights, signs, windows or gates are permitted.

## Exposed 2023–2025 training results (simulated, not prospective)

| Full PR, carried-before-fill | Base | Severe | Supersevere |
|---|---:|---:|---:|
| CAGR | -3.83% | -6.06% | -8.40% |
| Max drawdown | -25.93% | -28.38% | -30.91% |
| 2023 | -3.71% | -6.29% | -9.00% |
| 2024 | 5.61% | 3.09% | 0.45% |
| 2025 | -12.54% | -14.19% | -15.93% |
| USD turnover from USD10k | 491228.51 | 474937.87 | 458236.99 |

**30/30 physical cells feasible**, but **30/30 binding economic gate failures across two funding orders** (30 individual gate violations, not 30 failed physical cells). All optional modules had **negative net marginal log growth**: base Opportunity -0.05335, RV -0.22010, Stress -0.00146. Raw activations: Opportunity 35, RV 55, Stress 1. Do not reweight/reverse/rescue these rejected PR modules.

**Independent evidence:** scalar independent signal/allocator oracle **0 mismatches across 157 weekly decisions and five recomputed books**; 26,303 hourly independent cash reconciliations, 0 mismatches; 26,303 independent fill/funding reconciliations, 0 mismatches; **60/60** independent receipt arithmetic checks; **30/30** binding gate violations reproduced; **4/4** tamper controls rejected. Frozen raw results: `pr_full_training_frozen_result_20261101.json` and `pr_frozen_independent_receipt_audit_20261101.json`. These attest internal arithmetic, NOT source-perfect execution or profitable live trading.

**Next path:** no V98 complete candidate approved. The authenticated worst-side hourly funding mark envelope permits exploratory training but the **13,524 exchange-origin exact event markPrice values remain missing** (HTTP 451). Required: authorized exchange-origin fundingRate raw pages/export with original URLs, HTTP Date/headers, UTC capture, SHA256 and independent custody verification. Historical account-specific fees, bid/ask/depth/impact and untouched future validation remain unverified. New architectural hypotheses must be genuinely distinct, preregistered, and evaluated as a complete portfolio. No 2026+ training, XRP, Phase083, V14/V15/V99 tuning, V16/V99 Frozen or paper state touched; no real/paper authorization.
