# V98 Independent Phase047 — Open-Interest Crowding Preregistration

Status: frozen before any Phase047 return result and before the external-metrics feasibility probe is harvested.

## Hypothesis

Rapid causal growth in aggregate USD-M open interest is a direct leverage/crowding mechanism not present in the candle/funding-only Phase003-046 feature set. Cross-sectionally, contracts with stronger lagged 24h open-interest growth are hypothesized to underperform contracts with weaker growth after dollar and BTC-beta neutralization, because crowded leverage creates liquidation/position-unwind pressure.

## Frozen signal

Use only Binance public USD-M metrics archive `sum_open_interest` observations that were timestamped strictly before the portfolio decision. For each eligible symbol, compute `log(OI[t-1] / OI[t-25])` on the 1h information grid (24h change, with the execution hour excluded). Cross-sectional score is the negative percentile rank of this value minus 0.5. No price return, volume, funding, trade-count, OHLC-shape, peer-correlation or V99 input enters the alpha score.

Universe remains the existing causal top-10 liquid V98 universe. BTCUSDT is excluded from alpha holdings. At each 24h rebalance, regress the cross-sectional score on intercept plus the existing causal 720h BTC beta and trade the residual. Gross target/cap = 0.75. Between rebalances positions are held constant.

## Data feasibility gate

Phase047 may execute only if `reports/v98_independent_external_metrics_probe.json` confirms a stable archive schema across the sampled 2023/2024/2025/2026 months and all required symbols, including an unambiguous timestamp and `sum_open_interest`. If this gate fails, Phase047 is not backtested; repair may address acquisition/schema only and may not alter the frozen economic signal.

The verified daily archive is 5-minute source data rather than a pre-aggregated hourly file. The frozen 1h information grid is therefore canonicalized mechanically by selecting the last valid positive OI observation timestamped inside each UTC hour. Raw invalid/nonpositive rows are retained in integrity evidence; they are never interpolated or backfilled, and an hour is unavailable if it has no prior valid observation inside that same hour. This clarification is acquisition/schema repair only: it does not change the 24h lag, signal sign, rebalance cadence, gross, neutralization, universe rule, or any return-dependent choice.

## Evaluation

Exactly the existing V98 protocol: chronological training folds; realistic funding and base transaction costs; severe and supersevere costs/funding; regime analysis; concentration/tails; max drawdown; Profit Factor; payoff; win rate; positive days; beta/dollar neutrality; reproducibility and causality invariants. Validation opens only if the frozen training gate passes. Final holdout remains untouched until training and validation both pass and the candidate is formally frozen.

## Anti-overfit restrictions

No sign inversion, alternate OI window, smoothing search, cadence search, gross/leverage search, thresholding, regime filtering, symbol subset search, combination with Phase046 or other failed signals, or rescue tuning after seeing Phase047 results. V99 evidence/state is excluded from selection. If the frozen specification fails, the Phase047 OI-growth crowding hypothesis is closed.
