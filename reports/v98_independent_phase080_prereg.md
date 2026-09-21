# V98 Independent Phase080 — Preregistration

Status: FROZEN BEFORE PNL.

## Hypothesis
Cross-sectional medium-horizon trend quality may be more robust than raw momentum: assets whose 28-day net move is large relative to the total absolute hourly path may carry persistent directional information, while low-efficiency/noisy paths should not receive equal conviction. This is a fresh training-only hypothesis; Phase079 PnL is not used to tune any parameter.

## Frozen design
- Engine namespace: V98 Independent only.
- Training only: chronological folds through 2025-12-31. Validation and final holdout remain closed.
- Universe: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT.
- Signal uses only information available by t-1: over fixed 28-day / 672-hour window, efficiency = abs(net simple-price move) / sum(abs(hourly simple returns)); signed score = sign(net move) * efficiency.
- Rebalance: once daily at 00:00 UTC.
- Portfolio: long highest signed-efficiency asset and short lowest signed-efficiency asset, equal side notionals, gross 0.75, no parameter search.
- Missing/ineligible assets ignored; require at least two valid scores.
- Execution/evaluation: existing exact_fast V98 Independent machinery with realistic funding/costs; BASE, severe, supersevere.

## Frozen training gates
PASS requires simultaneously: aggregate return > 0; aggregate daily PF > 1.05; max drawdown >= -35%; no ruin; every chronological fold return > 0 and daily PF > 1.00; severe return > 0; supersevere return > 0. Any failure => REJECT_NO_RESCUE. Validation stays closed unless all training gates pass.

## Required evidence
Aggregate/fold/stress return, CAGR, max drawdown, PF, payoff, win rate, positive/negative days, turnover/exposure; regime attribution; concentration; asset contribution proxy; daily tails/CVaR; positions/prereg SHA256; explicit V16/V99 non-use and untouched holdout flags.

No V99 or V16 information is used to define, tune or select this hypothesis.
