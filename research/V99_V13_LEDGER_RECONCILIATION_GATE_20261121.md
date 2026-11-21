# V13 historical ledger — reconciliation gate (2026-11-21)

Status: **BLOCKED / research-only / NO PROMOTION**. This is a read-only investigation plan, not a repaired ledger or independent execution certification.

## Verified in repository

- `scripts/verify_paper_cycle_v13.py` checks PAPER_ONLY, forbids real orders, compares state/snapshot, validates simulated order side, positive displayed notional, sub-cent positive unrounded notional (< R$0.005), and raw/display reconciliation when raw exists.
- `scripts/triage_v13_ledger_discrepancies.py` uses Decimal/ROUND_HALF_EVEN, emits row indices and SHA-256, and exits 2 for missing raw or mismatch. Generated unrounded notional is **not** exchange-fill evidence.
- Actions 44910642961: adversarial-classifier succeeded; published-ledger-discrepancy-triage and published-ledger-provenance failed. Thus CI did **not** certify historical ledger continuity.
- Prior run reported 1,705 adjustments: 1,425 missing raw, 276 mismatch, 3 matched, 1 simulated subcent. These are audit classifications, not proven erroneous fills. Large reported differences (BTC R$130.85, ETH R$188.89) cannot be explained by two-decimal rounding alone.

## Root-cause investigation, no history mutation

1. Pin the `paper-results` commit SHA and SHA-256 of original ledger, state, snapshot, sync and generator source. Keep copies immutable and annotate original timestamps.
2. For each mismatch, extract original decision/adjustment indices, symbol, time, weights, displayed BRL, raw BRL, notional denomination, price timestamp, BRL FX rate and source revision. Compare `shown - raw` to ±R$0.005; differences beyond that threshold require tracing the **original** calculation/FX provenance, not changing the threshold.
3. For 1,425 missing-raw entries, find generator commit at each historical timestamp and determine whether the field was absent by schema version, serialization or data loss. Do not backfill with reconstructed values presented as original evidence.
4. Establish an independent, time-matched exchange/FX source receipt where available, including source URI, observation timestamp, currency, fee/funding tier and checksum. Distinguish *simulated paper notional* from actual exchange fills: PAPER_ONLY does not imply real executed orders or receipts.
5. Prepare a separate, additive reconciliation sidecar keyed by immutable original row hashes and source SHA, with classification: proven rounding, verified original calculation, unresolved provenance, or genuine inconsistency. Do not rewrite ledger/trades or `paper-results`.
6. Re-run adversarial tests and complete original-ledger verification in Actions; require 0 unexplained mismatches and 0 unresolved provenance entries for certification. Publish stale/research-only notice on public dashboard until verified market timestamp and paper refresh are independently confirmed.

## Engine boundary

V99 Frozen, V16 Frozen, historical paper and R106 train/validation/holdout remain untouched. C1 and D1 rejected; I1 blocked by 658/661 days of unlicensed/unreceived Deribit options history. Do not claim a validated profitable engine, infer ROI from CI success, unlock validation/holdout, or place orders.
