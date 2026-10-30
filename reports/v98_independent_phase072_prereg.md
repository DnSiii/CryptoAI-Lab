# V98 Independent Phase072 — preregistration

Status: FROZEN BEFORE ANY PHASE072 PNL.

## Independent hypothesis
Cross-sectional **volatility-normalized medium-term momentum**. At each daily 00:00 UTC rebalance, use only information available through t-1. For each asset compute trailing 30-day (720h) log return divided by trailing 30-day realized hourly volatility scaled by sqrt(720). Rank this fixed score across the five frozen symbols. Long the highest score and short the lowest score, equal absolute notional, market-neutral target gross 0.75. Hold until next daily rebalance.

This is deliberately distinct from Phase069 residual momentum and Phase070/071 funding carry: no funding value enters signal selection and no validation/holdout evidence is permitted.

## Frozen universe and periods
Symbols: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT.
Training folds: 2023, 2024, 2025, chronological and individually reported. Existing training-only data may include causal lookback history but PnL begins 2023-01-01. Validation remains closed unless every training gate passes. Final holdout remains untouched.

## Frozen implementation
- signal lookback: 720 hours
- rebalance: daily 00:00 UTC
- signal inputs shifted so current/future bar cannot affect current position
- score = 720h log return / (std of hourly log returns over prior 720h * sqrt(720)); assets lacking full finite history are ineligible
- choose exactly one highest eligible score long and one lowest eligible score short; if fewer than 2 eligible assets, stay flat
- target gross: 0.75, split 0.375 long / 0.375 short
- no parameter search, rescue, threshold sweep, asset deletion, regime tuning, or post-result changes
- apply the repository's existing V98 Independent realistic transaction cost and funding accounting identically to prior phases; repeat under severe and supersevere cost assumptions

## Frozen training gates
PASS requires all simultaneously:
1. aggregate training total return > 0
2. aggregate daily Profit Factor > 1.05
3. aggregate max drawdown > -35%
4. each chronological fold 2023, 2024, 2025 has total return > 0
5. each fold daily Profit Factor > 1.00
6. severe-cost aggregate total return > 0
7. supersevere-cost aggregate total return > 0
8. no ruin / causal-integrity / isolation failure

Any failure => REJECT_NO_RESCUE and validation stays closed.

## Mandatory diagnostics
Report aggregate/fold return, CAGR, max drawdown, PF, payoff, win rate, positive/negative days, worst/best day, p01/p05/CVaR05, turnover/gross/net exposure; BASE/severe/supersevere; regime attribution; asset contribution and concentration; tail-day concentration; reproducibility hashes. Preserve final_holdout_untouched=true, v99_used=false, v16_used=false, parameter_search=false, rescue_allowed=false.