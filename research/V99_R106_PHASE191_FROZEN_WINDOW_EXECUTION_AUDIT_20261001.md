# V99 R106 Phase191 — frozen-window execution audit (2026-10-01)

Status: DATA_ONLY. Economic trials: 0. Holdout: untouched.

## Work completed

The Blockscout schema/provenance probe passed on canonical USDC and USDT logs with deterministic double execution. The next implementation therefore preserved the preregistered TRAIN windows exactly: 17,000,000–17,000,199; 18,000,000–18,000,199; 19,000,000–19,000,199.

A frozen-window collector was added with fail-closed validation for emitter, blockHash, transactionHash, logIndex, blockNumber, topics/data, duplicate canonical identity, conflicting block hashes, complete pagination, and independent block-endpoint identity sampling. It reads no prices, returns, PnL, regimes, benchmarks, validation outcomes, or holdout.

## Execution evidence

The first workflow attempt exposed an overly broad Frozen guard because the workflow filename itself contains `v99` and `frozen-windows`; this was a CI naming false positive, not a scientific result. The guard was narrowed to actual V16_FROZEN/V99_FROZEN artifact patterns.

Before accepting any data result, pagination was independently audited and hardened: a single 1000-row page is not evidence of complete coverage. The collector now paginates until a short page and fails at a fixed safety cap rather than silently truncating.

The first real paginated execution then hit HTTP 429 from Blockscout. This is transport throttling, not hypothesis rejection. The implementation now uses bounded exponential retry plus request spacing without changing windows, identities, source semantics, or any scientific gate.

## Decision discipline

No economic trial is authorized yet. PASS still requires both assets across all three frozen windows, deterministic double-run, canonical identity, no conflicting block hashes, independent block identity/finality evidence, issuer-specific semantic reconciliation, and causal t-1 aggregation. A 429 or other transport failure remains FAIL_CLOSED for the source path and does not increment the economic trial counter.
