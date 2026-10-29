# V99 I1 — correct source feed coverage vs market tenor availability (2026-10-29 03:54 BRT)

**SOURCE_ONLY/HOLD — NO PROMOTION. No licensed original 661-day economic TRAIN, no certified option lifecycle, no ROI, no orders.**

## Critical-path correctness fix
The original 661-day source importer previously demanded BTC and ETH valid 21–45-day puts every hour and rejected a day if that tenor was absent. That is not a valid test of transport completeness: a valid live options feed can exist while the particular desired maturity has no instruments. A false transport-gap veto would prevent correctly recording an I1 CASH/source-ineligible decision even after acquiring a complete original archive.

Preregistered before code in commit d1a132ea7516c35f0b03a8767474976d29847a9c. The importer now retains all old 21–45d descriptive and 28–45d entry counts, and separately counts original valid BTC/ETH live puts at ANY future expiry. Its 24/24 hourly feed-presence heuristic uses only these separate live-any-tenor counts. Actual fixed I1 28–35d eligibility, 90 Mondays, signal, strategy, risk, costs and economics were not changed. A 60d put does NOT become an eligible I1 entry.

The primary lifecycle reader and separately implemented independent original-byte oracle were corrected to use live-any-tenor only for weak daily feed presence, while retaining strict original 28–35d same-contract entry/holding checks. The independent oracle also rederives new live coverage counters from the raw compressed bytes and rejects a forged 24-hour claim; fixture compatibility is retained. This is NOT a vendor completeness attestation.

## Executed GitHub CI evidence
- [Actions 40831845658](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40831845658): **SUCCESS**, 15 synthetic local-import/adversarial tests plus 12 offline licensed-transfer tests, including a 661-day original-shaped fixture with an entirely noneligible >45d live options day, independent lifecycle replay, and a forged hourly-coverage rejection. The actual nonfixture probe still printed BLOCKED_ORIGINAL_LICENSED_661_DAY_OPTIONS_ARCHIVE_MISSING.
- [Actions 40831828527](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40831828527): **SUCCESS**, full synthetic 661-day lifecycle source/held-contract adversarial controls and independently recomputed 180 fixed asset-week coverage. No original licensed quote lifecycle or economics was supplied.
- Changes: commits 8459bac, 4b6dbe5, e26e3ef, a6ac37f, bd1afdb, a6d9402, 8555517 and 074878c. Preregistration ancestry enforced in both CI workflows. No Frozen, paper, legacy champion or sealed validation/holdout paths changed.

## What remains blocking real delivery
1. Licensed non-sample original Deribit BTC/ETH options BBO+size+arrival/venue timestamps across 2021-12-09..2023-09-30, including all actual entry, same-contract marks and expiry fixings; currently 658/661 original days absent. Vendor completeness rights/coverage attestation and private authenticated key are still missing. Alternative: independently authenticated equivalent provider, first verified on a previously fixed calendar-eligible signal-positive TRAIN date, before any bulk procurement.
2. Dated original native contract size/lot, applicable 2021–2023 account fee tier and delivery fees, expiry index/TWAP, collateral and liquidation terms; conservative size-aware historical fill simulation and independent source-to-NAV accounting. A backtest cannot claim actual fills for hypothetical historical trades.
3. A distinct pre-registered complete engine with original 5 chronological folds, six regimes, severe/supersevere costs, DD/tails, fixed benchmark and independent economics. I1 remains deprioritized pending source feasibility; C1 and other failed architectures remain rejected. The source-only fix does not establish an edge.

**Decision: SOURCE_ONLY/HOLD, 0/180 economically certified option lifecycles, NO TRAIN ROI, NO PROMOTION/ORDERS.** Sealed validation from 2023-10-01, final holdout from 2024-01-18, V16/V99 Frozen, paper and champion remain untouched.
