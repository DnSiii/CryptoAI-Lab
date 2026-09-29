# V99 R106 — Phase177 reconstruction integrity specification

Date: 2026-09-29
Status: DATA/INTEGRITY ONLY — no PnL, no holdout.

## Purpose

Materially harden the preregistered deterministic 30-day BTC options-IV reconstruction before any extraction or alpha evaluation. This document does not alter the fixed economic construction in the Phase177 preregistration.

## Fail-closed row identity

Every raw observation must retain source endpoint, request parameters, instrument_name, event timestamp, conservative availability timestamp, trade/sequence identifier when supplied, price, amount, direction and source retrieval timestamp. Duplicate detection is keyed by the strongest exchange identity available; timestamp alone is never a duplicate key because many instruments legitimately trade simultaneously.

## Instrument admissibility

Only BTC option instruments whose metadata can be recovered first-party are admissible. Instrument name parsing must agree with exchange metadata for expiry, strike and call/put type. Any disagreement, missing expiry, missing strike or ambiguous legacy naming rejects that instrument rather than inferring it.

## Causal availability

Feature state at hour H may use only rows with conservative availability_time < H. After hourly aggregation, the entire reconstructed state receives the separately preregistered additional one-hour t-1 shift. Retrieval time in 2026 is provenance metadata only and must never substitute for historical publication time.

## Frozen-TRAIN firewall

Raw-cache construction and all integrity reports must reject any observation with event or availability timestamp at/after 2024-01-18T00:00:00Z. No post-boundary row may be used to infer gaps, calibrate solver tolerances, select expiries, repair metadata, choose signs or estimate missing states.

## Coverage gate

Passing requires deterministic coverage reporting for every TRAIN calendar month and every temporal fold. Reports must include rows/instruments/expiries by month, missing hours, maximum consecutive missing hours, solver failures, and hours where the two expiries bracketing 30 days cannot both be constructed. Missingness is reported, never future-filled.

## Numerical invariants

Black-style inversion must use fixed tolerances from code constants, deterministic initialisation and explicit arbitrage-bound checks. Non-finite inputs, prices outside bounds, non-convergence, non-positive time-to-expiry or non-positive forward are missing. Identical immutable cache must reproduce byte-identical hourly feature output and manifest hashes.

## Anti-overfit lock

No alternative strike bucket, delta target, expiry pair, interpolation method, smoothing, clipping, sign, asset, solver tolerance or missing-data repair may be tried after PnL inspection. If this canonical reconstruction cannot pass DATA/INTEGRITY, Phase177 is rejected without rescue tuning.

## Promotion boundary

This specification authorizes no alpha and no PnL. Only after first-party historical inputs pass provenance, causal availability, frozen-TRAIN, coverage, duplicate, numerical and reproducibility gates may a separate first-alpha hypothesis be preregistered.

V16 Frozen and V99 Frozen remain untouched.