# V98 HQ — authenticated early-close source addendum (DATA ONLY, 2026-10-26)

This addendum is registered **after** the first HQ official source-only execution failed its newly strengthened close-time integrity check, and **before** any HQ economic PnL, parameter selection or seven-slot candidate. It is not an economic preregistration or a rescue of the previously rejected strict complete-grid spot source. The original HQ preregistration and failed source run remain immutable evidence.

## Independent forensic witness
- [Official March close-time forensic run](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40441353424), Binance publisher SHA256 sidecars checked independently, four BTC/ETH/BNB/SOL March-2023 monthly ZIPs.
- Exactly **one** close-time anomaly per asset, each at 2023-03-24 12:00 UTC, row 564. All four 13:00 UTC bars are genuinely absent from the publisher archives.
- Publisher-authenticated early close_time_ms:
  - BTCUSDT: **1679661581646** (12:39:41.646 UTC)
  - ETHUSDT: **1679661583061** (12:39:43.061 UTC)
  - BNBUSDT: **1679661581451** (12:39:41.451 UTC)
  - SOLUSDT: **1679661586948** (12:39:46.948 UTC)
- Corresponding March archive SHA256 remains pinned in the original HQ module. These timestamps are not inferred from future prices and cannot be fitted.

## Exact source-only policy (before any economic run)
- Preserve the four **observed** 12:00 partial bars with their exact publisher OHLCV, **but flag `full_hour=0`**. Never pretend they represent a complete 60-minute observation.
- Preserve the four **missing** 13:00 calendar bars with `observed=0, full_hour=0` and empty prices/volumes.
- Every other one of the 73,144 full-hour observations must have exactly `close_time=open_time+3599999` and `full_hour=1`. No other early/late close, missingness or schema exception is permitted.
- The 73,148 observed prices remain unmodified; the 73,152-row calendar is unchanged. Eligibility for ANY spot-derived rolling signal requires both `observed=1` and `full_hour=1` for every historical input hour. This excludes the partial 12:00 bar and every window touching 12:00 or missing 13:00. No forward fill, interpolation, zero-return substitution or trading on the halt interval.
- Verify all 100 publisher ZIP checksums, 4 pinned partial closes, 4 exact missing hours, 73,144 full-hour eligible asset-hours, two deterministic canonical builds and independent 100-archive receipt reconciliation.
- All source-only decisions remain DATA_ONLY; no 2025, 2026+, XRP, contaminated Phase083, V14/V15/V99 internals, Frozen or paper. No PnL or live orders.

If any pinned partial close, SHA, mask, coverage or causal rule fails, HQ source is **rejected** without silent repair. This is a provenance correction to prevent a false 60-minute observation, not an alpha/sign/window/threshold/fee/leverage adjustment.
