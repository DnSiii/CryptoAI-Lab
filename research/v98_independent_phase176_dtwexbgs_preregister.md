# V98 Independent — Phase176 preregistration

Status: PREREGISTERED BEFORE ECONOMIC INSPECTION
Parent evidence: Phase175 DTWEXBGS DATA_ONLY PASS on 2023-01-01..2025-12-31.

## Isolation
- Branch: `research/v98-independent-zero` only.
- V98 Independent namespace only.
- V16 Frozen, V99 Frozen, all V99 research/workflows/reports/paper state are forbidden inputs and forbidden outputs.
- Final V98 holdout (2026-08-01..2026-09-15) remains unopened and forbidden.

## Scientific hypothesis
A strengthening broad USD is a macro headwind for crypto risk. A causal, slow-moving DTWEXBGS strength state may improve robustness of an otherwise frozen V98 candidate by reducing gross exposure during sustained USD-strength regimes. This is an orthogonal macro-state hypothesis, not a rescue/tuning of Phase172/173.

## Data and causality contract
- Macro series: FRED/H.10 `DTWEXBGS`, exactly the family audited in Phase175.
- Economic discovery/training window: 2023-01-01..2025-12-31 only.
- Same-day macro use is forbidden.
- Conservative availability rule: each observation becomes usable only on the next US business day after its observation date; strategy joins only the latest causally available value. No backfill from future observations.
- Missing macro observations are forward-filled only after they have become causally available.

## Frozen hypothesis transform
No parameter sweep is permitted in Phase176.
1. Compute 63-observation percent change of causally available DTWEXBGS.
2. `USD_STRONG = change_63 > 0`; otherwise `USD_NOT_STRONG`.
3. Compare exactly two predeclared variants against the same frozen underlying V98 signal: CONTROL (gross multiplier 1.00) and MACRO-GATED (gross multiplier 0.50 when USD_STRONG, else 1.00).
4. No thresholds, lookbacks, multipliers, asset weights, execution lag, or cost assumptions may be selected from observed PnL.

## Evaluation contract
- Chronological evidence only; no shuffled CV.
- Report total return, max drawdown, Profit Factor, payoff, win rate, positive days, trade/turnover counts, and per-year results.
- Report USD_STRONG vs USD_NOT_STRONG and existing market regimes where available.
- Report per-asset contribution, top/bottom tail contribution, concentration, and whether improvement depends on a small number of days/assets.
- Apply existing realistic base costs/funding plus severe and supersevere cost scenarios unchanged.
- Deterministic rerun / reproducibility and invariant checks are mandatory.

## Promotion/rejection discipline
Phase176 is discovery evidence only. Promotion requires broad robustness, not one headline metric: no catastrophic MDD/PF deterioration, no dependence on one asset/regime/tail, and cost-stress survival. A promising result must be frozen before any 2026 validation. Validation parameters may not change after seeing validation. Final holdout remains untouched until a formally frozen candidate passes validation.

## Anti-overfit / forbidden actions
No V99 information; no final-holdout information; no rescue after failure; no grid/random/Bayesian search; no post-result threshold adjustment; no cherry-picking years/assets/regimes; no weakening gates. If this fixed hypothesis fails, reject it and move to a scientifically distinct family.
