# V99 R106 — Amberdata as a second viable *request* for Deribit I1 historical executable quotes (2026-10-30 13:xx BRT)

**SOURCE PROCUREMENT RESEARCH ONLY — NOT ACQUIRED, NOT ECONOMICS, NO PROMOTION.** The already frozen I1 source feasibility target is **2022-01-23 UTC**, for the original 2022-01-24 Monday decision. Do not change the date, BTC/ETH scope, 28–35d fixed tenor, or 2021-12-09..2023-10-01 TRAIN boundary.

## New first-party vendor evidence (not a dataset delivery)

Amberdata's own Deribit market-data page explicitly advertises **BTC/ETH options order-book events, order-book snapshots, tickers, and historical options data**, including API routes `/market/options/order-book-events/{instrument}/historical` and `/market/options/order-book-snapshots/{instrument}/historical`. Its page says historical Deribit options **trading data** starts 2021-05-21 and separately markets broader options coverage back to 2018-08-13. **Neither statement proves that 2022-01-23 BTC+ETH *quote-event and size* data exist**, nor that historical full-universe availability or source capture times are supplied. Vendor order-book snapshots are described as one-minute REST captures; that cadence **cannot be presumed to satisfy the I1 fixed <=300-second, synchronized two-strike original source gate**, especially across entry and lifecycle marks. Request event-level quotes with sizes and both exchange/capture clocks, not vendor marks or a trade tape.

Official primary sources:
- https://www.amberdata.io/deribit-market-data
- https://www.amberdata.io/order-book
- https://www.amberdata.io/market-data

This is a **new vendor route**, not a claim that a paid product or free trial exists. No account, quote, sample, payment, license or API token has been obtained. Existing CoinAPI and Tardis intake code remains unmodified.

## Precise external evidence required *before* payment, adaptation or original economic replay

Ask Amberdata in writing to provide, for **Deribit OPTIONS 2022-01-23 UTC 00:00–24:00**, (1) all historical BTC and ETH listed put strikes/expiries (including nontrading contracts); (2) original best bid/ask and **displayed bid/ask sizes** for each instrument, exchange-event time and **actual collection/availability timestamp**, preserving raw order/capture gaps; (3) a representative **authorized original non-first-of-month sample** with file bytes, independently supplied SHA256, exact schema and venue-to-normalized field mapping; (4) dated commercial/research redistribution/retention license and precise product/price, with no purchase assumption; (5) written complete-venue universe, outage/gap manifest and evidence of 2021-12-09..2023-09-30 coverage for **both** assets. Also separately require dated historical Deribit fee-tier/premium cap, tick/lot/contract size, coin collateral, liquidation/margin, delivery/expiry and index terms; a vendor book cannot certify private account fills or funding cash.

**Decision tree:** no sample/license/sha/venue clock/size -> `SOURCE_HOLD`; valid original sample -> run the existing `research.tools.v99_r106_i1_single_day_source_feasibility` only after an explicitly preregistered vendor-to-native **lossless** conversion and a separate original-byte independent oracle; sample fails -> `SOURCE_VETO_NOT_LOSS`; sample passes -> evaluate **full 661-day acquisition**, never assume it; only a fully licensed 661-day source + native cost/settlement + independent economics can begin I1 complete TRAIN. Existing Tardis 4-year ordinary annual entitlement is insufficient for 2021 start unless written extended coverage; Volar BTC-only history cannot cover ETH.

**NO NEW ROI / NO STRATEGY / NO CI ECONOMICS / NO ORDERS.** As of the latest verified evidence, 658/661 original quote days are missing and 0/180 I1 lifecycles economically certified. C1/C2/D1/D2/D3/E1/F1/G1/H1 and other rejected systems remain rejected. V16/V99 Frozen, paper/results, champion, public dashboard, validation [2023-10-01,2024-01-18) and final holdout >=2024-01-18 untouched.
