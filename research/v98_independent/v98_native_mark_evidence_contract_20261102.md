# V98 Independent — exact funding markPrice authorized evidence contract (2026-11-02)

**Status:** importer implemented, synthetic-only tests; **zero** real raw settlement marks supplied or independently authenticated. Do not mark funding provenance or account execution validated.

## Required exchange-origin raw capture
Use an authorized network or Binance-provided export to obtain complete historical USD-M `GET /fapi/v1/fundingRate` responses for **BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT**, UTC **2022-12-01 00:00 through 2025-12-31 16:00**, inclusive. Each row must contain `symbol,fundingTime,fundingRate,markPrice`. Expected: **3,381 rows per asset; 13,524 total**. Preserve raw unmodified JSON response bodies and the exact official HTTPS request URL, HTTP status, response headers, UTC retrieval timestamp and SHA256 for each paginated response. Do not store credentials, cookies or signed account URLs in the repository. Capture files must remain outside Git until explicitly authorized and checked for secrets. Each file's URL must point to the official `fapi.binance.com/fapi/v1/fundingRate` endpoint. This API's `markPrice` is the settlement-associated price; 1h/1m mark-price candles and conservative bounds are **not exact replacements**.

Example local-only `custody_manifest.json` (repeat captures until all four symbols and all timestamps covered):

```json
{
  "captures": [
    {
      "symbol": "BTCUSDT",
      "file": "btc_page_0001.json",
      "sha256": "<64-character lowercase SHA256 of raw JSON bytes>",
      "source_url": "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&startTime=1669852800000&limit=1000",
      "retrieved_at_utc": "2026-11-02T22:00:00Z",
      "http_status": 200,
      "response_headers": {"Content-Type": "application/json", "Date": "<original server Date header>"}
    }
  ]
}
```

The `research/v98_independent/v98_native_mark_ingest.py` tool checks file hashes, URL/headers/time metadata, every unique funding event, exact calendar and pinned native funding-rate reconciliation, mark positivity and the existing mark-envelope bounds. If the actual mark lies outside the pre-existing envelope, it **fails closed for source-integrity investigation** rather than silently rewriting an already exposed strategy. Output is a canonical source-only CSV and a receipt explicitly marked **NOT independently authenticated**: self-supplied manifest fields alone cannot prove exchange origin.

Example offline invocation, after separately obtaining the four existing V98-only SHA-pinned source artifact directories:

```bash
python research/v98_independent/v98_native_mark_ingest.py \
  --raw-root /secure/authorized_binance_funding_captures \
  --old-root old \
  --old-envelope old-envelope/v98_official_mark_envelope_training.csv \
  --new-root new --corrected-root corrected \
  --out-dir /secure/v98_exact_mark_reconciliation
```

**Independent attestation:** preserve independent network/transport logs or Binance signed/support provenance; have a second reviewer reconcile the raw-body hashes and canonical CSV to the pinned rates and exact event timestamps. A syntactically valid self-reported manifest does not establish authenticity.

**Other blockers unaffected:** account-specific maker/taker schedules effective on the simulated dates, executable historical bid/ask/depth/market impact at target sizes, USD-M collateral/maintenance-margin/liquidation and risk-tier rules for the account, and untouched chronological validation/clean future holdout. Without these, no real executable PnL, no approved V98, no paper/live. Historical HTTP 451 from hosted runners cannot be bypassed by fabricating responses or using an unverified third-party mirror.
