# Phase195-AN — Research paper prefix audit

**DATA_ONLY/HOLD.** The main-branch V99 research-paper workflow checks paper schema and isolation but has no immutable published-prefix comparison before pushing to `paper-results`. This is a publication-safety gap, not proof of the underlying data-drift cause.

Across real artifacts 37817608480 → 37874980951, F1 and F3 each rewrite 415 forward equity hours from 2026-09-21 10:00 UTC. Across 37874980951 → 37912157984, each rewrites 424 hours from the same timestamp. R98, F7 and F12 remain unchanged on shared forward hours.

Retained overlapping operation records also change: F1 1191/1387 then 1271/1480; F3 1295/1401 then 1368/1478. The first divergence predates the earliest retained operation, so capped logs cannot prove the root cause.

All five historical backtest curves contain 24 points after the 2026-09-16 paper boundary. F1 backtest history starts drifting on July 24; F3 on June 15. A local fail-closed guard rejected both artifact pairs. Do not promote, rewrite paper, alter frozen engines or use holdout for selection. Next: causal fixed-input replays and separately dated append-only reconciliation only after independent authentication.
