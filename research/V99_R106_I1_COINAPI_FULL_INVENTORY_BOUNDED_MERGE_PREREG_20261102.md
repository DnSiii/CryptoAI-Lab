# V99 I1 — CoinAPI original-chain capacity repair (preregistered 2026-11-02, TRAIN only)

## Real internal blocker
The existing original CoinAPI day specification rejects >256 individual option-contract quote partitions in the production converter, original 661-day chain and original Sunday parity. Even simply increasing that cap is unsafe: both the production k-way merge and independent oracle open one gzip stream per contract, exhausting ordinary runner file-descriptor limits for a complete BTC/ETH option universe. Thus an authorized full inventory cannot pass the source-to-derived intake, regardless of vendor access.

## Fixed implementation and acceptance (before code)
* Permit **2..4096** original contract partitions per TRAIN day, with unique keys/symbols/paths and the existing BTC+ETH requirement. Reject >4096 explicitly; never silently truncate a universe.
* Preserve the exact stable total order of the old merge: original arrival in 100ns, then the source's original index. Use at most **64 simultaneously open original partitions** through per-batch disk-backed sorted runs, then merge at most 64 runs. Do not buffer an entire historical day in RAM. Fail closed on empty, malformed, out-of-order or changed original compressed bytes.
* Independent oracle must independently parse original 100ns data and compare every derived row using its own bounded disk-backed merge, not trust the production output or hashes alone. Preserve exact row/price/clock parity and strict no-overwrite publication.
* Synthetic regression: >256 distinct BTC/ETH option partitions, deliberately interleaved/tied timestamps, and independent parity; >4096 rejected before reading files. Existing 661-day missing-license and missing-original gates must remain blocked.
* No license acquisition, no economic ROI, no native fee/fill certification, no validation/holdout/Frozen/paper/legacy modifications, no orders, NO PROMOTION.

This repair removes a deterministic *internal* ingestion blocker; it does not solve the separately documented absent 658/661 licensed original days or missing native economics.