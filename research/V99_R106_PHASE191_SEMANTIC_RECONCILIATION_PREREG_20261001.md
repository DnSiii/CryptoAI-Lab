# V99 R106 Phase191 — issuer-semantic reconciliation preregistration (2026-10-01)

Status: preregistered before frozen-window harvest. Scope: DATA_ONLY. Economic trials: 0. Holdout: untouched.

## Purpose

The next gate tests whether canonical Ethereum logs can be converted into issuer-specific stablecoin supply-flow observations without price, return, PnL, regime, benchmark, validation, or holdout information. This document freezes the interpretation before seeing the frozen-window output.

## Fixed inputs

Only canonical USDC (`0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48`) and USDT (`0xdac17f958d2ee523a2206206994597c13d831ec7`) logs from the already frozen TRAIN windows 17,000,000–17,000,199; 18,000,000–18,000,199; and 19,000,000–19,000,199 are eligible. No window may be moved, shortened, substituted, or selected after observing results.

## USDC semantics

USDC supply flow is recognized only from canonical `Transfer(address,address,uint256)` events emitted by the canonical token contract. Mint requires `from == 0x0000000000000000000000000000000000000000`; burn requires `to == 0x0000000000000000000000000000000000000000`. Ordinary transfers are not supply flow. Malformed topic count, noncanonical indexed addresses, ambiguous zero-address decoding, or invalid amount encoding fails closed.

## USDT semantics

USDT must be reconciled using its issuer-specific issuance/redemption semantics rather than assuming modern ERC-20 mint/burn behavior. `Issue(uint256)` and `Redeem(uint256)` events from the canonical contract are the primary supply-flow evidence. `Transfer` events may be used only as reconciliation evidence where contract semantics support it; they must not silently replace Issue/Redeem. Unknown or ambiguous topic0 values are classified as unknown, never inferred into issuance/redemption.

## Identity, ordering, and causality

Every accepted event retains `(blockHash, transactionHash, logIndex)` and block number. Duplicate identities or conflicting block hashes fail closed. Aggregation is chronological. Any eventual model feature derived from block/day t becomes eligible no earlier than t+1; same-period information is forbidden. This DATA_ONLY stage does not authorize an economic backtest.

## Required reconciliation report

For each asset/window report: raw canonical log count; recognized supply-event count; mint/issue amount; burn/redeem amount; net flow; unknown-topic count; malformed/ambiguous count; duplicate count; block-identity/finality status; and deterministic output hash. Amounts remain integer base units in the integrity layer; decimal conversion is presentation-only and cannot affect identities or sums.

## PASS / FAIL_CLOSED

PASS requires all six asset-window cells to have canonical identities, complete pagination, no conflicting block hashes, deterministic replay, independently supported block identity/finality, and unambiguous issuer-specific supply semantics. Any missing source evidence, transport truncation, schema ambiguity, unexplained semantic mismatch, or nondeterminism is FAIL_CLOSED and leaves `economic_trials = 0`.

## Economic firewall

No direction, threshold, lag beyond mandatory t-1, weighting, regime split, cost assumption, benchmark comparison, or selection rule may be tuned from this gate. A later economic hypothesis must be separately preregistered only after this semantic gate passes. Severe/supersevere costs, temporal folds, chronological train-only selection, benchmark envelope, and untouched holdout remain mandatory for any later authorized trial.
