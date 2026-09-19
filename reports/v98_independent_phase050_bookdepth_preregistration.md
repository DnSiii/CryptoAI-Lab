# V98 Independent — Phase050 Book-Depth Imbalance Preregistration

Status: FROZEN BEFORE ANY ALPHA/BACKTEST RESULT.

## Scientific rationale
Phase050 tests an orthogonal microstructure mechanism: persistent cross-sectional imbalance between bid-side and ask-side quoted USD-M futures depth. This is distinct from executed volume/taker flow, trade count/size, OHLC pressure, open interest, positioning and funding families already tested.

## Data gate
Source is Binance public USD-M daily `bookDepth` archive. The feasibility probe established the schema `timestamp, percentage, depth, notional` across BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT and BNBUSDT for 2023/2024/2025. Historical coverage/integrity must be audited before alpha evaluation. Days without adequate intraday coverage are missing, never forward-filled across gaps.

## Frozen signal
For each symbol and UTC day, use only observations available before the next trading decision. At each timestamp, define bid notional as the sum of `notional` for negative `percentage` levels and ask notional as the sum for positive `percentage` levels. Compute imbalance `(bid_notional - ask_notional) / (bid_notional + ask_notional)` and aggregate to the UTC-day median. The decision signal for day t is the previous completed UTC day's median imbalance (`shift(1)`), so no same-day/future book observation may affect a position.

Cross-sectionally rank the lagged imbalance each decision day. Long the strongest half and short the weakest half with equal-weight legs, dollar neutral, gross exposure 0.75. Preserve the existing V98 BTC-beta neutralization convention with 720h causal beta and 24h rebalance. No alternate percentage subset, smoothing window, sign inversion, threshold, gross, rebalance cadence or rescue tuning is permitted after results are observed.

## Evaluation discipline
Training only first. Preserve chronological folds and the existing V98 base realistic costs/funding plus severe and supersevere cost stresses. Report total return, max drawdown, Profit Factor, payoff, win rate, positive days, chronological fold results, regime results, concentration and tail/pathology diagnostics, data coverage and reproducibility hashes. Validation remains locked unless the frozen training gate passes. Final holdout remains untouched unless a candidate is formally frozen and reaches the final holdout gate.

## Rejection rule
Reject without rescue tuning if the existing V98 training/robustness gate fails, including inconsistent chronological folds, unacceptable drawdown/PF, severe/supersevere fragility, pathological concentration/tails, or inadequate point-in-time data coverage. A rejection closes this exact book-depth-imbalance specification; any future book-depth hypothesis must be economically distinct and separately preregistered.
