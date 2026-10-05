# V98 Independent Phase240 — pre-execution implementation audit

Status: completed before observing any Phase240 performance result.

## Preregistration-to-code check
- Family is the preregistered idiosyncratic shock-recovery relative-value test, not a continuation of residual moment/persistence ranking.
- Frozen grid is exactly beta lookback {168,336} x scale lookback {72,168} x k=1 x H {4,8} = 8 unique specs.
- Direction is frozen reversal: long lowest standardized lagged residual shock; short highest. No post-result sign flip is allowed.
- Chronological evaluation folds remain 2023, 2024, 2025 only; >=2026 is explicitly firewalled.
- Costs remain 7/14/28 bp and realized funding is PIT via the existing V98 funding dataset.

## Causality audit
- Rolling beta is shifted one hour before residual construction, so residual(u) uses beta information through u-1.
- Residual scale is a lagged rolling MAD: median/MAD windows are shifted before the scale is applied.
- Decision open(t) indexes `shock.iloc[i-1]`; no t return or future observation enters selection.
- PnL uses `w.shift(1) * rr`, preserving execution/accounting convention used by recent decision-grade phases.

## Risk/accounting diagnostics
Evaluator emits return, max drawdown, Profit Factor, payoff, win rate, positive days, best/worst day, L1 turnover, signal count, p01/p05/p50/p95/p99 hourly tails, per-asset PnL/funding contribution, maximum asset concentration and lagged BTC bear/bull/sideways diagnostics. Gross exposure is normalized and asserted <=1.

## Anti-overfit disposition
No threshold, asset subset, regime gate, sign flip or rescue has been added. Phase240 must be rejected as a family if the unchanged annual gate fails. Holdout 2026+ remains sealed regardless of attractive isolated training cells.
