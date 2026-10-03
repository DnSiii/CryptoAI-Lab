# V98 Independent — Phase220 pre-result audit

Status: **PRE-RESULT / HOLD INTERPRETATION UNTIL MAD CHECK**

## Scope and isolation
- Branch reviewed: `research/v98-independent-zero` only.
- Phase220 implementation and workflow are V98 Independent namespaced; no V16/V99/paper state is used for signal selection.
- Frozen universe/spec grid matches preregistration: 4 alt perpetuals; N={21,63}, spread={1.0,1.5}, hold={4h,8h}; 8 specs total.
- 2026+ is blocked by the data loaders and workflow firewall. BTC is used only for ex-post regime labels.

## Causality/economics checks
- Funding-derived scores are timestamped at `ceil(fundingTime)+1h`, enforcing the stated `fundingTime <= t-1h` availability rule.
- Price returns use `pct_change(fill_method=None)`; positions are applied with a one-bar lag in PnL.
- Pair weights are +0.5/-0.5, gross exposure is asserted <=1.0, and the implementation permits only one pair at a time, so same-asset overlap cannot occur.
- Funding cashflows use signed prior-bar position and point-in-time funding events; trading turnover is charged under base/severe/supersevere schedules.
- Fold outputs include return, MDD, PF, payoff, win rate, positive days, trade tails, asset concentration, funding contribution and BTC bull/bear/sideways diagnostics.

## Independent issue found before results
The preregistration says the robust scale is the trailing MAD of the same N-event window. The first implementation computes a rolling median, then a second rolling median of absolute deviations from time-varying rolling medians. That is not exactly `median(|x - median(window)|)` for each window. This was detected before any Phase220 result was harvested or interpreted.

**Decision:** any output produced by the current first implementation is non-decision-grade and must not be used to reject/promote/tune Phase220. Correct the MAD implementation to an exact deterministic rolling-window MAD, strengthen the static invariant, rerun both deterministic passes, and only then apply the frozen mechanical gate. This is a preregistration-fidelity correction, not a semantic rescue and does not alter N/S/hold/sign/universe/gates.

## Anti-overfit disposition
No result has been used to change signal direction, threshold, asset set, hold, cost schedule, or gate. Holdout remains closed. Champion remains unchanged pending a corrected, reproducible Phase220 evaluation.
