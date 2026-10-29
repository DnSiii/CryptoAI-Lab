# V98 Independent KY — dispersion carry + concentrated dual-horizon trend + breakout recovery (2026-10-29)

**Pre-PnL immutable architectural hypothesis.** KX was permanently rejected at +48.0613% base training CAGR against >50% preregistered gate. KY is NOT a parameter adjustment or continuation of KX: it replaces KX fixed strategic BTC/SOL/BNB beta with concentrated dual-horizon relative strength; KX volatility-normalized weekly selection with prior-range price breakouts; KX single-asset negative-funding long with a signed two-leg cross-sectional funding spread; KX falling-market relative resilience with a 24h reversal following 168h market contraction. All KX receipts/results are excluded from KY selection.

## Data firewall
Exactly Phase243 authenticated Clean-4 BTCUSDT ETHUSDT BNBUSDT SOLUSDT USD-M 1h, 2022-12 warmup, 2023-2024 training only. Source load must use the existing phase1260 authenticated loader and signed native funding; no 2025/2026+, XRP, Phase083, V14/V15/V99 internals. Execute at next actual open from completed t close, causal risk bounds, native costs, both funding orders. No Frozen/paper/live modifications.

## Seven composed slots, fixed before results
1. **Growth Core 0.66:** every 672h, assets with BOTH completed 168h and 672h positive log returns are eligible; choose top two by 672h log return, invest 0.44 and 0.22 long, respectively. If only one qualifies, allocate 0.66 to it; otherwise cash. No post-result asset-specific exceptions.
2. **Opportunity 0.12:** at each 168h weekly event, if idle, buy asset with maximum excess above prior 168 completed-hour HIGH (current completed close / max(high[t-168:t]) - 1), strictly positive excess and 336h positive return, hold 168h. Breakout entry is distinct from KX Sharpe-like score.
3. **Relative Value 0.10:** weekly if idle, rank 168h native signed funding paid by long; if cross-asset difference between max and min exceeds 0.0015 cumulative per unit notional, long 0.05 lowest and short 0.05 highest for 168h. The funding spread is a precommitted economic hypothesis, not a price-mean-reversion rescue. No opposing physical positions permitted by allocator.
4. **Stress/Recovery 0.06:** weekly if idle, when broad equal-weight 168h return negative but 24h return positive, buy the strongest 24h recovering asset only if its own 24h return positive; hold 168h. Different state transition from KX.
5. **Regime Router:** TREND when broad 672h positive; RECOVERY when broad 168h negative and 24h positive; DEFENSE when broad 168h negative; otherwise MIXED.
6. **Dynamic Allocator:** persistent independent unit rows, source gross <=0.94, >=5% physically reserved cash, signed gross (not net), pending exit cannot fund new entry, ablations do not refill Core.
7. **Risk Governor:** prior-only 336h OHLC, 672h signed native funding, staged exit quote envelope, next actual open, native fee/slippage/funding, strict physical cash and gross bounds, independent settlement oracle.

## Pre-PnL hard gate
18,288 pinned hours, authentic source manifest, causal future mutation, no invalid quote entry, no silent row changes, <=0.94 source gross, >=8 entries per year for EACH optional sleeve in 2023 and 2024. Failure rejects KY before PnL.

## Economic and independent gates (only after source PASS)
5 independent books x base/severe/supersevere x both funding orders x two Ubuntu OS = 30 cells; 60 independent original receipts, 5 full-hour settlement oracles. CAGR >50% base and >30% severe; severe 2023 and 2024 each positive; severe max DD <45%; base and severe turnover <=USD600k; each sleeve Full-minus-ablation net log growth >0.02 combined in base and severe and >=-0.03 for each individual year. Verify PF, payoff, win rate, positive days, concentration/tails, regimes, reproducibility, causality, 81-corner settlement and funding. No post-result rescue, no 2025 validation before complete internally frozen PASS, no external benchmark until separate validation passes, no live orders.
