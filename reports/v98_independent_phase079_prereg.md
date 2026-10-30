# V98 Independent Phase079 — Preregistration

Status: FROZEN BEFORE PNL.

## Hypothesis
Cross-sectional downside semivolatility may contain a defensive risk premium distinct from directional momentum/reversal: assets with persistently smaller negative-return dispersion may outperform, risk-adjusted, assets with larger downside dispersion after realistic perpetual costs.

## Frozen design
- Engine namespace: V98 Independent only.
- Training only: chronological folds through 2025-12-31. Validation and final holdout remain closed.
- Universe: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT.
- Signal: causal hourly simple returns shifted one hour; over fixed 28-day / 672-hour window compute sqrt(mean(min(return,0)^2)). Lower score is preferred.
- Rebalance: once daily at 00:00 UTC.
- Portfolio: long lowest downside-semivol asset and short highest downside-semivol asset, equal side notionals, gross 0.75, no parameter search.
- Missing/ineligible assets ignored; require at least two valid scores.
- Execution/evaluation: existing exact_fast V98 Independent machinery with realistic funding/costs; BASE, severe, supersevere.

## Frozen training gates
PASS requires simultaneously: aggregate return > 0; aggregate daily PF > 1.05; max drawdown >= -35%; no ruin; every chronological fold return > 0 and daily PF > 1.00; severe return > 0; supersevere return > 0. Any failure => REJECT_NO_RESCUE. Validation stays closed unless all training gates pass.

## Required evidence
Aggregate/fold/stress return, CAGR, max drawdown, PF, payoff, win rate, positive/negative days, turnover/exposure; regime attribution; concentration; asset contribution proxy; daily tails/CVaR; positions/prereg SHA256; explicit V16/V99 non-use and untouched holdout flags.

No V99 or V16 information is used to define, tune or select this hypothesis.
