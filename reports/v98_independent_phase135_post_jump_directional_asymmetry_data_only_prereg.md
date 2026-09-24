# V98 Independent — Phase135 Post-Jump Directional Asymmetry DATA_ONLY preregistration

Status: PREREGISTERED AFTER Phase134 REJECT_NO_RESCUE. Phase134 parameters are closed and will not be rescued or retuned.

## Motivation
Phase134 produced positive aggregate expectancy and survived severe/supersevere friction, but failed the frozen yearly-fold gate in 2025 (negative return and PF below 1.02). This is evidence of temporal instability, not permission to tune Phase134. Phase135 is therefore a scientifically distinct DATA_ONLY audit of whether completed broad downside-jump days have a stable, causal next-day directional asymmetry across calendar folds, without constructing or evaluating a tradable strategy.

## Frozen data scope
Use only V98 Independent canonical hourly market data and only 2023-01-01 through 2025-12-31 UTC. Assets remain BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT. Validation and final holdout remain forbidden. No V16/V99/Phase083 information may be used.

## Frozen construction
For each asset/hour compute completed log return. For each asset/day define scale using only the preceding 28 completed UTC days: median absolute hourly log return. A downside jump is hourly log return <= -3.0 times that prior scale. A broad shock day requires jumps in >=3 assets. For DATA_ONLY integrity, record only event timestamps/counts and availability of the subsequent completed UTC day per asset/fold; do not compute, print, persist, rank, correlate, or inspect next-day return magnitudes, alpha, PnL, PF, DD, payoff, win rate, costs or funding.

## Frozen DATA_ONLY gates
Require strictly increasing timestamps, zero duplicates, zero rows after 2025-12-31 23:00 UTC, >=20 broad-shock event days overall, >=5 event days in each 2023/2024/2025 fold, >=95% of event days with a complete subsequent UTC day for >=4/5 assets, deterministic event hash, and exact reproducibility on rerun. PASS_DATA_ONLY only establishes that a later separately preregistered directional-asymmetry hypothesis is testable. Any failure closes this family without rescue.

## Isolation
V98 Independent namespaced files only. No parameter search, no Phase134 rescue, no alternative threshold/lookback/breadth after this preregistration, no validation, no final holdout, no V16/V99 use.