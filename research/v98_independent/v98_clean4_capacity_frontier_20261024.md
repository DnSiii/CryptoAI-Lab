# V98 Independent — authenticated Clean-4 physical capital frontier (2026-10-24)

**Source-only, NOT a trading result.** Official reproducible GitHub Actions run **40096146644**, V98-only workflow `v98-independent-clean4-capacity-frontier.yml`, source script `v98_clean4_capacity_frontier.py`. Authenticated original pinned Dec2022–Dec2024 Clean-4 1h and native funding loader; manifest SHA256 `833013a2e18836a203afd267ca698175907cff8f4c153c919a7811f14cb80752`. Exact 313 previous-completed-hour 24h-window minima were independently cross-checked against the physical governor implementation at four timestamps. No 2025 holdout, 2026+, XRP, external V14/V15/V99, or paper accessed.

## Empirical constraint, USD maximum simultaneously authorized notional

The current **read-only** staged exit governor uses 0.25% hourly participation, 50% stressed quote-volume haircut, 2.2x exit-friction multiplier, and the inherited 25% BAGovernor entry fraction. Therefore per-asset maximum authorized notional at a completed signal is

`0.25 * 0.0025 * 0.50 / 2.2 * minimum_previous_336h_24h_quote_volume`.

This is a **conservative capacity upper bound**, not a promised fill, not a leverage target, not a prediction, and not a free pass through stressed collateral. In the ringfenced BX each of four books additionally receives only 25% of the global quote/exit envelope.

| 2023/2024 | 2023 median max USD | 2024 median max USD |
| --- | ---: | ---: |
| BTCUSDT | 527,910 | 735,484 |
| ETHUSDT | 304,987 | 412,875 |
| BNBUSDT | 19,377 | 25,506 |
| SOLUSDT | 37,077 | 176,418 |
| **All four combined, simultaneous** | **938,763** | **1,388,141** |

Combined 2023 p05 / p95 **USD355,344 / USD1,556,701**; combined 2024 p05 / p95 **USD770,253 / USD2,721,031**. Median total authorized gross capacity was only **9.39% of USD10m in 2023** and **13.88% in 2024** under the existing physical constraints. This directly explains why USD10m training paths often show sharply diminished CAGR despite profitable USD10k cases. It does **not** prove a universal impossibility of scaling a different instrument universe or a separately validated execution design.

## Practical critical path

A new V98 cannot manufacture capacity by simply increasing nominal capital or relabeling gross exposure. To credibly relax the current liquidity haircut/participation/exit horizon, evidence needed is **historical Binance USD-M order-book depth and/or authenticated executed-order/aggTrades market-impact calibration, including adverse and stressed hours**, with separate source provenance and preregistration. Current pinned OHLC quote volume and native funding alone do not establish the fill quality of substantially larger participation. **Alternative without external evidence:** retain the conservative physical limits and optimize compounding for realistically deployable capital; prioritize deeper BTC/ETH liquidity and avoid claiming USD10m can be fully deployed. This is a constraint on feasible growth, not a replacement objective of minimizing risk.

This diagnostic is a substantive input to the next *genuinely distinct* seven-slot hypothesis, not an approval or rescue of rejected BX/BW. BX remains frozen rejected, V16/V99 Frozen and paper untouched, 2025 future holdout sealed.

Official source audit: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40096146644 .
