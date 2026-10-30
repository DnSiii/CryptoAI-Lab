# V98 Independent Phase243 — evidence-inventory integrity audit (2026-10-08)

Scope: research/v98-independent-zero; V98-only metadata and training reports. No 2026+ holdout, no external-engine files, no PnL-based parameter selection.

## Defects in the original inventory builder
1. The reports directory scan accepts any filename containing "phase", including non-V98 files. It must be an explicit V98 namespace allowlist.
2. The free-text search labels preregistrations as rejected merely because they warn against REJECTED_NO_RESCUE families; Phase243 itself is a false-positive example.
3. "CHAMPION" or "PROMOTED" mentioned in a rejection narrative is not evidence of promotion.
4. Legacy authoritative decisions under research/v98_independent_phase*.md are omitted.
5. PASS_TRAINING_FREEZE_FOR_VALIDATION and REJECT_VALIDATION_NO_RESCUE require full-token parsing, not partial narrative matches.
6. Validation-phase rejection must disqualify the earlier frozen training candidate (Phase180 -> Phase181; Phase185 -> Phase186; Phase065 -> Phase066; Phase075 -> Phase076).
7. The prior opened Phase083 holdout is permanently ineligible for selection per V98 state.

## Independent training-results audit (not promotion)
Existing V98-only committed Phase225, Phase233, Phase235 and Phase239 result payloads each contain eight specs and three calendar folds, with 7/14/28 bp cost scenarios. Reapplied the frozen annual gate (base return>0, PF>1, MDD>=-35%, positive days>50%, severe return>0 and severe PF>1) without modifying any result: 0/8 survivors in each family (0/32 specs). Across 96 spec-year base cells, 0 positive compounded returns; Phase235 and Phase239 each have only one PF>1 cell. This is negative evidence, not a new tuning signal.

Phase222 has a preregistration and evaluator but no committed Phase222 result payload in the inspected V98 tree; it is not adjudicated here.

## Architecture disposition
Current V98 state declares champion=null and all seven Phase243 slots awaiting inventory/new research. Training-only passes cannot be treated as eligible when their linked untouched validation rejected them. No sleeve is promoted from this audit. Phase241/242 remain preregistered isolated-alpha backlog under the new Phase243 architecture; no system PnL has been evaluated.

## Reproducibility/next gate
A hardened V98-only inventory implementation and 15 deterministic negative-control unit tests were prepared locally, including V99 filename decoy, hypothetical rejection, validation lineage and opened-holdout exclusion. Remote executable update was blocked by integration safety checks; do not represent it as deployed. Next: land the validated inventory tool through an authorized path, run it against the full V98 checkout, inspect every candidate source, then preregister a seven-slot system before any portfolio PnL. Holdout remains locked.
