# V98 Independent Phase1005 — O complete seven-slot growth architecture (preregistered)

## Decision boundary
Phase1001 rejected N_full on all 90 authenticated historical cells (common intrabar failure). N_full stays REJECTED; no sign/window/threshold/gross rescue. Phase1004 independently reproduced a stable M_full hash **different** from the recorded frozen pin (six identical observed hashes, zero matching the pin). Treat that inconsistency as a reproducibility quarantine. O is a genuinely new complete seven-slot candidate; it does **not** inherit frozen M/N target weights, parameters, allocations or performance.

## Thesis and fixed architectural hypothesis (source-only before economics)
O seeks high long-run compounded growth by holding causally persistent directional winners and dynamically reallocating across orthogonal opportunities, with survival constraints. All choices below are registered before observing O historical returns; no parameter grids or after-the-fact edits. Long-only USD-M Clean-4 (BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT), chronological 2022-12 warmup and 2023/2024 training, 2025+ and future holdout untouched. Native funding and conservative mark data only through independently authenticated same-run economic gate.

1. **Growth Core:** cross-asset positive 336h trend blended with positive 72h acceleration, divided by causal 168h downside semideviation (no hindsight), normalized long-only.
2. **Opportunity Sleeve:** 48h prior-high breakout plus positive 24h acceleration, conditioned on prior 168h realized volatility being below its prior 720h 40th percentile; no lookahead or retroactive breakout fill.
3. **Relative-Value Sleeve:** cross-sectional 168h return above the contemporaneous Clean-4 median, only for assets with positive 336h momentum; long-only, not an invented short book.
4. **Stress/Recovery Sleeve:** 336h market drawdown below -10% in the previous 168h, followed by positive 24h market return and improving 24h breadth; allocate to assets with positive 24h returns but negative 168h returns (distinct from Growth Core).
5. **Regime Router:** causal 168h market momentum, breadth, and realized 168h volatility relative to a past-only 720h median; risk-on requires >=3 positive 168h trends and market momentum positive and volatility below median; risk-off requires negative market momentum and <=1 positive trend. State change requires 12 consecutive hours of candidate state.
6. **Dynamic Allocator:** active-sleeve weights (Growth .50, Opportunity .20, RV .15, Recovery .15) reallocated among nonempty sleeves, updated at daily UTC close and on confirmed regime changes; target gross risk-off .35, neutral .90, risk-on 1.50; per-asset <=.70, gross <=1.75, unallocated stays cash. These are initial hypotheses, not tuned to the known rejected March 2023 bar.
7. **Risk Governor:** independently precommitted worst-case opening shock check from causal prior 720h observed max high/open and low/open, 16 OHLC corners, fee-aware opening sell-only LP candidate from Phase1002, previous-hour quote participation 5%, fail-closed. The governor cannot use current-bar high/low to choose orders. For O target construction, apply a cash reserve of >=10% of equity before intrabar stress checks. No hidden leverage; any dynamic exposure up to gross 1.50 is explicit and fully audited. Historical intrabar caps remain hard rejection gates, not optimization goals.

## Sequence and non-negotiable gates
A. Implement O's own pure source-only target builder, explicit seven-slot diagnostics and independent deterministic tests (chronology, no 2025+, t-1 execution, asset cap, sleeve ablations, no current-bar information).
B. Verify source-only target hash twice in independent processes after fresh Phase803 100 official OHLC ZIP authentication; require stable hashes. Record code SHA and inputs; freeze O targets **before** any economic PnL.
C. Run authenticated native funding, mark and OHLC source gates, then fixed chronological 2023/2024 full funded 90-cell economic matrix (5 paths x 3 fee tiers x 2 orderings x 3 capital modes) with full hourly survival, costs, intrabar corners, drawdown, CAGR, PF, payoff, win rate, positive days, concentration and tails. The O_full marginal against O-only ablations must be positive on preregistered growth gates. Do not select using future validation or benchmark results.
D. If training passes, independently freeze O and run a separate untouched 2025 validation. Only after internal freeze + validation may V14/V15/V99 be opened for external superiority benchmarking.
E. Any O failure is REJECT, no cosmetic rescue; next hypothesis must be a genuinely different complete architecture. Preserve N rejection and Phase1004 M reproducibility quarantine.

## Current status
PREREGISTERED SOURCE ONLY. No O PnL, no economic approval, no benchmark read, no 2025+ data access. Frozen V16/V99 untouched.
