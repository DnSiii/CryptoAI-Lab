# V98 Independent Phase1098 — preregister causal protective-shock source (pre-economic)

2026-10-23. U remains UNFROZEN, no U historical PnL or 2025 access.

To remove the last unspecified implementation degree of freedom in Phase1093 preplaced brackets, define **one immutable shock window of 336 completed 1h bars**, consistent with the preregistered U 336h directional/relative-value horizon (not selected from U PnL). At the close of bar s, measure each bar j's adverse down shock as max(0,1-low[j]/close[j-1]) and favorable/up shock as max(0,high[j]/close[j-1]-1). Use the rolling maximum over the last 336 completed bars j<=s, with at least 336 valid observations; otherwise fail closed. Quantize to 8 decimal places before use. No post-result alternate window, sign, gross, or stop distance.

At the close of s, brackets for s+1 are planned using close[s], prior quote volume[s], trailing down[s], trailing up[s], and fully covered carried/desired units. A signed reversal that cannot be covered by a preplaced linked order fails closed. No future OHLC or funding can alter order placement. Actual s+1 funding is permitted only in ex-post solvency verification, never as a signal or order input.

2022 warmup supplies historical features. The first training NAV is independently initialized at Jan 1, 2023, with separate 2023 and 2024 chronological fold accounting; no 2022 performance is presented as training PnL. Separate 2025 validation remains untouched until all pre-registered 2023/2024 economic gates pass.

Next: synthetic shock no-leak and pathological-bar tests, remote CI, authenticated four-runner source receipt, independent signed execution/funding oracle, full U freeze, THEN historical 90-cell training.
