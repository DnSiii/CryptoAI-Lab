# V99 R106 Phase180 — historical block-arrival source audit

Decision: **SOURCE FOUND; STILL NOT ADMITTED TO ALPHA / PNL**.

## Why this changes the prior state
The prior market-time audit correctly rejected miner-declared `header.time` as an availability timestamp. A genuinely orthogonal historical source now exists: `bitcoin-data/block-arrival-times`, which stores per-node millisecond timestamps for when a block arrived / was first connected at the observing node. Its README explicitly distinguishes these observations from header timestamps, documents extraction from Bitcoin Core `debug.log`, and runs QA against header time.

The repository also has commits dated before the untouched holdout boundary. In particular, commits in December 2023 added/split historical arrival sources and KIT monitoring data. This establishes that the dataset/repository was publicly materialized before 2024-01-18, avoiding a purely post-holdout source discovery artifact. It does **not** by itself prove full TRAIN coverage or economic admissibility.

## Provenance observed
- Source repository: `bitcoin-data/block-arrival-times`.
- Schema: `height, header_hash, timestamp_ms` per source.
- Semantics: timestamp is node-observed block arrival / first-connect time, not miner-declared block time.
- Multiple independent source files exist (0xB10C, KIT, vostrnad, n-thumann, darosior, etc.).
- Source README documents debug.log/ZMQ provenance for several files.
- Upstream QA checks arrival timestamps against canonical block-header timestamps.
- Upstream statistics code keeps the earliest arrival per height **within each source** and computes weekly (1008-block) source coverage.

## Scientific risks that remain
1. **Observer dependence:** arrival time is node/location/topology specific; it is not a universal market timestamp.
2. **Earliest-source hindsight:** taking the minimum across all observers would use an ex-post observer ensemble and can move information earlier than any fixed deployable observer. This is forbidden.
3. **Changing source set:** sources start/stop at different dates. A dynamic minimum can create survivorship/composition artifacts.
4. **Clock quality:** node wall clocks can drift; cross-source ordering at millisecond scale is not assumed reliable without audit.
5. **Coverage gaps:** full TRAIN + pre-roll coverage has not yet been demonstrated for one preregistered observer/source.
6. **Repository publication != event availability:** Git commit dates establish public archival provenance, not that a hypothetical trading system consumed that exact node feed live. Phase180 may use arrival timestamps only as a conservative availability proxy after the fixed-observer gate passes.

## Fail-closed admission gate
Before any PnL/economic evaluation:
- pin one source **chronologically using TRAIN-only coverage/integrity criteria**, never future/holdout performance;
- forbid cross-source `min(timestamp)` and source switching to fill gaps;
- require pre-roll + TRAIN coverage report by temporal fold and 1008-block bucket;
- verify `(height, hash)` uniqueness and canonical-chain hash agreement;
- verify timestamps are integer milliseconds, monotone pathologies are reported, and extreme header/arrival deltas are surfaced rather than clipped;
- require explicit gap policy: missing observation => missing feature, never header-time substitution or forward/back fill;
- bind upstream repository commit, source blob SHA, raw SHA-256, canonicalized SHA-256, gate report SHA-256 and feature artifact SHA-256;
- preserve structural one-block lag in Phase180 features after market-time alignment;
- hard reject any row aligned at/after `2024-01-18T00:00:00Z` during selection/development;
- run the existing temporal-fold, severe/supersevere-cost, regime-matrix, benchmark-envelope and reproducibility gates unchanged if and only if data admission passes.

## Preregistered source-selection rule
Selection is data-only. Among sources whose historical observations cover the required pre-roll + complete TRAIN span, choose the lexicographically first source after filtering by the fixed integrity requirements above. If no single source passes, **Phase180 is rejected**. Do not combine sources to manufacture coverage. Do not inspect PnL to choose an observer.

## Current status
Phase180 moves from `market_time source absent` to `candidate point-in-time source found`, but remains **DATA/FEATURE-only**. No alpha, PnL, threshold/window search, holdout inspection, or benchmark comparison is authorized yet.

V16 Frozen and V99 Frozen remain untouched.
