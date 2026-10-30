# V98 Independent — prevent inflated funding-order scenario counts (2026-10-27)

This is an **artifact-only methodological finding**, not a new strategy, economic rescue, improved PnL or training approval. It does not change the immutable IF rejection.

## Independently verified result
- Original IF 2023-2024 [30-cell physical training and independent oracle run](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40483375577), five independently funded paths x three cost tiers x two funding orders x two operating systems.
- Separate [artifact-only uniqueness audit](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40484104086), using the original frozen 22.04 economic receipts: **15/15 funding-order pairs have exactly equal annual and full-history economics** (NAV, funding, turnover, costs, PF, payoff, win rate, CVaR, drawdown and concentration). All 15 have **zero forced risk ratchets** and exactly 53 physical fill hours matching 53 target updates. No source/strategy/PnL recomputation.
- Mechanism: IF signal epochs are t=744+336k, 336 divisible by 8; actual fills are at t+1, i.e. never on native eight-hour funding boundaries. With no unscheduled ratchet, carried-before-fill and new-after-fill pay exactly the same native funding. Cross-OS reproduction is a numerical integrity check, not a new economic scenario.

**Honest accounting:** 30/30 physically surviving/reproduced execution cells, **15 economically distinct path x cost scenarios**, and five independent full-hour physical oracles. Do not report 30 independent economic opportunities or treat two funding orders as corroborating profit evidence. IF remains **REJECT_IF_HISTORICAL_GROWTH_OR_MARGINAL**.

## Critical-path optimization for *future* V98-only architectures
Precommit an execution-event audit: record every actual fill's native funding-event indicator, including emergency risk ratchets. If **zero** event-aligned fills and governor authorization is order-invariant, the second funding order is mathematically redundant and can be verified by an artifact-only equivalence certificate instead of repeating the full backtest. If any fill occurs on a funding boundary, or governor behavior differs, **run both orders** and retain full physical checks. Always preserve severe/supersevere costs, independent funding ledger oracle, chronological folds, source provenance, and separate future holdout. Do not retroactively change frozen experiment results.

This reduces avoidable runtime only when equivalence is proved; it does not relax risk, economic gates, reproducibility or future validation.
