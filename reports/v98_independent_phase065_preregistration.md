# V98 Independent — Phase065 preregistration

Status: **FROZEN BEFORE PNL**

## Independent hypothesis

Test whether a simple **cross-sectional 30-day residual momentum** effect exists across the same five liquid USD-M assets after removing the contemporaneous BTC market component. This is intentionally independent of Phase064 positioning/OI data: it uses only lagged hourly close returns from the already frozen V98 training-only crypto dataset and no derivatives positioning fields.

## Universe and chronology

Universe frozen: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT.
Training folds frozen and chronological: calendar 2023, 2024, 2025, evaluated separately and aggregate.
Validation remains closed until all training gates pass. Final holdout remains untouched.

## Signal frozen before PnL

At each UTC day boundary t:
1. Use information ending at t-1 only.
2. Compute each asset's trailing 30-calendar-day log return.
3. Compute BTC's trailing 30-calendar-day log return.
4. Residual score = asset 30d log return minus BTC 30d log return. BTC residual is therefore zero by construction.
5. Rank the four non-BTC assets by residual score.
6. Long the highest residual asset and short the lowest residual asset, equal absolute weights; BTC carries zero signal exposure.
7. Hold for the next UTC day and rebalance once daily.

No threshold search, alternate horizon, inversion, asset deletion, volatility filter, regime gate, rescue, or parameter sweep is allowed after seeing Phase065 returns.

## Exposure and execution

Gross exposure frozen at 0.75 (0.375 long + 0.375 short), market-neutral by construction at rebalance. Execution uses next-hour/next-period returns only after signal formation. Apply the same realistic V98 transaction-cost and funding accounting conventions already used by the independent lab. Report BASE, severe and supersevere cost scenarios.

## Mandatory diagnostics

Aggregate and each chronological fold must report: total return, CAGR, max drawdown, daily Profit Factor, payoff, win rate, positive/negative days, turnover, worst/best day, p01/p05 and CVaR05. Also report regime analysis, asset contribution/concentration, top/bottom tail contribution, exposure diagnostics, and reproducibility hashes where available.

## Frozen promotion gate

Training may advance to a separately frozen validation only if ALL are true under BASE:
- aggregate total return > 0
- aggregate daily PF > 1.05
- aggregate max drawdown > -35%
- each of 2023, 2024 and 2025 has total return > 0
- each fold daily PF > 1.02
- no ruin/data-integrity/causality failure

Severe and supersevere are mandatory robustness reports but do not override a failed BASE gate. A BASE failure is **REJECT_NO_RESCUE**.

## Isolation contract

V99 and V16 evidence, parameters, reports, branches, workflows and paper state must not be used to select/tune Phase065. No validation or final-holdout observation is permitted before the corresponding gate. This preregistration itself contains no Phase065 PnL.
