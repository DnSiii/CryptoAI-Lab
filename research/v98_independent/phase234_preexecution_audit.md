# V98 Independent Phase234 — independent pre-execution audit

Status: completed before observing any Phase234 result.

## Scope and preregistration lock
- Hypothesis/grid remains exactly the Phase234 preregistration committed at `ad4f62ce9831a97de44bd56e0f3cfdf0e7a0568c`.
- Exactly 8 frozen specs; no sign flip, rescue threshold, asset exclusion, regime filter, or post-result tuning.
- Calendar training folds are 2023, 2024, 2025. 2026+ is a hard unopened firewall.

## Causality audit
- `open(t)` decision reads residual-volatility `signal.iloc[i-1]` only.
- Rolling beta and residual volatility therefore end no later than `open(t-1)` for the trading decision.
- BTC regime labels are also shifted one row before attribution.
- Funding is timestamped point-in-time and charged against lagged held position.

## Accounting / stress audit
- Book is cross-sectional long-low-idvol / short-high-idvol, equal absolute weights and dollar-neutral at each event.
- Overlapping sleeves are normalized so gross exposure cannot exceed 1; evaluator raises on invariant breach.
- Turnover is absolute position change and frozen costs are 7/14/28 bp; validator requires cost monotonicity.
- Required portfolio diagnostics: total return, max drawdown, Profit Factor, payoff, win rate, positive days, funding contribution, BTC bull/bear/sideways regimes, tails, per-asset contribution and max asset concentration.

## Tail/concentration caveat
Event-level trade tails are diagnostic because overlapping sleeves make exact trade attribution non-additive. Portfolio accounting is authoritative for gate decisions; tail summaries cannot independently rescue a failed annual gate.

## Mechanical gate
For every 2023/2024/2025 base-cost fold: return > 0, PF > 1, positive-days > 0.5, max DD > -50%; additionally severe PF > 0.90 and supersevere PF > 0.80. Every fold must pass for a spec to survive. No survivors => `REJECT_FAMILY_NO_RESCUE`.

## Reproducibility plan
Run the evaluator twice from identical rebuilt training-only inputs and require identical deterministic payload SHA256 before validation. Any mismatch is an integrity failure, not an economic result.
