# V98 Independent Phase1181 — AC official 90-cell training dispatcher preregistration

Date 2026-10-23, **before AC historical PnL**. Phase1180 froze AC full executable code after 15/15 authenticated source hashes and 90/90 exact synthetic receipts. Do not alter the frozen code or source hashes.

## Source and execution
- For each of the five independent path jobs, freshly attest official Binance USD-M Clean-4 Dec-2022..Dec-2024 1h OHLC and native V98 signed mark/funding, verify all 15 Phase1178 source hashes and all five Phase1180 code blob SHA pins **before** any historical PnL.
- Execute 2023-01-01T00:00Z through 2024-12-31T23:00Z inclusive (17,544 hourly transitions), Dec-2022 warmup only. Separate 2023/2024 folds; 2025 remains completely untouched; never access 2026+, XRP, Phase083 or external engines.
- Exactly five paths x three starting capitals ($10k/$1m/$10m) x three fees (.0007/.0012/.002) x two native funding timing orders (carried-before-fill/new-after-fill) = 90 independent economic cells. Each begins with all cash, zero inventory at 2023-01-01 00:00.
- Use AC source score at t-1, prior completed close/quote, t+1 actual opening fill, self-financing fees, signed native mark settlement, 81 adverse OHLC corners and explicit no-free-exit failure. Rebalance on UTC hours divisible by 12 (00/12 UTC), otherwise carry inventory.
- Causal 24h covariance = 24 times sample covariance (ddof=0) of **336 hourly log returns ending at t-1**, plus diagonal ridge 1e-8. No future returns.
- Causal down shock per asset = max(.25, maximum prior-336h one-hour gap/low loss relative to preceding close), clipped below 1 at 0.99; up shock = max(.30, maximum prior-336h one-hour gap/high gain relative to preceding close). No ex-post 2025 calibration. These are risk envelopes, not objectives.
- Adverse 720h funding bound per asset = max(.001, sum of absolute native funding rates in the prior 720 completed hours); applies to actual signed inventory in governor. Signed settlement mark low/high comes only from authenticated source.
- All hard AC Phase1176 risk/capacity limits and Phase1177 actual-open cash ledger remain unchanged. Any failing hour is a failed cell; do not skip, replace, interpolate, or silently continue after failure.

## Receipts, decisions and metrics
- Attempt all 90 cells regardless of early failures; report every failure reason, first failure hour, costs, funding, turnover, exposure, gross/net/asset concentration, 2023 and 2024 net compounded returns/CAGR, hourly max drawdown, positive days, daily tail CVaR5, daily gain/loss ratio, daily win rate and daily payoff. Trade-level PF/win/payoff must be computed by a separately frozen FIFO audit before any promotion; **daily proxies must never be mislabeled trade PF**.
- AC is accepted for separate future validation **only** if 90/90 executable, positive net compounded growth in both 2023/2024 under base and severe costs, robust positive marginal sleeve contribution, reproducible receipts and full independent trade-level accounting. Otherwise reject AC without parameter, sign, fee, window, threshold or leverage rescue.
- Official economic workflow may report preliminary cells while queued/running; partial cells cannot promote AC. 2025 validation and external benchmarks are forbidden until complete internal freeze and acceptance.

## Isolation
Write only new `research/v98_independent/phase1182_*` economic dispatcher and `.github/workflows/v98-independent-phase1182-*` workflow/receipts. No V16 Frozen, V99 Frozen, V99 research, V99 workflows/reports or V99 paper state changes.
