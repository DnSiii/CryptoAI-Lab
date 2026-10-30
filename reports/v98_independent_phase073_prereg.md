# V98 Independent Phase073 — pre-registration

## Hypothesis
Cross-sectional **medium-horizon reversal after volatility standardization** may capture overreaction that is structurally different from Phase072 momentum and from prior raw short-term reversal. At each daily decision point, compute each asset's lagged 14-day return divided by its lagged 14-day realized volatility. Long the lowest standardized-return asset and short the highest.

## Frozen specification before any Phase073 PnL
- Engine namespace: V98 Independent only.
- Universe: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT.
- Training only: existing chronological V98 training folds through 2025-12-31.
- Lookback: 336 hours (14 days), fixed.
- Signal information set: prices through t-1 only; realized volatility also ends at t-1.
- Score: lagged 14-day log return / lagged 14-day realized volatility.
- Direction: long minimum score, short maximum score.
- Rebalance: once daily at 00:00 UTC; positions held until next rebalance.
- Gross exposure: 0.75, split equally 0.375 long / 0.375 short.
- No parameter search, no threshold sweep, no rescue after PnL.
- Use the existing V98 exact execution/cost/funding model unchanged, including BASE, severe and supersevere scenarios.

## Mandatory training diagnostics and gate
Report aggregate and chronological folds 2023/2024/2025 with return, max drawdown, daily Profit Factor, payoff, win rate and positive days; severe/supersevere; regimes; concentration/tails; asset contribution; activation/exposure; reproducibility hashes.

Frozen PASS gate: aggregate return > 0; aggregate daily PF > 1.05; max drawdown >= -35%; every chronological fold return > 0 and PF > 1.00; severe return > 0; supersevere return > 0; no ruin. Any failure => REJECT_NO_RESCUE and validation remains closed. Only a complete PASS may freeze the candidate and permit a separately executed validation gate. Final holdout is not to be inspected at this stage.

## Independence / anti-overfit declaration
Phase073 is specified before observing any Phase073 PnL. Phase072's failure is used only to reject Phase072, not to optimize Phase073 parameters. V99 and V16 evidence must not be used to select or tune this hypothesis.
