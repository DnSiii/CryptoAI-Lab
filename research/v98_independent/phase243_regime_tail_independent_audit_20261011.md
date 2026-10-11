# V98 Independent — Phase240 regime/tail recorded-results audit (2026-10-11)

**Scope:** research/v98-independent-zero, V98-only, Phase240 *recorded* training-fold results. This is an independent accounting/robustness audit, **not** a new backtest, new alpha experiment, strategy rescue, holdout test, or promotion. No V16/V99 changes.

**Evidence:** phase240_results.json Git blob SHA `55c13167d1f29683a2a18c3a8e7a695ea090c4f9`; frozen 8 specifications x 3 chronological years (2023, 2024, 2025) x 3 costs = 72 recorded evaluations. No 2026+ data.

- **72/72** net returns negative and Profit Factor < 1; **216/216** bear/bull/sideways regime records also negative and PF < 1 (72 each for base, severe, supersevere). There is no regime with positive recorded performance to select without cherry-picking.
- **240/240** matched base→severe→supersevere comparisons monotonically worsen return, PF, MDD, win rate and positive days. This is a recorded-results invariant, not an independent price-data backtest.
- **72/72** records have |1st-percentile downside| > 99th-percentile upside, on the *recorded tail sampling horizon*. Largest reported single-day loss: **-24.6206%**; maximum reported asset concentration: **27.5970%**; recorded MDD range approximately **-95.8163% to -99.9999996%**.
- Tail quantiles are ordered in **72/72**. Crucially, **do not compare** tail_p99 to best_day as if they were the same sampling horizon: six supersevere records have best_day < tail_p99. Without verified common granularity, this is *not* an integrity failure. The two quantities must be audited separately.
- PF vs payoff×win-rate/(1−win-rate) has small maximum absolute residuals (global **0.0015041**, regime **0.0021978**). These are diagnostic only: event weighting/zero-return treatment has not been authenticated, so do not falsely impose exact equality.

**Decision:** Phase240 REJECT_FAMILY_NO_RESCUE; Phase243 BLOCKED_SOURCE_CONFLICT; no champion. The XRP 2023-11-14 11:00 UTC monthly 1h quote/base conflict is unresolved. Independently checksum-verified daily 1m/1h originals are still required. No source repair, no weakening gates, no holdout access. Preserve realistic funding, severe/supersevere costs, chronological folds and all full promotion gates.