# V98 Independent Phase141 — Treasury Curve Steepening Risk-On preregistration

Status: **FROZEN BEFORE T10Y2Y VALUES / CRYPTO RETURNS / ALPHA / PNL ARE INSPECTED TOGETHER**.

## Causal economic hypothesis

A sustained steepening of the U.S. 10Y-minus-2Y Treasury curve can reflect a shift away from restrictive short-end conditions and toward an easier forward macro/liquidity configuration. The single frozen V98 hypothesis is: when the most recently available T10Y2Y observation is above its value 20 available observations earlier, hold a modest equal-weight long crypto basket; otherwise remain flat.

Phase140 passed the preregistered point-in-time shortcut audit: 36 month-end ALFRED vintages across 2023-2025, 1,501 overlapping observations, zero mismatches versus current FRED, and no future-dated observations. This authorizes current FRED history with a conservative publication lag for this exact economic test.

## Frozen signal / execution

- Macro source: FRED/ALFRED T10Y2Y.
- Training only: 2023-01-01 through 2025-12-31.
- Signal: T10Y2Y[t] - T10Y2Y[t-20 available observations] > 0.
- Direction: steepening => long; otherwise flat.
- No level threshold, percentile, magnitude filter, alternate lookback, sign flip, normalization, or parameter sweep.
- Publication causality: observation dated d may affect crypto positions only from 00:00 UTC on d+1 calendar day.
- Missing/non-business dates: carry only the latest already-released signal state; never interpolate macro values.
- Basket: equal-weight BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT.
- Target gross when active: **0.45** total (0.09 each).
- Hard execution audit cap: **0.50** gross, intentionally leaving headroom for tiny mark-to-market drift.
- Decision/rebalance at 00:00 UTC only; positions persist until next decision.

## Frozen training gates

1. Aggregate training total return > 0; daily PF >= 1.05; max drawdown >= -35%.
2. Every chronological training fold: return > 0 and daily PF >= 1.02.
3. Severe costs/funding: return > 0 and PF >= 1.02.
4. Supersevere costs/funding: return > 0 and PF >= 1.00.
5. Single-asset share of positive raw price contribution <=45%.
6. Top-10 positive-day contribution share <35%.
7. Max observed open gross <=0.50.

## Anti-overfit / isolation

- Phase083 opened window is forbidden for selection.
- Validation remains closed.
- No V16 or V99 evidence/state/report is used.
- No rescue if Phase141 fails.
- Failure closes this exact steepening-risk-on hypothesis. No inverse direction, threshold tuning, alternate lookback, gross tuning, or post-hoc regime filter is allowed.
