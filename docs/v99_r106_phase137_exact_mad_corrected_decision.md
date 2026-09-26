# V99 R106 Phase137 — Exact-MAD corrected decision

Status: TRAIN_ALPHA_REJECT — PERMANENTLY REJECTED AS PREREGISTERED.

The corrected replay executed the literal preregistered same-window 168h MAD: `median(abs(window - median(window)))`. This supersedes the earlier invalid implementation for scientific decision purposes.

## Corrected TRAIN evidence
- active hours: 18,050
- ROI: -0.9865277104167834
- profit factor: 0.2725004808535934
- max drawdown abs: 0.9865423370209684
- positive-hour ratio: 0.2398337950138504
- robust mean excluding top 1%: -0.00026373514429574253
- healthy temporal folds: 0 / 4

## Integrity / causality
- Phase136 OKX hashes reproduced: true
- OKX rows per instrument: 18,672
- Binance minimum coverage gate: 0.98; no missing-price filling
- complete tradable score shift: t-1 (1 hour)
- feature inputs strictly pre-TRAIN-end: true
- post-TRAIN targets: zero
- max portfolio L1: 1.0000000000000004 (floating tolerance)
- holdout rows used for feature construction: 0
- holdout rows used for selection: 0
- V16 Frozen and V99 Frozen untouched

## Decision
Phase137 fails the first chronological TRAIN gate catastrophically and has 0/4 healthy temporal folds. Under the preregistered anti-overfit discipline, no sign flip, parameter retune, symbol filtering, severe/supersevere rescue, or holdout inspection is authorized. Phase137 is rejected. Severe/supersevere downstream gates are not run because they cannot rescue a candidate that failed the upstream TRAIN gate.

Phase138 was preregistered before this corrected PnL was harvested and is now authorized to execute exactly as frozen in `docs/v99_r106_phase138_okx_binance_return_innovation_preregister.md`.
