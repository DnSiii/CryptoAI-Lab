# V98 Independent — Phase064 Derivatives Positioning Mechanism Preregistration

Status: PREREGISTERED BEFORE ANY PHASE064 CRYPTO PNL.

## Evidence gate
Phase063 passed DATA_FEASIBILITY_ONLY with all 30/30 frozen Binance USD-M daily metrics archives and all 180/180 frozen field checks available. Phase063 computed no crypto return, alpha or PnL.

## Single frozen economic mechanism
Hypothesis: broad increases in aggregate USD-M open-interest value accompanied by broad net-long account positioning represent persistent risk demand; broad decreases accompanied by net-short positioning represent persistent risk-off demand.

Source: Binance public USD-M futures daily `metrics` archives only.
Fixed universe: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT.
Fixed source fields used by the mechanism:
- `sum_open_interest_value`
- `count_long_short_ratio`

No other Phase063 field is used for signal construction. The unused feasible fields are not searched.

## Frozen transformation and causality
For each symbol and UTC day t:
1. use the final finite metrics observation from archive day t-1; never day t;
2. compute 7-calendar-day open-interest-value growth as OI_value(t-1) / OI_value(t-8) - 1;
3. positioning direction is sign(count_long_short_ratio(t-1) - 1);
4. symbol vote is +1 only when OI growth > 0 and positioning direction > 0; -1 only when OI growth < 0 and positioning direction < 0; otherwise 0;
5. cross-sectional vote is sign(sum of the five symbol votes). A tied sum is 0.

The resulting cross-sectional vote is applied equally to the five fixed USD-M perpetuals at 00:00 UTC each day. Gross exposure is fixed at 0.75 when vote is non-zero (0.15 absolute exposure per symbol) and zero when tied. Positions are held until the next 00:00 UTC rebalance.

There is no threshold beyond zero, no ratio magnitude weighting, no volatility targeting, no symbol selection, no regime filter, no sign inversion, no alternative lookback, no cadence search, no exposure search and no rescue variant.

## Frozen training and execution contract
Training only: chronological folds 2023, 2024 and 2025 from the existing V98 Independent configuration/data boundary. Validation remains closed during Phase064 training. Final holdout remains untouched.

Execution must use the existing V98 Independent exact backtest path with realistic funding and the already-frozen base/severe/supersevere cost and funding stress definitions. No cost reduction is permitted.

Required reporting: aggregate and each chronological fold total return, Profit Factor, payoff, win rate, positive days and max drawdown; severe and supersevere aggregate metrics; regime metrics; concentration/tails; source/coverage diagnostics; reproducibility/invariant tests.

## Frozen training promotion gate
Phase064 may advance to a separate validation-only phase only if ALL conditions hold under BASE costs/funding:
- aggregate training total return > 0;
- aggregate daily Profit Factor > 1.05;
- aggregate max drawdown > -35%;
- each of 2023, 2024 and 2025 has total return > 0;
- each of 2023, 2024 and 2025 has daily Profit Factor > 1.02.

Severe and supersevere results are mandatory diagnostics and must be preserved even if weak; they cannot be used to retune Phase064. Any failure of the frozen BASE gate means REJECT_NO_RESCUE for this exact mechanism. Do not invert the signal, alter 7 days, change gross 0.75, drop symbols, change weighting, add a regime, choose another Phase063 field, or otherwise rescue after seeing PnL.

## Isolation contract
Engine namespace: V98 Independent only. V99 Frozen/research/workflows/reports/paper state and V16 Frozen are forbidden inputs and must not be modified. Prior V98 failures may not be used to tune this mechanism. Validation may be opened only after every training gate passes and the training evidence is frozen. Final holdout may be inspected only after training and validation pass and a candidate is formally frozen.