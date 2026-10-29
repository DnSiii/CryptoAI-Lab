# V98 MB — preregistered causal joint-capital allocation and atomic execution (2026-10-29)

**PRE-RESULT COMMIT.** MB is a NEW, complete seven-slot architecture. MA/LZ/LY and all rejected candidates remain frozen; do not transplant or retune rejected sleeves. This document is frozen before MB code, authenticated source evaluation, or PnL. No 2025+, XRP, contaminated Phase083, V14/V15/V99 or paper reads.

## Data, chronology and costs
Only SHA-authenticated Clean-4 2022-12 warmup and 2023-24 training: BTC/ETH/BNB/SOL Binance USD-M 1h, 18,288 bars/asset, 9,144 native signed funding events. Signals at completed t, next-open fills at t+1; no intra-hour future OHLC/mark/rate may influence pre-fill weights or capacity. Use SHA-pinned official mark 1h OHLC worst-side funding envelope for ex-post conservative settlement; not exact funding-tick mark. Both funding orderings. Base fee/slippage 4/2bps, severe 10/10bps, supersevere 15/20bps.

## New economic hypothesis: growth-score competition, not static sleeve allocation
1. **Growth Core:** every 336 completed hours from t=744, rank four assets by 504h log-return divided by (0.08 + 3x 168h realized hourly volatility); only positive 504h assets. Hold 0.44/0.22 NAV in top two if 168h positive-return breadth >=3, else 0.30/0.12 if breadth 1-2; zero in breadth 0. No lookahead.
2. **Opportunity:** every 168h, rank positive 168h assets by 72h log-return minus 72h prior return (t-144 to t-72). Enter +0.13 NAV in strongest with strictly positive acceleration and 72h return >0. Hold 168h, no same-clock reentry.
3. **Relative Value:** every 336h, rank four assets by their 168h log-return minus median of four 168h log-returns. Pair long strongest residual and short weakest residual, 0.08 NAV each, only if cross-sectional residual spread >0.06 and both 168h quote-volume windows valid. Hold 336h, no same-clock reentry. Economic mechanism is relative trend persistence and market-neutral dispersion, not MA funding carry.
4. **Stress/Recovery:** every 72h, if at least two assets' 168h log-returns are negative and at least two assets' 48h log-returns are positive, long strongest positive 48h asset at +0.11 NAV. Hold 144h, no same-clock reentry. This is 48h multi-asset recovery with distinct capital allocator, not MA's 24h selection.
5. **Regime Router:** breadth of positive 168h returns: bull >=3, mixed 1-2, bear 0; core as above, opportunity allowed only breadth >=2; RV and Stress independent.
6. **Dynamic Allocator:** reserve gross <=0.90 NAV and compete for capital based on each sleeve's trailing ex-ante 168h risk-adjusted trend score. Core reserved at its scheduled weight; optional sleeves scaled proportionally to fit remaining gross. If a sleeve is ablated, its capital stays in cash, never reallocated. No result-driven allocation.
7. **Risk Governor:** atomic close/reduce-first pretrade planner, cost-aware before any increase, never gross >100% NAV at any intermediate state, final <=0.93 NAV after fees and worst funding. If pretrade future-dependent funding or intrabar high/low is required to size, reject (never peek). Funding event must be conservatively reserved from known pre-fill information, with post-fill realized worst-side funding checked against reserve. Intrabar adverse OHLC equity strictly positive.

## Pre-PnL source gate
Independent replay of three sleeve entry calendars, synthetic and authenticated future mutation, zero invalid/silent updates, max intended gross <=0.90, >=8 entries/sleeve/year in both 2023 and 2024. Failure = permanent source-only rejection, no PnL.

## Physical economic gates
Five books: full, core-only, minus Opportunity, minus RV, minus Stress; three cost tiers x two signed funding orderings = 30 actual full-hour cells. Full base CAGR >50%, severe >30%, severe annual returns >0 for both 2023/24, severe max drawdown <45%, base/severe turnover <=USD600,000 per USD10,000 initial. Each sleeve's full-minus-ablation net log-growth >0.02 base/severe, and each annual marginal >-0.03. Record max intrabar drawdown, 1% CVaR, concentration, positive days, PF, payoff, win rate, costs and reproducibility. No post-result sign/window/threshold/gross rescue.

Any training pass is provisional only. Freeze entire MB before separate independent all-hour ledger/settlement oracle, cross-OS, 81-corner checks, separate 2025 validation and untouched future holdout. External benchmarks only after internal freeze and separate validation. No live authorization or guaranteed PnL.
