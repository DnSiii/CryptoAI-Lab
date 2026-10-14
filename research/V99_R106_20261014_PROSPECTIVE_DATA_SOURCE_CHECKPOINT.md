# V99 R106 — Real prospective source access and permanent receipts

**UTC date: 2026-10-14. Status: DATA_ONLY/HOLD. No economic trial, paper release, real order, Frozen edit, training/holdout contamination, or model promotion.**

## Verified official data from current Actions runs

| Gate | Run | Verified result |
| --- | --- | --- |
| Binance Vision public 1H ZIP + native `.CHECKSUM` | 38629680205 | PASS, 16 tests, three Binance USDM hourly archives for 2026-10-12: BTC, ETH, SOL, with CRC, 24-hour continuity and three independent SHA256 checks |
| OKX real public 1H candles + venue server time | 38630182430 | PASS, 19 tests, five phase136-preregistered OKX USDT swaps with complete confirmed candles to 2026-10-14 20:00 UTC, unfinished bar excluded |
| Permanent immutable OKX market observations | 38630865416 | PASS, 19 market + 11 append-only tests, first commit `2c33549c34335993d4d5e502ed14ef1a30ddbc46` on dedicated receipt branch |
| OKX live native multipliers, tick/lot sizes and funding notices | 38631347210 | PASS, 13 native semantics tests; public future funding notice is NOT evidence of settled funding |
| Permanent immutable native terms/funding receipt | 38631825856 | PASS, 13 native + 11 append-only tests, commit `403efa30afbf7a06d25c7e128e083efe1a639bf5` |
| Cross-check both original raw source streams | 38632326536 | PASS, 7 forensic tests and actual source-pair; result `TWO_FIRST_PARTY_SOURCE_STREAMS_CONSISTENT_DATA_ONLY`, evidence artifact **11926577019**, SHA-256 `3fe182ac7ca6a9953084630aa0aa89bac84897015540184e0a9e2f68dbb459b7` |

Receipts are stored in the separate GitHub branch `research/v99-r106-live-receipts`. The first paired acquisition-hour is `2026-10-14T20`, folders:
- `receipts/v99_r106_okx/2026-10-14T20` — first recorded 20:18:13 UTC.
- `receipts/v99_r106_okx_terms/2026-10-14T20` — first recorded 20:25:01 UTC.

Both checked against exact SHA-256 of the persisted raw HTTP bytes plus public OKX server-time receipts and GitHub Actions run IDs. Latest common completed price candle: **2026-10-14 20:00 UTC**. Conservative earliest eligible future decision: **2026-10-14 22:00 UTC**. That is *not* a trade and does not backdate observed data.

The native contract conversion differs materially: BTC-USDT-SWAP contract value **0.01 BTC**, ETH **0.1 ETH**, SOL **1 SOL**, XRP **100 XRP**, DOGE **1000 DOGE**. The source has native notices of funding rates, not independently authenticated cash settlement or executed fees.

## Future source-acquisition jobs on main (first push-run verified)

- `v99-r106-hourly-source-receipts.yml`: minute 37 UTC hourly, price data and native public UTC clock, strict append-only write to receipt branch.
- `v99-r106-hourly-native-terms.yml`: minute 43 UTC hourly, native terms and funding notices.
- `v99-r106-asof-pair-audit.yml`: minute 50 UTC hourly, independent read-only pair provenance check.

**The first push-triggered execution of all three succeeded. Future scheduled runs are NOT yet independently observed.** The source branch is permanent Git history; receipt artifacts also retain original byte evidence up to 90 days. No writes were made to the original `paper-results` ledger.

## Remaining research limitation

Binance USD-M REST returned HTTP 451 on GitHub Actions; Binance Vision daily archives are delayed. The new OKX path is public first-party observed data, but **not a Binance-compatible substitute** and not an exchange-signed/third-party independently attested historical discovery record.

Do not port R106 F3/F7 signals, exposure, fees or funding economics from Binance to OKX without separate preregistration and native validation. Fee tier, fill slippage, historical first-seen evidence, true settled funding, fully reconciled hourly native PnL, complete candidate position journal and validation of engine behavior are still missing.

The old R106 five-variant paper ledger Git blob `97ce6ea8e9b58a9616892d915c86d96ae3c54225` remains unchanged, with immutable F1/F3 capped operations and contaminated old backtest references. It cannot pass the original publication gate. The clean new-epoch schema has passed offline tests but **no new paper return, new champion or legitimate PnL** has been produced.

**Next gate:** confirm future distinct hourly acquisition receipts; freeze a separate OKX-native shadow-replay accounting specification using first-party contract units and settled-funding history, under strictly causal prospective provenance. Any later economic hypothesis must use allowed TRAIN-only data and untouched final holdout.
