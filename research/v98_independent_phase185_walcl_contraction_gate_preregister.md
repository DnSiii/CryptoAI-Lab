# V98 Independent — Phase185 WALCL contraction gate preregistration

Status: **PREREGISTERED / TRAINING-ONLY ECONOMIC TEST / HOLDOUT CLOSED**

## Hypothesis frozen before PnL

Central-bank balance-sheet contraction is a macro-liquidity headwind for crypto. Use only the causally available native weekly FRED `WALCL` observations that passed Phase184.

Exactly one transformation is allowed:

- Compute `WALCL_4W_CHANGE = WALCL_t / WALCL_{t-4} - 1` on native weekly observations.
- After the conservative availability lag, forward-carry the latest causally available state to daily crypto timestamps; no interpolation of WALCL values.
- If `WALCL_4W_CHANGE < 0`, gross exposure multiplier = **0.50**.
- Otherwise, gross exposure multiplier = **1.00**.
- CONTROL = identical underlying V98 training stack with multiplier always 1.00.
- No alternate lookback, threshold, sign, nonlinear sizing, asset-specific rule, sweep, optimization, or rescue.

The zero threshold is economic (contraction vs non-contraction), not selected from the Phase184 descriptive distribution. Four native observations approximate one month and are fixed before any crypto PnL is computed.

## Research firewall

- Economic evaluation: training 2023-01-01 through 2025-12-31 only, preserving chronological folds 2023/2024/2025.
- Validation dates >=2026-01-01 and final holdout remain closed.
- V16/V99 files, workflows, reports, paper state, metrics, and candidates may not be read or used.
- Preserve existing V98 realistic costs/funding plus severe and supersevere stress schedules and existing gross-cap/invariants.

## Required report

CONTROL vs WALCL gate must report base/severe/supersevere total return; max drawdown; Profit Factor; payoff; win rate; positive days; 2023/2024/2025 folds; existing market-regime breakdown; concentration by asset; tail contribution/dependence; gross-cap; and deterministic rerun identity.

## Decision discipline

This is one preregistered candidate, not a sweep. Apply the existing V98 training promotion gates without weakening them. Any failed mandatory gate => `REJECT_NO_RESCUE`. Only a complete training pass may be frozen for untouched validation in a separate preregistered phase. No final holdout may be opened here.