# V98 Independent Phase1205 — AE breakout source-only deterministic constants (2026-10-23)

This is the first executable AE source component under the already preregistered Phase1204 seven-slot architecture. No historical system PnL, no 2025 data, no external benchmarks, no AD signal import or parameter search.

**Source**: Clean-4 hourly OHLC/quote/native funding mask, strict continuous UTC index starting 2022-12-01, ending before 2025-01-01. All decisions at completed bar t may first trade at open t+1.

**Growth core**: 240 prior completed hourly highs/lows (strictly t-240..t-1). A completed close[t] > previous 240h maximum high sets long state +1; close[t] < previous 240h minimum low sets short -1; otherwise carry prior state. 48 prior log-return standard deviation ending t-1, floored at 0.002. Risk-neutral signal scale = inverse prior volatility, cap inverse-vol relative weights to 0.1..10, normalize absolute signed weights to gross 0.65; zero if no state. No forward extrema.

**Opportunity**: count distinct assets with fresh directional breakout in the trailing 24 completed hours; only if >=3 same-sign fresh breakouts, assign an extra signed 0.12 gross distributed across qualifying assets for the next 12 completed decisions, otherwise zero. No funding surprise or AD opportunity signal.

**Relative value**: if >=1 long-state and >=1 short-state asset, long basket +0.10 gross, short basket -0.10 gross, equal asset notionals within side; otherwise zero. Zero net at all times.

**Regime**: causal 24h average of fraction of assets closing above their own prior 240h channel midpoint; state smooth = 0.90 * previous + 0.10 * latest average occupancy; off if <0.40, on if >0.60, transition otherwise. Output one-hot [off,transition,on]. This is not AD's Bayesian likelihood model.

**Structural gate**: all finite shapes, no future influence on earlier decisions, correct 240h warmup, no NaN leak, deterministic reproducibility, source-only output; reject if causal/source gate fails without changing constants post-result. No historical AE PnL or validation before the complete seven-slot engine freezes.
