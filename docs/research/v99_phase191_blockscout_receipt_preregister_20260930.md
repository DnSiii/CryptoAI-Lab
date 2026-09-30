# V99 Phase191 — Blockscout receipt provenance audit preregistration

Date: 2026-09-30
Scope: DATA_ONLY. Economic trial counter remains zero.

## Motivation
The prior Routescan path failed closed because `logIndex` was not canonical (`0x`). Phase191 must not infer, repair, renumber, or synthesize log identity/order. This preregistration defines an orthogonal source audit before any economic use.

## Candidate source
Blockscout Ethereum REST/API is considered only as a provenance transport. It is not approved by this document.

## Frozen audit gates (defined before observing economic outcomes)
1. Ethereum mainnet only; USDC and USDT canonical Ethereum contracts only.
2. Preserve the same three previously frozen TRAIN windows. No shrinking or moving windows to obtain a pass.
3. Every accepted event must have canonical non-null `blockHash`, `transactionHash`, and integer `logIndex` (or an independently receipt-verifiable exact equivalent). Missing/malformed identity is a hard fail.
4. Event emitter must equal the approved token contract. Topics/data must be structurally valid and decoded only with issuer-specific semantics already frozen for Phase191 (USDC Mint/Burn; USDT Issue/Redeem). No zero-address heuristic for USDT.
5. Duplicate `(blockHash, transactionHash, logIndex)` identities are forbidden unless byte-identical and deterministically deduplicated before aggregation; conflicting duplicates are a hard fail.
6. A block height mapping to conflicting block hashes is a hard fail.
7. Finality must be established independently from the candidate event payload; unfinalized observations are forbidden.
8. Determinism: two identical DATA_ONLY runs over fixed windows must produce byte-identical canonicalized output/hash.
9. Causality: daily feature aggregation remains t-1. No same-day event may influence a decision timestamp that precedes the event.
10. No price, PnL, benchmark, regime labels, validation outcome, or holdout data may be read during this source audit.

## Decision rule
PASS only if all gates pass for both assets across all three frozen TRAIN windows. Otherwise FAIL_CLOSED with a machine-readable reason. A transport/source failure is not a scientific rejection of the stablecoin-flow hypothesis and does not increment the economic trial counter.

## If PASS
Only then implement deterministic issuer-specific reconciliation and a single preregistered economic hypothesis. The hypothesis must be selected chronologically on TRAIN, retain temporal folds, severe/supersevere costs, regime matrix, benchmark envelope, and untouched holdout.

## If FAIL
Do not patch missing provenance by inference. Record the failure mechanism and inspect a scientifically orthogonal immutable source/receipt path.