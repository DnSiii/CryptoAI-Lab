# V98 Independent Phase221 — pre-result implementation audit

Audit performed after implementation/workflow creation and before observing any Phase221 result payload.

## Preregistration fidelity
- Frozen grid is exactly 8 specs: W {168,336} x L {6,24} x hold {4,8}.
- Universe is ETH/BNB/XRP/SOL; BTC is benchmark only.
- Direction is continuation exactly as preregistered: long highest residual score, short lowest, 0.5/0.5 gross exposure.
- No thresholds, asset subsets, regime filters, sign inversions, or parameter interpolation were introduced.

## Causality/data integrity
- Price returns use `pct_change(fill_method=None)`.
- Both alt and BTC return streams are shifted one hour before rolling beta; therefore beta and residual score at decision t end at t-1.
- Beta requires full W observations and finite/non-negligible BTC variance; residual score requires full L observations.
- Missing/non-finite/tied cross sections produce no trade.
- Canonical data firewall rejects any timestamp >= 2026-01-01 and duplicate/non-monotone timestamps.

## Execution/risk/cost audit
- Pair exposure is +0.5/-0.5 and gross exposure invariant <=1.
- Global pair holding window prevents overlapping Phase221 pair events.
- Execution PnL uses next hourly open-to-open return through position shift, preventing same-bar signal execution.
- Established V98 costs are frozen at base 7 bp, severe 14 bp, supersevere 28 bp per turnover unit.
- Funding is PIT carry only, never a feature; funding events are applied only at their hourly settlement bucket crossed by an already-held position.

## Evaluation discipline
- Training folds remain 2023, 2024, 2025 separately; 2026+ holdout is unopened.
- Required metrics include return, MDD, PF, payoff, win rate, positive days, trades, p01/p05/p50/p95/p99, worst/best trade, asset concentration, funding contribution, and bull/bear/sideways attribution.
- Workflow runs evaluator twice and requires byte-identical report SHA, plus monotonic base -> severe -> supersevere degradation.
- Mechanical promotion gate remains return > 0 and PF > 1 in all three training folds. No rescue is permitted if 0/8 pass.

## Independent audit conclusion
Implementation is decision-eligible subject to successful workflow invariants/reproducibility. No result has been used to modify the frozen hypothesis. Champion remains unchanged and holdout remains closed.
