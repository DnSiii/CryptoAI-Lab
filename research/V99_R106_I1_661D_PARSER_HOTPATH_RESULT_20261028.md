# V99 I1 — bounded 661-day original-tape parser optimization: verified real-byte parity (2026-10-28 20:59 BRT)

**Decision: SOURCE_ONLY/HOLD — NO PROMOTION.** This is a real ingestion hot-path improvement, **not** a complete option strategy, historical economic TRAIN, ROI, paper return, fill or certified trading execution.

## Ex-ante change and code
- Preregistered **before implementation** in [V99_R106_I1_661D_PARSER_HOTPATH_PREREG_20261028.md](V99_R106_I1_661D_PARSER_HOTPATH_PREREG_20261028.md), commit `ef397ac2e5aff38ef475f86a704556fae0800d18`.
- Implemented per-day bounded 32768-entry LRU of **symbol-derived contract metadata only** in `research/tools/v99_r106_i1_local_tape_import.py`, commit `5ea7cc0a49a2422f2891a31f59f23a54ef6074fa`. Original venue/arrival/event clocks, row-level bid/ask/size, expiry bounds, quote staleness, gzip CRC/EOF, source byte hash and 24/24-hour checks remain per-row and unchanged.
- Added adversarial repeated-symbol test: later crossed quote must not inherit earlier valid price or size; malformed symbols rejected, both BTC and ETH checked, commit `e93b4210336446a2142a03f90a7acbb9ff4a7405`.
- Added automatic exact pinned original-day SHA/byte/row/asset-count assertions to the real-source workflow, commit `7ba1bf8ee53fb50f106dedf4e5534e66ede7a1d1`. Independent oracle remains a separate full gzip replay, not the production cache.

## Actually executed GitHub Actions
- [Local 661-day fixture CI 40790174048](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40790174048): **SUCCESS**, 14/14 local tape/adversarial tests and 12/12 licensed-transfer offline tests. Fixture does not prove market or economics.
- [Real unchanged 2022-06-01 source CI 40790173759](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40790173759): **SUCCESS**, 23/23 offline controls, full real gzip production scan and independent second-pass oracle PASS. End-to-end real-day step 23:52:51.823–23:56:31.694 UTC = ~219.9s.
- [Pinned branch-head real source CI 40790799343](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40790799343): **SUCCESS**, 23/23 offline controls, same real gzip full production scan and independent oracle PASS; exact byte/row/count pin PASS. End-to-end real-day step 23:57:08.824–23:59:05.677 UTC = ~116.9s.
- Before optimization, [real original source CI 40784124850](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40784124850) end-to-end real-day step ~292.7s (23:00:01.235–23:04:53.960 UTC). Observed post-change elapsed steps were shorter, but network/runner variability means **no isolated scanner-only speedup percentage is claimed**.

## Exact real-byte invariants
All actual post-change real-day runs preserve the independently verified pre-change original:
- Compressed SHA-256 `9d7b1e62fb7f16648348154ebcece472461d3038c96e61ca7e96de4ce8adcdbd`, **217,070,416 bytes**.
- **14,720,180** original CSV rows; valid causal put quote rows BTC **1,778,798**, ETH **3,138,873**.
- BTC **24/24** and ETH **24/24** UTC arrival-hour buckets, independently replayed from original gzip. This is necessary continuity evidence for **one** day only, not vendor gap attestation or a verified 28–35d entry book.

## Remaining critical path (unchanged)
- **External:** lawful licensed original BTC+ETH Deribit OPTIONS BBO/size/arrival/mark tape covering **2021-12-09..2023-09-30 (661 days)**; only **one** free public day independently verified, **660 missing**. Need vendor gap attestation and dated first-party native fee tier/caps, lot/size units, margin/liquidation and delivery/index receipts, or independently authenticated equivalent. Tardis paid grant / CoinAPI authenticated archive are possible alternatives, **not acquired**.
- **Internal once original bytes arrive:** scalable durable per-day ingestion/retention; independently bind all **180** causal Monday intents to full original eligible books, original underlying index, 28–35d fixed vertical, conservative size-aware modeled execution, original native cost/margin/delivery, 661-day portfolio and five chronological folds/3x2/severe/supersevere/tails/DD/benchmark with independent replay.
- 0/180 original option lifecycles economically certified. **NO ECONOMIC TRAIN, NO ROI, NO VALIDATION, NO HOLDOUT, NO PROMOTION, NO ORDERS.** Frozen V16/V99, legacy champion and paper-results untouched.
