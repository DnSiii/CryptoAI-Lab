# V99 R106 Phase191 — indexed-log source audit

Date: 2026-09-30
Status: DATA_ONLY; zero economic trials; holdout untouched.

## Question
Can a keyless indexed Ethereum log API replace the unavailable public archive RPC transport without weakening Phase191 provenance requirements?

## Fixed scope
The probe retained the three already-fixed TRAIN-era windows (17,000,000–17,000,199; 18,000,000–18,000,199; 19,000,000–19,000,199) and the canonical USDC/USDT Ethereum contracts. No price, PnL, regime, benchmark or holdout data was queried.

## Evidence
A keyless Routescan/Etherscan-compatible log probe was implemented with pagination, emitter checks, block/transaction hash validation, duplicate detection and per-height block-hash consistency. CI run 36773913058 passed the V16/V99 Frozen guard but failed on the first real-data probe because at least one returned record encoded `logIndex` as bare `0x`, which is not a valid integer quantity and therefore cannot satisfy the immutable `(blockHash, transactionHash, logIndex)` identity required by Phase191.

The probe was subsequently hardened to fail closed on malformed event topics/data as well; this is a data-integrity change, not a relaxation.

## Decision
**REJECT Routescan keyless indexed logs as the Phase191 scientific source in the observed schema.** Do not coerce bare `0x` to zero, infer log order, deduplicate without logIndex, or weaken identity requirements merely to make coverage pass. Such repairs would manufacture provenance not supplied by the source.

This is not a rejection of the stablecoin-flow hypothesis. Phase191 remains pre-economic with zero trials. The archive-RPC path is also infrastructure-blocked, so the next scientifically valid route is a distinct source that supplies canonical block hash + transaction hash + valid log index (or transaction receipt logs from which log index is canonical) and can be independently finality-checked. A keyed source may be used only if credentials already exist in CI; no secret should ever be committed.

## Invariants preserved
- V16 Frozen and V99 Frozen untouched.
- causal t-1 semantics unchanged.
- chronological TRAIN-only selection unchanged.
- holdout untouched.
- no economic threshold/lookback/direction selected.
- no severe/supersevere gate weakened.
- no source defect converted into synthetic provenance.
