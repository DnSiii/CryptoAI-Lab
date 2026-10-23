# V99 R106 D1 C164 — original self-financing hourly ledger integrated, source CI verified (2026-10-23 BRT)

**Decision: DATA_ONLY/HOLD — NO PROMOTION.** No historical economic TRAIN, ROI, first-party execution/funding authentication, validation, holdout, orders, or paper publication.

## Additive source deployment
- Branch: `research/v99-r106-native-all-regime-engine`. Baseline `21396e6fc169cb780256496f7668ee51c846c702`; integrated CI source commit `fef73af0d78356ae72a336b5e0b355b55de80f8b`.
- Restored **five exact original source modules** from the prior C153/C152 local package: C127 native fees + stress, C128 per-fill cash/BASE inventory, C135 execution marks/slippage, C129 hourly variation margin + modeled funding + full NAV, C140 causal t-1 decisions -> C139 paired fills -> C129 independent replay.
- Restored **three exact original test files** for C128, C129, C140. All eight GitHub blob SHA-1 identities were independently checked against local Git-blob hashes. Six previously deployed dependency modules were checked byte-identical to the local package; none were overwritten.
- Added two **source-only** CI workflows. GitHub compare baseline -> integrated CI commit: **10 added files, 0 modified/deleted**. V16 Frozen, V99 Frozen, champion, paper-results, previous rejection evidence and any strategy parameter remained untouched.

## Actual executed checks
1. Local isolated C128/C129/C140 suite: **48/48 pytest tests passed**. Includes negative controls for doubled BASE fees, missing quote fees, negative cash, invented/missing funding fixes, off-mark slippage, wrong-hour fills, cross-hour discontinuity, scenario market-path mismatch, lookahead, and sealed partitions.
2. GitHub Actions **39990758232**, job **120541587141**, commit `41e0c5b`: **17/17 original C128 pytest tests** plus **87/87 C163–C153 unittest regressions**, all green (**104/104**). Explicit no-economics/no-promotion checks passed.
3. GitHub Actions **39991131189**, job **120542858418**, commit `fef73af`: **48/48 C128/C129/C140 pytest tests** plus **87/87 earlier regressions**, all green (**135/135**). An additional 48-hour two-scenario cold-cash synthetic replay checked 12 modeled funding events, the independent hourly account, and permission gates. Full job logs and step outcomes were inspected.

## Scientific interpretation and blockers
- All 48-hour and earlier full-TRAIN structural fixtures are **synthetic**; an `OKX` source string and a green CI do not authenticate market prices, native fee tier, contract specifications, fills, or actually settled funding. No economic ROI was calculated. This integration removes missing *source* dependencies but does **not** authorize historical scoring.
- C139/C151 synthetic fills may fail illustrative contract grids; do not retune fixed D1 parameters to force a win or claim real OKX incompatibility from invented terms.
- C1/C2 and 100 archived alpha candidates remain rejected; D1 remains one distinct preregistered architecture, not an optimized winner.
- Keep validation `[2023-10-01,2024-01-18)` and final holdout `>=2024-01-18` sealed. Historical R106 holdout-peeking lineage is not a clean final test.
- Next: additively integrate original C141–C147/C152 decision/feature/account readiness gates, verify all existing remote blobs before each merge, execute integrated source-only CI; separately bind first-party historically as-of OKX BTC/ETH spot+perp hourly marks, actual settled funding, account-specific fee tiers, dated instrument lot terms, and fill/slippage receipts. Only after provenance gates pass may one preregistered full economic TRAIN trial be executed with five chronological folds, 3x2 regimes, severe/supersevere, tail/DD, benchmarks and independent replay. **No economic trial was dispatched in C164.**

**DATA_ONLY/HOLD; NO PROMOTION; no orders; no paper publication; no holdout.**
