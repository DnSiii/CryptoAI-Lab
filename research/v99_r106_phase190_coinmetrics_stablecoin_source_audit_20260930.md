# V99 R106 — Phase190 candidate source audit: Coin Metrics stablecoin supply

Date: 2026-09-30
Status: DATA_ONLY / NO PNL / HOLDOUT UNTOUCHED

## Purpose

Audit a genuinely orthogonal information family after Phase189 without creating another local OHLCV/volume transform. This document does not preregister an economic alpha and does not authorize PnL.

## Candidate

Coin Metrics Network Data asset metrics for USD stablecoins, initially USDT and USDC, with `SplyCur` as the candidate native circulating-supply state. The provider documentation exposes a Community API root without an API key, a stablecoin asset group containing USDC/USDT, and an official example requesting `SplyCur` for USDC at 1d frequency.

This is economically orthogonal to the exhausted exchange-price, OHLCV, funding, positioning, aggTrades and same-venue volume families because the primitive is token supply state rather than exchange trading state.

## What is established from provider documentation

1. Coin Metrics API v4 exposes a Community HTTP API at `https://community-api.coinmetrics.io/v4` without an API key.
2. The reference-data stablecoin group includes `usdc` and `usdt`.
3. The official getting-started documentation demonstrates `SplyCur` in an asset-metrics request for `usdc` at 1d frequency.
4. Asset metrics are keyed by asset and time; therefore the natural research cadence for this candidate is daily, not hourly. Any eventual signal must be known strictly before the traded bar and may not forward-fill information prior to its admissible effective time.

## Critical unresolved gates

Phase190 remains BLOCKED from economic preregistration until all of the following are established from the actual API/catalog response and persisted deterministically:

- `SplyCur` is Community-accessible for both USDT and USDC, not merely documented in a paid example;
- exact min/max coverage spans enough pre-holdout TRAIN history for chronological temporal folds;
- timestamp semantics are suitable for point-in-time use, including whether a 00:00 daily observation represents state known at that timestamp or a completed-day value only knowable later;
- historical values are reproducible or can be frozen with raw-response SHA256 plus retrieval metadata;
- asset semantics account for multi-chain stablecoin representations without accidental double counting or retrospective remapping;
- missing observations/revisions can be handled without backfill leakage;
- no holdout values are inspected during this source audit.

## Deterministic admission protocol

A future DATA_ONLY probe should query catalog metadata first for `usdt` and `usdc`, persist only schema/coverage metadata, then retrieve a bounded TRAIN-only sample if Community access is confirmed. Raw bytes and normalized output must receive SHA256 checksums. The probe must fail closed on ambiguous timestamps, insufficient TRAIN coverage, unsupported metrics, or inconsistent reruns.

Only after that probe passes may a Phase190 economic hypothesis be preregistered. Parameters, lag convention, aggregation cadence, temporal folds, severe/supersevere costs, regime matrix and benchmark envelope must be frozen before any candidate PnL is observed.

## Explicit anti-overfit restrictions

Do not test multiple supply transforms to find a winner. Do not sweep USDT-vs-USDC combinations, lags, thresholds or lookbacks before preregistration. Do not infer issuance/redemption events from revised future snapshots. Do not inspect holdout coverage values or PnL while resolving provenance.

## Parallel-source conclusion

DefiLlama also exposes stablecoin circulating-supply/history products, but current documentation mixes free/paid surfaces and does not by itself solve immutable PIT/revision semantics. It remains a secondary corroboration source, not an admissible primary Phase190 source at this stage.

## Decision

Coin Metrics stablecoin supply is the strongest current candidate for the next orthogonal V99 information family, but Phase190 is NOT YET ADMITTED. Next action is a deterministic catalog/Community-access/timestamp-semantics probe. No PnL is authorized until that gate passes.
