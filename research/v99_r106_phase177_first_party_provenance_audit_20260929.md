# V99 R106 — Phase177 first-party provenance audit

Date: 2026-09-29
Scope: DATA/INTEGRITY only. No return/PnL/holdout inspection.

## New first-party evidence

Deribit release notes dated 2021-06-25 state that ETH DVOL was launched while BTC DVOL was already live. The same release notes document an optimized `markprice.options.{index_name}` feed whose initial event sent all option mark prices, subsequent events propagated changes, values were rounded to four decimals, and a timestamp field was added. This is contemporaneous evidence that a timestamped option mark-price surface existed before the V99 TRAIN start (2021-12-01).

This materially improves provenance versus reconstructing IV from sparse last trades: the historical scientific target should be the timestamped mark-price surface if a first-party historical replay/export can be proven, because it avoids endogenous selection on only instruments that happened to trade.

## Important caveat

Existence of the live feed in June 2021 does **not** prove that Deribit currently exposes a complete first-party historical archive/replay for every TRAIN timestamp. Modern APIs or current instrument metadata cannot be silently substituted for point-in-time observations.

## Admission decision

Phase177 remains fail-closed and DATA/INTEGRITY-only. Before alpha/PnL, require all of:

1. first-party historical retrieval/replay path for the timestamped option mark-price surface;
2. complete TRAIN-only coverage audit over `[2021-12-01T00:00:00Z, 2024-01-18T00:00:00Z)` with the existing holdout firewall;
3. explicit event/availability timestamps and an additional t-1 decision lag;
4. contemporaneous instrument identity/expiry/strike metadata sufficient to apply the preregistered nearest-forward-ATM construction without modern-catalog leakage;
5. deterministic manifests (SHA-256, row counts, min/max timestamps, duplicate identity, monotonicity, missing periods and per-fold coverage);
6. no arbitrary forward-fill across stale marks; missing/stale states remain missing under a preregistered rule;
7. byte-identical reconstruction on rerun.

If first-party historical mark-price replay cannot be proven, reject this route rather than falling back to third-party archives or tuning a trade-based staleness threshold after seeing PnL.

V16 Frozen and V99 Frozen untouched. Holdout untouched.
