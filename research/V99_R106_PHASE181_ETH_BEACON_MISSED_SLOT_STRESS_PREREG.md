# V99 R106 — Phase181 Ethereum Beacon Missed-Slot Stress preregistration

Date: 2026-09-29
Status: PREREGISTERED / DATA-ONLY

## Scientific question
Can exogenous-looking degradation in Ethereum beacon-chain block production — specifically missed scheduled slots — provide an orthogonal, causal market-stress state without relying on miner-declared wall-clock timestamps or derivative-market variables already explored by V99?

This is a data/integrity hypothesis first. No alpha or PnL may be inspected until the DATA gate passes unchanged.

## Fixed causal construction
Ethereum beacon slots have a protocol-defined schedule. For each canonical execution/beacon observation, derive only information whose availability is established by a subsequently observed canonical block. A slot is not treated as known-missed at its scheduled instant; missed-slot status becomes usable only after a later canonical observation establishes the gap. Apply an additional market-bar t-1 lag after this availability mapping.

Precommitted descriptive windows: 32 slots (one epoch), 256 slots (8 epochs), 2048 slots (64 epochs). These windows are protocol-motivated and must not be searched or replaced based on PnL.

Candidate DATA-only features after admissibility:
- missed-slot count/rate per fixed window;
- longest consecutive missed-slot run per fixed window;
- time since last canonical observed block, computed from protocol slot schedule rather than proposer-supplied timestamp;
- first difference of missed-slot rate, fixed windows only.

No threshold, sign, transform, interaction, or trading rule is selected at this stage.

## DATA gate — fail closed
Required before feature admission:
1. canonical mainnet slot/block history covering the full TRAIN interval `[2021-12-01, 2024-01-18)` plus enough pre-roll for 2048 slots;
2. deterministic slot identity and parent-root continuity checks;
3. explicit handling of the Bellatrix/Merge transition without mixing unavailable execution semantics into pre-Merge rows;
4. no use of post-cutoff records to infer pre-cutoff canonicality or fill gaps;
5. no silent interpolation/imputation of missing source records;
6. SHA-256 provenance for raw/canonical inputs and byte-identical rebuild test;
7. coverage and gap report by temporal fold;
8. firewall rejecting any source row at/after `2024-01-18T00:00:00Z` from TRAIN construction;
9. t-1 market alignment invariant proving a feature at market bar t cannot change when slot/block records available only after t-1 are perturbed;
10. fixed source/provider chosen on DATA quality only, never PnL.

## Rejection conditions
Reject Phase181 before PnL if full TRAIN + pre-roll canonical coverage cannot be demonstrated, canonicality requires future/holdout knowledge, source semantics are ambiguous across the Merge, reproducibility fails, or market-time availability cannot be established conservatively.

## If DATA gate passes
Only then implement the fixed features and evaluate using the existing V99 chronological train-only selection, temporal folds, causal t-1, severe/supersevere costs, regime matrix, benchmark envelope, concentration/tail audits, and untouched final holdout. No gate is relaxed because prior hypotheses failed.

## Protected assets
V16 Frozen and V99 Frozen are read-only. Final holdout remains untouched during DATA/feature admission.
