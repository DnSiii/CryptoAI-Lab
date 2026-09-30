# V99 R106 Phase191 — RPC transport audit

Status: DATA_ONLY / no economic trial / holdout untouched.

## Evidence harvested

Run 36744484177 reached the Frozen-path guard successfully, then failed before any chain sample was accepted. All three configured transports failed: one HTTP 403, one HTTP 525, and one endpoint requiring an API key. Therefore the run is a transport/access failure, not evidence for or against the stablecoin hypothesis and not evidence of empty historical coverage.

## Scientific decision

1. Do not reinterpret transport failure as a negative sample.
2. Do not open price, PnL, regime, benchmark, severe/supersevere, or holdout evaluation until real finalized TRAIN-era logs pass provenance/coverage gates.
3. Do not alter the three fixed probe windows (17,000,000–17,000,199; 18,000,000–18,000,199; 19,000,000–19,000,199) in response to transport outcomes.
4. Public endpoints are transport fallbacks only. Adding/removing a transport does not create an economic trial and must not alter event semantics.
5. Fail closed if every transport is unavailable, if a window is not finalized, if a provenance field is absent/malformed, if a log identity duplicates, if a height has conflicting block hashes, or if any contract/window has zero accepted logs.

## Current remediation

Commit 8da5a0b expands transport diversity and hardens error classification/provenance validation while preserving the fixed windows and zero-PnL boundary. An explicit `ETH_RPC_URL` remains first priority if configured; public transports are fallback only.

## Advancement gate

Phase191 may advance beyond DATA_ONLY only after:

- all six contract/window cells (USDC + USDT across three fixed TRAIN-era windows) are non-empty;
- all accepted logs have blockHash, transactionHash, logIndex and blockNumber provenance;
- windows are below a finalized tip;
- two independent executions emit byte-identical deterministic coverage payloads;
- Frozen-path guard passes.

After that, and still before PnL, the next unit is event-semantic reconciliation: USDC Mint/Burn semantics and USDT Issue/Redeem semantics must be decoded separately and reconciled against immutable log provenance. Only a single pre-registered economic hypothesis may follow. No post-hoc inversion, threshold search, window search, or stablecoin-family rescue is permitted from Phase191 evidence.
