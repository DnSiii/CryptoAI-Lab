# V99 R106 — Phase177 first-party history gate decision

Date: 2026-09-29
Status: fail-closed; no PnL.

## Evidence harvested

Current Deribit documentation establishes that volatility-index instruments and market-data requests existed in the exchange API lineage, and that market-data messages include MarkPrice and UnderlyingPx fields. This supports historical contemporaneous existence of the information class, but it does **not** establish that Deribit currently exposes a first-party replay/archive containing the complete point-in-time option surface for the immutable TRAIN interval.

The current API documentation exposes production real-time interfaces; the documentation evidence located in this audit does not identify a public first-party endpoint/archive that can replay historical option mark-price/IV snapshots over `[2021-12-01, 2024-01-18)`.

## Scientific decision

Existence-at-the-time != retrievable point-in-time history.

Phase177 therefore remains blocked at the DATA gate. We will not:
- infer historical marks from current instrument metadata;
- substitute a third-party vendor/archive merely to obtain coverage;
- reconstruct missing surface history from future-known listings;
- inspect returns to choose a convenient subset of dates/contracts;
- weaken the immutable TRAIN interval.

## What would reopen Phase177

Only one of the following:
1. a Deribit first-party historical replay/archive with documented timestamps and complete TRAIN coverage; or
2. immutable first-party raw captures already present in the repository whose provenance predates decisions and whose hashes/coverage pass the preregistered integrity specification.

Until then Phase177 is **NOT ADMITTED FOR ALPHA/PNL**.

## Next research direction

The next hypothesis must be scientifically distinct and use a source whose historical point-in-time availability can be proven before alpha design. It must not recycle the already exhausted OHLCV/funding/OI/crowding/taker/premium/order-book/macro families merely under a new transform.

V16 Frozen, V99 Frozen and holdout remain untouched.