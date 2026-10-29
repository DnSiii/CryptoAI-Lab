# V98 Independent KU — inverse-volatility trend compounder / trend pullback / funding-adjusted alt spread / bearish ETH carry (2026-10-29)

**Independent complete-portfolio hypothesis preregistered before KU source or PnL.** KT was permanently rejected at authenticated source gate (Opportunity 1/3 and Stress 7/5 in 2023/2024); no KT threshold/window/sign rescue. KU uses four economically different mechanisms and its own complete seven-slot frozen design, not KT source edits or rejected KS signals.

## Immutable source firewall
Phase243 pinned Binance USD-M Clean-4 BTC/ETH/BNB/SOL 1h Dec-2022 warmup and 2023-2024 chronological training, native 8h signed funding/mark. Completed close t decision, actual open t+1. No 2025, 2026+, XRP, Phase083, V14/V15/V99 internals, Frozen, paper, or real orders.

## Seven slots (gross target 0.94, reserve 0.06)
1. **Growth Core 0.58:** at each 336h event, use BTC and ETH independently. A coin is eligible if its completed 672h log return is positive. Allocate 0.58 long **inverse proportional to its prior 336h realized hourly volatility** across eligible assets (single eligible gets full 0.58), otherwise cash. Fixed units between events; not KS leader rotation or KT breadth/mean filter.
2. **Opportunity 0.14:** at each 168h event while idle, long ETH for 168h only if its completed 672h return is positive **and** its last completed 24h return is negative. This is trend-conditioned pullback, not KT compression expansion, KS carry-adjusted acceleration or a breakout.
3. **Relative Value 0.12 gross:** each 168h event while idle, compute for BNB and SOL completed 336h log return **minus the actual signed funding rate paid over that window**. Long the higher funding-adjusted trend score at 0.06, short lower at 0.06, for 168h; deterministic BNB tie-break. This is funding-adjusted alt momentum, not KS low-vol spread, KT BTC residual spread, or KM pure funding carry.
4. **Stress/Recovery 0.08:** daily while idle, if ETH 336h log return <0 and its close below its trailing 672h median, short ETH 0.08 for 120h. Slow bearish carry protection, not KS 24h volatility crisis short or KT failed-selloff ETH long.
5. **Regime Router:** BULL if BTC/ETH 672h trend positive, BEAR if ETH bearish condition true, MIXED otherwise; no retroactive gating.
6. **Dynamic Allocator:** persistent four signed unit rows; no gross>0.94 at source, 6% reserved, signed cash-aware physical allocator with >=5% reserve, no opposing carried/pending, no intrahour exit cash recycling or refill after risk cuts; ablations keep unused capital in cash.
7. **Risk Governor:** prior-only OHLC 336h, funding 672h, native mark/quote staged exit, exact physical liquidation, three fee tiers, two funding orders, independent 81-corner every-hour oracle.

## Precommitted acceptance
Source-first: exact 18,288 hourly records, SHA pins, native funding, synthetic + real-history future mutation, no invalid-quote entries or silent row rebalances, >=8 optional sleeve source entries EACH 2023 and 2024. Any failure permanently rejects KU before PnL; no post-result repair.

On source pass, 5 independent books (Core/Full/three leave-one-out) x 3 fee tiers x 2 funding orders x 2 OS = 30 physical cells, 60 independently audited original receipts, five every-hour 81-corner oracle audits, cross-OS determinism. Full CAGR >50% base and >30% severe, severe both annual returns >0, severe DD<45%, base/severe absolute turnover <=USD600k, each optional sleeve Full-minus-ablated log growth >0.02 combined base AND severe and >=-0.03 in each calendar year. All orders must pass. PF, payoff, win rate, positive days, tails, concentration, cost/funding and causal execution must be reported. Only internal training freeze/pass opens separate 2025 validation; untouched future holdout and external benchmark comparison later. No live trading.
