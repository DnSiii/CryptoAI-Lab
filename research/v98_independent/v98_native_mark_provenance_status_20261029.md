# V98 Independent — native funding mark provenance status (2026-10-29)

**READ-ONLY SOURCE AUDIT, NOT STRATEGY PERFORMANCE OR FINAL NATIVE-TICK ATTESTATION.**

Authenticated Clean-4 original 2022-12 through 2024-12, BTC/ETH/BNB/SOL 1h. Official exchange historical `/fapi/v1/fundingRate` API, which would return `fundingTime`, `fundingRate` and exact `markPrice`, is blocked from GitHub Actions: run `40906303351` reports HTTP **451** on primary host and non-JSON responses on fallback. No exact exchange funding-tick markPrice archive is available from that API in the runner.

**Alternative actually completed:** official checksum-verified `markPriceKlines` 1h archives for **25 months x four assets = 100 monthly ZIPs**, plus checksum-verified official daily ZIPs for missing 2023-02-24 monthly rows. GitHub Actions `40907620525` PASS. All **9,144 original funding event timestamps** matched a same-hour official mark-price candle, including **3 recovered funding timestamps per asset** from the daily archive; no synthetic price imputation or 2025+ access. Original conservative funding mark lies within the corresponding official mark 1h OHLC for **100% of 9,144 events**.

| Asset | Events | Median absolute gap, conservative mark vs official 1h open | Maximum gap | Conservative mark outside official same-hour OHLC |
| --- | ---: | ---: | ---: | ---: |
| BTCUSDT | 2,286 | 0.2306% | 7.2108% | 0 |
| ETHUSDT | 2,286 | 0.2760% | 10.1623% | 0 |
| BNBUSDT | 2,286 | 0.2733% | 5.0077% | 0 |
| SOLUSDT | 2,286 | 0.5263% | 23.0714% | 0 |

**Limitation:** an official **hourly candle open is NOT the exact mark at funding settlement**. Large open-to-conservative differences, especially SOL, demonstrate why it is incorrect to silently substitute the candle open for the exact funding-tick mark. The 1h candle OHLC provides an independently attested historical interval, not an exact tick-level valuation. Original conservative marks are not promoted to exact native marks by this audit.

**Precisely missing for exact native-tick settlement:** official 2022-12..2024-12 per-symbol `fundingTime, fundingRate, markPrice` records, with source identity/checksum and full 2,286-event coverage per asset, or an independent timestamp-level equivalent. Alternative: retain original conservative marks and run a **pre-registered two-sided mark-envelope sensitivity test** using independently checksummed same-hour mark OHLC, without treating that as exact. No final exact-tick funding gate can be asserted until this evidence or an explicitly accepted conservative-envelope contract is in place.

All changes V98 Independent only. No V99/Frozen/paper, 2025 holdout, 2026+, XRP or live trading touched.
