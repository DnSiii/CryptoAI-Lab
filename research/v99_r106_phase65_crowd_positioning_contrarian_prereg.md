# V99 R106 Phase65 — Native crowd-positioning contrarian pre-registration

## Status
PRE-REGISTERED BEFORE TRAIN EVALUATION.

Phase64 native OI-expansion confirmation was rejected train-only (0/4 healthy folds). Phase65 does not retune Phase64's sign, horizon, OI field, winsorization, or thresholds. It tests a distinct economic mechanism available in the already-audited Binance USD-M metrics archive.

## Single hypothesis
Crowded account positioning contains a contrarian cross-sectional premium: assets with relatively more accounts positioned long should receive relatively lower target weight, while assets with relatively more accounts positioned short should receive relatively higher target weight.

Native field: `count_long_short_ratio` from Binance USD-M daily metrics.

Fixed transform:

`feature_t = -log(count_long_short_ratio_t).shift(1)`

No threshold, horizon, sign, field, winsor, or parameter grid is permitted after seeing results. Cross-sectional portfolio mapping is the existing Phase31 deterministic mapper. Gross alpha budget is fixed at 0.20.

## Causality / data discipline
- consume only archives through the Phase63 audited `train_end`;
- SHA256 CHECKSUM and ZIP CRC verification for every consumed archive;
- no fill for missing archives;
- feature is shifted one full hourly bar (`t-1`);
- chronological train-only decision;
- untouched holdout MUST NOT be listed, downloaded, parsed, scored, summarized, or used for selection;
- V16 Frozen and V99 Frozen remain untouched.

## Train gate
Use the existing severe per-side cost and the same four chronological temporal folds/robust-tail diagnostic used by Phase64. Promotion requires the pre-existing `stable_train` gate (including temporal-fold health and robust mean excluding top 1%).

If train gate passes: freeze the exact specification before any holdout evaluation. If it fails: reject Phase65; do not rescue it with sign flip, alternate positioning field, smoothing, thresholds, or parameter tuning. A future hypothesis must be separately pre-registered and economically distinct.
