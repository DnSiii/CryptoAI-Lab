# V98 Independent Phase074 — pre-registration

## Hypothesis
Cross-sectional **trend-efficiency momentum** may distinguish persistent directional movement from noisy endpoint returns. For each asset, use the absolute lagged 28-day log return divided by the sum of absolute hourly log returns over the same lagged window as an efficiency ratio, then multiply that efficiency by the signed lagged 28-day log return. Long the highest score and short the lowest. This is a new path-quality signal rather than a rescue or parameter tweak of Phase073 reversal.

## Frozen specification before any Phase074 PnL
- Engine namespace: V98 Independent only.
- Universe: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT.
- Training only: chronological V98 training folds through 2025-12-31.
- Lookback: 672 hours (28 days), fixed ex ante.
- Signal information set: prices through t-1 only.
- Signed return: log(close[t-1] / close[t-673]).
- Efficiency ratio: abs(signed return) / sum(abs(hourly log returns)) over the same lagged 672-hour window.
- Score: signed return * efficiency ratio.
- Direction: long maximum score, short minimum score.
- Rebalance: once daily at 00:00 UTC; hold until next rebalance.
- Gross exposure: 0.75, split 0.375 long / 0.375 short.
- No parameter search, no threshold sweep, no direction flip, no rescue after PnL.
- Existing V98 exact execution/cost/funding model unchanged, including BASE, severe and supersevere.

## Mandatory training diagnostics and gate
Report aggregate and chronological folds 2023/2024/2025 with return, max drawdown, daily Profit Factor, payoff, win rate and positive days; severe/supersevere; regimes; concentration/tails; asset contribution; activation/exposure; reproducibility hashes.

Frozen PASS gate: aggregate return > 0; aggregate daily PF > 1.05; max drawdown >= -35%; every chronological fold return > 0 and PF > 1.00; severe return > 0; supersevere return > 0; no ruin. Any failure => REJECT_NO_RESCUE and validation remains closed. Only complete PASS permits a separately executed validation gate. Final holdout remains untouched.

## Independence / anti-overfit declaration
Phase074 was specified before observing any Phase074 PnL. Phase073 evidence is used only to reject Phase073, not to tune Phase074. V99 and V16 evidence must not be used to select or tune this hypothesis.
