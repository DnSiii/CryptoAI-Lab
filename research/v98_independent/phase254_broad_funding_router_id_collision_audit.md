# V98 Independent — Phase254 Broad-Funding Router ID-collision audit

Status: **INVALID_PHASE_ID_COLLISION_BEFORE_PNL**.

Two independent research paths preregistered Phase254 concurrently.

Chronology from immutable Git commits:
- Shadow Equity Governor Phase254 preregistered first at 2026-10-14T19:52:53Z.
- Broad-Funding Router was preregistered later at 2026-10-14T19:54:03Z.

Therefore Phase254 is reserved for the earlier Shadow Equity Governor.

At the time this collision was detected:
- Shadow Phase254 had passed causal tests and was rebuilding source data, but had not entered its performance step.
- Broad-Funding Phase254 had not completed dependency installation and had not entered tests/source rebuild/performance.
- No Broad-Funding performance result had been produced, committed, uploaded or inspected.

The Broad-Funding hypothesis is migrated unchanged to Phase255 before performance. Its economic rule, parameters, comparator and gates are frozen exactly as already preregistered; only the phase identifier and namespaced filenames change.

Any output later produced by the already-running Phase254 Broad-Funding workflow is administratively invalid and must not be inspected, selected, cited as performance evidence, or used to alter Phase255.

This is a concurrency/governance repair, not a scientific rescue.
