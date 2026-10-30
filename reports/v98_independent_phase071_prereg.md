# V98 Independent Phase071 — preregistration

Status: FROZEN BEFORE PNL.

## Motivation
Phase070 showed aggregate funding-carry edge but failed 2025. Phase071 tests a structural, ex-ante condition rather than rescuing Phase070 parameters: funding carry should only be deployed when cross-sectional funding dispersion is large enough to compensate execution friction and weak carry differentiation.

## Hypothesis
At the daily 00:00 UTC rebalance, compute each asset's realized funding over the prior 168 completed hours (strict t-1). Rank five frozen symbols. Long the lowest trailing-funding asset and short the highest, but only when the cross-sectional range between highest and lowest trailing funding exceeds a threshold fixed from an economically interpretable annualized carry-spread floor.

## Frozen specification
- Engine: V98 Independent only.
- Symbols: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT.
- Training only: frozen folds 2023, 2024, 2025; no validation or final holdout access.
- Funding lookback: 168 completed hours.
- Rebalance: daily 00:00 UTC.
- Gross exposure when active: 0.75, market-neutral 0.375 long / 0.375 short.
- Score: trailing 168h realized funding sum.
- Long: lowest score; short: highest score.
- Activation: trailing funding range >= 0.0015 (15 bps over seven days). This is frozen before any Phase071 PnL and represents roughly 78% simple annualized spread before compounding.
- Otherwise flat.
- No parameter sweep, no rescue, no Phase070 outcome-based threshold tuning.

## Costs and gates
Use the existing frozen V98 BASE, severe and supersevere execution/funding model. Training gates are unchanged: aggregate return > 0, daily PF > 1.05, max DD >= -35%, no ruin; every chronological fold return > 0 and PF > 1.00; severe return > 0 and PF > 1.00; supersevere must avoid ruin and retain >=10% of positive BASE profit.

Report payoff, win rate, positive/negative days, regimes, concentration, asset contribution, tails, turnover and reproducibility hashes.

## Isolation
V16 and V99 are prohibited. Validation remains unopened unless every training gate passes. Final holdout remains UNTOUCHED.