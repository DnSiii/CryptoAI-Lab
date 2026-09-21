# V98 Independent Phase075 — pre-registration

## Hypothesis
Cross-sectional **downside-risk asymmetry** may capture a defensive risk premium distinct from momentum, reversal, funding carry, and trend efficiency. Over a lagged 21-day window, estimate each asset's downside semivariance and upside semivariance from hourly log returns. Rank by downside share = downside_semivariance / (downside_semivariance + upside_semivariance). Long the asset with the lowest downside share and short the asset with the highest downside share.

## Frozen specification before any Phase075 PnL
- Engine namespace: V98 Independent only.
- Universe: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT.
- Training only: chronological V98 training folds through 2025-12-31.
- Lookback: 504 hours (21 days), fixed ex ante.
- Signal information set: hourly log returns through t-1 only.
- Downside semivariance: rolling mean of squared negative hourly log returns, with non-negative observations contributing zero.
- Upside semivariance: rolling mean of squared positive hourly log returns, with non-positive observations contributing zero.
- Score: downside_semivariance / (downside_semivariance + upside_semivariance).
- Direction: long minimum score (least downside-dominated), short maximum score (most downside-dominated).
- Rebalance: once daily at 00:00 UTC; hold until next rebalance.
- Gross exposure: 0.75, split 0.375 long / 0.375 short.
- No parameter search, no threshold sweep, no direction flip, no rescue after PnL.
- Existing V98 exact execution/cost/funding model unchanged, including BASE, severe and supersevere.

## Mandatory training diagnostics and gate
Report aggregate and chronological folds 2023/2024/2025 with return, max drawdown, daily Profit Factor, payoff, win rate and positive days; severe/supersevere; regimes; concentration/tails; asset contribution; activation/exposure; reproducibility hashes.

Frozen PASS gate: aggregate return > 0; aggregate daily PF > 1.05; max drawdown >= -35%; every chronological fold return > 0 and PF > 1.00; severe return > 0; supersevere return > 0; no ruin. Any failure => REJECT_NO_RESCUE and validation remains closed. Only complete PASS permits a separately executed validation gate. Final holdout remains untouched.

## Independence / anti-overfit declaration
Phase075 is a new downside/upside path-distribution family, not a parameter rescue of Phase074. It was specified before observing any Phase075 PnL. Phase074 evidence is used only to reject Phase074. V99 and V16 evidence must not be used to select or tune this hypothesis.