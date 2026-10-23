# V98 Independent Phase1196 — AD 81-corner executable survival governor preregistration (2026-10-23)

**Role:** a survival constraint on the complete AD portfolio, not a strategy for minimizing drawdown. No historical AD system PnL, 2025+, XRP, Phase083, V14/V15/V99, or any rejected-engine signals. This is distinct from the AD multiplicative wealth allocator.

At completed t, desired signed weights are a **proposal only**; actual target units are determined using **t+1 open** prices and actual prior inventory/equity, with causal prior quote volume, prior rolling minimum quote volume, prior OHLC downside/upside bounds and adverse native 720h funding bound. Never assume the target was filled.

### Frozen constraints
- 81 joint four-asset adverse price corners from each asset's [open*(1-down), open, open*(1+up)] with down in [0,0.99), up>=0; inputs must be causally measured, not inferred from t+1 highs/lows.
- At each corner after worst-case execution fees/slippage and adverse funding, equity >= **35%** of pretrade equity; per-asset absolute exposure <= **35%** of stressed equity; gross <= **115%** and absolute net <= **65%** of stressed equity.
- Stress execution costs: 0.002 fee plus 0.003 slippage per traded notional; no free exits. Every order notional <= **0.3%** of prior hourly quote volume. Any increase in absolute asset inventory requires stressed entry exposure <= **0.15%** of trailing 336h minimum quote volume AND 2x stressed exit reserve <= **0.3%** of that minimum quote volume. No hidden leverage.
- A deterministic scalar interpolation from actual carried units toward desired units searches 101 values lambda=1.00,0.99,...,0.00; take the largest executable feasible step. This is **not** AC's score-based four-pass coordinate optimizer. If no candidate passes, fail closed and explicitly report unexecutable inventory; never silently zero inventory. Actual executor must separately mark gaps, funding before/after fill and self-financing cash.
- No post-result relaxation of floor, concentration, quote capacity, fee, slippage, sign, or gross. Validate 81-corner enumeration, finite inputs, stressed exit reserve, gap failures, scalar monotonicity assumptions and adverse short squeezes synthetically before any official AD system PnL.
