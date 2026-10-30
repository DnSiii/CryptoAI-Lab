# V98 Independent — Phase225 implementation audit

Status: **PASS_FOR_EXECUTION**. Holdout 2026+ remains CLOSED.

Audit performed after implementation and before any Phase225 result exists.

## Preregister mapping
- Exactly 8 frozen specs: V {2.0,3.0} × residual |R| {0.015,0.025} × H {4h,8h}.
- Signal uses completed information only: r6 is shifted to end at t-1; cross-sectional median is same t-1 panel; abnormal-volume numerator is volume(t-1), while the 168h baseline ends at t-2 and therefore excludes the shock bar.
- Entry/exit accounting is open(t) to open(t+H); same-asset overlap is prohibited; simultaneous eligible assets are equal-weighted with gross exposure <=1.
- Costs are frozen at round-trip-equivalent turnover stresses 7/14/28 bp and realized Binance funding is booked causally at the first hourly accounting timestamp strictly after settlement.
- Folds are independent calendar 2023/2024/2025; loaders hard-fail on any timestamp >=2026-01-01.

## Diagnostics/invariants
Evaluator reports return, max drawdown, PF, payoff, win rate, positive days, trade count, BTC 168h bull/bear/sideways regimes, five-asset PnL contribution/concentration, funding contribution and closed-trade attributed tails including exit turnover. Validator independently requires all fields, tail ordering, five assets, three regimes, monotonic cost degradation, exact fold/stress sets and deterministic payload SHA.

## Known risks frozen before results
1. Volume bursts can coincide with liquidation cascades, so contrarian tails may be strongly left-skewed.
2. Sparse high-threshold specs can fail the >=30 trades/year gate even with positive expectancy.
3. Five-asset cross-sectional median is robust but coarse; no alternative benchmark may be substituted after observing results.
4. Equal weighting at entry can cause later gross exposure below one when independently timed positions expire; this is intentional, not leverage normalization.
5. Funding is accounting-only and cannot be used as a Phase225 selection feature.

## Mechanical disposition
Run twice from identical training-only inputs and require byte-identical output plus validator pass. If 0/8 specs satisfy return>0, PF>1, positive-days>50%, and >=30 trades in every year at base cost, disposition is `REJECT_FAMILY_NO_RESCUE`. No threshold, horizon, asset, regime, or year rescue is permitted.
