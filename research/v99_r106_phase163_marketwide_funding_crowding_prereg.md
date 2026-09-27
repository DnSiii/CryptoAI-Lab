# V99 R106 Phase163 — Market-Wide Funding Crowding Reversion

PREREGISTERED BEFORE ANY Phase163 PnL.

## Motivation and family boundary
Phases159-162 tested cross-sectional relative-value funding transforms and all failed TRAIN. That family is closed: no threshold rescue, sign flip, parameter search, or reuse of its PnL to tune Phase163.

Phase163 is scientifically distinct: it does **not** demean funding cross-sectionally and does not trade relative funding ranks. It tests whether the market-wide median funding level is a directional crowding state: unusually positive broad funding implies crowded longs and a subsequent negative premium; unusually negative broad funding implies crowded shorts and a subsequent positive premium.

## Frozen hypothesis
- TRAIN only: 2021-12-01 through 2024-01-18, identical transport/calendar contract to Phase159-162.
- Universe/data transport: exactly Phase159 PASS_DATA_ONLY assets and deterministic Binance Vision funding archive.
- At each valid event with >=4 assets, compute scalar cross-asset median funding `M` without cross-sectional demeaning.
- Normalize `M` with trailing Exact-MAD168 using history shifted by one valid event.
- REVERSION only: scalar direction `-z(M)`; clip magnitude to 1 only as the predeclared leverage safety cap, then distribute equally across available Phase159 assets so portfolio L1 <= 1.
- Execution lag: +1 hour after signal availability; causal past-only event matching <=1h.
- No grid, no sign flip, no rescue, no threshold search, no asset selection.
- Same severe-cost TRAIN evaluator and four chronological temporal folds used by Phase159-162.
- Holdout rows used for feature construction/selection: 0/0.
- If base TRAIN gate fails, reject and do not run downstream stress gates.
- If it passes, freeze before severe/supersevere, regime matrix, tails/concentration, benchmark envelope and reproducibility.
- V16 Frozen and V99 Frozen are immutable.
