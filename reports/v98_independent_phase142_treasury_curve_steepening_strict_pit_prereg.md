# V98 Independent Phase142 — strict-PIT Treasury steepening risk-on

Status: **FROZEN BEFORE ANY ADMISSIBLE PHASE142 CRYPTO RETURN / ALPHA / PNL IS INSPECTED**.

## Why Phase142 exists

Phase141 consumed an experiment identifier before the governing Phase140 full PIT gate had passed. Its generated result was quarantined and removed without being read. Phase142 therefore starts from a clean admissible precondition.

To avoid post-result tuning, the economic structure below is inherited from the already-frozen Phase141 preregistration. The only causal correction is data provenance/timing: Phase142 uses the exact ALFRED point-in-time observations audited by the governing Phase140 report and waits until **d+2 00:00 UTC**, strictly after the accepted d+1 vintage date.

No Phase141 economic result is used or inspected.

## Frozen PIT dependency

Required report: `reports/v98_independent_phase140_t10y2y_full_pit_audit.json`.

Required decision: `PASS_PIT_DATA_ONLY`.

Phase142 must reacquire the 2023-2025 ALFRED PIT series using the identical observation-date + 1 calendar-day vintage contract and must reproduce the exact Phase140 normalized PIT SHA-256 before touching crypto returns. Any hash mismatch aborts the experiment with no PnL.

Only PIT observations inside 2023-2025 are eligible. Before 20 accepted observations have accumulated, the strategy remains flat.

## Frozen economic hypothesis

A sustained steepening of the U.S. 10Y-minus-2Y Treasury curve can reflect easing short-end pressure / improving forward liquidity conditions.

Single hypothesis:
- series: T10Y2Y;
- statistic: current accepted PIT observation minus the observation **20 accepted observations earlier**;
- direction: delta > 0 => risk-on long; otherwise flat;
- no level threshold, magnitude filter, percentile, normalization, alternate lookback, inverse sign, regime filter or parameter sweep.

## Frozen causality and execution

For an observation dated d:
1. retrieve only its ALFRED vintage dated d+1 calendar day;
2. it may affect a crypto decision only from **d+2 00:00 UTC**;
3. missing observations are never interpolated;
4. once a state is released, the latest already-released state may carry forward until a later accepted observation changes it.

Basket:
- BTCUSDT
- ETHUSDT
- BNBUSDT
- XRPUSDT
- SOLUSDT

When active: equal weights, target gross **0.45** total (0.09 each).
When inactive: flat.
Decision clock: 00:00 UTC.
Hard execution guard: **0.50 gross**. This is a risk cap distinct from the 0.45 target and is not a tunable gross parameter.

## Frozen training gates

Training data only: 2023-01-01 through 2025-12-31.

Mandatory:
1. aggregate total return > 0;
2. aggregate daily PF >= 1.05;
3. aggregate max drawdown >= -35%;
4. every chronological fold (2023, 2024, 2025): return > 0 and daily PF >= 1.02;
5. severe costs/funding: return > 0 and PF >= 1.02;
6. supersevere costs/funding: return > 0 and PF >= 1.00;
7. single-asset share of positive raw-price contribution <= 45%;
8. top-10 positive-day contribution share < 35%;
9. max observed open gross <= 0.50.

All return, PF, drawdown, tails, concentration, gross, fold and stress diagnostics are reported even if the candidate fails.

Any failed mandatory gate => **REJECT_NO_RESCUE**.

PASS_TRAINING permits only a separately preregistered validation on the already-defined 2026-01-01..2026-07-31 validation window. It does not authorize any opened/final holdout.

## Isolation

- Phase083 is permanently forbidden for selection.
- New forward holdout 2026-09-16..2026-10-15 remains locked.
- No V16 or V99 evidence/state/report may be read.
- No Phase141 generated result may be read.
- No rescue through sign flip, lookback, threshold, basket, gross, timing, costs or post-hoc regime filtering.
