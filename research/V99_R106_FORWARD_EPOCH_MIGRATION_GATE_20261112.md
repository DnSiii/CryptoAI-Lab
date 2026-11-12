# V99 R106 — forward epoch migration gate (2026-11-12)

Status: **BLOCKED / RESEARCH ONLY / NO PROMOTION**. This document is a migration contract, **not** evidence that a new epoch has been initialized.

## Reproducible blocker

GitHub Actions run 43178061046, job 131047019065, exited 2 at the fail-fast preflight. Source: `research/tools/v99_r106_legacy_epoch_feasibility.py`. The immutable published ledger's raw SHA-256 was `f188c4d95761c4ddf4719f4d86bfab0faa54a65f79d576f42ce3cc4f09e17089` at inspection. Both F1 and F3 have operation histories at the legacy cap; all five variants (F1/F12/F3/F7/R98) have historical backtest references crossing the paper start boundary. The audit explicitly tests the unchanged old ledger against itself: the failure is independent of any new candidate. **Do not rerun to force publication, increase the cap on the old ledger, truncate its operations, rewrite its reference, or bypass the guard.**

## Minimum safe independent forward epoch

1. Preserve the published ledger bytes, SHA-256, original boundary, variant IDs, historical curves and old operation histories. Keep legacy dashboard series visible but labelled *immutable historical research; no live execution*.
2. Acquire **first-party, timestamped as-of source receipts** for the proposed new start: exchange identifier, symbol, venue, interval, close timestamp, acquisition timestamp, raw payload hash, provenance URL or archive identifier, settlement/funding event IDs, fee tier and execution assumptions. Validate UTC closed-hour alignment, continuity, duplicate keys and causal availability before choosing the boundary. Missing or stale receipts mean **do not initialize**.
3. Create a **new versioned namespace and epoch ID** with its own initialization timestamp and immutable cut. No old operation or reference can be copied as a new trade. The new journal must be append-only, uniquely keyed by epoch/variant/event, with explicit unrounded and rounded notionals, position transitions, fees/funding, cash and capital. Unbounded storage must still enforce per-run event and resource safety limits, not a silent fixed total-history cap.
4. Independently reconstruct each proposed hour from original closed market candles and source receipts; check t-1 decision causality, fills, accounting, no duplicated events, non-finite values, funding settlement, per-asset/portfolio reconciliation and zero-real-order mode. Reject any mismatch. Keep severe and supersevere cost paths separate.
5. Publication must be **atomic**: run adversarial checks (missing receipt, stale receipt, duplicated event, altered prior hash, negative/NaN notional, zero-rounded notional >= half-cent, boundary overlap, fake funding, changed legacy bytes), then independent prefix verification and CI success before publishing the new namespace. An unsuccessful new epoch must leave the old ledger and dashboard intact.
6. The dashboard must display independent **last source candle UTC**, **last successful publish UTC**, and visible **STALE / RESEARCH ONLY / NO REAL ORDERS** warnings. Never call the new epoch a validated profitable engine. Retain sealed validation and holdout; do not use contaminated R106 historical diagnostics to tune.

## Separate economic dependency

I1 is not certified: 658 of 661 required original Deribit option-history days remain unavailable/unlicensed. Written authorization/licence and complete BTC/ETH original historical series with venue-native execution, margin, settlement and fees are required before economic evaluation. Do not buy or infer missing records, and do not extrapolate economics from three demonstration days. D1 and C1 remain rejected. This forward-publication repair is **not** an alpha promotion.

Next implementation work: identify source receipt schema and the new epoch journal writer, add a read-only bootstrap audit with hard failure on missing provenance, and run independent CI before any publication switch.
