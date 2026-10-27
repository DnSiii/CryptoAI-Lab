# V99 I1 — original TRAIN fold binding and CASH wallet validity guard (2026-10-27, preregistered before code)

Status **SOURCE_ONLY/HOLD — NO PROMOTION**. This is a correctness/security guard for the already fixed I1 fixture-only integration, not a new alpha candidate, economic TRAIN, return claim, or strategy retune.

## Observed material defects
1. `_check_signal` accepts any integer fold 1..5, even when its `decision_ms` belongs to another chronological fold. The independent oracle also only checks membership, so an altered fold label can pass both implementations, undermining any future five-fold evidence.
2. `fixture_open_fixed_vertical` does not call `wallet.check()` before the no-signal/no-eligible-book CASH return. Consequently a malformed or insolvent input wallet can receive a nominally valid CASH verdict without state validation. The independent CASH oracle compares equality but does not independently check basic wallet solvency.

## Fixed acceptance rule, predeclared
- Bind every I1 decision timestamp to the **existing frozen** chronological FOLD_EDGES: 2021-12-09T00:00Z; 2022-04-20T04:00Z; 2022-08-30T09:00Z; 2023-01-09T14:00Z; 2023-05-21T19:00Z; 2023-10-01T00:00Z. A supplied `fold` must equal the unique interval containing `decision_ms`, otherwise raise `SIGNAL_FOLD_TIME_MISMATCH`. The independent oracle must compute the same edges *without importing the primary selector or its fold helper*.
- Validate wallet invariants on **all** decision paths, including CASH. The independent oracle must independently reject a CASH proof if its before-wallet has invalid initial coin, negative cash/reserve, reserve exceeding cash, bad clock, or an empty-wallet reserve/marks inconsistency. Never interpret an unchanged invalid wallet as certified CASH.
- Add adversarial tests for a valid Monday with deliberately wrong fold and an invalid wallet with a NO_PREMIUM signal, including forged CASH oracle. Retain positive baseline severe/supersevere tests.
- Run actual GitHub CI and original-source intersection/independent byte oracle; preserve the historical block. No economic ROI, no orders, no validation/holdout, no Frozen/paper/champion changes. If CI fails, correct only implementation/fixtures, not strategy rules.

## Scope
Only this preregistration, the I1 fixed bridge, independent I1 fixture oracle, their isolated tests, and (after actual evidence) a result note. The external historical BTC/ETH 2021–2023 option quote/depth and native terms blocker remains unchanged.
