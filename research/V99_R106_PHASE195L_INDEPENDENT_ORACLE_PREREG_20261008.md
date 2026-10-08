# V99 Phase195-L — independent library oracle (preregistered 2026-10-08)

Fixed Ethereum mainnet TRAIN height 17,000,000. Phase195-J observed 102 transactions and 237 logs from dRPC; Publicnode individual receipts were null. No economic data, selection, PnL or holdout access.

Hypothesis: independent Ethereum libraries (eth-utils Keccak, rlp and trie HexaryTrie) reconstruct the exact pre-Shanghai receipt MPT root from all ordered dRPC receipts. The independently implemented receipt serialization checks transaction index/hash, block linkage, status, type 0/1/2, cumulative gas, log order, log bloom, block gas/bloom, and complete 102-receipt cardinality. Reconstruct execution header hash and compare fixed header fields between Publicnode and dRPC. Run known-vector and mutation controls first.

A passing root is PROVISIONAL_ROOT_MATCH_UNANCHORED, NOT a consensus anchor, provider-independent receipt parity, latency proof, complete 776-day TRAIN coverage, or promotion. Any failure is HOLD. Frozen V16/V99, holdout, temporal folds, severe/supersevere costs, regime matrix, benchmark envelope, and anti-overfit discipline remain untouched. No economic trials authorized.

Workflow uses pinned independent libraries, records immutable Actions evidence, and may return a successful diagnostic workflow with a HOLD result; the decision JSON, not CI green, controls promotion.
