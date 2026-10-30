# V98 NL — immutable 2023–24 training rejection (2026-10-30)

**REJECTED. NO RESCUE, NO RETUNE, NO PROMOTION.** Original preregistration commit `dc25bd21daab9f84cc48901c3c16d07e34b099e0`; original implementation commit `38453732a0b316478574051dfebb5adab0094924`; original CI run https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41093651503; immutable artifact ID `12994444175` (30-cell receipt, 17,543-hour ledger, source/fill/PnL/economic audits).

**Source PASS:** 17,544h Clean-4 Dec-2022..Dec-2024, 9,144 native signed funding events, 53/53 forced core refreshes, zero all-hour independent weight/activity mismatches, zero silent updates, synthetic future-mutation PASS. 2023 weekly Opportunity/RV/Stress 48/53/25; 2024 49/52/32, all above preregistered minima.

**Original physical 30/30 PASS, economic REJECT:** USD10k original full carried-before-fill training 2023–24, official worst-side mark envelope:
- Base CAGR **-1.974%**, turnover **USD500,255.93**, ending equity **USD9,608.85**, signed funding **-USD654.32**, fees **USD200.10**, slippage **USD100.05**.
- Severe CAGR **-6.810%**, turnover **USD473,047**; supersevere CAGR **-11.790%**, turnover **USD445,752**.
- Core-only base CAGR **-1.375%**; removing RV improves full CAGR to **+0.034%**, removing Stress improves to **-0.048%**. Opportunity helped vs its ablation (-4.623%), but cannot rescue the complete system.
- **20 preregistered economic failures** across both funding orders, including base/severe CAGR, severe DD and 2023/24 annual checks, negative RV and Stress marginal contribution. Rejection is final.

**Independent checks PASS as forensic validation, not promotion:** all 17,543 hours signed funding/PnL reconciled to USD9,608.85; 17,543 source-to-fill quantities, 520 rebalance events, zero quantity mismatches; independent 30-cell arithmetic and economic-gate recomputation passed. The original JSON decision token has a cosmetic typo `REJECT_EARLY_TRAINLNG`; the failure list, exit code 2 and independent economic audit establish rejection. Do not modify the rejected candidate merely to fix that spelling.

**Root cause (training only):** high-turnover multi-horizon trend continuation did not compound; core itself lost money, relative-value trend spread and BTC trend-shock overlay had negative marginal growth. This rejects the NL hypothesis, not a mandate to flip signs or optimize its windows post hoc. Next step must be a genuinely distinct portfolio architecture or solve an external source/settlement gate, with pre-result registration.

**Source limitation:** exact exchange funding-event `markPrice` missing from official `/fapi/v1/fundingRate` (HTTP 451). Official 1h mark OHLC and signed rates permit a checksum-authenticated conservative worst-side envelope but not exact tick certification. Required: 2,286 timestamp-matched `fundingTime,fundingRate,markPrice` records per asset with verifiable origin, or independent timestamp-level equivalent. No 2025 validation, 2026+, XRP, Phase083, V14/V15/V99 benchmarks, Frozen or paper/live accessed. Only V98 Independent files changed.
