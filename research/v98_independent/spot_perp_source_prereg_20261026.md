# V98 Independent — spot/perpetual basis source integrity preregistration (2026-10-26)

**Source-only, preregistered before retrieval, no alpha, PnL or candidate selection.** HP and all earlier rejected candidates stay rejected. Motivation: repeated 2023–2024 physical training failures in Opportunity and Stress/Recovery with futures OHLC, funding and executed-taker-flow; seek an **independent exchange spot-price information class**, not another post-result variation of a rejected signal. No assumption of predictability.

Exact official Binance SPOT monthly 1h kline ZIP archives and matching provider .CHECKSUM sidecars:
`https://data.binance.vision/data/spot/monthly/klines/{SYMBOL}/1h/{SYMBOL}-1h-{YYYY}-{MM}.zip`
with `{SYMBOL}` in BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT and months Dec-2022 through Dec-2024 inclusive (25 months x 4 = 100 ZIPs and 100 CHECKSUMs). Do NOT download 2025, 2026+, XRP or alternate providers; no daily fallback, missing-row interpolation, source shopping or post-result repair. Official Binance USD-M perpetual source stays independently SHA-pinned and untouched.

Pass requires all 100 exact archive objects and matching sidecars, 100 provider SHA256 checks, one expected CSV member per ZIP, exact UTC hourly grid, exactly 18,288 timestamps per asset and 73,152 total asset-hours, unique strictly increasing open_time, finite positive OHLC with high/low geometry, finite nonnegative quote-volume, and byte-identical two-pass canonical reconstruction. Emit SHA256 manifest and a single 2022–2024 spot canonical artifact with deterministic UTF-8 CSV. No spot/futures return join or directional sign/window/threshold/PnL selection. Failure -> FAIL_SPOT_SOURCE_INTEGRITY; no fallback or candidate claim.

Any subsequent economic hypothesis using spot/futures basis must be separately preregistered and run through the same native 30-cell, 81-corner physical and independent ledger gates with 2025 untouched. This source pilot does not promote any engine or authorize trading. Branch research/v98-independent-zero; only V98 Independent files/workflow.
