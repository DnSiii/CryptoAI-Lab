# V98 Independent — official premium-index full source frozen integrity receipt (2026-11-01)

**SOURCE VALIDATED; NO TRADING EDGE OR PnL CLAIM.** The complete Binance Vision USD-M 1h premium-index series is now a separate authenticated research input, not a substitute for missing funding-event `markPrice`. Clean-4 only, 2022-12-01 00:00 UTC through 2025-12-31 23:00 UTC. No 2026+, XRP, Phase083, V14/V15/V99, paper/live.

## Verified source
- [Four-file source feasibility](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41299098077) passed, vendor SHA verified for BTC Jan-2023, ETH Jun-2024, BNB Jan-2025 and SOL Dec-2025.
- [Complete source + separate independent audit](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41299240043): **148/148 official monthly asset archives covered, 108,192/108,192 hourly asset rows, 27,048 per asset**, 4 daily vendor-SHA repairs, no quarantined hours, no synthetic fill. Independent audit passed exact UTC hourly calendar, vendor ZIP SHA per row, report CSV SHA and 2026 exclusion. The source run and independent audit both succeeded.
- **Canonical CSV SHA256:** `c301a38642f229ca2746ae33baaf58e4bb21ac280a1a99dbbc328cc074caaad4`.
- GitHub Actions source artifact: `v98-independent-premium-clean4-2022-2025-source-only`, run `41299240043`, artifact ID `13080472775`, 30-day retention until 2026-12-01. Contains `v98_premium_2022_2025_verified_hourly.csv` and `v98_premium_2022_2025_source_report.json`, with 148 per-month original vendor ZIP and CSV hashes and four daily hashes. Rebuild from official Binance Vision using [capture](v98_premium_full_source_20261101.py) and [independent audit](v98_premium_full_independent_audit_20261101.py); do not trust the artifact past retention.
- A second, independent local check of the downloaded artifact confirmed identical CSV SHA256, exactly 27,048 rows for each of BTC, ETH, BNB and SOL, and correct first/last UTC timestamps. This is source integrity, not strategy validation.

## Exactly four official monthly archive omissions, repaired with independently checksummed official DAILY rows
The first fail-closed run `41299153834` quarantined the **entire four incomplete monthly archives** instead of filling missing hours. Inspection showed precisely one absent 24h UTC day per archive. The recovery is not interpolation; it inserts exactly the missing 24 original hourly records from Binance Vision daily archives, each with its own vendor `.CHECKSUM` and per-row SHA attribution, then requires full monthly and global UTC continuity. Other source values remain untouched.

| Asset | Monthly archive | Missing UTC day | Official daily ZIP SHA256 |
|---|---|---|---|
| BTCUSDT | 2023-02 | 2023-02-24 | `1e8a12c4f1eaf2f242350e034363c9518bdb1a39f04b8b45a8b79a35ade3ce67` |
| BNBUSDT | 2023-02 | 2023-02-24 | `0b11d2b7fc62e8b33bd899ff30f645e2dd6edcb3563033605d92bf6dab55c03e` |
| ETHUSDT | 2023-04 | 2023-04-09 | `5c3509c1d39ebc88cbc35dec0e60a0a27ce617cf2603056509787956272fd5bf` |
| SOLUSDT | 2023-04 | 2023-04-09 | `1512bae6c4334d071f9130f35a4b3cc2b384111007d01ac792ce8b8dcacace38` |

## Critical path
This new official premium-index series permits a **genuinely distinct, preregistered basis/premium economic hypothesis**, rather than more retuning of failed price-only/OI candidates. It has not been fed into any PnL, and it is not a champion. Next: define seven-slot economic mechanism and causality before inspecting its returns, then run full physical costs/ablations and independent gates.

**Unresolved independent blocker:** 13,524 exact exchange-origin funding-event `markPrice` objects (symbol/fundingTime/fundingRate/markPrice, original HTTP request/response bytes and headers, pagination, SHA256, authorized custody) are still unavailable from the direct USD-M historical API (HTTP 451). Authorized raw exchange-origin export with independent V98-only verification is an acceptable alternative. Premium-index OHLCV is not event-tick markPrice. Untouched prospective validation and final holdout also absent. No paper/live authorization.
