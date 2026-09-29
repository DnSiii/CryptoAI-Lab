# V99 R106 — Phase180 Bitcoin block-production stress DATA preregistration

Date: 2026-09-29
Status: preregistered before data harvest, feature construction or PnL.

## Scientifically distinct hypothesis family

Test an orthogonal **Bitcoin network block-production stress** family using only canonical Bitcoin block headers available by time t. The economic mechanism is exogenous operational/security stress: unexpectedly slow/fast block production relative to the protocol difficulty state may capture mining/network disruption not represented by exchange OHLCV, funding, OI, taker flow, insurance balances or macro releases.

This phase is DATA/INTEGRITY only. No direction, threshold, lookback, normalization, interaction or exposure is authorized.

## Source and causality gate

Preferred source is a reproducible Bitcoin Core chain snapshot / RPC-derived header table, not a mutable third-party analytics series. For each accepted block, preserve at minimum block hash, height, previous-block hash, header timestamp, bits/difficulty representation and chain identity.

Before alpha design, prove:
- canonical chain continuity across immutable TRAIN `[2021-12-01T00:00:00Z, 2024-01-18T00:00:00Z)`;
- no post-firewall block used for cleaning, normalization, cadence estimation or feature construction;
- block header availability is assigned causally: a block may influence a bar only after that block is known, then the project t-1 execution lag is applied;
- SHA-256 of raw/exported header snapshot and canonical table;
- monotone heights, exact parent-hash continuity, duplicate/conflicting-height checks;
- timestamp sanity checks without silently rewriting miner timestamps;
- difficulty-transition consistency at protocol retarget boundaries;
- deterministic reconstruction from frozen raw bytes;
- coverage across every existing temporal fold.

## Anti-overfit preregistration

No returns/PnL may be inspected in this DATA phase. If DATA passes, a separate alpha preregistration must freeze exactly one economically justified realization before evaluation. No sign search, threshold search, lookback grid, failed-fold deletion, TRAIN shortening, post-hoc asset subset, holdout access or third-party gap fill.

Any later alpha evaluation must retain chronological train-only selection, temporal folds, severe/supersevere costs, regime matrix, benchmark envelope, concentration/tail audits, causality t-1 and reproducibility.

V16 Frozen and V99 Frozen untouched.
