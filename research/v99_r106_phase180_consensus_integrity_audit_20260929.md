# V99 R106 Phase180 — Bitcoin header consensus/integrity audit (2026-09-29)

Status: **DATA GATE ONLY — no alpha/PnL/holdout inspection.**

## Independent failure-mechanism audit

The first Phase180 gate checked chain continuity, MTP and whether `bits` changed only at a 2016-block boundary. That was necessary but insufficient: an arbitrary difficulty value at a legitimate boundary could pass. A corrupted/non-mainnet header hash could also pass because proof-of-work was not checked.

The gate is now explicitly Bitcoin mainnet and fail-closed on:

1. compact-target decoding and mainnet pow-limit;
2. 64-hex block-hash encoding and `hash <= target` proof-of-work;
3. exact parent/height continuity;
4. MTP consensus ordering;
5. unchanged `bits` away from retarget boundaries;
6. consensus retarget recomputation at each boundary, including 1/4x–4x timespan clamp;
7. mandatory 2016-block pre-roll when a retarget cannot otherwise be verified;
8. absolute holdout firewall at 2024-01-18T00:00:00Z.

## Causality interpretation

Header `time` remains miner-declared consensus metadata, not an exact observation/arrival clock. Passing consensus integrity therefore does **not** authorize same-bar use. Any eventual Phase180 feature remains t-1 shifted after aggregation. No sub-bar timing alpha is permitted.

## Anti-overfit / admission decision

No feature sign, window, threshold, asset subset, regime exception, PnL, benchmark comparison or holdout value was inspected while hardening this gate. Phase180 is **not admitted to alpha** until a complete TRAIN-only canonical header extract (plus required pre-roll) passes the deterministic gate and reproducibility checks.

## Next gate

Run the invariant suite in GitHub Actions. If green, acquire/construct canonical TRAIN-only mainnet headers with validation pre-roll, emit source/canonical SHA-256 manifests, run the gate twice for byte-identical output, then perform a coverage/cadence audit before preregistering exactly one block-production-stress feature family.
