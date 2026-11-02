# V98 Independent — native settlement and executable-cost evidence contract (2026-11-02)

**Source-integrity engineering only. No V98 candidate approved, no seven-slot PnL, no independent future validation, no paper/live authorization.** This contract removes ambiguity from two external delivery blockers; it is not another alpha phase.

## Expected native funding events

`v98_delivery_expected_funding_export.py` reads the authenticated Clean-4 2022-2025 source bridge and writes an exact `asset,funding_time_ms,funding_rate` CSV plus SHA256 receipt. It verifies 27,048 UTC hours, 13,524 signed events (3,381 each for BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT), and the 2025-exposed training firewall. Pinned artifacts: runs 40064588623, 40908310578, 41076438477 and 41226345264. No XRP, 2026+, Phase083 holdout or external-engine internals.

## External requirement 1: exact settlement markPrice

Provide original raw JSON response pages from Binance USD-M `/fapi/v1/fundingRate`, with `symbol,fundingTime,fundingRate,markPrice` for **all 13,524 events**, original request URLs, original HTTP Date headers, UTC capture time, per-page SHA256 and independent source custody. The importer accepts official settlement-time millisecond offsets of 0-60s from the authenticated 8h slot, and rejects duplicate, missing, nonmonotonic, rate-conflicting, nonfinite, off-slot or 2026+ records. GitHub Actions previously returned HTTP 451 for this API. A separately authenticated exchange-origin timestamp-level export is an alternative subject to independent review; official hourly mark OHLC is a *conservative interval*, never the exact funding tick. Monthly Binance Vision funding-rate archives contain rates, not the required exact mark.

**SHA256 and plausible URL strings do not authenticate exchange origin.** Even 13,524/13,524 internally matching pages are only a byte/calendar preflight, not an independent origin attestation. Do not commit API credentials or private account identifiers.

## External requirement 2: historical account-specific execution

Provide dated account-applicable spot and USD-M fee schedules, effective taker/maker treatment, funding settlement/fee currency, bid/ask spread and order-book depth at expected sizes, slippage/impact, collateral and liquidation rules. Preserve original bytes, issuer, applicable tier, SHA256 and effective dates without gaps across exposed training. Public nominal fee tables and hypothetical spread/slippage are **not** account-specific executable evidence. Keep private proofs outside the public repository.

## Single authorized handoff (implemented 2026-11-02)

The evidence directory now accepts **exactly one** native mark transport, never multiple: (A) `native_pages_manifest.json` plus original SHA256-matched raw page JSON files, (B) `authorized_funding_pages.jsonl` in the existing `v98_authorized_funding_mark_ingest.py` handoff format, or (C) `authorized_exchange_export_manifest.json` plus a separately authorized, original exchange-origin CSV and a separate custodian-attestation file. The (C) path is intended for lawful, authorized exports when the API returns HTTP 451; it is not a substitute for independent origin verification. Option B reuses the original request URL, HTTP status 200, original RFC 7231 `Date` header, UTC retrieval timestamp, verbatim response body and its SHA256. Both transports must bind every record to the **same SHA-pinned 13,524-event native funding calendar**. For B, the structural importer writes a separate exact-mark CSV retaining both the original exchange `fundingTime` and the authenticated 8-hour `fundingSlotTime`; offsets 0-60 seconds are supported, larger offsets rejected. A 2026+ event or out-of-request-window event is rejected. The official host string, plausible headers and self-computed SHA do **not** independently prove Binance origin.

The same evidence directory must contain `account_costs_manifest.json`, with continuous integer-millisecond `fee_periods` covering 2022-12-01 to 2026-01-01 (exclusive), each declaring `spot_taker_bps`, `perp_taker_bps`, `spot_spread_bps`, `perp_spread_bps`, `spot_impact_bps`, `perp_impact_bps`. It must reference original account-specific proof files under `account_fee_schedule`, `historical_bid_ask_depth`, `collateral_liquidation_policy`, each with a basename-only `file`, `sha256`, `issuer` and `applicable_account_tier`. No symlinks or non-integer effective dates. This is a **byte/schema preflight only**: a separate independent reviewer must authenticate issuer, account applicability, time-effective fee rates, real order-book depth and fill economics. Preserve sensitive account proofs outside public GitHub.

`v98_delivery_evidence_gate.py` consumes the evidence directory, the SHA-pinned native expected CSV and its declared digest; it returns a **HOLD** without external proofs and only a structural **PASS requiring independent authentication** when internally consistent. Neither state authorizes portfolio PnL claims, paper or live execution.

## Authorized exchange-origin CSV alternative to HTTP 451 (2026-11-02)

The new `v98_delivery_authorized_exchange_export.py` implements transport **C** without contacting a blocked API or inventing mark prices. Place the following **private** files in the same evidence directory:

- `original_exchange_export.csv`: original authorized exchange-origin UTF-8 CSV, exactly `symbol,fundingTime,fundingRate,markPrice` in this order; 13,524 native events (3,381 per asset), per-asset strictly increasing timestamps, 0–60s settlement offsets, no XRP or 2026+. Never substitute OHLC or a synthetic mark envelope.
- `custody_attestation.pdf` (or other independently issued original file): separate provenance document identifying how the custodian acquired the export. The preflight checks only that its bytes match the declared SHA256. **A self-written document is not valid independent attestation**; a reviewer must verify issuer, original source, signatures where available, acquisition chain and account/exchange applicability outside the program.
- `authorized_exchange_export_manifest.json`, containing the original CSV and custody-file basenames and SHA256 values:

```json
{
  "source_type": "authorized_exchange_origin_export",
  "schema": "symbol,fundingTime,fundingRate,markPrice",
  "exchange_issuer": "ACTUAL_ISSUER_FROM_ORIGINAL_EXPORT",
  "independent_custodian": "ACTUAL_INDEPENDENT_CUSTODIAN",
  "custody_method": "DOCUMENTED_AUTHORIZED_EXPORT_METHOD",
  "export_reference": "ORIGINAL_EXPORT_REFERENCE",
  "captured_at_utc": "2026-11-02T06:00:00Z",
  "export_file": "original_exchange_export.csv",
  "export_sha256": "ACTUAL_SHA256_OF_ORIGINAL_CSV",
  "custody_attestation_file": "custody_attestation.pdf",
  "custody_attestation_sha256": "ACTUAL_SHA256_OF_ATTESTATION"
}
```

The timestamp above is an **illustrative manifest example**, not a claim that such an export exists. The code rejects absent/ambiguous transports, unsafe paths, changed bytes, missing events, duplicate or out-of-order records, one-native-tick rate conflicts, nonfinite/negative marks and post-2025 events. Only after a separate complete account-cost preflight does it publish `v98_authorized_native_preflight.csv`; it never overwrites a conflicting output. This alternative does not require an original HTTP `Date` header because it is **not** an HTTP-response capture. It cannot be presented as a Binance API response.

**External evidence still missing:** no original authorized CSV, no authentic independent custody proof, and no account-specific historical fees, order-book/depth and collateral/liquidation proofs have been supplied. Thus the gate remains HOLD, and no V98 trading engine, PnL, paper or live state is approved.

## Gates and execution

`v98_delivery_evidence_gate.py` returns `HOLD_MISSING_EXTERNAL_EVIDENCE` when external proofs are absent or inconsistent. Complete internally consistent but unverified evidence returns `PASS_BYTE_AND_CALENDAR_PREFLIGHT_REQUIRES_INDEPENDENT_AUTHENTICATION`. Neither result is a trading approval. A separate independent origin/custody audit, real fill replay and complete causal seven-slot V98 training/validation remain necessary. Base/severe/supersevere costs, tail/concentration, marginal contribution, chronological validation, frozen candidate, untouched future holdout and only post-freeze external benchmarking remain binding.

The new V98-only workflow runs 12 synthetic negative controls, exports the authenticated expected 13,524-event calendar from pinned artifacts, and asserts that absent external proofs produce an explicit HOLD. **Green CI means source calendar and evidence-preflight code worked, not that the trading engine works.** Rejected engines remain rejected; V16/V99/Frozen/paper unchanged.

## Authorized-network collection path (2026-11-02)

`v98_delivery_native_mark_collector.py` is now an executable V98-only acquisition utility, not a mock proof. On a machine **authorized to reach the official Binance USD-M endpoint**, use the SHA-pinned native expected CSV from the workflow artifact and run:

```bash
python research/v98_independent/v98_delivery_native_mark_collector.py \\
  --expected-funding-csv /private/v98_expected_native_funding_2022_2025.csv \\
  --expected-funding-sha256 3a7e5cc35152663ecfd08edb991c9f5cf1db845877cfb0d0b802d0682f55e7c1 \\
  --evidence-dir /private/v98-native-evidence
```

The collector requests only 2022-12-01 through 2025-12-31 (endTime is 2026-01-01 minus one millisecond), pages 1,000 events at a time, and tries only `fapi.binance.com` then `fapi1.binance.com` **on a connectivity outage**. HTTP 451/403/418 is a hard stop, never a reason to switch hosts. It retains original response-body bytes (UTF-8 text), original HTTP Date, URL, UTC retrieval time and SHA256; it never manufactures missing marks or silently falls back to candle prices. The independent V98 importer must reconcile every expected native event and rate **before** the collector publishes `authorized_funding_pages.jsonl`. Partial or conflicting captures are not published. HTTP 451 on the primary host is already a jurisdiction/access blocker: use a permitted independent exchange-origin export and authenticate custody; do not bypass access restrictions.

The manifest transport of `v98_delivery_evidence_gate.py` now also exposes a canonical `v98_authorized_native_preflight.csv` after source and cost structural checks, matching the JSONL transport's columns. For JSONL, the independent importer now stages both CSV and receipt privately and publishes neither when the account-cost preflight fails; a conflicting existing output is rejected without overwrite. Both outputs are **source-only and unauthenticated**; do not use for physical system PnL until independent provenance, account cost/fill proof and chronological seven-slot validation are complete. Original private account proofs must remain outside public GitHub.
