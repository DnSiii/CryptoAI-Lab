# V99 Phase191 — Blockscout DATA_ONLY handoff

Status: DATA_ONLY source-integrity phase. No economic candidate is promoted by this phase.

## Frozen scientific boundary

- V16 Frozen and V99 Frozen are immutable.
- The only admissible windows are the three pre-registered TRAIN block windows in `research/tools/v99_phase191_blockscout_frozen_windows.py`.
- HOLDOUT, price/PnL, regime scoring, benchmark comparison, parameter tuning, and candidate selection remain closed during Phase191.
- `economic_trials` must remain `0` throughout this source audit.
- Any eventual feature derived from this source must be causal at decision time (`t-1`) and must enter the normal chronological train-only / temporal-fold / severe+supersevere-cost / regime-matrix / benchmark-envelope gates. Phase191 cannot waive any downstream gate.

## Evidence harvested before this handoff

The Blockscout transport has exposed multiple source-pathologies while still upstream of economic evaluation: HTTP 429 rate limits, dense pagination, missing `blockHash`, and right-padded `null` topic entries. The current collector is intentionally fail-closed except for the narrowly evidenced normalization of *trailing* `null` topic padding; internal/leading nulls and malformed topic hashes remain fatal.

Checkpointing is incremental and atomic (`tmp -> replace`) and the workflow restores prior DATA_ONLY snapshots before continuing. Recursive block-window bisection is transport-only: it does not change the three externally pre-registered TRAIN windows or select observations using outcomes.

## Acceptance gates — preregistered before seeing any economic result

A Phase191 source snapshot may advance beyond DATA_ONLY only if all of the following pass:

1. Capture completes for both frozen contracts across all three TRAIN windows.
2. Two offline, zero-network replays of the exact same snapshot are byte-identical.
3. Every accepted row has canonical tx hash, block number, log index, address, topic structure, data payload, and a verified/canonical block identity; removed/reorg-ambiguous rows are not silently accepted.
4. Contract identity and issuer-specific semantics reconcile independently; ambiguous issuer attribution is a rejection, not a tunable branch.
5. Event timestamps/order used downstream are demonstrably causal and compatible with `t-1`; no same-bar/future information is permitted.
6. Source diagnostics (pagination splits, repaired block hashes, trailing-null-topic rows, duplicate-identity count, snapshot SHA256) are persisted so a later audit can reproduce the exact accepted dataset.
7. V16 Frozen and V99 Frozen guards remain clean.

Failure of any item keeps the source quarantined and leaves `economic_trials = 0`.

## Independent failure-mechanism audit

The collector is fail-closed on duplicate canonical event identity `(blockHash, transactionHash, logIndex)` after transport pages/subwindows are concatenated; it does **not** silently deduplicate or sort away overlap. A successful window therefore reports `duplicate_identities = 0`. The acceptance report must also be inspected for concentration: repaired-hash or trailing-null-topic concentration in a narrow block interval can indicate provider-specific pathology rather than harmless formatting.

The collector now embeds the SHA256 of the canonical serialized source snapshot and the number of recursive pagination splits in the deterministic replay output. That hash, together with byte-identical offline replay, is the reproducibility anchor; a later run with a different source SHA must be treated as a distinct source realization and must not be silently compared as though it were identical evidence.

## Next scientifically distinct step after source acceptance

Do **not** tune a trading rule immediately. First build the issuer-specific causal `t-1` feature table from the accepted snapshot and run a feature-only audit: availability lag, missingness by temporal fold, event-rate concentration by contract/window, tail concentration, and regime-independent coverage. Only if that audit passes should one pre-register a single economic hypothesis and send it through the existing chronological train-only selection, temporal folds, severe/supersevere costs, regime matrix, benchmark envelope, reproducibility, and anti-overfit gates.

If Phase191 fails, diagnose the source failure and either repair it with a source-semantic justification or reject this data family. Do not compensate by weakening economic gates.
