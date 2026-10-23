# V98 Independent Phase1074 — S signed funded chronological ledger preregistration (2026-10-23)

No S historical PnL has been observed. This preregistration fixes economic accounting *before* 90-cell evaluation and does not modify S signal or risk parameters.

- Source-only Phase1071–1072 two-runner PASS is mandatory before any official economic invocation. Source must be official Clean-4 18,288h, native 9,144 funding events, typed signed (18288,4,2) mark bounds, frozen five S target SHA256 hashes.
- At open(t), execute target computed at close(t-1), using only quote_volume(t-1), shocks(t-1), funding-bound(t-1). Intrabar 16-corner and actual OHLC stress audits must pass. Native funding settlement debits/credits use held-before-fill and held-after-fill separately, always adverse signed mark side. No lookahead.
- Prior shock inputs: backward-only 720h rolling **maximum** of realized hourly low/open downside and high/open upside, minimum 24 completed observations; do not use the current bar. Prior native funding reserve: backward-only 720h maximum absolute native rate, available history only.
- Fee tiers fixed: 0.0007, 0.0012, 0.0020. Capital modes: immediate USD 10,000; capacity_1m USD 1m and capacity_10m USD 10m, both capped at 1% of t-1 quote turnover. Funding orders: carried_before_fill and new_after_fill.
- Report hourly/daily NAV, 2023/2024 separate fold CAGR/log wealth, max hourly/daily drawdown, PF, payoff, win rate, positive days, CVaR, asset concentration HHI, gross/net exposures, fees/funding/turnover, rejection index/reason, and reproducible receipt.
- All 90 cells must survive and pass positive year-by-year full-engine log wealth at base/severe, positive marginal versus all ablations across relevant cases, and other precommitted safety gates. Any failure rejects S, not an invitation to repair parameters after the fact.

No 2025 validation, 2026+, XRP, Phase083, or V14/V15/V99 access.