# V98 Independent JS — cross-asset 5m shock propagation source-only preregistration (2026-10-28)

**New information source, NOT a JR or JQ rescue, and NOT an economic engine.** JR's same-asset early-trough/buyer-shift and late-liquidation seven-slot hypothesis is terminally rejected on 2023–2024 independently audited economic grounds. JQ's unmasked complete 5m source is source-rejected. JS investigates a genuinely different market mechanism: **direction and timing of BTC 5-minute shocks propagating into ETH/BNB/SOL five minutes later**, versus reverse propagation. It does not select long/short direction, threshold, budget, alpha, or economic outcome here.

Universe: Binance USD-M BTC/ETH/BNB/SOL 5m monthly vendor ZIP plus SHA256 sidecar, 2022-12 through 2024-12 only, pinned Clean-4 1h/funding and independently audited whole-asset-month 5m mask source run 40668217706. No 2025+, XRP, Phase083, V14/V15/V99 internals, Frozen, paper or live. Reverify every archive SHA, UTC 5m continuity and OHLC/quote geometry; independently aggregate 5m to pinned 1h at the original strict tolerances (price rtol 2e-10/atol 1e-8, quote rtol 2e-8/atol 1e-6). **If any asset-month fails, disable all cross-asset features for that month for all four assets**. No interpolation, source replacement, threshold relaxation or partial bar repair.

For each complete UTC hour t, define twelve ordered native 5m log returns for each asset: r[0]=log(close5m[0]/open5m[0]); r[j]=log(close5m[j]/close5m[j-1]) for j=1..11. For each ALT in ETH/BNB/SOL, compute observed source-only features:
- BTC-to-ALT lag covariance proxy = mean(r_BTC[j-1] * r_ALT[j]) for j=1..11.
- ALT-to-BTC reverse lag covariance proxy = mean(r_ALT[j-1] * r_BTC[j]) for j=1..11.
- BTC early sell pressure = sum(min(r_BTC[j],0)) for j=0..5.
- ALT late response = sum(r_ALT[j]) for j=6..11.
- BTC late response = sum(r_BTC[j]) for j=6..11.

These are **completed-hour observations, not predictions**. Any future strategy may only use them after hour t completes, earliest trade t+1 actual open, and must invalidate any lookback crossing the source mask. Produce full calendar hourly ALT mask (18,288 hours x three alts =54,864 rows), vendor archive SHA manifest, feature CSV SHA, exact quarantined months, and two-OS byte-identical independent audit. A future **new** complete seven-slot architecture needs a separate preregistration before any PnL. No 2025 validation or benchmark until it passes its own training and independent gates.
