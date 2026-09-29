# V99 R106 — Phase179 BitMEX insurance-fund DATA preregistration

Date: 2026-09-29
Status: preregistered before harvesting and before any alpha/PnL.

## Scientifically distinct realization

Phase178 rejected the Binance realization because archive immutability and balance-change attribution could not be proven. Phase179 tests the same broad systemic-loss-absorption mechanism on a different venue whose first-party API explicitly documents `GET /api/v1/insurance` as **Get Insurance Fund History** and exposes timestamp filtering/pagination.

This is a DATA/INTEGRITY phase only. No direction, threshold, smoothing, lookback, currency subset, event definition or exposure is authorized here.

## Immutable TRAIN gate

TRAIN remains `[2021-12-01T00:00:00Z, 2024-01-18T00:00:00Z)`; endpoint is a hard firewall. Before alpha design, harvest must prove:

- public first-party endpoint, no user/account semantics;
- complete pagination for the requested TRAIN interval, deterministic query parameters and stable sort;
- raw-response SHA-256 per page and canonical-table SHA-256;
- schema and units by currency;
- min/max timestamp, row count, duplicate/conflict checks;
- expected cadence inferred without looking at returns, missing-timestamp map and longest gap;
- coverage for every existing temporal fold;
- no post-firewall row used for cleaning, cadence inference, normalization or interpolation;
- explicit availability semantics; conservative project t-1 applied after source timestamp;
- rerun reproducibility: same canonical bytes/hash from the frozen raw snapshot.

## Semantic audit required

Before alpha design, first-party documentation/source evidence must determine whether balance changes can arise from venue deposits, withdrawals, transfers, contract/currency migrations or other administrative actions. If liquidation stress cannot be separated from administrative changes, either a preregistered event taxonomy must be possible from first-party contemporaneous fields or the phase fails closed.

## Anti-overfit / no-rescue

No PnL inspection until DATA gate passes. No sign search, threshold search, event-window search, smoothing search, currency cherry-picking, TRAIN shortening, failed-fold deletion, third-party fill or holdout access.

If DATA passes, a separate alpha preregistration is mandatory before returns are inspected and must retain chronological train-only selection, temporal folds, severe/supersevere costs, regime matrix, benchmark envelope, concentration/tail audits and reproducibility.

V16 Frozen and V99 Frozen untouched.
