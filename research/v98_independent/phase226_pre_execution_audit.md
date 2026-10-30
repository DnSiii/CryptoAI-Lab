# V98 Independent — Phase226 pre-execution audit

Status: **PASS_FOR_IMPLEMENTATION — RESULT BLIND**. Holdout 2026+ CLOSED.

## Independence
Phase226 is scientifically distinct from Phase225: Phase225 faded abnormal-volume shocks using volume plus residual return; Phase226 excludes volume entirely and tests persistence of idiosyncratic residual momentum. It is also directionally distinct (continuation rather than reversal). No Phase225 winning cell exists to inherit; its rejected thresholds are not being rescued.

## Causal audit
- All signal components end at t-1.
- 30-day beta uses only completed historical hourly returns.
- Ranking is formed before open(t); execution starts at open(t).
- Fixed H exit is open(t+H).
- Funding cannot enter the signal and is booked only for realized settlements crossed while position is live.
- Hard firewall must reject any price/funding timestamp >= 2026-01-01.

## Allocation / concentration audit
Single-extreme per side and 0.5 side cap deliberately prevent a one-sided signal from silently consuming 1.0 gross. Existing cohorts cannot be resized to admit new cohorts. New entries may only consume free capacity; no same-asset overlap. This avoids the Phase225 allocator pathology while preserving the preregistered economics.

## Failure mechanisms frozen before results
1. Residual momentum may simply be beta-estimation noise; inspect year/regime sign consistency.
2. SOL/XRP may dominate tails; inspect signed asset contribution and max concentration.
3. 24h continuation may reverse before H=8; horizon differences are diagnostic only, not permission to tune after harvest.
4. Q=2% may be sparse and fail >=30 trades/year; do not lower Q.
5. Trading costs/funding may erase gross persistence; 7/14/28 bp stresses remain mandatory.
6. Long/short asymmetry may reveal market beta leakage; aggregate success cannot rescue a failed all-year gate.

## Implementation acceptance checklist
Evaluator must enforce exactly 8 specs, 2023/24/25 folds, chronological inputs, gross<=1, no same-asset overlap, deterministic serialization/SHA, required metrics/tails/assets/regimes, and cost monotonicity. Validator should independently recompute gate logic and reject malformed/missing cells. Two identical-input runs must be byte-identical before result harvest.
