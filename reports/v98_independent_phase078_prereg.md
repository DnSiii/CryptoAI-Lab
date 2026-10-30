# V98 Independent Phase078 — Preregistration

Status: FROZEN BEFORE PNL.

## Hypothesis
Cross-sectional residual momentum after removing the contemporaneous equal-weight market component may isolate asset-specific persistence that is obscured by common crypto beta.

## Frozen design
- Engine namespace: V98 Independent only.
- Training only: existing chronological training folds through 2025-12-31. Validation and final holdout remain closed.
- Universe: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT.
- Signal: hourly log returns, shifted one hour for causality; at each hour subtract the cross-sectional mean return; sum residual returns over a fixed 14-day / 336-hour lookback.
- Rebalance: once daily at 00:00 UTC.
- Portfolio: long highest residual-momentum score and short lowest residual-momentum score, equal side notionals, gross 0.75, no parameter search.
- Missing/ineligible assets are ignored at that event; require at least two valid scores.
- Execution/evaluation: existing exact_fast V98 Independent machinery with configured realistic funding and costs; BASE, severe and supersevere scenarios.

## Frozen training gates
PASS requires all simultaneously: aggregate return > 0; aggregate daily PF > 1.05; max drawdown >= -35%; no ruin; each chronological fold return > 0 and daily PF > 1.00; severe return > 0; supersevere return > 0. Any failure => REJECT_NO_RESCUE. Validation remains unopened unless every training gate passes.

## Required evidence
Aggregate/fold/stress return, CAGR, max drawdown, PF, payoff, win rate, positive/negative days, turnover/exposure; regime attribution; concentration; asset contribution proxy; daily tails/CVaR; positions/prereg SHA256; explicit V16/V99 non-use and untouched holdout flags.

No V99 or V16 information is used to define, tune or select this hypothesis.
