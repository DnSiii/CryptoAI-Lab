# V98 Independent Phase1188 — AD online core/router constants locked before source and system PnL (2026-10-23)

## Boundary and status
Distinct Phase1186 AD seven-slot complete-engine hypothesis; Phase1187 permanently rejected AC is **not** a tuning input. This document fixes **only** Growth Core and Regime Router mathematics and their causal observation order. Other five slots, execution and risk must be independently preregistered and integrated before any AD official historical system PnL. No external V14/V15/V99, 2025 validation, XRP, 2026+, or contaminated Phase083.

## Growth Core (causal self-financing virtual experts)
Three **long-only/cash** experts with four Clean-4 assets in fixed order BTC, ETH, BNB, SOL:
- Expert E0 broad long: 0.25 each asset.
- Expert E1 adaptive leadership: at completed bar t, use 96-hour cumulative log return divided by sqrt(168) times causal 168-hour return standard deviation (floor 0.002 per hour). Apply stable softmax to the four values with temperature 1.0, then mix 10% equal weight to prevent single-asset dominance. No AC ordinal 168/720 signs/ranks.
- Expert E2: 100% cash.
At bar t, **first** update each expert's virtual wealth using only its **prior completed-bar** weights and realized close[t-1] to close[t] simple returns, subtract 0.0012 per dollar of virtual absolute turnover at the last expert rebalance, and signed native funding cash for events observed at t. Then update posterior with cumulative log wealth using stable softmax with fixed learning rate 0.35; floor posterior probabilities at 0.05 and renormalize. New expert target weights formed only **after** this update for next bar t+1. Expert E1 refresh every 24 hours at t divisible by 24 after 336 warmup hours; otherwise carry. No artificial upside cap or historical return sign flips. Virtual returns are *causal online features*, not executable AD portfolio PnL.
At 336 completed hours, initial expert wealth 1, equal posterior; before that the system stays in cash. At every update, invalid/nonpositive virtual wealth **fails closed**; no clipping negative wealth into profitability.

## Regime Router
Three-state Bayesian HMM: risk-off, transition, risk-on. Transition matrix diagonal 0.985 and off-diagonal 0.0075; initial posterior [1/3,1/3,1/3]. Observation x_t is equally weighted market **log** return at completed t divided by previous 168h standard deviation of market log returns, floor 0.002; x_t clipped to [-8,8] only for numerical likelihood stability (not trading return). Gaussian emission means [-0.45,0,+0.45] and standard deviations [1.25,1.40,1.25]. Update posterior from t observation only; no forward/backward smoothing, hindsight regime segmentation or threshold optimization. Router reports the full posterior, not a static 0/1/2 gate.

## Deterministic and causal contract
- Complete hourly UTC contiguous chronology, Dec-2022 warmup through **no later than Dec-2024** for this initial two-fold training implementation; 2025 untouched until AD freeze and internal success.
- Exact Clean-4 column order and strictly valid OHLC. Native funding event mask required; non-events must have zero funding.
- Floating online states are not presented as pre-frozen cross-OS hashes; deterministic signed quantized observer hashes may be proposed separately **before** authenticated source evaluation, with strict tolerance and two-OS replication.
- At t, only bars <=t and native events <=t may influence targets for t+1; changing bar t must not change any state at t-1.
- No historical system NAV/CAGR/PF is computed by this source-only phase. Frozen full engine will later require 90-cell chronological training, native signed mark/funding, 81-corner stress, executable exit liquidity and independent FIFO PF.
