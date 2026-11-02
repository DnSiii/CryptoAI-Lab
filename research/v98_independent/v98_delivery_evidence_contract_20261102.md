# V98 Independent — native settlement and executable-cost evidence contract (2026-11-02)

**Source-integrity engineering only. No V98 candidate approved, no seven-slot PnL, no independent future validation, no paper/live authorization.** This contract removes ambiguity from two external delivery blockers; it is not another alpha phase.

## Expected native funding events

`v98_delivery_expected_funding_export.py` reads the authenticated Clean-4 2022-2025 source bridge and writes an exact `asset,funding_time_ms,funding_rate` CSV plus SHA256 receipt. It verifies 27,048 UTC hours, 13,524 signed events (3,381 each for BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT), and the 2025-exposed training firewall. Pinned artifacts: runs 40064588623, 40908310578, 41076438477 and 41226345264. No XRP, 2026+, Phase083 holdout or external-engine internals.

## External requirement 1: exact settlement markPrice

Provide original raw JSON response pages from Binance USD-M `/fapi/v1/fundingRate`, with `symbol,fundingTime,fundingRate,markPrice` for **all 13,524 events**, original request URLs, original HTTP Date headers, UTC capture time, per-page SHA256 and independent source custody. The importer accepts official settlement-time millisecond offsets of 0-60s from the authenticated 8h slot, and rejects duplicate, missing, nonmonotonic, rate-conflicting, nonfinite, off-slot or 2026+ records. GitHub Actions previously returned HTTP 451 for this API. A separately authenticated exchange-origin timestamp-level export is an alternative subject to independent review; official hourly mark OHLC is a *conservative interval*, never the exact funding tick. Monthly Binance Vision funding-rate archives contain rates, not the required exact mark.

**SHA256 and plausible URL strings do not authenticate exchange origin.** Even 13,524/13,524 internally matching pages are only a byte/calendar preflight, not an independent origin attestation. Do not commit API credentials or private account identifiers.

## External requirement 2: historical account-specific execution

Provide dated account-applicable spot and USD-M fee schedules, effective taker/maker treatment, funding settlement/fee currency, bid/ask spread and order-book depth at expected sizes, slippage/impact, collateral and liquidation rules. Preserve original bytes, issuer, applicable tier, SHA256 and effective dates without gaps across exposed training. Public nominal fee tables and hypothetical spread/slippage are **not** account-specific executable evidence. Keep private proofs outside the public repository.

## Gates and execution

`v98_delivery_evidence_gate.py` returns `HOLD_MISSING_EXTERNAL_EVIDENCE` when external proofs are absent or inconsistent. Complete internally consistent but unverified evidence returns `PASS_BYTE_AND_CALENDAR_PREFLIGHT_REQUIRES_INDEPENDENT_AUTHENTICATION`. Neither result is a trading approval. A separate independent origin/custody audit, real fill replay and complete causal seven-slot V98 training/validation remain necessary. Base/severe/supersevere costs, tail/concentration, marginal contribution, chronological validation, frozen candidate, untouched future holdout and only post-freeze external benchmarking remain binding.

The new V98-only workflow runs 12 synthetic negative controls, exports the authenticated expected 13,524-event calendar from pinned artifacts, and asserts that absent external proofs produce an explicit HOLD. **Green CI means source calendar and evidence-preflight code worked, not that the trading engine works.** Rejected engines remain rejected; V16/V99/Frozen/paper unchanged.
