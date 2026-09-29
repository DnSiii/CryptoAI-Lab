# V99 R106 — Phase177 IV reconstruction preregistration

Date: 2026-09-28
Status: PRE-PNL SPECIFICATION. No returns inspected.

## Scientific question

Can a deterministic BTC options-implied-volatility state, reconstructed only from first-party Deribit historical observations available during frozen TRAIN, provide information orthogonal to exhausted price/funding/OI/crowding/flow/macro families?

## Data gate before any signal

No PnL code may run until a first-party extraction proves all of:
- option instruments and trades cover frozen TRAIN `[2021-12-01, 2024-01-18)`;
- contemporaneous Deribit BTC index observations required for moneyness are available with documented timestamps;
- expired instruments are discoverable deterministically (`include_old=true`);
- source rows are immutable-cached with SHA-256 manifests;
- duplicates, gaps, monotonicity and fold coverage pass;
- every observation carries event time and conservative availability time;
- no row at or after holdout boundary enters cache/evaluation.

If any requirement fails, reject Phase177 without rescue tuning.

## Reconstruction — fixed before PnL

To minimize researcher degrees of freedom, only a single canonical state is permitted if the data gate passes:

1. underlying: BTC only;
2. option venue: Deribit only;
3. target horizon: 30 calendar days, matching DVOL's economic horizon;
4. use only observations strictly available before the decision timestamp;
5. choose the two listed expiries bracketing 30 days when both exist; no expiry cherry-picking;
6. within each expiry, estimate ATM IV from the call/put observations nearest forward-ATM under one deterministic tie-break (lower absolute log-moneyness, then lexicographic instrument name);
7. derive IV with one Black-style solver and fixed numerical tolerances; failed/non-finite solves are missing, never imputed from future data;
8. interpolate variance linearly in time to exactly 30 days; no fitted smile, no spline, no hyperparameter search;
9. aggregate to hourly last-known state only after applying documented publication latency;
10. apply an additional one-hour causal t-1 shift before strategy use.

No strike grid, delta bucket search, expiry search, sign search, smoothing-window search, clipping search or asset search is allowed.

## Integrity/reproducibility invariants

A future extractor must emit: source URL/endpoint, request parameters, retrieval timestamp, SHA-256 per cache shard, row count, min/max event timestamp, min/max availability timestamp, instruments, expiries, missing-hour map, duplicate identities and solver-failure counts. Re-running from identical cache must reproduce byte-identical feature output.

## Evaluation discipline if and only if data gate passes

The first alpha hypothesis will be preregistered separately before PnL. It must retain chronological train-only selection, temporal folds, severe and supersevere costs, regime matrix, benchmark envelope, tail/concentration audits and untouched holdout. Phase177 cannot be promoted from aggregate TRAIN ROI alone.

V16 Frozen and V99 Frozen remain untouched.
