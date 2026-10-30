# V98 Independent — Phase059 Macro Risk Overlay Preregistration

Status: FROZEN BEFORE ANY PHASE059 PnL/RETURN COMPUTATION.

## Hypothesis
A broad crypto long exposure should be held only when lagged public macro-risk conditions are benign: equity volatility is below its trailing annual median, the 10Y Treasury yield is not above its trailing annual median, and the effective federal funds rate is not rising versus 21 observations earlier. This is an exogenous risk-state hypothesis, not a cross-sectional crypto signal.

## Frozen inputs
- FRED VIXCLS, DGS10, DFF only; Phase058 established training-era feasibility.
- Crypto execution universe/data remain V98 Independent only.
- Training research interval and chronological folds remain those in `config/v98_independent.json`.
- Validation remains closed until the training gate passes; final holdout remains untouched until training + validation pass and the candidate is frozen.

## Frozen causal construction
1. FRED observations are treated conservatively: each dated observation becomes usable only on the following UTC day; forward-fill occurs only after that one-day lag.
2. For VIXCLS and DGS10, compute a trailing 252-observation median using only lagged observations, minimum 126 observations.
3. DFF direction is `DFF_t <= DFF_{t-21 observations}` using only lagged observations.
4. Macro risk-on requires all three simultaneously: `VIXCLS <= median252(VIXCLS)`, `DGS10 <= median252(DGS10)`, and non-rising DFF.
5. No sign search, threshold search, lookback search, cadence search, series subset search, regime rescue, or post-result inversion is allowed.
6. Portfolio when risk-on: equal-weight long the frozen five-symbol universe BTCUSDT/ETHUSDT/SOLUSDT/XRPUSDT/BNBUSDT, total gross 0.75. Otherwise flat. Rebalance daily at 00:00 UTC; positions are carried between rebalances.
7. No shorting and no leverage above 0.75 gross.

## Costs and funding
Use the existing V98 Independent exact execution engine and frozen base/severe/supersevere per-side costs and funding debit/credit multipliers from `config/v98_independent.json`.

## Mandatory evaluation
Training aggregate plus chronological 2023/2024/2025 folds; base/severe/supersevere; max drawdown; Profit Factor; payoff; win rate; positive days; tails; concentration; turnover; gross/net exposure; regime analysis; reproducibility/causality invariants.

Training gate is the existing V98 Independent gate (no relaxation). Any unevaluable mandatory metric is a failure. Validation is computed only after training passes. Final holdout is never opened by Phase059 training/validation code.

## Anti-overfit decision
- Training fail: REJECT Phase059 without rescue tuning or sign flip.
- Training pass: open validation exactly once under the same frozen construction.
- Validation fail: REJECT without rescue.
- Training + validation pass: freeze candidate; final holdout remains a separate one-shot gate.
