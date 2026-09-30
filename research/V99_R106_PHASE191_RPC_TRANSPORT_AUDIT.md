# V99 R106 Phase191 — RPC transport audit

Status: DATA_ONLY / no economic trial / holdout untouched.

## Evidence harvested

Run 36759026209 executed commit `524210521c556aba77304c9a38d76b16605a93af`. The Frozen-path guard passed, then the collector failed in `select_endpoint()` before accepting any chain sample. None of the seven configured transports simultaneously passed the pre-registered `finalized` + historical `eth_getLogs` archive probe.

Observed failure classes, in configured order: HTTP 403; HTTP 525; API-key authentication required; HTTP 400; HTTP 403; HTTP 429; JSON-RPC `-32046 Cannot fulfill request`.

This supersedes the earlier three-endpoint transport observation. It remains an infrastructure/access result, not evidence for or against the stablecoin-flow hypothesis and not evidence of empty historical coverage.

## Scientific decision

1. Do not reinterpret transport failure as a negative sample.
2. Do not open price, PnL, regime, benchmark, severe/supersevere, or holdout evaluation until real finalized TRAIN-era logs pass provenance/coverage gates.
3. Do not alter the three fixed probe windows (17,000,000–17,000,199; 18,000,000–18,000,199; 19,000,000–19,000,199) in response to transport outcomes.
4. Public endpoints are transport fallbacks only. Adding/removing a transport does not create an economic trial and must not alter event semantics.
5. Fail closed if every transport is unavailable, if a window is not finalized, if a provenance field is absent/malformed, if a log identity duplicates, if a height has conflicting block hashes, or if any contract/window has zero accepted logs.
6. Keep one endpoint pinned for the entire successful collection. Never mix chunks from heterogeneous RPCs merely to complete coverage.

## Current remediation status

Commit `52421052` pins one endpoint per coverage run and requires that endpoint to pass both `finalized` and earliest-window archive-log probes before selection. This removes the risk that fallback logic silently combines histories from different transports. Chunk size 50 is transport-only and leaves the scientific windows unchanged.

The pinned-endpoint workflow behaved correctly by failing closed when no transport qualified. Economic trial count remains zero; Phase191 is neither rejected nor promoted.

## Advancement gate

Phase191 may advance beyond DATA_ONLY only after:

- one single endpoint passes finalized + archive probes and serves the complete run;
- all six contract/window cells (USDC + USDT across three fixed TRAIN-era windows) are non-empty;
- all accepted logs have blockHash, transactionHash, logIndex and blockNumber provenance;
- windows are below a finalized tip;
- two independent executions emit byte-identical deterministic coverage payloads;
- Frozen-path guard passes.

After that, and still before PnL, the next unit is event-semantic reconciliation: USDC Mint/Burn/zero-address Transfer semantics and USDT Issue/Redeem semantics must be decoded separately and reconciled against immutable log provenance. Only a single pre-registered economic hypothesis may follow. No post-hoc inversion, threshold search, window search, reduced-window rescue, explorer aggregate substitution, or stablecoin-family rescue is permitted from Phase191 evidence.

## Safe parallel work while transport remains unavailable

Semantic/invariant tooling may continue using synthetic fixtures only: event-family decoding, deduplication identity, sign convention, block/log ordering and t-1 aggregation. This work remains PnL-free and cannot inspect holdout observations.
