# V98 C3 independent complete-system architecture preregistration — 2026-11-13

Status: HYPOTHESIS ONLY; no performance claim, no promotion, no access to 2026+ or Phase083. C2 remains frozen and rejected for promotion; its 4x ablations motivate a genuinely distinct low-turnover architecture, not a threshold rescue. No V14/V15/V99 information may enter design or selection.

## Predeclared C3: slow structural trend + cash-efficient opportunity + defensive relative-value

Training: authenticated Binance USD-M Clean-4 BTCUSDT ETHUSDT BNBUSDT SOLUSDT, 1h, Dec 2022 warmup through Dec 2025, native V98 funding, next-open t-1 execution, 1x/2x/4x native costs. No XRP. Independent future holdout untouched.

Seven slots:
1. Growth Core: 56-day positive absolute trend with 28-day confirmation; top two by 56-day return, 0.42 budget.
2. Opportunity Sleeve: 14-day breakout beyond the previous 28-day highest completed close, 0.12 budget, single winner.
3. Relative-Value Sleeve: strongest positive 56-day return relative to equal-weight Clean-4 median with positive absolute 56-day return, 0.12 budget, single winner.
4. Stress/Recovery Sleeve: if at least three assets have negative 28-day returns, choose the strongest positive 14-day return among assets with negative 28-day returns, 0.09 budget.
5. Regime Router: existing V98 causal regime_multiplier applied after sleeves, unchanged.
6. Dynamic Allocator: existing V98 compose_weights applied after sleeves; idle budget stays cash, no leverage, unchanged.
7. Risk Governor: existing V98 governor_multiplier applied to complete portfolio, unchanged.

Distinct hypothesis from C2: replace fast impulse/volatility-expansion selection with slow structural breakout and relative breadth; weekly 168-hour recomputation, no optimization grid. Fixed weights and lookbacks are preregistered here before results. Each sleeve can be idle. Deterministic tie-break by asset symbol. All data read through completed close only.

Evaluation: run entire chronological Clean-4 historical replay for all three costs; independently reconcile equity/funding/turnover; chronological annual/monthly folds, max DD, PF, payoff, win rate, positive days, tails, concentration, stress regimes, prefix invariance, source hashes, and four sleeve leave-one-out counterfactuals with no redistribution. Reject C3 if it fails any mandatory causal/source/accounting gate, if full system lacks economically meaningful long-run growth, or if marginal contributions and 4x stress demonstrate fragility. No after-the-fact changes to these thresholds or signs. Freeze a candidate only after separate chronological validation; compare external engines only after internal freeze and validation. Never treat tests or CI success as investment validation.
