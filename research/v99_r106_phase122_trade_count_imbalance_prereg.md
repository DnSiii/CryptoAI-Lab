# V99 R106 Phase122 — raw aggressive trade-count imbalance (preregistered)

Status: **PREREGISTERED ONLY — eligible only after Phase121 is formally decided**.

## Scientific question
Does imbalance in the *number* of buyer- versus seller-aggressive executions contain train-only cross-sectional information distinct from quantity imbalance (Phase120) and size-conditioned pressure (Phase121)?

## Frozen hypothesis
- Source: official Binance USD-M `aggTrades` archives already provenance/integrity-gated by Phases118–119.
- Train ends 2024-01-18 00:00:00 UTC exclusive. Holdout values may not be downloaded, parsed, summarized, selected on, or inspected.
- Universe: exactly the same precommitted resource rule used by Phase120: 12 smallest Phase118 listed pre-holdout compressed-byte totals, lexical tie-break; at least 8 must be executable. No return/PnL-based membership changes.
- Per asset/hour feature: `(buyer_aggressive_trade_count - seller_aggressive_trade_count) / (buyer_aggressive_trade_count + seller_aggressive_trade_count)`; missing if denominator is zero.
- Cross-section: median/MAD robust z using >=8 available assets, then `tanh`.
- Direction: continuation. No sign flip.
- Entire signal shifted by one complete hourly bar (t-1) before execution.
- Portfolio: cross-sectional L1 normalization, gross alpha budget 0.20, canonical R106 execution/guardrails.
- Missing archives/hours remain missing; no future backfill or synthetic imputation.

## Anti-overfit lock
Single hypothesis. No grid over horizon, transform, sign, universe, gross, threshold, or lookback. No parameter may be changed because of Phase122 PnL.

## Gates
1. Integrity/causality/executable-universe invariants.
2. Train-only severe-cost gate + chronological folds.
3. PASS only: freeze exact spec and run supersevere costs.
4. PASS only: regime matrix plus concentration/tail/pathology audit.
5. PASS only: benchmark envelope plus deterministic reproducibility/invariant rerun.
6. Holdout remains sealed until every preceding gate passes unchanged.

Any scientific failure permanently rejects this exact hypothesis. Infrastructure may be repaired without changing the frozen hypothesis.

## Independence rationale
Phase120 weights executions by traded quantity. Phase122 deliberately discards size and asks whether directional event frequency itself carries information, testing order-flow persistence/fragmentation rather than notional pressure. This is an orthogonal feature construction, not a parameter tweak.
