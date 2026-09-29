# V99 R106 — Phase180 Bitcoin block-production integrity/causality specification

Date: 2026-09-29
Status: DATA/INTEGRITY ONLY — no PnL inspected or authorized.

## Independent audit finding

Bitcoin header `time` is miner-declared, not an observation/arrival timestamp. Consensus only requires it to be strictly greater than median-time-past of the previous 11 blocks and not more than two hours into the future according to a validating node. Therefore raw header time MUST NOT be treated as exact market availability time. Historical canonical headers alone cannot reconstruct historical peer-arrival latency.

For this phase the conservative causal event time is defined as `max(header_time, previous_11_median_time)` for ordering diagnostics only; execution still receives the project's mandatory additional t-1 bar lag. No sub-bar or latency alpha is permitted. Any feature requiring historical receive-time is rejected as unidentifiable from headers.

## Deterministic integrity gate

Accepted canonical table columns:
`height,hash,previousblockhash,time,mediantime,bits,difficulty,chainwork`.

Fail closed if any invariant fails:
1. chain is Bitcoin mainnet and heights are unique/strictly increasing;
2. `previousblockhash[h] == hash[h-1]` for every interior TRAIN row;
3. no conflicting hash at one height and no duplicate `(height,hash)`;
4. `time[h] > median(time[h-11:h])` using only predecessors; never repair miner timestamps;
5. target decoded from compact `bits` is positive/non-overflow and header hash satisfies target when serialized raw header bytes are available;
6. difficulty/target changes are permitted only at mainnet 2016-block retarget boundaries; validate against consensus-compatible target reconstruction rather than fitting observed cadence;
7. raw and canonical SHA-256 manifests are stable across two independent reconstructions;
8. every existing temporal TRAIN fold has coverage; no post-firewall row participates in cleaning/statistics;
9. reject any row with height/time-derived inclusion beyond immutable firewall `2024-01-18T00:00:00Z`;
10. no interpolation, forward fill, third-party gap repair, orphan substitution, or post-hoc TRAIN shortening.

## Timestamp pathology audit

Report, without filtering:
- negative/zero miner timestamp deltas;
- delta versus predecessor median-time-past;
- gaps > 2x, 3x, 6x and 12x protocol target interval;
- counts adjacent to difficulty boundaries;
- concentration by month and temporal fold.

These are diagnostics, not alpha thresholds.

## Reproducibility output

Manifest must contain source/node version, chain tip used for extraction, first/last accepted height/hash, row count, TRAIN min/max header time, SHA-256 raw bytes, SHA-256 canonical CSV, invariant results, fold coverage and firewall count. Run twice and require byte-identical canonical output.

## Decision rule

Only after this DATA gate passes may Phase180 preregister exactly one economic alpha realization. No sign/lookback/threshold/asset search is allowed before that preregistration. Holdout remains untouched. V16 Frozen and V99 Frozen remain untouched.
