# V99 R106 Phase191 — issuer-semantic reconciliation preregistration (2026-10-01)

Status: preregistered before frozen-window harvest. Scope: DATA_ONLY. Economic trials: 0. Holdout: untouched.

## Precedence / anti-retuning rule

The pre-existing `research/tools/v99_phase191_event_semantics_guard.py` is the controlling semantic specification. This document may make its reporting requirements explicit but MUST NOT redefine those semantics after data are observed. An independent audit caught an initially drafted Transfer-only USDC wording before any frozen-window result was harvested; that wording conflicted with the already-frozen guard and is therefore void. No data result was inspected to make this correction.

## Fixed inputs

Only canonical USDC (`0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48`) and USDT (`0xdac17f958d2ee523a2206206994597c13d831ec7`) logs from the already frozen TRAIN windows 17,000,000–17,000,199; 18,000,000–18,000,199; and 19,000,000–19,000,199 are eligible. No window may be moved, shortened, substituted, or selected after observing results.

## Frozen issuer semantics

For USDC, native `Mint`/`Burn` amounts are the supply-flow view encoded by the existing guard. Zero-address `Transfer` amounts are independent reconciliation evidence when present; if both views are present and disagree, the gate fails closed. Ordinary transfers are not supply flow.

For USDT, `Issue` and `Redeem` are the supply-flow events. A zero-address `Transfer` MUST NOT be silently treated as issuance/redemption; the existing guard explicitly fails that case. Unknown or ambiguous events remain unknown and cannot be inferred into a favorable class.

## Identity, ordering, and causality

Every accepted event retains `(blockHash, transactionHash, logIndex)` and block number. Duplicate identities, conflicting block hashes, malformed immutable hashes, nonpositive amounts/timestamps, or non-strict event order fail closed under the existing guard. Aggregation is chronological. `lagged_net_by_block` exposes at block b only cumulative signed flow through blocks strictly before b, preserving causal t-1. This DATA_ONLY stage authorizes no economic backtest.

## Required reconciliation report

For each asset/window report: raw canonical log count; recognized supply-event count; native mint/issue amount; native burn/redeem amount; reconciliation evidence where applicable; net flow; unknown/malformed count; duplicate/conflict status; block-identity/finality status; and deterministic output hash. Integrity-layer amounts remain integer base units.

## PASS / FAIL_CLOSED

PASS requires all six asset-window cells to have complete pagination, canonical identity, no conflicting block hashes, deterministic replay, independently supported block identity/finality, and issuer-specific semantic reconciliation consistent with the pre-existing guard. Missing source evidence, transport truncation, schema ambiguity, semantic mismatch, or nondeterminism is FAIL_CLOSED and leaves `economic_trials = 0`.

## Economic firewall

No direction, threshold, extra lag, weighting, regime split, cost assumption, benchmark comparison, or selection rule may be tuned from this gate. A later economic hypothesis must be separately preregistered only after the semantic/data gate passes. Severe/supersevere costs, temporal folds, chronological train-only selection, benchmark envelope, reproducibility, and untouched holdout remain mandatory for any later authorized trial.
