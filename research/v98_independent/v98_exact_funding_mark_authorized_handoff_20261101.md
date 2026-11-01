# V98 exact funding-event markPrice — authorized source handoff (2026-11-01)

**Status: EXTERNAL SOURCE BLOCKED, NOT AN APPROVED ENGINE.** V98 Clean-4 native funding rates and conservative 1h mark envelopes already support exposed 2022-12 to 2025-12 training, but 13,524 exchange-origin **exact funding settlement marks** remain absent. Prior historical `/fapi/v1/fundingRate` requests returned HTTP 451. Do not treat premium-index candles, hourly mark envelopes, a third-party mirror or synthetic values as exact exchange event marks.

## Exact evidence needed to unblock

An authorized acquisition of **all 13,524** Binance USD-M `/fapi/v1/fundingRate` records for BTCUSDT, ETHUSDT, BNBUSDT and SOLUSDT from 2022-12-01 00:00 UTC through 2025-12-31 16:00 UTC inclusive (3,381 events per symbol, 8-hour calendar). Each row must retain `symbol`, `fundingTime` in UTC epoch milliseconds, `fundingRate` and **`markPrice` as received from the exchange**. Provide the original raw JSON response bytes for each API page, original HTTPS request URL, UTC retrieval time, HTTP status and original response headers (at least `Date`), plus SHA256 for every page. A custody document must identify who acquired the data, by what authorized account/location/method, when, and where original immutable raw responses are retained; independent reviewer must verify custody and reconcile a sample against the exchange. **A checksum proves integrity, not Binance authorship.**

Do not attempt to evade regional restrictions. The alternative is an exchange-origin authorized export with equivalent row-level provenance, original exchange attestations and independently reviewed chain of custody; if it is not a raw HTTP page export, a separate adapter must be independently preregistered and tested before use. No manual backfill from price candles.

## Offline adapter and expected-rate binding

`v98_authorized_funding_mark_ingest.py` is a **fail-closed source-only validator**, not a trading engine. The dedicated V98-only Actions workflow `v98-independent-authorized-exact-mark-readiness.yml` reconstructs the exact expected 13,524 `(asset, fundingTime, fundingRate)` tuples from existing SHA-pinned Clean-4 artifacts and tests malformed-mark and raw-response tampering rejection. Its receipt is explicitly `PASS_NATIVE_RATE_EXPECTATION_ONLY_EXACT_MARK_ORIGIN_STILL_MISSING` until real exchange evidence arrives.

For authorized raw response pages, supply UTF-8 JSONL with one object per page:
```json
{"url":"https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&startTime=1669852800000&endTime=1670000000000&limit=1000","status":200,"response_headers":{"Date":"...original exchange HTTP Date..."},"retrieved_at_utc":"2026-11-01T12:00:00Z","response_body":"[...verbatim JSON array of exchange records...]","response_body_sha256":"64 lowercase hex SHA256 of UTF-8 response_body"}
```
The displayed example is a **schema illustration, not market evidence**. The URL date range must match the actual response; preserve raw response body unchanged. Run:
```bash
python research/v98_independent/v98_authorized_funding_mark_ingest.py \
  --pages authorized_binance_funding_pages.jsonl \
  --expected v98_native_expected_funding_2022_2025.csv \
  --output v98_exact_mark_structural_receipt.json
```
The tool checks official host/path, request bounds, 200 status, HTTP Date header, body SHA256, 8h chronology, uniqueness, finite positive mark, native rate reconciliation and **full coverage**; any missing or conflicting event aborts. Its only possible successful decision is `STRUCTURAL_MATCH_ONLY_ORIGIN_ATTESTATION_REQUIRED`, not `PASS_OFFICIAL`. A separate independent human/source-origin gate must approve custody before exact marks replace the conservative proxy in V98.

## Economic and deployment gates still mandatory

Even with all exact marks, no historical rejected candidate (PK, PL, etc.) may be cosmetically rescued. A **new preregistered seven-slot V98** must pass causal full-history physical costs, severe/supersevere costs, independent accounting and chrono validation; then be frozen before untouched prospective/holdout evidence and only then external V14/V15/V99 comparison. The Phase083 holdout is contaminated; 2026+ cannot be inspected for training. This handoff neither claims PnL nor grants paper/live authorization.

**Scope:** only branch `research/v98-independent-zero` and V98 Independent files; V16 Frozen, V99, other research branches, paper and holdout remain untouched.
