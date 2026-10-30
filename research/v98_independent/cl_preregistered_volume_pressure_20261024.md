# V98 Independent CL — volume-weighted candle-pressure seven-slot architecture (PREREGISTERED 2026-10-24)

## Independent economic hypothesis
CL tests **volume-weighted intrabar close-location pressure** as a causal proxy for persistent aggressive buying/selling. It is a genuinely different *observable* from CK structural buy-and-hold/native carry-spread, CH cross-horizon price-momentum rank, CI channel compression, and CJ EMA acceleration. No rejected source signal, weight vector, threshold, result, or module is copied. Generic conservative V98 physical settlement/governor machinery may be reused without modifying it. Rejection is final, never retune CL after seeing its PnL.

## Data firewall and physical protocol
Exactly four authenticated Binance USD-M 1h assets BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, Dec-2022 warmup through 2024-12-31 training only. Read pinned OHLC, quote volume, native 8h signed funding and native conservative mark bounds. XRP quarantined. No 2025, 2026+, V14/V15/V99, Phase083 or paper. Features computed on completed bar t; positions may change no earlier than actual open t+1. 2160h warmup, 168h decision grid, 336h core grid. Shared collateral; module inventory frozen between decisions; no invisible leverage. Two funding orderings and base/severe/supersevere cost stress.

## Seven slots — immutable preregistration
1. **Growth Core:** at 336h intervals, calculate last 504h volume-weighted candle close-location value CLV=(2*close-high-low)/(high-low), with each bar weighted by clipped sqrt(quote_volume / mean quote_volume of last 504h) in [0.25,4]. Eligible assets have weighted CLV mean >0.05 and 1008h log return >0. Long top two eligible by weighted CLV (0.65/0.35), or single eligible at 1, else cash. Not a rank of price momentum, EMA or persistent fixed inventory.
2. **Opportunity Sleeve:** at 168h intervals, among BNB/SOL with positive last 48h weighted CLV, last 48h weighted CLV exceeding the preceding 48h by >0.10 and close above trailing 168h median close, long the alt with the largest acceleration; otherwise cash. This is signed-volume *flow acceleration*, not CK BTC-to-alt lag or CI volatility compression.
3. **Relative-Value Sleeve:** at 168h intervals, rank all four assets by 168h weighted CLV mean. If max-min >0.12, long highest at +0.5 and short lowest at -0.5; else cash. No native funding carry rank, no close-return residual spread; signed native funding still settles positions.
4. **Stress/Recovery Sleeve:** at 168h intervals, if at least two assets have negative 168h log returns, use last 48h BTC volume-weighted CLV: >0.05 => long BTC; <-0.05 => short BTC; otherwise cash. No CK broad-market 24h directional gate.
5. **Regime Router:** RISK_ON when >=3 assets have positive 336h weighted CLV and BTC 168h log return >0; RISK_OFF when <=1 have positive CLV and BTC 168h return <0; otherwise MIXED.
6. **Dynamic Allocator:** budgets [core,opp,RV,stress] RISK_ON [1.80,0.45,0.25,0.15], MIXED [1.35,0.40,0.30,0.35], RISK_OFF [0.70,0.25,0.45,0.60]. Shared NAV and pre-committed conservative physical clipping.
7. **Risk Governor:** unchanged V98 CG buffered physical authorizer: 60% stressed post-fill NAV, 40% floor, 18% maintenance, 0.25% prior-hour participation, staged 25% exit, 81 intrabar corners, 24h adverse continuation, native funding reserve. No relaxation.

## Preregistered fail-fast gates
- Source: pinned provenance, causal future-perturbation invariance, deterministic replay, each module >=4 nonzero allocated epochs in **each** of 2023/2024, Relative Value >=10 in each year. If not, REJECT_CL_SOURCE; do not calculate PnL.
- Economic: 20 USD10k cells (core/full/minus each satellite x base/severe x both native funding orders) independently reproducible across Ubuntu 22.04 and 24.04; full positive annual log growth 2023 and 2024, 2y CAGR >50% base and >30% severe, severe max DD <45%, **each** satellite annual full-minus-ablated log growth >0 in both years, both costs and funding orders. If any fails, freeze CL rejected; no retuning or 2025.
- If all pass: 90-cell scale including USD1m/10m and supersevere, independent event-by-event funding/fees/mark/81-corner replay, PF/payoff/win rate/positive days, concentration/tails/regimes/capacity, then internally freeze complete engine before separate untouched chronological validation. External benchmarks only after that validation.

**Authorized files:** `research/v98_independent/cl_*` and `.github/workflows/v98-independent-cl-*` on `research/v98-independent-zero`. Do not modify Frozen, V99, workflows/paper, or prior rejected architectures.
