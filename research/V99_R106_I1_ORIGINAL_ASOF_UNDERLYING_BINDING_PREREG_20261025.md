# V99 I1 — original same-update index-to-option entry binding (preregistered 2026-10-25 05:xx BRT)

**SOURCE_ONLY / HOLD / NO PROMOTION.** The existing 46 original quote-pair screen is NOT a trade, a return, or a fill. This work closes the specific missing **as-of original underlying reference** interface, without guessing historical native lot units or fees.

## Fixed algorithm before execution

1. Read only archived TRAIN Deribit ticker gzip receipts from Actions 40170453274 (two Sundays, 2022-05-01 and 2023-01-01, last five minutes before 00:00 UTC Monday), the first-party instrument registry from 40148052668, and the previously executed source-credit result from 40174287180. Require SHA256 for every original compressed minute receipt and the unchanged source report.
2. Replay every raw capture in physical order. For every final eligible option book listed in the original report, locate **exactly the same symbol, local arrival timestamp and exchange timestamp** in the original ticker payload. Do not substitute a nearby record, interpolate, or use later information. Extract the optional exchange-published `index_price`, `underlying_price`, and `underlying_index` from that exact ticker update. Require positive finite Decimal prices, never infer one from another. Preserve source-field absence as `null`.
3. Bind each of the 46 adjacent put-vertical rows by the exact original symbols and timestamps. Report the raw index fields for both legs separately and a strict **same-reference** flag only if both `index_price` values exist, are positive, and are identical as Decimal values; never silently average asynchronous prices. Do not infer executable underlying trades, size, contract multiplier, FX, fee tier, or a coin-collateral NAV.
4. Independently reconstruct each same-update field from original gzip bytes and verify every joined row and the original credit output hash. A forged index value or symbol must fail. Report counts and missingness, even if zero references exist.
5. Never open validation [2023-10-01,2024-01-18), holdout >=2024-01-18, immutable Frozen, paper/results, champion, or send orders. This is an input bridge to a future **complete** five-fold, 3x2, severe/supersevere native-coin engine. No parameter fitting or strategy ranking.

## Gate

Original same-update underlying/index provenance is **not** certified entry execution, settlement, lot-size units, historical account fee tier or margin. Even a successful source/index join cannot unlock a historical ROI. Require complete 91-Sunday BTC/ETH bid/ask+size history and holding-period receipts, documented native size conversions and margin/liquidation rules, and independent full portfolio reexecution before TRAIN can be economically certified. **NO PROMOTION.**
