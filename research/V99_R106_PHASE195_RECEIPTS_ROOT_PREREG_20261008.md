# V99 R106 Phase195-B — canonical receiptsRoot source audit (preregistered 2026-10-08)

Status: DATA_ONLY, economic_trials=0. This is a source-integrity hypothesis, NOT an economic model selection or approval. V16 Frozen, V99 Frozen and holdout remain untouched.

## Falsifiable hypothesis
At the previously selected Ethereum mainnet TRAIN height 17,000,000, a complete ordered set of canonical transaction receipts, encoded using legacy or EIP-2718 typed receipts, must reconstruct the execution header receiptsRoot through an Ethereum Keccak-256 Merkle Patricia Trie. The fixed height cannot be changed based on outcome.

## Required gates
1. Pin chain ID 1, block height/hash, timestamp in frozen TRAIN [2021-12-01T00:00:00Z, 2024-01-18T00:00:00Z), canonical execution header and its independently authenticated consensus provenance.
2. Retrieve ALL transactions and ALL ordered receipts. Verify receipt transaction index, cumulativeGasUsed, status, 256-byte logsBloom recomputed from ALL log addresses/topics, exact ordered logs and noncanonical RPC quantities. Recompute receiptsRoot using RLP(index) trie keys, EIP-2718 typed envelopes and Keccak-256 (not NIST SHA3-256).
3. Match root to independently anchored header; fail closed on omitted logs, malformed fields, forked headers, incomplete receipts, receipt type errors or mismatches. Compare separate source operators, not just two endpoint aliases. A supplied unauthenticated header is insufficient for canonicality.
4. Prove historical publication latency and t-1 availability. Modern replay does not prove a past observer had data at the time.
5. Require all 776 fixed interior TRAIN days, before/after boundary sentinels, six chronological folds, independent source provenance and deterministic replays before any economic hypothesis. Preserve severe/supersevere costs, regime matrix, benchmark envelope, holdout and anti-overfit gates unchanged.

## Negative controls
- Delete an unrelated receipt log from only one provider: full-receipt parity must fail.
- Delete the same unrelated log from both providers: parity may pass but canonical receipt-root check must fail.
- Change typed receipt prefix, status, cumulative gas, transaction index, bloom, log address/topics/data or receipt order: receipt-root or invariant gate must fail.
- Feed identical endpoints behind two labels: independence remains unverified, not PASS.

Decision: only source integrity may advance upon verified evidence. No price, PnL, backtest, threshold selection or holdout inspection is authorized by this gate.