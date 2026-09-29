# V99 R106 Phase180 — independent market-time causality audit

Decision: **NOT ADMITTED TO ALPHA / PNL**.

## Failure mechanism
Bitcoin block-header `time` is miner-declared consensus metadata. It is constrained by consensus but it is not a point-in-time record of when the research system, exchange, or market could first observe the block. Consequently, joining Phase180 features to exchange bars using header `time` can move information earlier than its true availability and create lookahead even though feature computation itself is structurally h-1.

## Fail-closed rule
The Phase180 feature artifact may be constructed and integrity-tested, but its manifest must state `market_time_alignment_admissible=false`. No alpha/backtest/economic gate may consume it until an independent historical `observed_at` source with point-in-time provenance, TRAIN coverage, deterministic hashes, temporal-fold coverage, and the existing holdout firewall is validated.

No proxy such as header time, median-time-past, next exchange candle, block explorer display time, or present-day reconstructed arrival time may silently substitute for historical observation time.

## Anti-overfit decision
We do not inspect PnL to decide whether this requirement matters. We do not search offsets, delays, windows, or timestamp transformations. If valid observation-time history cannot be established, Phase180 is rejected at the data/causality gate.

## Preserved invariants
- feature windows remain fixed at 6/36/144 blocks;
- structural causal lag remains one block;
- chronological train-only selection remains mandatory;
- untouched holdout starts 2024-01-18T00:00:00Z;
- temporal folds, severe/supersevere costs, regime matrix, benchmark envelope and reproducibility gates remain unchanged;
- V16 Frozen and V99 Frozen are not modified.

## Next admissible work
Search only for genuinely point-in-time historical block-arrival provenance. Before any economic test, validate coverage and semantics independently and bind raw data + gate report + feature output by SHA-256. If this cannot be demonstrated, close Phase180 as a causal-data rejection and move to a scientifically distinct hypothesis.
