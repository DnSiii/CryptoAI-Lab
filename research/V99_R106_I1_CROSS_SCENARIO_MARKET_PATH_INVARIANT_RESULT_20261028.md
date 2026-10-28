# V99 I1 — cross-scenario common original market-path invariant: verified result (2026-10-28, 11:57 BRT)

**Decision: SOURCE_ONLY/HOLD — NO PROMOTION.** This corrects a concrete accounting-integrity vulnerability, not a profitable or source-certified options strategy.

## Observed defect, fixed before numerical replay
The original 661-day severe/supersevere native-coin replay allowed distinct cost-dependent exposure paths (correct) but failed to enforce identical *market observations* when both paths referenced the same event. An adversarial journal could substitute a different option contract/quote or delivery index in one scenario, creating fictitious relative returns while retaining valid daily underlying indices and balanced internal accounting.

Ex ante rules were committed **before** implementation: [preregistration 8f00e6d](https://github.com/DnSiii/CryptoAI-Lab/commit/8f00e6d1b91d1dc261ba5c1333513cec9b9895b2).

Implemented a fail-closed common-market-path check in `research/tools/v99_r106_i1_native_event_equity.py`:
- Both scenarios OPEN same asset/week => same **full** original candidate Quote inventory, including symbols, prices, sizes, venue/arrival timestamps, expiry and index; different modeled costs and scenario risk vetoes remain allowed.
- Both scenarios MARK same exact short/long contract pair at same clock => same original two-sided book.
- Both scenarios settle same asset at same contractual expiry => identical delivery index, regardless of fee or position-ID differences.
- Intra-scenario repeated market observation with conflicting values is also rejected. All checks run before NAV; common daily BTC/ETH index and passive benchmark checks remain intact.

Added an **independent** oracle in `research/verification/independent_v99_r106_i1_market_path_oracle.py` without importing the production replay. The integrated original-signal/BBO-to-numeric runner now calls this oracle **before** source-byte identity and provisional NAV. It reports counts of common original observations as integrity metrics only, never as exchange attestation.

## Actual CI execution and decision
- [Native event replay Actions 40710868534](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40710868534): **SUCCESS, 22/22 tests**. Adversarial substitution of a selected OPEN strike, MARK ask, and delivery index was rejected; a legitimate severe OPEN / supersevere CASH exposure divergence remained accepted. Original official economic gate still refused uncertified source.
- [Original-to-provisional integrated Actions 40710877383](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40710877383): **SUCCESS, 9/9 tests**. Original BBO tampering was changed in **both** synthetic scenarios to ensure the separate original-source-byte audit (rather than merely scenario parity) still rejects it. Independent market-path oracle rejected manipulated MARK and delivery index.
- In the actual nonfixture GitHub CI attempt, original archived causal signal receipt reproduced **182/182** observations, **180/180** fixed intents, **132** positive. Source access stopped exactly at `ORIGINAL_661D_MANIFEST_NOT_DELIVERED`. **0/180** original option lifecycles economically certified. No historical NAV, ROI, native economic TRAIN or paper PnL produced.
- CI workflow files now require the preregistration commit to be an ancestor and trigger on independent oracle changes. A superseded integration run failed because its old BBO-falsification test expected the *later* source gate; the test was corrected to alter both scenarios equally and the final CI passed. No protection was weakened.

## Remaining critical path
**External:** lawful complete Deribit BTC+ETH original OPTIONS BBO/size/venue+arrival capture for **2021-12-09..2023-09-30**, independent original index/delivery receipts, dated native contract-size/fee-tier/margin/liquidation terms, and conservative size-aware simulated execution evidence. An actual trade fill record is not a prerequisite for an untraded backtest; authentic executable quote/depth evidence and conservative modeling are. Tardis five-year invoiced OPTIONS entitlement or independently verified Amberdata/CoinAPI equivalent is a possible acquisition path, **not acquired**.

**Internal:** generate the complete 661-day original source-driven OPEN/MARK/SETTLE journal and cost-path-specific risk vetoes without caller-chosen instruments, fee/margin/index assumptions or missing marks; independently replay the native coin portfolio and severe/supersevere economic gates. Existing same-path parity is necessary but insufficient: two identically forged scenario sources would still agree. Do not treat this as an original historical economic backtest.

V16 Frozen, V99 Frozen, legacy champion, paper/results, validation [2023-10-01, 2024-01-18) and final holdout >=2024-01-18 untouched. No orders, no promotion.
