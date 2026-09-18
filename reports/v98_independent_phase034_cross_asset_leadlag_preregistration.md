# V98 Independent — Phase 034 Cross-Asset Lead-Lag Network — Preregistration

Status: preregistered before any Phase034 result is observed.

## Hypothesis
Among the point-in-time liquid universe, lagged returns of peer assets may contain causal cross-sectional information about the next return of each asset. A rolling multivariate peer lead-lag model can capture decentralized information propagation not represented by the previously rejected BTC-only lead-response family.

## Frozen specification
- Universe: point-in-time top 10 liquid assets; BTC excluded from tradable targets but may remain a peer predictor when available.
- Liquidity lookback: 720h; minimum history: 2160h.
- Return inputs: close prices shifted by one full bar before any feature construction.
- Lead-lag estimation window: 720h, minimum 360 complete observations.
- For each tradable asset j, fit OLS using only lagged historical data: r_j(t) = intercept + sum_i b_ji * r_i(t-1), peers i != j.
- Current score for j: sum_i b_ji * r_i(current lagged observation). No contemporaneous/future input.
- Rebalance: every 6h.
- Cross-sectional score is rank transformed, then neutralized against intercept and contemporaneously known unconditional rolling BTC beta.
- Gross target/cap: 0.75.
- No coefficient/sign/window/cadence/gross/threshold/regime search after seeing results.

## Evaluation / gates
Use the existing V98 chronological training folds and unchanged training gate. Evaluate realistic base costs/funding plus severe and supersevere cost/funding stresses, concentration/tails, drawdown, PF, payoff, win rate, positive days, regimes and beta neutrality. Validation may be inspected only if the frozen training gate passes. Final holdout remains untouched unless a candidate passes training and validation and is formally frozen.

## Anti-overfit decision
If rejected, close this cross-asset lead-lag architecture without sign inversion, window/cadence rescue, subset cherry-picking or parameter tuning. Move to a genuinely orthogonal family.