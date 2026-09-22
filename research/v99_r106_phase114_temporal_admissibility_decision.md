# V99 R106 Phase114 — temporal admissibility decision

This decision is made from Phase114 data availability plus the already-frozen `stable_train` gate definition. No bookDepth alpha or return relationship is computed.

## Facts
- Strict Phase114 audit: 48/48 canonical symbols have valid bookDepth data, one schema, ±1..±5 bands, ~30-second cadence.
- Strict admitted archive content begins **2023-01-01** and ends before **2024-01-18 00:00 UTC**.
- Existing R106 temporal folds for the relevant train window are:
  1. 2021-12-01 00:00 — 2022-06-13 11:00
  2. 2022-06-13 12:00 — 2022-12-24 23:00
  3. 2022-12-25 00:00 — 2023-07-07 11:00
  4. 2023-07-07 12:00 — 2024-01-18 00:00
- Existing `stable_train` requires at least **3 valid folds**, each with the existing minimum active-hour requirement, and at least 3 healthy folds.

## Consequence
A signal sourced exclusively from Phase114 bookDepth can have substantive observations only in folds 3 and 4. Therefore, under the preserved temporal-fold contract, **the maximum possible number of valid folds is 2**.

No candidate based solely on this source can pass the existing `stable_train` promotion gate, regardless of its PnL.

## Decision
- Do **not** launch a Phase115 bookDepth alpha merely to obtain an automatically ineligible backtest.
- Do **not** alter fold boundaries, reduce the valid-fold requirement, backfill pre-2023 order-book values, or combine synthetic/imputed bookDepth history to rescue eligibility.
- Keep Phase114 as a completed orthogonal data audit; bookDepth may be revisited only in a future protocol whose evaluation window/gates are defined independently before observing candidate outcomes.
- Continue V99 R106 research with a genuinely distinct source/mechanism that has enough pre-2023 history to satisfy the existing temporal-fold gate.

This is a gate-integrity decision, not an alpha rejection. V16 Frozen and V99 Frozen remain immutable; holdout market values remain untouched.
