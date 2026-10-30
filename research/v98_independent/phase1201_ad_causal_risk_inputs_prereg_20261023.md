# V98 Independent Phase1201 — AD causal market/exit/funding risk-input contract (2026-10-23)

Before any official AD historical PnL, replace Phase1198/1200 synthetic **fixed** downside/upside/funding/quote assumptions with real **strictly prior** Clean-4 inputs for the 81-corner Phase1196 governor and Phase1197 executor.

For decision/execution hour t (>=720), use **only** bars s<t:
- Downside bound per asset: max(0.25, max over previous 336 completed bars of 1-low_s/close_{s-1}), cap 0.99.
- Upside bound: max(0.30, max over previous 336 completed bars of high_s/close_{s-1}-1).
- Entry/exit liquidity minimum: min prior 336 quote-volume bars; order quote reference: quote[t-1].
- Adverse 720h native funding bound: max(0.005, sum of absolute native funding settlement rates in hours t-720..t-1). No sign-based free funding and no 2025+.
- Fail closed if any required prior window is missing, nonfinite, invalid or misaligned. At t, the *current* bar high/low may be used only **after** execution to audit intrabar survival, never to set risk input before t+1 open.
- All risk limits, execution costs and funding orders remain exactly Phase1196/1197; no post-result relaxation. Test prefix causality, exact window exclusion, severe gap, signed funding and no future leakage synthetically. This is not historical system PnL.
