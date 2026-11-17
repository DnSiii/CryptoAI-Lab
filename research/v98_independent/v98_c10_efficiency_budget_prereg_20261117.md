# V98 Independent C10 — preregistration, 2026-11-17

C9 is rejected and immutable. C10 is a **distinct trend-efficiency / volatility-budget portfolio**, not a modification or rescue of C9. This hypothesis is specified before C10 results are observed. Training only: authenticated Clean-4 1h Dec-2022 through Dec-2025, native funding, next-open causal execution, costs 1x/2x/4x. XRP quarantined; no 2026+ or contaminated holdout.

Seven slots:
1. Growth Core: 90-day and 30-day positive return, 30-day directional efficiency > 0.20, split 0.32 equally across qualifying assets.
2. Opportunity: 7-day positive return and 30-day directional efficiency > 0.35, allocate 0.16 to highest 7-day return.
3. Relative Value: 30-day return above cross-sectional median, positive 7-day return; allocate 0.12 to highest residual.
4. Stress/Recovery: after broad 30-day drawdown (at least 3 assets negative), wait for at least 3 positive 7-day returns; then hold the lowest 30-day realized-volatility eligible asset for seven daily decisions at 0.12, only while its 7-day return stays positive. No lookahead.
5. Regime Router: per-asset 30-day efficiency > 0.20 and positive 30-day return => 1.0; positive 30-day return but low efficiency => 0.5; otherwise 0.25. Never uses C9 volatility-spike router.
6. Dynamic Allocator: deterministic per-asset inverse 30-day realized-volatility scaling of each sleeve, normalized to preserve its gross sleeve budget; caps 0.35 per asset and 0.72 total. Inverse-vol allocation is computed solely from completed closes, not PnL feedback.
7. Risk Governor: existing causal drawdown governor remains a survival constraint, never disabled for deployable results.

Daily decision cadence, 2160-hour warmup; only completed closes through t and fill at t+1 open. No leverage, no shorts, no external engines. Hypothesis: trend efficiency reduces churn and adverse supersevere-cost effects while inverse-vol budgets preserve compound-growth opportunities; this is uncertain, not a performance claim.

**Frozen decision rule:** require full 27,048-hour native replay and source hashes, reconciliation, seven-slot ablations/counterfactuals at all three costs, positive economic marginal contribution for each alpha sleeve and both router/allocator under 4x, robust chronological training/validation, independent replay and severe tails. Governor evaluated on survival, not positive PnL. No post-result threshold/sign/window/cap adjustment; reject failed C10, then pursue genuinely distinct hypothesis. Do not use 2026+ holdout for selection or benchmark V14/V15/V99 before internal freeze and validation.
