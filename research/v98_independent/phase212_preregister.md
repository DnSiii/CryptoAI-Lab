# V98 Independent Phase212 — preregistration

Frozen before any Phase212 result is observed.

## Hypothesis
**Range-position exhaustion reversal**: an altcoin hourly candle that has an unusually large true range relative to its own trailing history and closes near an extreme may represent short-horizon exhaustion. Test a contrarian entry on the next hour, using only each asset's own OHLC history. This is orthogonal to Phase211 BTC lead-lag, Phase210 hour-of-week residuals, Phase209 cross-sectional dispersion, Phase208 volatility-compression breakout, and Phase207 funding/residual families.

Assets: ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT. BTC is not a signal input.

## Causality
At decision timestamp `t`, all signal inputs are from the fully closed candle `t-1` or earlier. Define `TR(t-1)=max(high-low, abs(high-prev_close), abs(low-prev_close))/prev_close`. Trailing robust baseline (median and MAD) must end at `t-2`; no value from candle `t` may enter signal construction. Close-location value on `t-1`: `CLV=((close-low)-(high-close))/(high-low)`, with zero for zero-range candles.

Long at `t open` when range z-score >= threshold and CLV <= -clv_threshold. Short at `t open` when range z-score >= threshold and CLV >= clv_threshold. Exit at `t+H open`. No overlapping position per asset.

## Frozen grid — exactly 8 specs
Cartesian grid:
- robust lookback L: {168h, 336h}
- range z threshold: {2.5, 3.5}
- hold H: {3h, 6h}

Fixed `clv_threshold = 0.70`; MAD scale = 1.4826. If MAD <= 0 or required bars are absent, no signal. No additional filters.

## Evaluation
Chronological training folds only: calendar 2023, 2024, 2025. Validation/final holdout remains unopened. Warm-up may use prior history but cannot originate a trade outside the evaluated fold.

Use the existing V98 Independent point-in-time funding files and identical cost convention used by Phases 208–211:
- base round-trip cost: 0.07%
- severe: 0.14%
- supersevere: 0.28%
Funding is charged/credited only at funding timestamps actually crossed while the position is open, with correct long/short sign.

For every spec × fold × cost level report: compounded return, max drawdown, Profit Factor, payoff, win rate, positive days, trade count, best/worst trade, p01/p05/p50/p95/p99 tails, per-asset return/funding contribution, max asset concentration, and bull/bear/sideways decomposition using the established V98 regime definition.

## Mechanical training gate
A spec is training-fold coherent only if **all 2023/2024/2025 base folds have return > 0 and PF > 1**. This gate is necessary, not sufficient for promotion. Severe/supersevere, MDD, tails, concentration, regimes and reproducibility must then be independently audited before any later gate.

If 0/8 specs pass, close the entire Phase212 family as `REJECT_FAMILY_NO_RESCUE`. Do not invert, tweak CLV, alter thresholds/lookbacks/holds, exclude losing assets/regimes, or inspect holdout to rescue it.

## Integrity / reproducibility
Rebuild canonical training data independently; assert monotonic unique timestamps and `<2026-01-01` firewall for prices and funding. Run evaluator twice and require byte-identical report SHA256 before interpreting economics.

No V16 Frozen, V99 Frozen/research/workflows/reports/paper state may be read for tuning or modified. Champion is unchanged by preregistration.
