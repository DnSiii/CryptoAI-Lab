# V98 Independent — Phase243 funding boundary convention sensitivity (2026-10-08)

Status: PREREGISTERED ACCOUNTING-ONLY; NOT AN ALPHA EXPERIMENT OR PROMOTION GATE.
Branch: research/v98-independent-zero. Scope: five V98 Phase050 assets; training-only 2023–2025, no 2026+ holdout.

## Motivation
An 8h exchange funding settlement near open(t) may occur before or after a portfolio's hypothetical open(t) rebalance. The existing Phase243 integration preregisters posttrade attribution (target w[t], cash at t+1). Hourly candles cannot identify precise intra-hour execution/mark-price ordering. A missing ordering stress test risks favorable attribution and hidden tails.

## Frozen diagnostic, no convention selection
1. PRIMARY, unchanged: posttrade settlement at scheduled t; cash=-w[t]*rate(t) in hourly interval ending at t+1.
2. SENSITIVITY ONLY: pretrade settlement at scheduled t; cash=-w[t-1]*(open[t]/open[t-1])*rate(t) in interval ending at t, prior to rebalance.
3. Same five SHA-audited V98-only native Phase206 funding files, same chronological folds, identical frozen weight paths, lagged information set, and base/severe/supersevere fees 7/14/28 bp. Exact and <=50ms jittered reports map to the same scheduled t.
4. Compare compounded return, MDD, PF, payoff, hourly win rate, compounded UTC positive days, funding contribution, worst/best days, daily tails, asset concentration, and regime attribution under BOTH conventions; report the signed difference, not the favorable one.
5. Explicitly distinguish synthetic adversarial fixtures from historical market backtests. The original posttrade primary remains the only preregistered execution convention; the pretrade alternative cannot rescue or promote a candidate. If differences are material, classify as execution-model uncertainty requiring higher-frequency data; do not optimize or tune.
6. Holdout <2026 firewall, source hashes, full 8h cadence, no price gaps, flat endpoints, and deterministic double-run remain mandatory. V16/V99 untouched.

No Phase243 real PnL has been examined to choose this sensitivity. This protocol is a diagnostic, not a new strategy family.
