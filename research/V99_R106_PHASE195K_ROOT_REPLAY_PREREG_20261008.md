# Phase195-K prereg — canonical receiptsRoot replay

Fixed Ethereum mainnet TRAIN height 17000000, same 102 transactions and 237 logs as Phase195-J. Recompute receipt logsBloom and Ethereum Keccak-256 Merkle Patricia Trie root from the ordered dRPC bulk receipts, with EIP-2718 type prefix and RLP(transactionIndex) keys. Verify the pre-Shanghai execution header RLP hash and compare the recomputed receiptsRoot to the header claim. Cross-check with independently available receipts if possible.

Reject any omitted receipt or log, wrong status/type, noncanonical quantity, bloom mismatch, wrong header hash, wrong transaction ordering, or root mismatch. Run known Keccak and trie vectors plus adversarial controls before live RPC. A matching unanchored header is provisional, not independent consensus, historical availability, or full TRAIN coverage. DATA_ONLY; no economics, holdout, Frozen changes or promotion.
