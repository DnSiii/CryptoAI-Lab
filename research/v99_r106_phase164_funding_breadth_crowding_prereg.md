# V99 R106 Phase164 — Funding Breadth Crowding Reversion

PREREGISTERED BEFORE ANY Phase164 PnL.

## Motivation and family boundary
Phase163 tested the magnitude-sensitive cross-asset median funding level and failed TRAIN (ROI -8.95%, PF 0.98435, robust mean < 0, 0/4 healthy folds). No rescue, sign flip, lookback/threshold search, or parameter tuning of Phase163 is permitted.

Phase164 is a distinct breadth hypothesis: it discards funding magnitudes and asks whether unusually one-sided participation across the market is itself a crowding state. This is not a threshold rescue of Phase163: the observable is frozen as the signed breadth of positive versus negative funding across the same deterministic asset set.

## Frozen hypothesis
- TRAIN only: 2021-12-01 through 2024-01-18; same deterministic Binance Vision transport/calendar contract as Phase159 PASS_DATA_ONLY.
- At each valid funding event with >=4 assets, compute breadth `B = (N_positive - N_negative) / N_available`; exact zeros contribute 0.
- Normalize B with trailing Exact-MAD168 using history shifted by one valid event.
- REVERSION only: scalar direction `-z(B)`; clip magnitude to 1 solely as the predeclared leverage safety cap.
- Distribute scalar equally across available frozen Phase159 assets; portfolio L1 <= 1. No asset selection.
- Execution lag +1 hour after signal availability; causal past-only event matching <=1h.
- No grid, no sign flip, no rescue, no threshold search, no alternative breadth definition after seeing PnL.
- Same severe-cost TRAIN evaluator and four chronological temporal folds used by Phase159-163.
- Holdout rows used for feature construction/selection: 0/0.
- If base TRAIN gate fails, reject and do not run downstream stress gates.
- If it passes, freeze before severe/supersevere, regime matrix, tails/concentration, benchmark envelope and reproducibility.
- V16 Frozen and V99 Frozen are immutable.
