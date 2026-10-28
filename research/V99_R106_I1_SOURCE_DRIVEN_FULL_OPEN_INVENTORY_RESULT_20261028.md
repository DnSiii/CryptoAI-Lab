# V99 I1 — full original 90-week OPEN inventory integration: actual CI result (2026-10-28 12:55 BRT)

**Decision: SOURCE_ONLY/HOLD — NO PROMOTION.** No historical option economic TRAIN or ROI. The 2021–2023 licensed original Deribit BTC/ETH option tape has not been delivered.

## Concrete internal critical-path change
The old original-to-provisional runner independently checked that each **caller-selected** OPEN quote existed in original source bytes, but allowed the caller to omit another eligible original strike and thereby bias the fixed vertical selector. That is a material backtest selection loophole, not merely a unit-test detail.

Two preregistrations were committed before code: [source-driven original 90-week inventory](https://github.com/DnSiii/CryptoAI-Lab/commit/854bd16c8fbd042720bd9019a42f1b4adf709e72) and [complete original OPEN inventory binding](https://github.com/DnSiii/CryptoAI-Lab/commit/b6571b0d7a514fa6117403fa084e8e8400cdc957).

Implemented:
1. Streaming original 661-day manifest SHA check and deterministic scan of the **90 immediately pre-Monday Sundays** (BTC+ETH, 180 fixed asset-week intents), selecting the physically last original Deribit put quote per symbol, rejecting stale/invalid last receipts, preserving full BBO, size, arrival/venue microseconds, original file SHA and row ordinal. Only contractual 28–35d expiry within TRAIN is eligible. No synthetic fallback or caller-selected candidate list.
2. Separate **independent** oracle rehashes the 661 files and independently reparses all 90 Sunday books to verify the 180 source-derived books, before NAV.
3. Integrated into the existing nonfixture original-to-provisional 661d runner: every OPEN must now expose **the entire original eligible source candidate inventory** (not just the selected short/long), with exact symbol/expiry/strike/BBO/size/clocks. Scenario-specific CASH remains allowed but not source-certified. Original Tardis quote files do not contain the underlying index, and their size units cannot be assumed to equal native contract lots. These remain explicitly uncertified.

## Executed CI and independent evidence
- [Original entry source inventory Actions 40720331520](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40720331520): **SUCCESS**, independent raw-byte 90-Sunday re-execution plus synthetic adversarial controls.
- [Integrated nonfixture Actions 40720641962](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40720641962): **SUCCESS, 10/10 tests**, including a **new adversarial original-source third eligible strike omitted from both caller OPEN journals**. The two selected BBOs were individually authentic and passed the old identity check, but the integrated full-inventory gate correctly rejected the omission before NAV.
- The CI also actually restored the archived original OKX/DVOL signal receipt and rebound **182/182 original causal signals, 180/180 fixed intents, 132 positive**. The actual original economic attempt stopped at `ORIGINAL_661D_MANIFEST_NOT_DELIVERED`, **0/180 original economically certified option lifecycles**. The 661-day fixture is synthetic, not original historical PnL.
- [Compare 0ac28e0..906ecf0](https://github.com/DnSiii/CryptoAI-Lab/compare/0ac28e00f99845e059c2c441b0ee9120bb18f140...906ecf0df6376732c7a5beea71375365396cee4c): 14 commits across only new/modified research source, tests, verification, preregistrations and two CI workflows. No immutable V16/V99 Frozen, legacy champion, paper/results, validation or holdout modified; no orders.

## Exact remaining critical path
**External, not in the repository:** lawful complete original **Deribit BTC+ETH OPTIONS** two-sided quotes **and sizes** with exchange and capture-arrival timestamps and instrument identity for every UTC day **2021-12-09 through 2023-09-30**, vendor licensing/completeness documentation, original independent underlying and expiry delivery indices, dated historical native contract size/lot conversion, account fee tier/delivery fees, and margin/maintenance/liquidation terms. Tardis five-year invoiced OPTIONS entitlement with confirmed coverage/fields is one route; independently verified CoinAPI/Amberdata equivalent is another. No entitlement or original full tape has been proven delivered. Real exchange trade fills are not required for an untraded backtest; conservative source-depth-aware **simulated** fills are required.

**Internal, not complete:** deterministic full original index-bound OPEN/MARK/SETTLE journal generation, native lot and fee/margin provenance binding, source-driven scenario-specific CASH risk veto, independently re-executed complete 661d native portfolio and five chronological TRAIN folds under severe/supersevere costs, 3x2 regimes, tails, drawdown and benchmark envelope. The source-driven entry inventory closes the caller-selected strike gap but does not itself create or validate an economic trading strategy.

C1 remains permanently rejected; no new candidate passed TRAIN. Validation [2023-10-01, 2024-01-18) and final holdout >=2024-01-18 remain sealed. **SOURCE_ONLY/HOLD; NO PROMOTION/ORDERS/PAPER CLAIMS.**
