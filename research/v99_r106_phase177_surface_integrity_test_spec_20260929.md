# V99 R106 — Phase177 option-surface integrity test specification

Date: 2026-09-29
Status: preregistered before any Phase177 PnL.

## Purpose

Define deterministic fail-closed checks for a future first-party Deribit historical option mark-price dataset. This document does not admit any dataset and does not authorize PnL.

## Immutable interval

TRAIN candidate interval: `[2021-12-01T00:00:00Z, 2024-01-18T00:00:00Z)`.
Any row at or after `2024-01-18T00:00:00Z` is a hard failure for the TRAIN artifact.

## Required raw identity

At minimum each observation must preserve: availability/event timestamp, instrument name, currency/index family, expiry, strike, option side, mark price and any exchange-supplied IV/underlying/forward fields used by reconstruction. Raw files are immutable and SHA-256 hashed before parsing.

Duplicate identity is `(availability_timestamp, instrument_name)` rather than timestamp alone. Conflicting duplicate payloads are a hard failure; byte-identical duplicates must be counted and explicitly deduplicated deterministically.

## Temporal/causal checks

- timestamps parse as UTC and are monotonic within each deterministic shard after canonical sorting;
- no post-firewall rows;
- no current-state metadata may fill historical fields;
- decision features use only observations available by the decision cutoff and then receive the project's additional t-1 lag;
- expiry/strike selection is performed from the contemporaneously observable universe, not from a hindsight list;
- publication gaps and stale marks are measured, never silently forward-filled.

## Coverage report

Emit by calendar month and existing temporal fold: expected decision timestamps, usable surface timestamps, missing fraction, stale fraction, number of listed instruments, number of admissible ATM brackets, expiry-roll failures and longest contiguous gap. Aggregate coverage cannot hide a failed fold.

## Numerical sanity

Reject non-finite/negative prices, impossible expiry ordering, malformed strikes, and violations of the preregistered option-price/arbitrage sanity bounds. Solver/interpolation code must be deterministic and report failures rather than substituting convenient contracts.

## Reproducibility

A manifest must include source identifiers, retrieval timestamp, raw SHA-256 hashes, parser version/commit, canonical row count, min/max event timestamps, duplicate/conflict counts, missing/stale statistics and output SHA-256. A second clean run over identical raw inputs must produce the identical canonical hash.

## Scientific gate

Only after provenance + all integrity checks pass may Phase177 define or execute an alpha. Any future alpha specification must be preregistered before returns are inspected and must retain temporal folds, severe/supersevere costs, regime matrix, benchmark envelope, concentration/tail audits and untouched holdout.

V16 Frozen and V99 Frozen untouched.
