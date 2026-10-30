# V98 Independent Phase081 — Preregistration

Status: FROZEN BEFORE PNL.

## Hypothesis
Cross-sectional 28-day channel location may capture persistent directional pressure with less sensitivity to a single endpoint return than raw momentum: assets trading near the top of their own lagged range may continue to outperform assets near the bottom. This is a fresh training-only hypothesis; Phase080 PnL is used only to reject Phase080, not to tune Phase081 parameters.

## Frozen design
- Engine namespace: V98 Independent only.
- Training only: chronological folds through 2025-12-31. Validation and final holdout remain closed.
- Universe: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT.
- Signal uses only information available by t-1: lagged close location inside its fixed 28-day / 672-hour rolling min-max channel, score = (close[t-1]-min)/(max-min)-0.5.
- Rebalance: once daily at 00:00 UTC.
- Portfolio: long highest channel-location asset and short lowest, equal side notionals, gross 0.75, no parameter search.
- Missing/ineligible/zero-range assets ignored; require at least two valid scores.
- Execution/evaluation: existing exact_fast V98 Independent machinery with realistic funding/costs; BASE, severe, supersevere.

## Frozen training gates
PASS requires simultaneously: aggregate return > 0; aggregate daily PF > 1.05; max drawdown >= -35%; no ruin; every chronological fold return > 0 and daily PF > 1.00; severe return > 0; supersevere return > 0. Any failure => REJECT_NO_RESCUE. Validation stays closed unless all training gates pass.

## Required evidence
Aggregate/fold/stress return, CAGR, max drawdown, PF, payoff, win rate, positive/negative days, turnover/exposure; regime attribution; concentration; asset contribution proxy; daily tails/CVaR; positions/prereg SHA256; explicit V16/V99 non-use and untouched holdout flags.

No V99 or V16 information is used to define, tune or select this hypothesis.
