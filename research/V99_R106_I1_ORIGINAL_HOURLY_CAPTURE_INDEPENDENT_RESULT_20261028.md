# V99 I1 — BTC/ETH original OPTIONS day temporal coverage: independent live verification (2026-10-28 20:04 BRT)

**Decision: SOURCE_ONLY/HOLD — NO PROMOTION.** No complete economic TRAIN, returns, trades, orders, validation, holdout, Frozen, paper or champion changes.

## Defect corrected and actual real-data CI

The former importer accepted a gzip with only a few valid BTC/ETH quotes as a nominal complete day, even when an entire UTC hour was missing. Implemented a nonfixture 661-day per-asset 24-hour quote-presence requirement and an **independent second-pass raw-gzip oracle**. A CRC-valid 23-hour capture is now rejected. The original source files are never uploaded. The 24-hour predicate uses valid causal noncrossed future <=45d puts for **source-day continuity**; a 28–35d option for a specific Monday entry is a separate stricter gate. The initial incorrect attempt to demand 28–45d contracts on *every* calendar day failed on live original source [40783534661](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40783534661); it was corrected with a separately preregistered semantic rationale **before the corrected implementation**, not based on economic PnL.

[CI 40784015128](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40784015128) **SUCCESS** on actual unchanged unauthenticated Tardis Deribit OPTIONS 2022-06-01 gzip. **22/22 offline controls PASS**, then live source scan and separate independent oracle PASS:

- Original compressed bytes **217,070,416**, SHA-256 **9d7b1e62fb7f16648348154ebcece472461d3038c96e61ca7e96de4ce8adcdbd** (identical to earlier independent downloads).
- All original CSV rows **14,720,180**. Valid original put quote rows expiring in (0,45] days: **BTC 1,778,798**, **ETH 3,138,873**. These are quotes, **not 28–35d eligible entries, executed orders, or realized gains**.
- BTC original valid quote presence **24/24 UTC arrival-hour buckets**; ETH **24/24**; second independent gzip replay agrees exactly. This rules out *entire missing hours* for this one date only; does **not** establish absence of within-hour vendor capture gaps or all contract universe.
- Offline synthetic 23-hour missing-bucket test correctly rejected; an all-day source with only 7-day puts correctly passes **source continuity** but cannot be used to assert a 28–35d trading candidate.
- [Local 661-day fixture CI 40783973643](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40783973643) **SUCCESS**; the nonfixture import rejects incomplete hourly source coverage even with a self-declared license file. Synthetic tests do not authenticate other days.

## Unchanged external and internal critical path

**External:** lawful original BTC+ETH Deribit OPTIONS quote/size/venue/arrival archive for **2021-12-09 through 2023-09-30**, all 661 days, with vendor gap attestation; only **1** public day has the above coverage proof. Original historical fee tier and fee cap, lot unit/contract metadata, margin/liquidation terms, and expiry delivery/index receipts are still not fully authenticated. An invoiced Tardis 5-year historical OPTIONS grant or independently authenticated equivalent remains an *unacquired* alternative; no payment or license is implied. Actual exchange fills do not exist for hypothetical orders; require conservative size-aware simulated execution, not fabricated receipts.

**Internal after original archive:** bind all 180 causal Monday intents to independently verified full original eligible books and exact underlying index; deterministic 28–35d vertical selection; conservative scenario-specific fees, slippage, size and margin; full 661-day native coin portfolio replay; independent re-execution and five-fold/3x2/severe/supersevere/benchmark/tail/DD gates. No 2023-10-01+ validation opened and no final holdout accessed.

**Gate:** 0/180 original option lifecycles economically certified. **NO ECONOMIC TRAIN / NO ROI / NO PROMOTION / NO ORDERS**. This is a verified source-integrity repair, not a working validated high-growth trading engine.