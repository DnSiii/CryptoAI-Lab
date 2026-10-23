# V98 Independent Phase1209 — AE strict t-1 causal risk/quote/funding inputs (2026-10-23)

For AE's independent Phase1208 81-corner governor, pre-register strict causal source arrays before historical system PnL or integration. Use **only** AE's validated Clean-4 1h OHLC, quote and native funding/event mask, ending before 2025. No AD module imports, XRP, future holdout, 2026+ or external benchmarks.

At execution hour t, every risk input is measurable no later than completed hour t-1:
- `down[t]` = min(0.99, max(0.35, max over 336 **prior completed** bars of max(0, 1-low[k]/close[k-1]))).
- `up[t]` = max(0.45, max over 336 prior completed bars of max(0, high[k]/close[k-1]-1)).
- `min_quote[t]` = minimum of quote_volume[k] for k=t-336..t-1; `prior_quote[t]` = quote_volume[t-1].
- `funding_bound[t]` = max(0.006, sum of absolute native funding_rate[k] for k=t-720..t-1), with non-event rates already zero.

Require >=721 rows, strict 720h warmup, finite nonnegative inputs, no current-hour price/funding/quote leakage. Source-only synthetic perturbation tests must verify current t changes cannot influence risk at t. No fixed synthetic replacement in any eventual AE official PnL or 180-cell crisis test. Failure blocks execution rather than relaxing constants.
