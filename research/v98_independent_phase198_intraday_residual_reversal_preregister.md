# V98 Independent — Phase198 preregistration

## Hypothesis
A scientifically distinct, execution-local hypothesis: **intraday residual reversal after market-adjusted hourly shocks**. After removing the contemporaneously observable broad crypto move using only lagged/closed bars, unusually large idiosyncratic 1h moves may mean-revert over a short fixed horizon. This is distinct from Phase196's rolling-volatility expansion trigger and Phase197's multi-hour dispersion-gated momentum.

## Isolation and data firewall
- V98 Independent namespace and `research/v98-independent-zero` only.
- Training discovery/evaluation ends strictly before 2026-01-01 UTC.
- Validation and final holdout remain unopened; final holdout must remain `null`.
- No V16/V99 code, parameters, reports, workflows, state, paper results, or outcomes may be used.
- Features and eligibility at decision time t use only fully closed information through t-1.

## Frozen signal family
At each decision hour, compute each asset's last closed 1h log return and subtract the cross-sectional median last-closed 1h return to obtain a market-adjusted residual. Estimate each asset's trailing residual-volatility scale from closed history only.

Grid is frozen before execution:
- residual-vol lookback: {72h, 168h}
- shock threshold: {|residual| / trailing_sigma >= 1.5, 2.0}
- holding horizon: {3h, 6h}

For eligible shocks, trade opposite the residual sign. If both long and short candidates exist, construct equal-weight long/short books with gross exposure capped at 1.0 and target net exposure 0. If only one side exists, do not open a directional book for that decision. No threshold optimization after results.

## Evaluation protocol
Chronological training folds are fixed: calendar 2023, 2024, 2025, plus aggregate 2023-2025. Report activity/episodes, total return/CAGR, max drawdown, daily Profit Factor, payoff, win rate, positive/negative days, turnover, gross/net exposure, best/worst day, p01/p05/CVaR, regime results (bull/bear/sideways), bottom-10 loss share and top-10 gain share.

Run realistic funding and transaction-cost accounting under the repository's established **base, severe, and supersevere** V98 cost schedules. No cost schedule may be weakened after observing results.

## Promotion gates
A candidate may advance only if all established V98 training gates pass, including positive and sufficiently broad fold behavior, acceptable PF and drawdown, regime breadth, non-pathological concentration/activity, and survival under severe/supersevere stresses. Zero-activity or effectively trivial-activity specs cannot pass.

## Reproducibility / invariants
- Canonical V98 training-only data rebuild before evaluation.
- Assert all price/funding inputs stop before 2026.
- Run the experiment twice from the same inputs and require byte-identical report output.
- Report must explicitly identify V98 Independent, Phase198, training-only scope, `validation: null` when present, and `final_holdout: null`.

## No-rescue rule
If the frozen family fails, reject it. Do not invert it, remove losing folds/regimes/tails, tune thresholds, alter costs, or inspect validation/holdout to rescue it. A subsequent idea requires a new preregistration and genuinely distinct causal rationale.
