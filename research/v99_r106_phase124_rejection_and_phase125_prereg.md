# V99 R106 — Phase124 decision + Phase125 preregistration

## Phase124 decision (train-only)
Phase124 trade-size participation concentration is permanently rejected. Under the preregistered severe-cost gate it produced train ROI -89.8699%, PF 0.450963, max DD 89.9573%, positive-hour ratio 35.8524%, robust mean excluding top 1% -1.38585e-4/h, and 0/4 healthy chronological folds. All four folds were negative (ROI -44.92%, -45.09%, -41.57%, -42.67%) with PF < 0.52 and negative robust mean ex-top1%. This is broad temporal failure, not an isolated tail. No sign flip, threshold search, cost relaxation, or retuning is allowed. Holdout was not parsed; V16 Frozen and V99 Frozen remained untouched.

## Family-level implication
Together with the already rejected flow/OI/positioning families and Phases121-123 aggressor variants, Phase124 argues against spending the next test on another aggTrades participation/count/concentration transformation. The next hypothesis deliberately changes information source and economic mechanism.

# Phase125 — Volatility Efficiency / Directional Persistence

## Scientific hypothesis
At a fixed 1h horizon, assets whose recent realized path is unusually directionally efficient (large net displacement relative to total absolute movement) exhibit short-horizon continuation after controlling cross-sectionally. This uses only canonical price history and is orthogonal to aggressor flow, OI, positioning, funding/premium and trade-size concentration.

## Frozen feature
For each asset and hour t, using canonical hourly close prices available through t:

- hourly log return r_t = log(C_t/C_{t-1});
- 24h directional efficiency E_t = sum_{i=t-23..t} r_i / sum_{i=t-23..t} |r_i|, only when all 24 returns exist and denominator > 0;
- at each timestamp, robust cross-sectional z = (E - median(E))/max(1.4826*MAD(E), 1e-9);
- raw score = tanh(z);
- tradable alpha at hour t+1 is the entire score shifted by one full hour (strict causal t-1);
- cross-sectional L1 normalization; gross alpha = 0.20.

Direction is **continuation** and is frozen now. No opposite-sign trial is permitted after seeing PnL.

## Universe and data discipline
Use the same chronological train-only universe-selection machinery and canonical hourly market data already used by R106. Asset eligibility must be determined without candidate PnL. Missing hours remain missing; no future fill/backfill. Minimum 8 executable assets. Training ends strictly before 2024-01-18T00:00:00Z. Untouched holdout must not be parsed or summarized.

## Gates
Single hypothesis, no grid. First run the standard severe-cost train gate and four chronological temporal folds. PASS requires the existing R106 mandatory train/fold criteria without relaxation. A FAIL is permanent for this exact hypothesis. Only PASS may freeze the exact specification and proceed, in the same order, to supersevere costs, regime matrix, tails/concentration, benchmark envelope, reproducibility/invariants, and only then the untouched holdout under the repository's existing formal release discipline.

## Anti-overfit prohibitions
No lookahead; no contemporaneous execution of E_t; no sign flip; no alternative 12/48/72h lookback after result; no threshold/grid search; no symbol dropping based on PnL; no fold exclusion; no cost relaxation; no holdout inspection. V16 Frozen and V99 Frozen are immutable.
