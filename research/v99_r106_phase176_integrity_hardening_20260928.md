# V99 R106 — Phase176 integrity hardening / source evidence

Date: 2026-09-28
Scope: DATA / INTEGRITY ONLY. No alpha/PnL/holdout access.

## Independent audit finding

The first manifest implementation had two fail-closed logic defects for the likely shape of a market-wide borrowing archive:

1. It treated repeated timestamps as duplicates even when rows represented different currencies. For a multi-currency panel the natural discovery identity is `(timestamp, currency)` when a unique currency column exists.
2. It required every CSV member to contain every TRAIN month. That incorrectly rejects legitimate monthly/sharded archives. Coverage must be measured over the complete supplied archive set while preserving per-member ordering/integrity checks.

Both defects are now corrected. The inspector also detects duplicate `(timestamp,currency)` identities across archive members, preventing silent overlap/double-counting when monthly or ZIP shards overlap. Holdout firewall remains `[2021-12-01, 2024-01-18)` and any row outside it still fails the gate.

## New first-party source evidence

OKX's current historical-data page still advertises historical borrowing rates from December 2021 onward. Separately, OKX's official API changelog documents a public market lending/borrow-history endpoint and its migration from `/api/v5/asset/lending-rate-history` to `/api/v5/finance/savings/lending-rate-history`. This is useful evidence that the concept is public/market-wide rather than private account history.

This does **not** prove that the endpoint/archive has complete frozen-TRAIN coverage, immutable point-in-time history, exact units/schema, or publication timing suitable for causal t-1 use. Therefore it is evidence for source semantics only, not admission.

## Tests hardened

The Phase176 tests now assert:
- post-TRAIN rows are detected;
- true duplicate `(timestamp,currency)` identities are detected;
- non-monotonic time is detected;
- two currencies at the same timestamp are valid, not duplicates;
- epoch milliseconds parse as UTC.

## Decision

**SOURCE REMAINS NOT ADMITTED FOR ALPHA/PnL.** No threshold, sign, asset, currency, window, or return was inspected. No holdout row was read. V16 Frozen and V99 Frozen remain untouched.

## Next deterministic action

Continue first-party acquisition/probing only. If raw borrowing-rate archive objects become reproducibly accessible, run the hardened manifest over the entire frozen TRAIN archive set and persist hashes + manifest. Then separately prove publication semantics/t-1. Only after both DATA and CAUSALITY gates pass may an alpha hypothesis be preregistered.
