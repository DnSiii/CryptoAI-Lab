# V98 Independent Phase381 — BNB signal-dependency source audit (2026-10-16)

Read-only replay of the frozen Phase252 daily 23:00 UTC trailing-168h funding decision from the four authenticated V98 funding CSVs. Training window only: 2023-01-01 through 2025-12-31, Dec-2022 warmup. No price/PnL, no selection, no other engines, no 2026+ or holdout.

- 1,096 decision days; original Clean-4 funding sum <= 0 on 274 days; BTC+ETH+SOL-only diagnostic sum <= 0 on 100 days.
- 192/1,096 daily decision flags (17.52%) differ when BNB's funding term is omitted. BNB drives 183 additional active flags and suppresses 9; this is a diagnostic, not a proposal to remove BNB or change Phase252.
- Yearly differing flags: 2023 = 85/365; 2024 = 48/366; 2025 = 59/365.
- BNB historical training rates exactly zero in 1,800/3,288 settlements (54.74%); yearly 507/1095 (2023), 582/1098 (2024), 711/1095 (2025). Other Clean-4 assets have zero exact-zero rates in the same window.

**Decision:** PENDING_INDEPENDENT_BNB_VENDOR_PROVENANCE. This establishes material dependence of the frozen opportunity activation on BNB funding and does not prove that zero rates are erroneous. No native-funded candidate was rerun or promoted. Phase252 remains partial historical leader; full seven-slot V98 champion remains unvalidated.
