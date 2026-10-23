# V98 Independent Phase1222 — AF strict t-1 causal governor risk inputs prereg (2026-10-23)

AF seven-slot portfolio must not use synthetic fixed risk bounds in any composed economic or crisis execution. Independently derive strict prior-only risk inputs from validated Clean-4 OHLC, quote and native signed funding, with no imports from rejected AD/AE modules, 2025/2026+ data, XRP or external benchmarks.

For actual execution at hour t:
- Downside = min(0.99,max(0.40,max of max(0,1-low[k]/close[k-1]) for **336 prior completed** hours k=t-336..t-1)).
- Upside = max(0.50,max of max(0,high[k]/close[k-1]-1) for the same 336 prior hours).
- Prior quote = quote_volume[t-1]; minimum quote = min quote_volume[k] over t-336..t-1.
- Adverse signed native funding bound = max(0.007,sum abs(native funding_rate[k]) over **720 prior** completed hours k=t-720..t-1).

Require strict continuous 720h warmup and finite nonnegative arrays. Current t OHLC, quote and funding cannot affect any t risk input; perturbation tests must prove effect begins no earlier than t+1. These source inputs constrain actual 81-corner collateralized orders, but passing source-only tests is not proof of profitability.
