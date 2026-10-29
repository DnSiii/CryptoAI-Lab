# V99 R106 I1 — held-position exact intraday fold MARK source repair (preregistration)

Date: 2026-10-29 10:49 BRT. **SOURCE_ONLY/HOLD; NO PROMOTION.**

## Reproducible defect before changes

The existing `research/tools/v99_r106_i1_source_to_mark_event_spine.py` compiles held-contract original marks **only at 23:59:59 UTC daily**, whereas the fixed five TRAIN folds have four intraday edges at **2022-04-20 04:00, 2022-08-30 09:00, 2023-01-09 14:00 and 2023-05-21 19:00 UTC**. The native wallet replay `_fold_snapshot` requires **same-clock marks for every open position** at each intraday edge. Thus an actual held option spanning a fold edge is structurally unable to reach an exact-fold NAV through the current original source spine. It must not silently use a previous-day mark, interpolate, or pretend that a daily mark is the exact edge.

## Fixed, ex-ante repair

1. Retain all original 661 daily 23:59:59 MARK requests. For each frozen intraday edge, **only when a selected original position is open at that exact time** (`decision_ms <= edge_ms < expiry_ms`), request a new **literal same-contract, pre-edge original quote** for BOTH legs with the existing <=300-second venue+arrival freshness, original compressed-byte manifest, size and causal checks. Insert the resulting additional MARK event at the true intraday time into the same UTC day, in chronological order. Do not fabricate marks or change entry/exit rules.
2. Extend the separately implemented lifecycle oracle to require the exact union of 661 daily clocks and the four frozen intraday clocks for each held position. Missing, duplicated, substituted or future fold-edge quotes must fail before NAV. Keep scenario-specific exposure differences legitimate.
3. Test a synthetic position actually spanning an intraday fold boundary and a missing edge quote; run the existing original-source integration CI on GitHub and independently verify. CI fixtures remain **software tests only**.

## Scientific boundary

No opening of validation [2023-10-01, 2024-01-18) or holdout >=2024-01-18; no historical option index/fees/lot/margin/fills or PnL certification; no C1/D1/D2/D3/E1/H1 retune; no orders, paper, Frozen or legacy champion writes. The **658 missing original Deribit days, written licensed entitlement, original delivery index, account fee/margin and hypothetical execution** remain external blockers after this internal correction. If no original edge quote is available, reject the position's numeric path rather than approximating.